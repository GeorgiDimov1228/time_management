import serial
import requests
import time
import sys
import datetime
from datetime import timezone # Import timezone

# --- Configuration ---
# Replace with your Arduino's serial port name
SERIAL_PORT = '/dev/tty.usbmodem101' # Make sure this is correct for your Mac
BAUD_RATE = 9600
# URL for the FastAPI app running on the host (via Docker port mapping)
API_BASE_URL = "http://localhost:8000/api"
# Cooldown period in seconds before allowing the NEXT action after ANY previous action
ACTION_COOLDOWN_SECONDS = 10 # Renamed from CHECKOUT_COOLDOWN_SECONDS
# --- End Configuration ---

def get_employee_status(rfid_tag):
    """Gets the last event status for the employee."""
    status_url = f"{API_BASE_URL}/employees/status?rfid={rfid_tag}"
    print(f"Checking status: GET {status_url}")
    try:
        response = requests.get(status_url, timeout=5)
        if response.status_code == 200:
            status_data = response.json()
            print(f"Status Response (200): {status_data}")
            # Attempt to parse the timestamp string into a datetime object
            if status_data.get("last_event_time"):
                try:
                    ts_str = status_data["last_event_time"].replace('Z', '+00:00')
                    dt_obj = datetime.datetime.fromisoformat(ts_str)
                    if dt_obj.tzinfo is None:
                         dt_obj = dt_obj.replace(tzinfo=timezone.utc)
                    status_data["last_event_datetime"] = dt_obj
                except ValueError:
                    print(f"Warning: Could not parse last_event_time '{status_data['last_event_time']}'")
                    status_data["last_event_datetime"] = None
            else:
                 status_data["last_event_datetime"] = None
            return status_data
        elif response.status_code == 404:
             print("Status Response (404): Employee not found.")
             return {"error": "not_found"}
        else:
            print(f"Status API Error ({response.status_code}): {response.text}")
            return {"error": "api_error"}
    except requests.exceptions.RequestException as e:
        print(f"Status HTTP Request failed: {e}")
        return {"error": "http_error"}
    except Exception as e:
        print(f"An error occurred during status check: {e}")
        return {"error": "unknown"}


def record_attendance(rfid_tag, action):
    """Records a check-in or check-out event."""
    if action not in ["checkin", "checkout"]:
        print(f"Invalid action: {action}")
        return

    attendance_url = f"{API_BASE_URL}/{action}?rfid={rfid_tag}"
    print(f"Recording attendance: POST {attendance_url}")
    try:
        response = requests.post(attendance_url, timeout=5)
        if response.status_code == 200:
            print(f"Attendance Response ({response.status_code}): {response.json()}")
        elif response.status_code == 404:
             print(f"Attendance Response (404): Employee not found for {action}.")
        else:
            print(f"Attendance API Error ({response.status_code}): {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Attendance HTTP Request failed: {e}")
    except Exception as e:
        print(f"An error occurred during attendance recording: {e}")


def process_rfid_scan(rfid_tag):
    """Determines action based on status and records attendance, including general cooldown."""
    # Sanitize the RFID tag
    rfid_tag = rfid_tag.strip()
    if not rfid_tag:
        print("Received empty tag, skipping.")
        return

    print(f"\nProcessing RFID: {rfid_tag}")
    status_info = get_employee_status(rfid_tag)

    if status_info.get("error") == "not_found":
        print(f"Cannot process scan: Employee with RFID {rfid_tag} not found in database.")
        return
    elif status_info.get("error"):
        print(f"Cannot process scan due to status check error for RFID {rfid_tag}.")
        return

    # Get last event details
    last_event = status_info.get("last_event")
    last_event_dt = status_info.get("last_event_datetime") # Use the parsed datetime object

    # --- Add General Cooldown Check ---
    if last_event_dt: # Check only if there WAS a previous event
        current_time_utc = datetime.datetime.now(timezone.utc)
        time_since_last_event = current_time_utc - last_event_dt
        print(f"Time since last event ('{last_event}' at {last_event_dt}): {time_since_last_event}")
        # Check if cooldown period has passed
        if time_since_last_event.total_seconds() < ACTION_COOLDOWN_SECONDS:
            print(f"Cooldown active: Cannot record new event yet. Need to wait {ACTION_COOLDOWN_SECONDS} seconds since last event.")
            return # Stop processing, do not record checkin or checkout
        else:
            print("Cooldown passed.")
    else:
        print("No previous event found, proceeding.")
    # --- End General Cooldown Check ---

    # Determine next action based on last event (only if cooldown passed or no previous event)
    if last_event == "checkin":
        next_action = "checkout"
    else: # If last event was 'checkout' or None (first time)
        next_action = "checkin"

    print(f"Determined next action: '{next_action}'")
    record_attendance(rfid_tag, next_action)


def main():
    """Main function to read from serial and trigger processing."""
    print(f"Attempting to connect to serial port {SERIAL_PORT} at {BAUD_RATE} baud...")
    # Update note about cooldown
    print(f"Action cooldown period set to {ACTION_COOLDOWN_SECONDS} seconds.")

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Connected to {SERIAL_PORT}. Waiting for RFID tags...")
        time.sleep(2)

        while True:
            try:
                if ser.in_waiting > 0:
                    line = ser.readline()
                    rfid_tag_from_serial = line.decode('utf-8', errors='ignore').strip()

                    if rfid_tag_from_serial:
                        process_rfid_scan(rfid_tag_from_serial)
                    else:
                        pass # Timeout or empty line
                else:
                     time.sleep(0.1) # No data waiting

            except serial.SerialException as e:
                print(f"Serial error: {e}. Attempting to reconnect...")
                ser.close()
                time.sleep(5)
                try:
                   ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
                   print("Reconnected.")
                   time.sleep(2)
                except serial.SerialException as recon_e:
                   print(f"Reconnect failed: {recon_e}. Retrying in 10s.")
                   time.sleep(10)
            except KeyboardInterrupt:
                print("\nExiting by user request.")
                break
            except Exception as e:
                 print(f"An unexpected error occurred in the loop: {e}")
                 time.sleep(1) # Prevent rapid error loops

    except serial.SerialException as e:
        print(f"Error: Could not open serial port {SERIAL_PORT}.")
        print(f"Details: {e}")
        sys.exit(1) # Exit if connection fails initially
    except Exception as e:
        print(f"An unexpected startup error occurred: {e}")
        sys.exit(1)
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("Serial port closed.")

if __name__ == "__main__":
    main()
