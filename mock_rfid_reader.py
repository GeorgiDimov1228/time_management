from flask import Flask, jsonify
import time
import random
import threading

app = Flask(__name__)

# Simulate a list of RFID cards
rfid_cards = [
    "0987654321",
    "1234567890",
    "5678901234",
    "9012345678"
]

# Control variables
active = True
scan_interval = 5  # seconds between simulated scans
current_card_index = 0

@app.route('/scan', methods=['GET'])
def scan():
    """Simulate an RFID card scan"""
    # 70% chance of returning a card, 30% chance of no card detected
    if random.random() < 0.7:
        return jsonify({"rfid": rfid_cards[current_card_index]})
    return jsonify({"rfid": None})

def rotate_cards():
    """Rotate through different cards to simulate different employees"""
    global current_card_index
    while active:
        time.sleep(scan_interval)
        current_card_index = (current_card_index + 1) % len(rfid_cards)
        print(f"Ready to scan card: {rfid_cards[current_card_index]}")

if __name__ == '__main__':
    # Start the card rotation thread
    card_thread = threading.Thread(target=rotate_cards, daemon=True)
    card_thread.start()
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)