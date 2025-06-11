import csv
import threading
import time
import json
import os
import uuid
import ping3
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime

# --- Configuration ---
DEVICES_FILE = 'devices.csv'
TAGS_FILE = 'tags.csv'
ROOMS_FILE = 'rooms.csv' # NEW: Rooms file
PING_INTERVAL = 10

# In-memory state
device_statuses = {}
status_lock = threading.Lock()
file_lock = threading.Lock()

# --- CSV File Handling (Generic) ---
def initialize_csv(filepath, fieldnames):
    with file_lock:
        if not os.path.exists(filepath):
            try:
                with open(filepath, mode='w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    print(f"Created {filepath}")
            except IOError as e:
                print(f"Error creating {filepath}: {e}")

def read_csv_data(filepath):
    with file_lock:
        if not os.path.exists(filepath): return []
        try:
            with open(filepath, mode='r', newline='', encoding='utf-8') as f:
                return [row for row in csv.DictReader(f) if row]
        except (IOError, csv.Error) as e:
            print(f"Error reading {filepath}: {e}")
            return []

def write_csv_data(filepath, fieldnames, data):
    with file_lock:
        try:
            with open(filepath, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            return True
        except IOError as e:
            print(f"Error writing to {filepath}: {e}")
            return False

# --- Core Pinging Logic ---
def check_device_status(device):
    device_id, address = device.get('id'), device.get('address')
    if not device_id or not address: return
    current_status = 'offline'
    try:
        if ping3.ping(address, timeout=2) is not False: current_status = 'online'
    except Exception: pass
    with status_lock:
        if device_id not in device_statuses or device_statuses[device_id]['status'] != current_status:
            device_statuses[device_id] = {"status": current_status, "timestamp": datetime.utcnow().isoformat() + "Z"}

def continuous_pinger():
    print("Pinger thread started...")
    while True:
        devices = read_csv_data(DEVICES_FILE)
        with status_lock:
            for device in devices:
                if device.get('id') not in device_statuses:
                    device_statuses[device.get('id')] = {"status": "checking", "timestamp": datetime.utcnow().isoformat() + "Z"}
        for device in devices: threading.Thread(target=check_device_status, args=(device,)).start()
        time.sleep(PING_INTERVAL)

# --- Flask Web Server ---
app = Flask(__name__)
CORS(app)

# --- API Endpoints ---
@app.route('/status', methods=['GET'])
def get_status():
    with status_lock: return jsonify(device_statuses.copy())

# Generic GET endpoint
@app.route('/<item_type>', methods=['GET'])
def get_items(item_type):
    if item_type == 'devices': return jsonify(read_csv_data(DEVICES_FILE))
    if item_type == 'tags': return jsonify(read_csv_data(TAGS_FILE))
    if item_type == 'rooms': return jsonify(read_csv_data(ROOMS_FILE))
    return jsonify({"error": "Invalid item type"}), 404

# DEVICES
@app.route('/devices', methods=['POST'])
def add_device():
    data = request.get_json()
    if not data or not data.get('address') or not data.get('friendlyName'):
        return jsonify({"error": "Missing required device data"}), 400
    devices = read_csv_data(DEVICES_FILE)
    new_device = {
        'id': str(uuid.uuid4()), 'address': data['address'], 'friendlyName': data['friendlyName'],
        'tagId': data.get('tagId', ''), 'roomId': data.get('roomId', ''), 'notes': data.get('notes', '')
    }
    devices.append(new_device)
    if write_csv_data(DEVICES_FILE, ['id', 'address', 'friendlyName', 'tagId', 'roomId', 'notes'], devices):
        return jsonify(new_device), 201
    return jsonify({"error": "Could not write to file"}), 500

@app.route('/devices/<item_id>', methods=['PUT'])
def edit_device(item_id):
    data = request.get_json()
    if not data: return jsonify({"error": "Missing data"}), 400
    devices = read_csv_data(DEVICES_FILE)
    device_found = False
    for i, device in enumerate(devices):
        if device.get('id') == item_id:
            devices[i].update({k: data.get(k, v) for k, v in device.items()})
            device_found = True
            break
    if not device_found: return jsonify({"error": "Device not found"}), 404
    if write_csv_data(DEVICES_FILE, ['id', 'address', 'friendlyName', 'tagId', 'roomId', 'notes'], devices):
        return jsonify(devices[i]), 200
    return jsonify({"error": "Could not write to file"}), 500

# TAGS & ROOMS (Generic Add/Delete)
@app.route('/<item_type>', methods=['POST'])
def add_tag_or_room(item_type):
    data = request.get_json()
    if not data or not data.get('name', '').strip():
        return jsonify({"error": "Missing name"}), 400
    
    filepath = TAGS_FILE if item_type == 'tags' else ROOMS_FILE if item_type == 'rooms' else None
    if not filepath: return jsonify({"error": "Invalid item type"}), 404
        
    items = read_csv_data(filepath)
    new_item = {'id': str(uuid.uuid4()), 'name': data['name'].strip()}
    items.append(new_item)
    if write_csv_data(filepath, ['id', 'name'], items):
        return jsonify(new_item), 201
    return jsonify({"error": "Could not write to file"}), 500

@app.route('/<item_type>/<item_id>', methods=['DELETE'])
def delete_item(item_type, item_id):
    if item_type == 'devices':
        filepath, fieldnames = DEVICES_FILE, ['id', 'address', 'friendlyName', 'tagId', 'roomId', 'notes']
    elif item_type == 'tags':
        filepath, fieldnames = TAGS_FILE, ['id', 'name']
        # Also untag devices
        devices = read_csv_data(DEVICES_FILE)
        for d in devices:
            if d.get('tagId') == item_id: d['tagId'] = ''
        write_csv_data(DEVICES_FILE, ['id', 'address', 'friendlyName', 'tagId', 'roomId', 'notes'], devices)
    elif item_type == 'rooms':
        filepath, fieldnames = ROOMS_FILE, ['id', 'name']
        # Also un-room devices
        devices = read_csv_data(DEVICES_FILE)
        for d in devices:
            if d.get('roomId') == item_id: d['roomId'] = ''
        write_csv_data(DEVICES_FILE, ['id', 'address', 'friendlyName', 'tagId', 'roomId', 'notes'], devices)
    else:
        return jsonify({"error": "Invalid item type"}), 404

    items = read_csv_data(filepath)
    items_to_keep = [i for i in items if i.get('id') != item_id]
    if len(items_to_keep) == len(items): return jsonify({"error": "Item not found"}), 404
    if write_csv_data(filepath, fieldnames, items_to_keep):
        if item_type == 'devices': 
            with status_lock: device_statuses.pop(item_id, None)
        return jsonify({"message": "Item deleted"}), 200
    return jsonify({"error": "Could not write to file"}), 500

# --- Main Execution ---
if __name__ == '__main__':
    ping3.EXCEPTIONS = True
    initialize_csv(DEVICES_FILE, ['id', 'address', 'friendlyName', 'tagId', 'roomId', 'notes'])
    initialize_csv(TAGS_FILE, ['id', 'name'])
    initialize_csv(ROOMS_FILE, ['id', 'name'])
    
    pinger_daemon = threading.Thread(target=continuous_pinger, daemon=True)
    pinger_daemon.start()

    print("--- Starting Flask Server (v3) ---")
    print("Features: Rooms, Dropdown Filters")
    print("----------------------------------")
    app.run(host='127.0.0.1', port=5000)
