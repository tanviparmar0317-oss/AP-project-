from PySide6.QtCore import QObject, Signal
import numpy as np
from models.data_model import DataModel, TcpWorker


class MainViewModel(QObject):
    status_changed = Signal(str)
    plot_data_ready = Signal(np.ndarray)
    connection_active = Signal(bool)

    def __init__(self):
        super().__init__()
        self.model = DataModel()
        self.worker = None
        self.is_connected = False

    def connect_to_server(self, port_str):
        try:
            port = int(port_str)
        except ValueError:
            self.status_changed.emit("Invalid port number.")
            return

        if self.is_connected:
            self.status_changed.emit("Already connected.")
            return

        self.model.reset()
        self.worker = TcpWorker("127.0.0.1", port)
        self.worker.new_data.connect(self._on_new_data)
        self.worker.connection_failed.connect(self._on_connection_failed)
        self.worker.disconnected.connect(self._on_disconnected)
        self.worker.start()
        self.is_connected = True
        self.connection_active.emit(True)
        self.status_changed.emit(f"Connecting to port {port}...")

    def disconnect_from_server(self):
        if self.worker and self.is_connected:
            self.worker.stop()

    def _on_new_data(self, chunk):
        self.model.append_chunk(chunk)
        data = self.model.get_original()
        self.plot_data_ready.emit(data)

    def _on_connection_failed(self, error_msg):
        self.is_connected = False
        self.connection_active.emit(False)
        self.status_changed.emit(f"Error: {error_msg}")

    def _on_disconnected(self):
        self.is_connected = False
        self.connection_active.emit(False)
        self.status_changed.emit("Disconnected.")

    def get_data_for_mode(self, mode):
        if mode == "RMS":
            return self.model.get_rms()
        elif mode == "Filtered":
            return self.model.get_filtered()
        else:
            return self.model.get_original()

    def get_buffer_fill(self):
        return self.model.buffer_fill
