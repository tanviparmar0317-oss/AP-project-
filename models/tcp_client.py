import socket
import numpy as np
import threading


CHANNELS = 32
SAMPLES_PER_CHUNK = 18
DTYPE = np.float64
PACKET_SIZE = CHANNELS * SAMPLES_PER_CHUNK * np.dtype(DTYPE).itemsize  # 4608 bytes


class TCPClient:
    """
    Connects to the TCP server and receives signal data chunks.

    Threading model: the receive loop runs in a background daemon thread
    so it never blocks the Qt event loop. _recv_exactly() guarantees that
    exactly one full packet (4608 bytes) is read per iteration, handling
    partial TCP reads that occur when packets split across segments.

    Calls on_data_callback(chunk) with shape (32, 18) for each packet.
    Calls on_status_callback(message) for connection status updates.
    """

    def __init__(self, on_data_callback, on_status_callback):
        self.on_data = on_data_callback
        self.on_status = on_status_callback
        self._socket = None
        self._thread = None
        self._running = False

    def connect(self, host: str, port: int):
        """
        Connect to the TCP server and start the background receive thread.
        Uses a 3-second timeout during connect so a wrong port fails fast
        instead of hanging indefinitely.
        """
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(3)        # fail fast if server not running
            self._socket.connect((host, port))
            self._socket.settimeout(None)     # blocking mode after connect
            self._running = True
            self._thread = threading.Thread(target=self._receive_loop, daemon=True)
            self._thread.start()
            self.on_status("Connected")
        except OSError as e:
            self.on_status(f"Could not connect: {e}")

    def disconnect(self):
        """Stop receiving and close the socket cleanly."""
        self._running = False
        if self._socket:
            self._socket.close()
            self._socket = None
        self.on_status("Disconnected")

    def _recv_exactly(self, n: int) -> bytes:
        """
        Read exactly n bytes from the socket.

        TCP is a stream protocol — a single recv() call may return fewer
        bytes than requested when a packet is split across TCP segments.
        This method loops until the full packet is assembled, which
        prevents silent data corruption and misaligned frames.
        """
        data = b""
        while len(data) < n:
            chunk = self._socket.recv(n - len(data))
            if not chunk:
                raise ConnectionError("Server closed the connection.")
            data += chunk
        return data

    def _receive_loop(self):
        """
        Background thread: reads exactly one full packet (4608 bytes) per
        iteration using _recv_exactly(), parses it into a (32, 18) float64
        numpy array, and forwards it to the data callback.
        """
        try:
            while self._running:
                raw = self._recv_exactly(PACKET_SIZE)
                data = np.frombuffer(raw, dtype=DTYPE).reshape((CHANNELS, SAMPLES_PER_CHUNK))
                self.on_data(data)
        except (OSError, ConnectionError) as e:
            if self._running:
                self.on_status(f"Connection lost: {e}")
        finally:
            self._running = False