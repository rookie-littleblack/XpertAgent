# Import the gRPC library for RPC communication
import grpc

# Replace with your server IP and port
# Note: Port 7934 is mapped to container's internal port 7834
#server_address = "192.168.1.23:7834"  # Internal container port
server_address = "192.168.1.23:7934"   # External mapped port

# Create an insecure channel (without SSL/TLS)
# For production, consider using secure channels with SSL/TLS certificates
channel = grpc.insecure_channel(server_address)

try:
    # Set a short timeout and attempt to establish connection
    # This will verify if the gRPC server is accessible
    # The timeout value is in seconds
    grpc.channel_ready_future(channel).result(timeout=10)
    print(f"Successfully connected to gRPC service: `{server_address}`")
except grpc.FutureTimeoutError:
    # If connection cannot be established within timeout period
    # This could be due to:
    # - Server not running
    # - Network connectivity issues
    # - Incorrect address/port
    # - Firewall blocking the connection
    print(f"Unable to connect to gRPC service: `{server_address}`")