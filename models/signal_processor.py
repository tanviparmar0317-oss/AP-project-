import numpy as np
from scipy.signal import butter, sosfiltfilt


# ---------------------------------------------------------------------------
# Filter coefficients pre-computed at module load time.
# butter() is expensive — rebuilding it on every call would waste CPU cycles
# on every Qt timer tick. The SOS (second-order sections) form is used
# instead of the 'ba' form because it is numerically stable for high-order
# filters and avoids coefficient blow-up near the Nyquist frequency.
# ---------------------------------------------------------------------------
_FS = 2048.0          # sampling frequency in Hz
_LOWCUT = 20.0        # high-pass cutoff: removes DC drift and motion artefacts
_HIGHCUT = 500.0      # low-pass cutoff: removes high-frequency noise above EMG band
_ORDER = 4            # 4th-order Butterworth: maximally flat passband, no ripple
_SOS = butter(_ORDER, [_LOWCUT, _HIGHCUT], btype='bandpass', fs=_FS, output='sos')

# sosfiltfilt pads the signal before filtering. The minimum signal length
# required is padlen = 3 * (2 * filter_order) - 1. For order 4: 3*8-1 = 23.
# We use 27 as a safe margin.
_MIN_FILTER_SAMPLES = 27


def compute_rms(signal: np.ndarray, window_size: int = 200) -> np.ndarray:
    """
    Compute a sliding-window RMS (Root Mean Square) envelope.

    Parameters
    ----------
    signal : np.ndarray, shape (N,)
        Input signal in volts (or raw units).
    window_size : int
        Number of samples per RMS window. Default 200 samples at 2048 Hz
        ≈ 97.7 ms — chosen to capture one full EMG burst envelope without
        over-smoothing fast transients.

    Returns
    -------
    np.ndarray, shape (N,)
        RMS envelope. The first (window_size - 1) samples use a shrinking
        window so the output is always the same length as the input.

    Notes
    -----
    Uses cumulative sum for O(N) efficiency instead of a naive O(N*W) loop.
    Formula: RMS[i] = sqrt( mean( x[max(0,i-W+1) : i+1] ** 2 ) )
    """
    squared = signal ** 2
    cumsum = np.cumsum(squared)
    sum_window = cumsum.copy()
    sum_window[window_size:] -= cumsum[:-window_size]
    counts = np.minimum(np.arange(1, len(signal) + 1), window_size)
    return np.sqrt(sum_window / counts)


def compute_filtered(signal: np.ndarray) -> np.ndarray:
    """
    Apply a zero-phase 4th-order Butterworth bandpass filter (20–500 Hz).

    Parameters
    ----------
    signal : np.ndarray, shape (N,)
        Input signal in volts (or raw units).

    Returns
    -------
    np.ndarray, shape (N,)
        Filtered signal. Returns the raw signal unchanged if fewer than
        27 samples are available — sosfiltfilt raises a ValueError for
        very short signals during the first seconds of streaming.

    Notes
    -----
    sosfiltfilt applies the filter twice (forward + backward pass), which
    produces zero group delay — no time shift in the output. This is
    critical for accurate offline inspection and correct EMG envelope timing.

    Filter parameters:
        Type      : Butterworth bandpass
        Order     : 4
        Low cut   : 20.0 Hz  (removes DC drift and motion artefacts)
        High cut  : 500.0 Hz (removes noise above the EMG frequency band)
        Sample fs : 2048.0 Hz
        Form      : SOS (numerically stable, avoids ba-form blow-up)
    """
    if len(signal) < _MIN_FILTER_SAMPLES:
        return signal   # not enough data yet — return raw to avoid crash
    return sosfiltfilt(_SOS, signal)