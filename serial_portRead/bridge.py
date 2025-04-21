# time_management/serial_portRead/bridge.py (Modified)
import serial
import httpx
import asyncio
import time
import sys
import datetime
import os # Import os
from datetime import timezone

# --- Configuration ---
SERIAL_PORT = '/dev/tty.usbmodem101'
BAUD_RATE = 9600
API_BASE_URL = "http://localhost:8000/api"
# --- Credentials Configuration (Use Environment Variables) ---
BRIDGE_USERNAME = os.getenv("BRIDGE_USERNAME")
BRIDGE_PASSWORD = os.getenv("BRIDGE_PASSWORD")
# --- End Configuration ---

# Use a single client instance
client = httpx.AsyncClient(base_url=API_BASE_URL, timeout=10.0)
# Global variable to store the auth token
_auth_token = None
_token_lock = asyncio.Lock() # Lock for token refresh

async def get_auth_token():
    """Fetches or returns the cached JWT token for the bridge."""
    global _auth_token
    async with _token_lock:
        # Simple check: If we have a token, assume it's valid for now.
        if _auth_token:
            return _auth_token

        if not BRIDGE_USERNAME or not BRIDGE_PASSWORD:
            print("Bridge ERROR: BRIDGE_USERNAME or BRIDGE_PASSWORD environment variables not set.")
            return None

        token_url = "/token" # Relative to base_url
        try:
            print(f"Bridge: Fetching auth token from {API_BASE_URL}{token_url}")
            response = await client.post(
                token_url, # Use relative URL
                data={"username": BRIDGE_USERNAME, "password": BRIDGE_PASSWORD}
            )
            response.raise_for_status()
            token_data = response.json()
            _auth_token = token_data.get("access_token")
            print("Bridge: Successfully obtained auth token.")
            return _auth_token
        except httpx.RequestError as e:
            print(f"Bridge: HTTP error fetching token: {e}")
        except httpx.HTTPStatusError as e:
            print(f"Bridge: Failed to fetch token. Status: {e.response.status_code}, Body: {e.response.text}")
        except Exception as e:
            print(f"Bridge: Unexpected error fetching token: {e}")

        _auth_token = None
        return None

async def process_rfid_scan(rfid_tag):
    """Sends the scanned RFID tag to the central API /scan endpoint with auth."""
    global _auth_token # Use the global token variable
    rfid_tag = rfid_tag.strip()
    if not rfid_tag:
        print("Received empty tag, skipping.")
        return

    token = await get_auth_token()
    if not token:
        print(f"Bridge: Cannot process scan for {rfid_tag}, failed to get auth token.")
        return

    print(f"\nBridge Processing RFID: {rfid_tag}")
    scan_url = "/scan" # Relative to base_url
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = await client.post(scan_url, json={"rfid": rfid_tag}, headers=headers)

        if 200 <= response.status_code < 300:
            print(f"Bridge: Scan processed successfully for {rfid_tag}. Response: {response.json()}")
        elif response.status_code == 401: # Unauthorized
            print(f"Bridge: Scan failed for {rfid_tag}. Authorization failed (401). Token might be invalid/expired.")
            # Invalidate the token
            async with _token_lock:
                _auth_token = None
        elif response.status_code == 404:
            print(f"Bridge: Scan failed for {rfid_tag}. Employee not found (404).")
        elif response.status_code == 429:
             print(f"Bridge: Scan failed for {rfid_tag}. Cooldown active (429).")
        else:
            print(f"Bridge: Scan failed for {rfid_tag}. Status: {response.status_code}, Body: {response.text}")

    except httpx.RequestError as e:
        print(f"Bridge: HTTP Request failed for {rfid_tag}: {e}")
    except Exception as e:
        print(f"Bridge: An unexpected error occurred during scan processing for {rfid_tag}: {e}")


async def read_serial(ser):
    """Reads lines from serial asynchronously."""
    loop = asyncio.get_running_loop()
    while True:
        try:
            line = await loop.run_in_executor(None, ser.readline)
            if line:
                rfid_tag_from_serial = line.decode('utf-8', errors='ignore').strip()
                if rfid_tag_from_serial:
                     asyncio.create_task(process_rfid_scan(rfid_tag_from_serial))
                else:
                    pass # Empty line
            else:
                 await asyncio.sleep(0.1)

        except serial.SerialException as e:
             print(f"Serial error: {e}. Attempting to reconnect...")
             ser.close()
             await asyncio.sleep(5)
             try:
                 ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
                 print("Reconnected.")
                 await asyncio.sleep(2)
             except serial.SerialException as recon_e:
                 print(f"Reconnect failed: {recon_e}. Retrying in 10s.")
                 await asyncio.sleep(10)
        except Exception as e:
            print(f"Error in serial read loop: {e}")
            await asyncio.sleep(1) # Prevent rapid error loops


async def main():
    """Main async function to connect and start reading."""
    # Ensure BRIDGE_USERNAME and BRIDGE_PASSWORD are set
    if not BRIDGE_USERNAME or not BRIDGE_PASSWORD:
        print("ERROR: BRIDGE_USERNAME or BRIDGE_PASSWORD environment variables are not set.")
        print("The bridge cannot authenticate with the API and will exit.")
        sys.exit(1)

    print(f"Attempting to connect to serial port {SERIAL_PORT} at {BAUD_RATE} baud...")

    # Attempt initial authentication before starting serial read
    print("Attempting initial authentication...")
    initial_token = await get_auth_token()
    if not initial_token:
         print("Initial authentication failed. Please check credentials and API status.")
         # Decide if you want to exit or proceed hoping it works later
         # sys.exit(1) # Optional: Exit if initial auth fails

    ser = None
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Connected to {SERIAL_PORT}. Waiting for RFID tags...")
        await asyncio.sleep(2)
        await read_serial(ser)

    except serial.SerialException as e:
        print(f"Error: Could not open serial port {SERIAL_PORT}.")
        print(f"Details: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
         print("\nExiting by user request.")
    except Exception as e:
        print(f"An unexpected startup error occurred: {e}")
        sys.exit(1)
    finally:
        if ser and ser.is_open:
            ser.close()
            print("Serial port closed.")
        await client.aclose() # Close the httpx client
        print("HTTP client closed.")

if __name__ == "__main__":
    asyncio.run(main())