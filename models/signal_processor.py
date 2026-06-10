import numpy as np
from scipy.signal import butter, sosfiltfilt


def compute_rms(signal: np.ndarray, window_size: int = 200) -> np.ndarray:
    """
    Compute the RMS (Root Mean Square) of a signal using a sliding window.
    Window size: 200 samples.
    Returns an array of the same length as the input.
    """
    output = np.zeros_like(signal)
    for i in range(len(signal)):
        start = max(0, i - window_size + 1)
        window = signal[start:i + 1]
        output[i] = np.sqrt(np.mean(window ** 2))
    return output


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