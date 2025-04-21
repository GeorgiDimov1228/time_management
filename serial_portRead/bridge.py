# time_management/serial_portRead/bridge.py
import serial
import httpx # Use httpx
import asyncio # Use asyncio
import time
import sys
import datetime
from datetime import timezone

# --- Configuration ---
SERIAL_PORT = '/dev/tty.usbmodem101'
BAUD_RATE = 9600
API_BASE_URL = "http://localhost:8000/api"
# Cooldown is handled server-side by the /scan endpoint, no need here
# --- End Configuration ---

# Use a single client instance
client = httpx.AsyncClient(base_url=API_BASE_URL, timeout=10.0)

async def process_rfid_scan(rfid_tag):
    """Sends the scanned RFID tag to the central API /scan endpoint."""
    rfid_tag = rfid_tag.strip()
    if not rfid_tag:
        print("Received empty tag, skipping.")
        return

    print(f"\nProcessing RFID: {rfid_tag}")
    scan_url = "/scan" # Relative to base_url
    try:
        response = await client.post(scan_url, json={"rfid": rfid_tag})

        if 200 <= response.status_code < 300:
            print(f"Scan processed successfully for {rfid_tag}. Response: {response.json()}")
        elif response.status_code == 404:
            print(f"Scan failed for {rfid_tag}. Employee not found (404).")
        elif response.status_code == 429:
             print(f"Scan failed for {rfid_tag}. Cooldown active (429).")
        else:
            print(f"Scan failed for {rfid_tag}. Status: {response.status_code}, Body: {response.text}")

    except httpx.RequestError as e:
        print(f"HTTP Request failed for {rfid_tag}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during scan processing for {rfid_tag}: {e}")


async def read_serial(ser):
    """Reads lines from serial asynchronously."""
    # pyserial is sync, so we run it in a thread pool executor
    # to avoid blocking the asyncio event loop.
    loop = asyncio.get_running_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    # This part is tricky - connecting serial directly to asyncio streams isn't standard
    # A common approach is to read in a separate thread and put results in an asyncio queue,
    # or use loop.run_in_executor for the blocking readline call.

    # Simplified approach using run_in_executor for readline:
    while True:
        try:
             # Run the blocking readline call in the default executor (thread pool)
            line = await loop.run_in_executor(None, ser.readline)
            if line:
                rfid_tag_from_serial = line.decode('utf-8', errors='ignore').strip()
                if rfid_tag_from_serial:
                     # Process the scan asynchronously without blocking serial read
                     asyncio.create_task(process_rfid_scan(rfid_tag_from_serial))
                else:
                    pass # Empty line
            else:
                 # If readline returns empty bytes (e.g., on timeout or disconnect), wait briefly
                 await asyncio.sleep(0.1)

        except serial.SerialException as e:
             print(f"Serial error: {e}. Attempting to reconnect...")
             ser.close()
             await asyncio.sleep(5)
             try:
                 # Reconnect attempt (still sync)
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
    print(f"Attempting to connect to serial port {SERIAL_PORT} at {BAUD_RATE} baud...")
    # Cooldown note removed as it's handled server-side
    ser = None
    try:
         # Serial connection is synchronous
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Connected to {SERIAL_PORT}. Waiting for RFID tags...")
        await asyncio.sleep(2)

        # Start the asynchronous serial reading task
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