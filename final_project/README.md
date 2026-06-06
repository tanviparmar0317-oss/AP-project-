# TCP Signal Visualizer

**Group Members:** Kavy, Tanvi, Isha

---

## How to Run

**1. Install dependencies**

```bash
pip install -r requirements.txt
```

**2. Start your TCP server** on localhost at your chosen port (e.g. 9000).
The server must stream raw `float64` data in packets of exactly **4608 bytes**
(32 channels × 18 samples × 8 bytes each).

**3. Launch the app**

```bash
python main.py
```

Run this from inside the `final_project/` directory.

---

## Using the App

| Control | What it does |
|---|---|
| Port input | Enter the TCP port your server is running on |
| Connect | Opens the TCP connection and starts live plotting |
| Disconnect | Stops streaming; enables offline inspection |
| Mode dropdown | Switch between Original, RMS, and Filtered signal views |
| Channel dropdown | Pick one of 32 channels to display live |
| Plot All Channels | Toggles a stacked overview of all 32 channels at once |
| Offline Inspect | Opens a static Matplotlib window for recorded data review |

---

## Signal Processing Details

### RMS
A rolling RMS is computed per channel with a window of **50 samples**.
For sample `i`: `RMS[i] = sqrt(mean(signal[i-49 : i+1]²))`

### Bandpass Filter
A **4th-order Butterworth bandpass filter** is applied using `scipy.signal.butter`
and `sosfilt` (second-order sections for numerical stability).

- **Low cutoff:** 1.0 Hz
- **High cutoff:** 40.0 Hz
- **Sample rate:** 250 Hz

This passes typical EEG/biosignal frequency content and removes DC drift and
high-frequency noise.

---

## Project Structure

```
final_project/
├── main.py                    ← App entry point
├── requirements.txt
├── README.md
├── models/
│   └── data_model.py          ← TCP thread, rolling buffer, signal processing
├── viewmodels/
│   └── main_viewmodel.py      ← Routes data between model and view
└── views/
    └── main_view.py           ← PySide6 GUI, VisPy live plot, Matplotlib offline
```

Architecture follows **MVVM**: the View knows nothing about TCP or data math,
the Model knows nothing about the GUI.
