import numpy as np
from scipy.signal import butter, sosfiltfilt


def compute_rms(signal: np.ndarray, window_size: int = 200) -> np.ndarray:
    """
    Compute the RMS (Root Mean Square) of a signal using a sliding window.
    Window size: 200 samples.
    Returns an array of the same length as the input.
    """
    squared = signal ** 2
    cumsum = np.cumsum(squared)
    sum_window = cumsum.copy()
    sum_window[window_size:] -= cumsum[:-window_size]
    counts = np.minimum(np.arange(1, len(signal) + 1), window_size)
    return np.sqrt(sum_window / counts)


def compute_filtered(signal: np.ndarray, fs: float = 2048.0) -> np.ndarray:
    """
    Apply a Butterworth bandpass filter to the signal.
    Parameters:
        - Bandpass: 20 Hz to 500 Hz
        - Order: 4
        - Sample rate (fs): 2048 Hz (typical for EMG/biomedical signals)
    """
    lowcut = 20.0
    highcut = 500.0
    sos = butter(4, [lowcut, highcut], btype='bandpass', fs=fs, output='sos')
    return sosfiltfilt(sos, signal)