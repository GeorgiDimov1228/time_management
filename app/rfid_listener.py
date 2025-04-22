# time_management/app/rfid_listener.py (Modified)
import asyncio
import httpx
import os # Import os to get credentials from environment variables
import threading
import time
from fastapi import HTTPException # Needed for potential credential errors

# --- Credentials Configuration (Use Environment Variables) ---
LISTENER_USERNAME = os.getenv("LISTENER_USERNAME")
LISTENER_PASSWORD = os.getenv("LISTENER_PASSWORD")
# --- End Configuration ---

class RFIDReader:
    def __init__(self, reader_id, reader_url, api_base_url="http://localhost:8000/api"):
        self.reader_id = reader_id
        self.reader_url = reader_url
        self.api_base_url = api_base_url
        self.running = False
        self.client = httpx.AsyncClient()
        self._auth_token = None # To store the JWT token
        self._token_lock = asyncio.Lock() # Lock for token refresh

    async def _get_auth_token(self):
        """Fetches or returns the cached JWT token."""
        async with self._token_lock: # Ensure only one task refreshes the token
            # Simple check: If we have a token, assume it's valid for now.
            # A robust implementation would check expiry or handle 401 errors.
            if self._auth_token:
                return self._auth_token

            if not LISTENER_USERNAME or not LISTENER_PASSWORD:
                 print(f"Listener {self.reader_id}: ERROR - LISTENER_USERNAME or LISTENER_PASSWORD environment variables not set.")
                 # Decide how to handle this - raise error, stop polling, etc.
                 # For now, return None which will cause process_scan to fail
                 return None

            token_url = f"{self.api_base_url}/token"
            try:
                print(f"Listener {self.reader_id}: Fetching auth token from {token_url}")
                # Note: httpx sends form data using the 'data' parameter
                response = await self.client.post(
                    token_url,
                    data={"username": LISTENER_USERNAME, "password": LISTENER_PASSWORD}
                )
                response.raise_for_status() # Raise error for bad responses (4xx, 5xx)
                token_data = response.json()
                self._auth_token = token_data.get("access_token")
                print(f"Listener {self.reader_id}: Successfully obtained auth token.")
                return self._auth_token
            except httpx.RequestError as e:
                 print(f"Listener {self.reader_id}: HTTP error fetching token: {e}")
            except httpx.HTTPStatusError as e:
                 print(f"Listener {self.reader_id}: Failed to fetch token. Status: {e.response.status_code}, Body: {e.response.text}")
            except Exception as e:
                print(f"Listener {self.reader_id}: Unexpected error fetching token: {e}")

            self._auth_token = None # Ensure token is None on failure
            return None

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
        token = await self._get_auth_token()
        if not token:
             print(f"Listener {self.reader_id}: Cannot process scan for {rfid}, failed to get auth token.")
             # Optional: Attempt to re-authenticate after a delay?
             return # Stop processing if no token

        headers = {"Authorization": f"Bearer {token}"}
        scan_url = f"{self.api_base_url}/scan"

        try:
            print(f"Listener {self.reader_id}: Sending RFID {rfid} to {scan_url}")
            response = await self.client.post(scan_url, json={"rfid": rfid}, headers=headers, timeout=5.0)

            if 200 <= response.status_code < 300:
                 print(f"Listener {self.reader_id}: Scan processed successfully for {rfid}. Response: {response.json()}")
            elif response.status_code == 401: # Unauthorized
                 print(f"Listener {self.reader_id}: Scan failed for {rfid}. Authorization failed (401). Token might be invalid/expired.")
                 # Invalidate the token so it's refreshed on the next attempt
                 async with self._token_lock:
                     self._auth_token = None
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
        # Attempt initial authentication
        await self._get_auth_token()

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


# --- Example of running listeners (remains the same) ---
async def main_listener_task():
    # Ensure LISTENER_USERNAME and LISTENER_PASSWORD are set in your environment
    if not LISTENER_USERNAME or not LISTENER_PASSWORD:
        print("ERROR: LISTENER_USERNAME or LISTENER_PASSWORD environment variables are not set.")
        print("The RFID listener cannot authenticate with the API and will not run.")
        return # Prevent listeners from starting without credentials

    readers_config = [
        {"id": "entrance", "url": "http://localhost:5000"}, # Using mock reader URL
        # {"id": "exit", "url": "http://192.168.1.101"}
    ]

    readers = [RFIDReader(config["id"], config["url"]) for config in readers_config]
    polling_tasks = [asyncio.create_task(reader.run_polling()) for reader in readers]

    try:
        await asyncio.gather(*polling_tasks)
    except asyncio.CancelledError:
         print("Listener tasks cancelled.")
    finally:
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