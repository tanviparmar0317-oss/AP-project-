import numpy as np
import threading


class DataBuffer:
    

    NUM_CHANNELS = 32

    def __init__(self, max_samples=10000):
        self.max_samples = max_samples
        self._buffer = np.zeros((self.NUM_CHANNELS, max_samples))
        self._lock = threading.Lock()

    def append(self, chunk: np.ndarray):
        with self._lock:
            n_new = chunk.shape[1]
            self._buffer = np.roll(self._buffer, -n_new, axis=1)
            self._buffer[:, -n_new:] = chunk

    def get_channel(self, channel_index: int) -> np.ndarray:
        
        with self._lock:
            return self._buffer[channel_index].copy()

    def get_all_channels(self) -> np.ndarray:
        with self._lock:
            return self._buffer.copy()

    def clear(self):
        with self._lock:
            self._buffer = np.zeros((self.NUM_CHANNELS, self.max_samples))