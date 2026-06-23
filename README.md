# TCP Signal Visualizer

> A PySide6 desktop application for real-time visualization and offline inspection of 32-channel EMG signals streamed over TCP.

**Group:** Kavy · Tanvi · Isha — Applied Programming 2026, FAU Erlangen-Nürnberg

---

## Table of Contents

- [Project Overview](#project-overview)
- [Team Responsibilities](#team-responsibilities)
- [Architecture (MVVM)](#architecture-mvvm)
- [Signal Processing](#signal-processing)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [Using the App](#using-the-app)
- [Project Structure](#project-structure)
- [Dependencies](#dependencies)

---

## Project Overview

This application connects as a TCP client to a mock EMG data server, receives a continuous stream of **32-channel × 18-sample float64 packets** (4608 bytes each), and visualizes the incoming signal in real time using **VisPy**. After disconnecting, the buffered recording can be inspected offline using **Matplotlib**.

Key features:

- Live rolling-window VisPy plot for a single selected channel
- Stacked all-channel overview with dynamic vertical offsets
- Three signal modes: raw, RMS, and bandpass-filtered
- Offline Matplotlib inspection of the full recorded buffer
- Full MVVM separation — View never touches the TCP socket directly
- Graceful error handling for connection failures, wrong ports, and missing data

---

## Team Responsibilities

| Member | Primary Role | Contributions |
|--------|-------------|---------------|
| **Tanvi** | Backend Engineer | Implemented the entire Model layer: TCP client with background threading (`tcp_client.py`), thread-safe rolling buffer (`data_buffer.py`), RMS and Butterworth bandpass filter signal processing (`signal_processor.py`). Co-responsible for error handling together with Kavy. |
| **Kavy** | Frontend Engineer | Implemented the entire View layer: VisPy live plot canvas, single-channel and all-channels stacked view, Matplotlib offline inspection window, and the PySide6 UI layout (`main_view.py`). Also built and integrated the mock TCP server (`TCP_Server/main.py`). Co-responsible for error handling together with Tanvi. |
| **Isha** | Integration & Documentation | Set up and maintained the GitHub repository, implemented the ViewModel layer connecting View and Model (`main_viewmodel.py`), defined shared application constants (`Constants.py`), wrote the application entry point (`main.py`), and authored the project documentation (`README.md`). |

---

## Architecture (MVVM)

The application strictly follows the **Model-View-ViewModel** pattern to ensure clean separation of concerns.

```
┌─────────────────────────────────────────────────────────────┐
│                          VIEW                               │
│  views/main_view.py                                         │
│  · PySide6 widgets (buttons, dropdowns, status label)       │
│  · VisPy canvas for live plotting                           │
│  · Matplotlib window for offline inspection                 │
│  · Calls ViewModel methods — never touches TCP directly     │
└──────────────────────────┬──────────────────────────────────┘
                           │  Qt Signals / method calls
┌──────────────────────────▼──────────────────────────────────┐
│                       VIEWMODEL                             │
│  viewmodels/main_viewmodel.py                               │
│  · Manages connection state and buffer state                │
│  · Routes signal mode selection (Original / RMS / Filtered) │
│  · Scales raw microvolt data to volts for display           │
│  · Emits Qt Signals to notify View of new data              │
└──────────────────────────┬──────────────────────────────────┘
                           │  method calls
┌──────────────────────────▼──────────────────────────────────┐
│                         MODEL                               │
│  models/tcp_client.py     — background thread, TCP socket   │
│  models/data_buffer.py    — thread-safe rolling buffer      │
│  models/signal_processor.py — RMS and bandpass filter       │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. `TCPClient` receives 4608-byte packets in a background thread and calls `on_data_callback(chunk)`.
2. `DataBuffer` appends each `(32, 18)` chunk into a thread-safe rolling NumPy buffer.
3. `MainViewModel` reads the buffer on a Qt timer tick, applies the selected signal processing mode, and emits `data_ready` to the View.
4. `MainView` receives the processed array and updates the VisPy canvas.

---

## Signal Processing

### Data Format

Each TCP packet contains:

```
32 channels × 18 samples × 8 bytes (float64) = 4608 bytes
```

Packets are reconstructed with:

```python
chunk = np.frombuffer(raw_bytes, dtype=np.float64).reshape(32, 18)
```

### RMS — Root Mean Square

A sliding-window RMS is computed per channel over the rolling buffer:

**Window size:** 200 samples

\[
\text{RMS}[i] = \sqrt{\frac{1}{W} \sum_{k=0}^{W-1} x[i-k]^2}, \quad W = 200
\]

### Bandpass Filter

Low-frequency DC drift and high-frequency noise above the EMG band are removed using:

| Parameter | Value |
|-----------|-------|
| Filter type | 4th-order Butterworth bandpass |
| Low cutoff | 20.0 Hz |
| High cutoff | 500.0 Hz |
| Sampling frequency | 2048.0 Hz |
| Implementation | `scipy.signal.sosfiltfilt` (zero-phase, SOS form) |

Zero-phase filtering via `sosfiltfilt` ensures no time-domain shift in the signal, which is critical for accurate offline inspection.

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/tanviparmar0317-oss/AP-project-.git
cd AP-project-
```

### 2. Create and activate a virtual environment (recommended)

```bash
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Running the Application

The TCP server must be running **before** launching the client application.

### Terminal 1 — Start the TCP server

```bash
source .venv/bin/activate
python TCP_Server/main.py
```

The server reads `recording.pkl` from its own directory and begins streaming simulated EMG data on port `12345`.

### Terminal 2 — Launch the visualizer

```bash
source .venv/bin/activate
python main.py
```

The GUI window will open. Enter port `12345` and click **Connect**.

---

## Using the App

### Controls

| Control | Type | Description |
|---------|------|-------------|
| **Port** | Input field | TCP port number (default: `12345`) |
| **Connect** | Button | Connects to the server and starts live streaming |
| **Disconnect** | Button | Closes the connection and pauses the plot |
| **Mode** | Radio buttons | Switch between **Original**, **RMS**, and **Filtered** signal |
| **Channel** | Dropdown | Select one of 32 channels for single-channel view |
| **Plot All Channels / Single Channel View** | Toggle button | Switch between stacked 32-channel overview and single-channel view |
| **Offline Inspect** | Button | Open static Matplotlib plot of the recorded buffer (available after disconnect) |
| **Status bar** | Label | Displays connection state and error messages |

### Typical Workflow

1. Start the TCP server in Terminal 1.
2. Run `main.py` in Terminal 2 — the GUI opens.
3. Enter port `12345` → click **Connect** → live signal appears.
4. Use **Channel** dropdown and **Mode** radio buttons to explore the data.
5. Click **Plot All Channels** for a full overview of all 32 channels.
6. Click **Disconnect** → then **Offline Inspect** to open the Matplotlib inspection window.
7. In the offline window, select channel and mode to review the full recorded session.

### Error Handling

The application handles the following situations without crashing:

- **Wrong port / server not running** → status label shows `"Could not connect: [Errno 61] Connection refused"`
- **Connection lost mid-stream** → status label updates, streaming stops cleanly
- **Offline Inspect with no data** → status label shows `"No data available for offline plotting"`
- **Invalid channel selection** → input is validated before passing to the ViewModel

---

## Project Structure

```
AP-project-/
├── main.py                     # Application entry point and global Qt stylesheet
├── Constants.py                # Shared parameters: channels, buffer size, sample rate
├── requirements.txt            # All Python dependencies
├── README.md                   # This file
├── recording.pkl               # Mock EMG biosignal database (used by TCP server)
├── TCP_Server/
│   └── main.py                 # Bundled mock TCP server — reads recording.pkl and streams data
├── models/
│   ├── __init__.py
│   ├── tcp_client.py           # Background TCP listener thread and packet reconstruction
│   ├── data_buffer.py          # Thread-safe rolling NumPy buffer for incoming chunks
│   └── signal_processor.py    # Butterworth bandpass filter and sliding-window RMS
├── viewmodels/
│   ├── __init__.py
│   └── main_viewmodel.py       # State management, mode routing, µV→V scaling, Qt Signals
└── views/
    └── main_view.py            # PySide6 UI layout, VisPy canvas, Matplotlib offline window
```

---

## Dependencies

```
numpy
scipy
matplotlib
pyside6
vispy
pyopengl
```

Install all with:

```bash
pip install -r requirements.txt
```

| Package | Purpose |
|---------|---------|
| `numpy` | Array operations, packet reconstruction, buffer management |
| `scipy` | Butterworth filter design and SOS zero-phase filtering |
| `matplotlib` | Offline signal inspection plots |
| `pyside6` | GUI framework — widgets, signals/slots, Qt timer |
| `vispy` | Hardware-accelerated real-time signal rendering |
| `pyopengl` | OpenGL backend required by VisPy |

---

