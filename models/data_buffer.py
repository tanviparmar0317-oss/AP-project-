import numpy as np
import threading


class DataBuffer:
    """
    Thread-safe rolling buffer for incoming (32, 18) EMG chunks.

    The TCP receive thread writes chunks via append(); the Qt timer thread
    reads via get_channel(), get_all_channels(), or get_snapshot(). A
    threading.Lock protects all array accesses to prevent race conditions
    between the two threads.

    get_snapshot() returns a full copy taken atomically under the lock,
    so the caller never holds a reference to the internal array and cannot
    see a mid-write state.
    """

    NUM_CHANNELS = 32

    def __init__(self, max_samples: int = 10000):
        """
        Initialise the buffer with zeros.

        Parameters
        ----------
        max_samples : int
            Number of samples to keep per channel in the rolling window.
            At 2048 Hz, 10000 samples ≈ 4.9 seconds of history.
        """
        self.max_samples = max_samples
        self._buffer = np.zeros((self.NUM_CHANNELS, max_samples))
        self._lock = threading.Lock()

    def append(self, chunk: np.ndarray):
        """
        Append a new (32, 18) chunk to the rolling buffer.

        Shifts existing data left by n_new columns and writes the new
        chunk into the rightmost columns, maintaining a fixed buffer size.
        """
        with self._lock:
            n_new = chunk.shape[1]
            self._buffer = np.roll(self._buffer, -n_new, axis=1)
            self._buffer[:, -n_new:] = chunk

    def get_channel(self, channel_index: int) -> np.ndarray:
        """
        Return a thread-safe copy of a single channel's buffer.

        Parameters
        ----------
        channel_index : int
            Channel to retrieve (0-indexed, 0–31).
        """
        with self._lock:
            return self._buffer[channel_index].copy()

    def get_all_channels(self) -> np.ndarray:
        """Return a thread-safe copy of all channels (shape: 32 x max_samples)."""
        with self._lock:
            return self._buffer.copy()

    def get_snapshot(self) -> np.ndarray:
        """
        Return a thread-safe atomic snapshot of the full buffer.

        Equivalent to get_all_channels() but named explicitly to signal
        intent: the copy is taken in one lock acquisition so all 32 rows
        reflect the same point in time. Use this in the ViewModel timer
        tick to avoid reading a partially-updated buffer.
        """
        with self._lock:
            return self._buffer.copy()

    def clear(self):
        """Reset the buffer to all zeros."""
        with self._lock:
            self._buffer = np.zeros((self.NUM_CHANNELS, self.max_samples))