import threading
import numpy as np
from PySide6.QtCore import QObject, Signal

from models.tcp_client import TCPClient
from models.data_buffer import DataBuffer
from models.signal_processor import compute_rms, compute_filtered
from Constants import NUM_CHANNELS, BUFFER_SIZE, SAMPLE_RATE

class MainViewModel(QObject):
    status_changed = Signal(str)
    connection_active = Signal(bool)

    def __init__(self):
        super().__init__()
        self.buffer = DataBuffer(max_samples=BUFFER_SIZE)
        self.client = TCPClient(
            on_data_callback=self._on_data_received,
            on_status_callback=self._on_status_updated
        )
        self._fill_count = 0
        self._fill_lock = threading.Lock()

    def _on_data_received(self, chunk: np.ndarray):
        self.buffer.append(chunk)
        with self._fill_lock:
            self._fill_count = min(self._fill_count + chunk.shape[1], BUFFER_SIZE)

    def _on_status_updated(self, msg: str):
        self.status_changed.emit(msg)
        if msg == "Connected":
            self.connection_active.emit(True)
        elif msg == "Disconnected" or any(err in msg for err in ["closed", "lost", "failed", "Could not connect"]):
            self.connection_active.emit(False)

    def connect_to_server(self, port_str: str):
        try:
            port = int(port_str)
            if not (0 <= port <= 65535):
                raise ValueError()
            self.clear_buffer()
            self.status_changed.emit("Connecting...")
            self.client.connect("127.0.0.1", port)
        except ValueError:
            self.status_changed.emit("Invalid Port")
            self.connection_active.emit(False)

    def disconnect_from_server(self):
        self.client.disconnect()

    def get_data_for_mode(self, mode: str) -> np.ndarray:
        # The raw recording is in microvolts. Scale to Volts to match the GUI camera.
        raw_data = self.buffer.get_all_channels() / 1e6

        if mode == "Original":
            return raw_data
        elif mode == "RMS":
            rms_data = np.zeros_like(raw_data)
            for i in range(NUM_CHANNELS):
                rms_data[i] = compute_rms(raw_data[i])
            return rms_data
        elif mode == "Filtered":
            filtered_data = np.zeros_like(raw_data)
            for i in range(NUM_CHANNELS):
                filtered_data[i] = compute_filtered(raw_data[i], fs=SAMPLE_RATE)
            return filtered_data
        return raw_data

    def get_buffer_fill(self) -> int:
        with self._fill_lock:
            return self._fill_count

    def clear_buffer(self):
        self.buffer.clear()
        with self._fill_lock:
            self._fill_count = 0
