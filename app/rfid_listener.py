import threading
import time
import requests
from fastapi import FastAPI, Depends

class RFIDReader(threading.Thread):
    def __init__(self, app, reader_id, reader_url):
        threading.Thread.__init__(self, daemon=True)
        self.app = app
        self.reader_id = reader_id
        self.reader_url = reader_url
        self.running = False
        
    def run(self):
        self.running = True
        while self.running:
            try:
                # Poll the reader for new scans
                rfid = self.poll_reader()
                if rfid:
                    self.process_scan(rfid)
            except Exception as e:
                print(f"Error reading RFID: {e}")
            time.sleep(1)
    
    def poll_reader(self):
        # Implementation depends on your reader
        # This is a simplified example
        response = requests.get(f"{self.reader_url}/scan")
        if response.status_code == 200:
            data = response.json()
            return data.get("rfid")
        return None
    
    
    def process_scan(self, rfid):
        # First, check the user's current state
        response = requests.get(f"http://localhost:8000/api/employees/status?rfid={rfid}")
        if response.status_code == 200:
            user_status = response.json()
            # If last event was check-out or no events today, do a check-in
            if user_status.get("last_event") == "checkout" or user_status.get("last_event") is None:
                requests.post(f"http://localhost:8000/api/checkin?rfid={rfid}")
            # If last event was check-in, do a check-out
            elif user_status.get("last_event") == "checkin":
                requests.post(f"http://localhost:8000/api/checkout?rfid={rfid}")
    
    def process_scan_based_on_entrance(self, rfid):
        # For entrance readers, create a check-in
        if self.reader_id == "entrance":
            requests.post(f"http://localhost:8000/api/checkin?rfid={rfid}")
        # For exit readers, create a check-out
        elif self.reader_id == "exit":
            requests.post(f"http://localhost:8000/api/checkout?rfid={rfid}")
        # Log the event
        print(f"Processed {self.reader_id} scan for RFID: {rfid}")
        
    def stop(self):
        self.running = False

def start_rfid_readers(app):
    # Configuration for your RFID readers
    readers = [
        {"id": "entrance", "url": "http://192.168.1.100"},
        {"id": "exit", "url": "http://192.168.1.101"}
    ]
    
    # Start a thread for each reader
    for reader_config in readers:
        reader = RFIDReader(app, reader_config["id"], reader_config["url"])
        reader.start()