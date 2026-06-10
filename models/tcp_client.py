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
    Runs the receive loop in a background thread.
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
        """Connect to the server and start background receive thread."""
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect((host, port))
            self._running = True
            self._thread = threading.Thread(target=self._receive_loop, daemon=True)
            self._thread.start()
            self.on_status("Connected")
        except OSError as e:
            self.on_status(f"Could not connect: {e}")

    def disconnect(self):
        """Stop receiving and close the socket."""
        self._running = False
        if self._socket:
            self._socket.close()
            self._socket = None
        self.on_status("Disconnected")

    def _receive_loop(self):
        """
        Background thread loop.
        Reads raw bytes from socket, reconstructs full packets,
        parses them into numpy arrays of shape (32, 18), and
        forwards each packet to the data callback.
        """
        byte_buffer = b""
        try:
            while self._running:
                chunk = self._socket.recv(4096)
                if not chunk:
                    self.on_status("Server closed connection")
                    break
                byte_buffer += chunk

                while len(byte_buffer) >= PACKET_SIZE:
                    packet_bytes = byte_buffer[:PACKET_SIZE]
                    byte_buffer = byte_buffer[PACKET_SIZE:]
                    data = np.frombuffer(packet_bytes, dtype=DTYPE)
                    data = data.reshape((CHANNELS, SAMPLES_PER_CHUNK))
                    self.on_data(data)

        except OSError as e:
            if self._running:
                self.on_status(f"Connection lost: {e}")
        finally:
            self._running = False