import sys
import time
import requests
import threading
from unittest import mock

# Add the current directory to the path so we can import the app modules
sys.path.append('.')

from app.rfid_listener import RFIDReader

def test_rfid_listener():
    """Test the RFID listener with mock data"""
    print("Starting RFID listener test...")
    
    # Create a mock FastAPI app
    mock_app = mock.MagicMock()
    
    # Create a reader instance that points to our mock server
    reader = RFIDReader(mock_app, "test-reader", "http://localhost:5000")
    
    # Start the reader in a separate thread
    reader_thread = threading.Thread(target=reader.run)
    reader_thread.daemon = True
    reader_thread.start()
    
    print("RFID reader started. Monitoring for scans...")
    print("Press Ctrl+C to stop.")
    
    try:
        # Run for a while to observe the behavior
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping RFID reader...")
        reader.running = False
        reader_thread.join(timeout=2)
        print("Test complete.")

def mock_process_scan(self, rfid):
    """Override the process_scan method to avoid making actual API calls"""
    print(f"RFID scanned: {rfid}")
    print(f"Would process scan for reader: {self.reader_id}")
    # In a real test, you could verify that the correct API calls would be made

def setup_test_environment():
    """Set up the test environment by patching the RFIDReader class"""
    # Patch the process_scan method to avoid actual API calls
    RFIDReader.process_scan = mock_process_scan
    
    # Verify mock server is running
    try:
        response = requests.get("http://localhost:5000/scan")
        if response.status_code != 200:
            print("Mock RFID server is not responding correctly.")
            return False
    except requests.exceptions.ConnectionError:
        print("Mock RFID server is not running. Please start it first.")
        print("Run: python mock_rfid_reader.py")
        return False
    
    return True

if __name__ == "__main__":
    if setup_test_environment():
        test_rfid_listener()