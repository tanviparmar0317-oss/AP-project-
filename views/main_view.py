import numpy as np
import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QSizePolicy
)
from PySide6.QtCore import QTimer, Qt

from vispy import scene
from vispy.scene import visuals

from viewmodels.main_viewmodel import MainViewModel
from Constants import NUM_CHANNELS, BUFFER_SIZE, SAMPLE_RATE


MODES = ["Original", "RMS", "Filtered"]
CHANNEL_ITEMS = [str(i) for i in range(1, NUM_CHANNELS + 1)]
PLOT_INTERVAL_MS = 50
TIME_AXIS = np.linspace(-BUFFER_SIZE / SAMPLE_RATE, 0, BUFFER_SIZE)
CHANNEL_OFFSET = 0.0002
ALL_CHANNEL_OFFSET = 0.00015


class MainView(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TCP Signal Visualizer")
        self.resize(1200, 750)

        self.viewmodel = MainViewModel()
        self.show_all_channels = False

        self._build_ui()
        self._connect_signals()

        self.plot_timer = QTimer()
        self.plot_timer.setInterval(PLOT_INTERVAL_MS)
        self.plot_timer.timeout.connect(self._refresh_vispy)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)

        top_bar = QHBoxLayout()

        self.port_input = QLineEdit("9000")
        self.port_input.setFixedWidth(80)
        self.port_input.setPlaceholderText("Port")

        self.connect_btn = QPushButton("Connect")
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.setEnabled(False)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(MODES)

        self.channel_combo = QComboBox()
        self.channel_combo.addItems(CHANNEL_ITEMS)

        self.plot_all_btn = QPushButton("Plot All Channels")
        self.offline_btn = QPushButton("Offline Inspect")
        self.offline_btn.setEnabled(False)

        self.status_label = QLabel("Status: Idle")
        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        top_bar.addWidget(QLabel("Port:"))
        top_bar.addWidget(self.port_input)
        top_bar.addWidget(self.connect_btn)
        top_bar.addWidget(self.disconnect_btn)
        top_bar.addSpacing(20)
        top_bar.addWidget(QLabel("Mode:"))
        top_bar.addWidget(self.mode_combo)
        top_bar.addWidget(QLabel("Channel:"))
        top_bar.addWidget(self.channel_combo)
        top_bar.addSpacing(20)
        top_bar.addWidget(self.plot_all_btn)
        top_bar.addWidget(self.offline_btn)
        top_bar.addStretch()
        top_bar.addWidget(self.status_label)

        root_layout.addLayout(top_bar)

        self.canvas = scene.SceneCanvas(keys="interactive", show=False, bgcolor="white")
        self.canvas.native.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root_layout.addWidget(self.canvas.native)

        self.view = self.canvas.central_widget.add_view()
        self.view.camera = scene.PanZoomCamera(aspect=None)

        self.line = visuals.Line(
            pos=np.column_stack([TIME_AXIS, np.zeros(BUFFER_SIZE)]),
            color="blue",
            width=1,
            parent=self.view.scene
        )

        self.all_lines = []
        colors = plt.cm.Blues(np.linspace(0.5, 0.9, NUM_CHANNELS))
        for i in range(NUM_CHANNELS):
            color = tuple(colors[i][:3]) + (1.0,)
            ln = visuals.Line(
                pos=np.column_stack([TIME_AXIS, np.zeros(BUFFER_SIZE)]),
                color=color,
                width=1,
                parent=self.view.scene
            )
            ln.visible = False
            self.all_lines.append(ln)

        x_axis = scene.Axis(
            pos=[[TIME_AXIS[0], 0], [TIME_AXIS[-1], 0]],
            tick_direction=(0, -1),
            font_size=8,
            axis_color="black",
            tick_color="black",
            text_color="black",
            parent=self.view.scene
        )

        self.view.camera.set_range(
            x=(TIME_AXIS[0], TIME_AXIS[-1]),
            y=(-0.001, 0.001)
        )

    def _connect_signals(self):
        self.connect_btn.clicked.connect(self._on_connect)
        self.disconnect_btn.clicked.connect(self._on_disconnect)
        self.plot_all_btn.clicked.connect(self._toggle_all_channels)
        self.offline_btn.clicked.connect(self._open_offline_window)

        self.viewmodel.status_changed.connect(self._on_status_changed)
        self.viewmodel.connection_active.connect(self._on_connection_active)

    def _on_connect(self):
        self.viewmodel.connect_to_server(self.port_input.text())
        self.plot_timer.start()

    def _on_disconnect(self):
        self.viewmodel.disconnect_from_server()
        self.plot_timer.stop()

    def _on_status_changed(self, msg):
        self.status_label.setText(f"Status: {msg}")

    def _on_connection_active(self, active):
        self.connect_btn.setEnabled(not active)
        self.disconnect_btn.setEnabled(active)
        self.offline_btn.setEnabled(not active)
        if not active:
            self.plot_timer.stop()

    def _refresh_vispy(self):
        mode = self.mode_combo.currentText()
        data = self.viewmodel.get_data_for_mode(mode)

        if self.show_all_channels:
            self.line.visible = False
            for i, ln in enumerate(self.all_lines):
                signal = data[i] + i * ALL_CHANNEL_OFFSET
                ln.set_data(pos=np.column_stack([TIME_AXIS, signal]))
                ln.visible = True
        else:
            for ln in self.all_lines:
                ln.visible = False
            ch = self.channel_combo.currentIndex()
            signal = data[ch]
            self.line.set_data(pos=np.column_stack([TIME_AXIS, signal]))
            self.line.visible = True

    def _toggle_all_channels(self):
        self.show_all_channels = not self.show_all_channels
        label = "Single Channel View" if self.show_all_channels else "Plot All Channels"
        self.plot_all_btn.setText(label)
        self.channel_combo.setEnabled(not self.show_all_channels)

    def _open_offline_window(self):
        win = OfflineWindow(self.viewmodel, self)
        win.show()


