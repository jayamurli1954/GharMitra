"""
Get your local IP address for mobile device connection
Run this to find the IP address to use in your mobile app
"""
import socket

def get_local_ip():
    """Get the local IP address of this machine"""
    try:
        # Connect to a remote server to get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        return "127.0.0.1"

if __name__ == "__main__":
    local_ip = get_local_ip()
    print("=" * 60)
    print("LOCAL NETWORK IP ADDRESS")
    print("=" * 60)
    print(f"Your local IP: {local_ip}")
    print(f"\nBackend URL: http://{local_ip}:8000")
    print(f"API URL: http://{local_ip}:8000/api")
    print("\nUpdate your mobile app config with this IP:")
    print(f"  API_URL: 'http://{local_ip}:8000/api'")
    print("\nMake sure:")
    print("  1. Your laptop and phone are on the SAME WiFi network")
    print("  2. Windows Firewall allows port 8000")
    print("  3. Backend is running on 0.0.0.0:8000 (not localhost)")
    print("=" * 60)

