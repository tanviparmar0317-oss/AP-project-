import time
from models.tcp_client import TCPClient
from models.data_buffer import DataBuffer

# Create buffer
buffer = DataBuffer()

def on_data(chunk):
    buffer.append(chunk)
    print(f"Received chunk | shape: {chunk.shape} | channel 0 mean: {chunk[0].mean():.4f}")

def on_status(msg):
    print(f"Status: {msg}")

# Connect to the Exercise 5 TCP server
client = TCPClient(on_data_callback=on_data, on_status_callback=on_status)
client.connect("localhost", 5005)  # change 5005 to your server's port if needed

# Listen for 5 seconds
time.sleep(5)
client.disconnect()

# Check buffer
channel_data = buffer.get_channel(0)
print(f"\nBuffer channel 0 — shape: {channel_data.shape}, last value: {channel_data[-1]:.4f}")