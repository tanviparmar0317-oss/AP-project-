"""
Mock EMG TCP Server
===================
Streams the contents of recording.pkl as a continuous loop of
32-channel x 18-sample float64 packets (4608 bytes each) to any
connected client at the real-time sample rate defined in the file.

Usage
-----
    python TCP_Server/main.py                     # default: localhost:12345
    python TCP_Server/main.py --port 9000         # custom port
    python TCP_Server/main.py --host 0.0.0.0 --port 12345  # all interfaces
"""

import os
import socket
import pickle
import numpy as np
import time
import threading
import argparse


class EMGTCPServer:
    def __init__(self, host='localhost', port=12345, pkl_file=None):
        self.host = host
        self.port = port
        if pkl_file is None:
            # Resolve recording.pkl relative to the project root
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.pkl_file = os.path.join(base_dir, 'recording.pkl')
        else:
            self.pkl_file = pkl_file
        self.server_socket = None
        self.clients = []
        self.running = False
        self.data = None
        self.sampling_rate = None
        self.CHANNELS = 32
        self.SAMPLES_PER_PACKET = 18
        self.load_data()

    def load_data(self):
        """Load EMG data from the PKL file into memory."""
        try:
            with open(self.pkl_file, 'rb') as f:
                self.data = pickle.load(f)
            self.emg_signal = self.data['biosignal'][:32, :, :]
            self.sampling_rate = self.data['device_information']['sampling_frequency']
            print(f"Data loaded successfully. Shape: {self.emg_signal.shape}")
            print(f"Sampling rate: {self.sampling_rate} Hz")
        except Exception as e:
            print(f"Error loading data: {e}")
            raise

    def print_data(self, data, window_index):
        """Print the current chunk of data (debug helper)."""
        print(f"\nSending window {window_index}:")
        print(f"Shape: {data.shape}")
        print("Data values:")
        for i in range(data.shape[0]):
            print(f"Channel {i + 1}: {data[i, :]}")
        print("-" * 50)

    def start(self):
        """Bind the server socket and start accepting connections."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        print(f"Server started on {self.host}:{self.port}")

        # Accept connections in a separate thread so the main thread stays alive
        accept_thread = threading.Thread(target=self.accept_connections)
        accept_thread.daemon = True
        accept_thread.start()

    def accept_connections(self):
        """Accept incoming client connections in a loop."""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                print(f"New connection from {address}")
                self.clients.append(client_socket)
                # Each client gets its own streaming thread
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket,)
                )
                client_thread.daemon = True
                client_thread.start()
            except Exception as e:
                if self.running:
                    print(f"Error accepting connection: {e}")

    def handle_client(self, client_socket):
        """
        Stream EMG data to a single connected client.

        Sends packets of shape (32, 18) as raw float64 bytes in a loop,
        cycling back to the start of the recording when it ends.
        Packet send rate is throttled to match the real sampling frequency.
        """
        try:
            num_windows = self.emg_signal.shape[2]
            window_index = 0

            while self.running:
                current_window = self.emg_signal[:, :, window_index].astype(np.float64)

                if window_index == 0:
                    print("server dtype:", current_window.dtype)
                    print("server shape:", current_window.shape)
                    print("server bytes:", current_window.nbytes)

                # Send the full packet atomically — sendall handles partial sends
                data_bytes = current_window.tobytes(order="C")
                client_socket.sendall(data_bytes)

                # Throttle to match real-time sample rate
                sleep_time = self.SAMPLES_PER_PACKET / self.sampling_rate
                time.sleep(sleep_time)

                window_index = (window_index + 1) % num_windows

        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            if client_socket in self.clients:
                self.clients.remove(client_socket)
            client_socket.close()

    def stop(self):
        """Stop the server and close all client connections."""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        for client in self.clients:
            client.close()
        self.clients.clear()
        print("Server stopped")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Mock EMG TCP server — streams recording.pkl data over TCP."
    )
    parser.add_argument(
        "--host", type=str, default="localhost",
        help="Host address to bind to (default: localhost)"
    )
    parser.add_argument(
        "--port", type=int, default=12345,
        help="Port number to listen on (default: 12345)"
    )
    args = parser.parse_args()

    server = EMGTCPServer(host=args.host, port=args.port)
    try:
        server.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.stop()