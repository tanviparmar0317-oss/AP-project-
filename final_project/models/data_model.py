import socket
import numpy as np
from scipy.signal import butter, sosfilt
from PySide6.QtCore import QThread, Signal


NUM_CHANNELS = 32
SAMPLES_PER_CHUNK = 18
BYTES_PER_PACKET = NUM_CHANNELS * SAMPLES_PER_CHUNK * 8
BUFFER_SECONDS = 10
SAMPLE_RATE = 250
BUFFER_SIZE = BUFFER_SECONDS * SAMPLE_RATE


def make_bandpass_filter(lowcut=1.0, highcut=40.0, fs=SAMPLE_RATE, order=4):
    nyq = fs / 2.0
    low = lowcut / nyq
    high = highcut / nyq
    sos = butter(order, [low, high], btype='band', output='sos')
    return sos


def compute_rms(data, window=50):
    rms_out = np.zeros_like(data)
    for ch in range(data.shape[0]):
        signal = data[ch]
        for i in range(len(signal)):
            start = max(0, i - window + 1)
            rms_out[ch, i] = np.sqrt(np.mean(signal[start:i+1] ** 2))
    return rms_out


def compute_filtered(data, sos):
    filtered = np.zeros_like(data)
    for ch in range(data.shape[0]):
        filtered[ch] = sosfilt(sos, data[ch])
    return filtered


class TcpWorker(QThread):
    new_data = Signal(np.ndarray)
    connection_failed = Signal(str)
    disconnected = Signal()

    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self._running = False
        self._sock = None

    def run(self):
        self._running = True
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(5.0)
            self._sock.connect((self.host, self.port))
            self._sock.settimeout(2.0)
        except OSError as e:
            self.connection_failed.emit(str(e))
            return

        raw_buffer = b""
        while self._running:
            try:
                chunk = self._sock.recv(4096)
                if not chunk:
                    break
                raw_buffer += chunk
                while len(raw_buffer) >= BYTES_PER_PACKET:
                    packet = raw_buffer[:BYTES_PER_PACKET]
                    raw_buffer = raw_buffer[BYTES_PER_PACKET:]
                    arr = np.frombuffer(packet, dtype=np.float64)
                    arr = arr.reshape((NUM_CHANNELS, SAMPLES_PER_CHUNK))
                    self.new_data.emit(arr)
            except socket.timeout:
                continue
            except OSError as e:
                if self._running:
                    self.connection_failed.emit(str(e))
                break

        if self._sock:
            self._sock.close()
        self.disconnected.emit()

    def stop(self):
        self._running = False
        if self._sock:
            try:
                self._sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass


class DataModel:
    def __init__(self):
        self.sos = make_bandpass_filter()
        self.rolling_buffer = np.zeros((NUM_CHANNELS, BUFFER_SIZE))
        self.buffer_fill = 0

    def append_chunk(self, chunk):
        n = chunk.shape[1]
        self.rolling_buffer = np.roll(self.rolling_buffer, -n, axis=1)
        self.rolling_buffer[:, -n:] = chunk
        self.buffer_fill = min(self.buffer_fill + n, BUFFER_SIZE)

    def get_original(self):
        return self.rolling_buffer.copy()

    def get_rms(self):
        return compute_rms(self.rolling_buffer)

    def get_filtered(self):
        return compute_filtered(self.rolling_buffer, self.sos)

    def reset(self):
        self.rolling_buffer = np.zeros((NUM_CHANNELS, BUFFER_SIZE))
        self.buffer_fill = 0