class OfflineWindow(QWidget):
    def __init__(self, viewmodel, parent=None):
        super().__init__(parent)
        self.viewmodel = viewmodel
        self.setWindowTitle("Offline Signal Inspector")
        self.resize(900, 550)
        self.setWindowFlags(Qt.Window)

        layout = QVBoxLayout(self)

        controls = QHBoxLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(MODES)
        self.channel_combo = QComboBox()
        self.channel_combo.addItems(CHANNEL_ITEMS)
        self.plot_btn = QPushButton("Plot")

        controls.addWidget(QLabel("Mode:"))
        controls.addWidget(self.mode_combo)
        controls.addWidget(QLabel("Channel:"))
        controls.addWidget(self.channel_combo)
        controls.addWidget(self.plot_btn)
        controls.addStretch()
        layout.addLayout(controls)

        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
        self.fig, self.ax = plt.subplots(figsize=(9, 4))
        self.mpl_canvas = FigureCanvas(self.fig)
        layout.addWidget(self.mpl_canvas)

        self.plot_btn.clicked.connect(self._do_plot)
        self._do_plot()

    def _do_plot(self):
        mode = self.mode_combo.currentText()
        ch = self.channel_combo.currentIndex()
        data = self.viewmodel.get_data_for_mode(mode)
        signal = data[ch]

        fill = self.viewmodel.get_buffer_fill()
        if fill < BUFFER_SIZE:
            signal = signal[-fill:] if fill > 0 else signal
            t = np.linspace(-fill / SAMPLE_RATE, 0, len(signal))
        else:
            t = TIME_AXIS

        self.ax.clear()
        self.ax.plot(t, signal, color="steelblue", linewidth=0.8)
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Amplitude")
        self.ax.set_title(f"Channel {ch + 1} — {mode}")
        self.ax.grid(True, alpha=0.3)
        self.fig.tight_layout()
        self.mpl_canvas.draw()
