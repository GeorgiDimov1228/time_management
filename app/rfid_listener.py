# time_management/app/rfid_listener.py (Illustrative async changes)
import asyncio # Import asyncio
import httpx # Import httpx
import threading
import time
# from fastapi import FastAPI # FastAPI app instance might not be needed directly

# Consider running this outside the main FastAPI app process if it's complex
# Or integrate properly using asyncio tasks within FastAPI startup/shutdown events

class RFIDReader: # Removed threading.Thread inheritance for async approach
    def __init__(self, reader_id, reader_url, api_base_url="http://localhost:8000/api"):
        self.reader_id = reader_id
        self.reader_url = reader_url
        self.api_base_url = api_base_url # Make API base URL configurable
        self.running = False
        self.client = httpx.AsyncClient() # Create one client instance

    async def poll_reader(self):
        try:
            response = await self.client.get(f"{self.reader_url}/scan", timeout=5.0)
            response.raise_for_status() # Raise exception for bad status codes
            data = response.json()
            return data.get("rfid")
        except httpx.RequestError as e:
            print(f"Error polling reader {self.reader_id} ({self.reader_url}): {e}")
        except Exception as e:
             print(f"Unexpected error polling reader {self.reader_id}: {e}")
        return None

    async def process_scan(self, rfid):
        # Use the direct /scan endpoint which handles logic and cooldown
        scan_url = f"{self.api_base_url}/scan"
        try:
            print(f"Listener {self.reader_id}: Sending RFID {rfid} to {scan_url}")
            response = await self.client.post(scan_url, json={"rfid": rfid}, timeout=5.0)

            if 200 <= response.status_code < 300:
                 print(f"Listener {self.reader_id}: Scan processed successfully for {rfid}. Response: {response.json()}")
            elif response.status_code == 404:
                 print(f"Listener {self.reader_id}: Scan failed for {rfid}. Employee not found (404).")
            elif response.status_code == 429:
                print(f"Listener {self.reader_id}: Scan failed for {rfid}. Cooldown active (429).")
            else:
                print(f"Listener {self.reader_id}: Scan failed for {rfid}. Status: {response.status_code}, Body: {response.text}")

        except httpx.RequestError as e:
            print(f"Listener {self.reader_id}: HTTP error processing scan for {rfid}: {e}")
        except Exception as e:
            print(f"Listener {self.reader_id}: Unexpected error processing scan for {rfid}: {e}")


    async def run_polling(self):
        self.running = True
        print(f"Starting polling for reader: {self.reader_id} ({self.reader_url})")
        while self.running:
            try:
                rfid = await self.poll_reader()
                if rfid:
                    await self.process_scan(rfid)
                # Adjust sleep time as needed
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Error in polling loop for {self.reader_id}: {e}")
                await asyncio.sleep(5) # Longer sleep on error

    async def stop(self):
        self.running = False
        await self.client.aclose() # Close the httpx client
        print(f"Stopped polling for reader: {self.reader_id}")


# Example of how to run these listeners with asyncio
async def main_listener_task():
    # Configuration for your RFID readers
    readers_config = [
        # Replace with actual URLs or get from config
        {"id": "entrance", "url": "http://localhost:5000"}, # Using mock reader URL
        # {"id": "exit", "url": "http://192.168.1.101"}
    ]

    readers = [RFIDReader(config["id"], config["url"]) for config in readers_config]
    polling_tasks = [asyncio.create_task(reader.run_polling()) for reader in readers]

    try:
        # Keep tasks running
        await asyncio.gather(*polling_tasks)
    except asyncio.CancelledError:
         print("Listener tasks cancelled.")
    finally:
        # Ensure stop is called on all readers
        await asyncio.gather(*(reader.stop() for reader in readers))
        print("All listeners stopped.")

# You would typically start this main_listener_task during FastAPI startup
# Example (in main.py):
# @app.on_event("startup")
# async def startup_event():
#     asyncio.create_task(main_listener_task())

# To run this file standalone for testing:
# if __name__ == "__main__":
#     try:
#         asyncio.run(main_listener_task())
#     except KeyboardInterrupt:
#         print("Manual interruption.")