import numpy as np
import threading


class DataBuffer:
    """
    Rolling buffer that stores incoming signal chunks.
    Holds the last max_samples samples for all 32 channels.
    Thread-safe using a lock.
    """

    NUM_CHANNELS = 32

    def __init__(self, max_samples=10000):
        self.max_samples = max_samples
        self._buffer = np.zeros((self.NUM_CHANNELS, max_samples))
        self._lock = threading.Lock()

    def append(self, chunk: np.ndarray):
        """
        Add a new chunk of shape (32, 18) to the buffer.
        Oldest samples are dropped when the buffer is full.
        """
        with self._lock:
            n_new = chunk.shape[1]
            self._buffer = np.roll(self._buffer, -n_new, axis=1)
            self._buffer[:, -n_new:] = chunk

    def get_channel(self, channel_index: int) -> np.ndarray:
        """Return all buffered samples for one channel (0-indexed)."""
        with self._lock:
            return self._buffer[channel_index].copy()

    def get_all_channels(self) -> np.ndarray:
        """Return the full buffer of shape (32, max_samples)."""
        with self._lock:
            return self._buffer.copy()

    def clear(self):
        """Reset the buffer to all zeros."""
        with self._lock:
            self._buffer = np.zeros((self.NUM_CHANNELS, self.max_samples))