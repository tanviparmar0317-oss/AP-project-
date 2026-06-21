# TCP Signal Visualizer

**Group Members:** Kavy, Tanvi, Isha

---

## Project Overview
This repository contains a PySide6-based real-time TCP Signal Visualizer for 32-channel electromyogram (EMG) signals. It utilizes VisPy for hardware-accelerated high-performance plotting and Scipy/Numpy for real-time digital signal processing.

The project follows the **Model-View-ViewModel (MVVM)** architectural pattern:
- **View:** `views/main_view.py` handles the PySide6 UI components, the VisPy visualizer canvas, and the Matplotlib offline inspection window.
- **ViewModel:** `viewmodels/main_viewmodel.py` translates and transfers signals between the View and the Model, managing buffer states, connection states, and scaling data from microvolts to volts.
- **Model:** 
  - `models/tcp_client.py` runs a background thread to receive binary TCP streaming packets of size 4608 bytes.
  - `models/data_buffer.py` maintains a thread-safe rolling buffer of the signal data.
  - `models/signal_processor.py` implements high-performance signal processing calculations.

---

## How to Run

**1. Create & Activate Virtual Environment (Optional but recommended)**
```bash
python -m venv .venv
source .venv/bin/activate
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Run the TCP Server**
We have packaged the university's mock TCP data server directly in the repository under the `TCP_Server/` directory. It reads the local `recording.pkl` database relative to its path and streams simulated EMG signal data.
```bash
python TCP_Server/main.py
```

**4. Launch the Client Application**
In a new terminal window (with the virtual environment activated), start the main application:
```bash
python main.py
```

---

## Using the App

| Control | Type | Description |
|---|---|---|
| **Port** | Input Field | Specify the port where the TCP server is running (defaults to `12345`). |
| **Connect** | Button | Connects to the local TCP server, starts the PySide6 refresh timer, and begins live plotting. |
| **Disconnect** | Button | Closes the TCP socket connection and pauses the visualizer. |
| **Mode** | Radio Buttons | Toggle between: <br>• **Original:** Raw incoming data.<br>• **RMS:** Sliding Root-Mean-Square calculation.<br>• **Filtered:** Real-time Bandpass Filter. |
| **Channel** | Dropdown | Select which of the 32 channels to display in Single Channel view. |
| **Plot All Channels / Single Channel View** | Button | Toggles between displaying a single channel and showing a stacked vertical layout of all 32 channels offset dynamically. |
| **Offline Inspect** | Button | Enabled when disconnected. Opens a static Matplotlib plot of the buffered signal data for detailed review. |

---

## Signal Processing Details

### RMS (Root Mean Square)
A rolling RMS is computed per channel using a sliding window:
- **Window size:** 200 samples
- **Equation:** $RMS[i] = \sqrt{\frac{1}{W} \sum_{k=0}^{W-1} x[i-k]^2}$ where $W = 200$.

### Bandpass Filter
A digital filter designed to remove high-frequency noise and low-frequency DC offset:
- **Filter Type:** 4th-order Butterworth bandpass filter (`scipy.signal.butter`).
- **Low Cutoff:** 20.0 Hz
- **High Cutoff:** 500.0 Hz
- **Sampling Frequency ($f_s$):** 2048.0 Hz
- **Implementation:** Implemented using Second-Order Sections (SOS) via `scipy.signal.sosfiltfilt` for numerical stability and zero-phase distortion.

---

## Project Directory Tree

```text
AP-project-/
├── main.py                     # Application entry point & global stylesheet
├── Constants.py                # Shared parameters (channels, buffers, sample rates)
├── requirements.txt            # Python dependencies
├── README.md                   # This instruction manual
├── recording.pkl               # Database containing biosignal data
├── TCP_Server/
│   └── main.py                 # Bundled mock TCP server with relative path loading
├── models/
│   ├── __init__.py
│   ├── tcp_client.py           # Background TCP listener and buffer parsing
│   ├── data_buffer.py          # Thread-safe rolling signal buffer
│   └── signal_processor.py     # Butter bandpass and RMS functions
├── viewmodels/
│   ├── __init__.py
│   └── main_viewmodel.py       # Intermediary scaling & mode router
└── views/
    └── main_view.py            # User interface layout & VisPy/Matplotlib visualization
```
