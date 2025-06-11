# PingyThingy - A Simple Network Device Status Tracker

PingyThingy is a lightweight, self-hosted web application designed to give you an at-a-glance overview of the online status of your local network devices. It's perfect for small offices, home labs, or managing IT/AV equipment in a specific location.

The application consists of a simple Python backend that handles the pinging and data storage, and a clean, single-file HTML frontend for a responsive user interface.

## Features

* **Real-time Status Monitoring:** Devices are pinged at a configurable interval to provide near real-time online/offline status.
* **Dynamic Dashboard:** Devices are automatically sorted to show offline devices first, so problems are immediately visible.
* **System Health Overview:** An uptime percentage bar gives you an instant health check of all your monitored devices.
* **Offline Notifications:** Receive a temporary pop-up banner when a device changes from online to offline.
* **Categorization:** Organize your devices using both **Tags** (e.g., "Lectern PC", "Camera") and **Rooms**.
* **Powerful Filtering:** Instantly filter the view by status, tag, room, or a combination, using dropdown menus.
* **Live Search:** Find any device quickly by searching for its name, address, or notes.
* **Smart Connection Button:**
    * For most devices, a button opens the device's IP/hostname in a new tab.
    * For devices tagged as "Lectern PC", the button intelligently changes to download a pre-configured **.rdp file** for an instant Remote Desktop connection.
* **Easy Data Management:** All devices, tags, and rooms are stored in simple `.csv` files for easy manual editing and backup.

## Setup & Installation

PingyThingy is split into two parts: the **Backend** (the server that does the work) and the **Frontend** (the webpage you look at).

### 1. Backend Setup

The backend is a Python script that requires a few libraries.

**Prerequisites:**
* Python 3

**Installation:**
1.  Place the `backend.py` file in a new folder.
2.  Create the `requirements.txt` file in the same folder.
3.  Open a terminal in that folder and run the following command to install the necessary Python packages:
    ```bash
    pip install -r requirements.txt
    ```
4.  Run the backend server. **On Linux, you will need to use `sudo`** because the ping library requires elevated permissions.
    ```bash
    # On Linux/macOS
    sudo python3 backend.py

    # On Windows (run terminal as Administrator)
    python backend.py
    ```
    The backend is now running. It will automatically create `devices.csv`, `tags.csv`, and `rooms.csv` if they don't exist.

### 2. Frontend Setup

The frontend is a single HTML file.

1.  Place the `index.html` file in a convenient location.
2.  Open the `index.html` file directly in your web browser (e.g., Chrome, Firefox, Edge).

That's it! The webpage will connect to your running backend and display the PingyThingy dashboard.
