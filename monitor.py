import socket
import logging
import subprocess
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Check if Minecraft server is already running
if os.system("systemctl is-active --quiet minecraft-server.service") == 0:
    logging.info("Minecraft server is already running. Exiting monitor.")
    exit()

HOST = '0.0.0.0'
PORT = 25565
DEBOUNCE_TIME = 5
last_attempt_time = 0

def wake_up_minecraft():
    logging.info("Waking up the server...")
    subprocess.call(["/bin/bash", "/var/www/minecraft/minecraft-wakeup.sh"])

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()

    logging.info(f"Started listening on port {PORT}")
    
    while True:
        conn, addr = s.accept()
        with conn:
            logging.info(f"Connection received from {addr}")
            
            # Read the initial data from the connection (at least 3 bytes)
            data = conn.recv(3)
            logging.info(f"Received {data}")
            if len(data) < 3:
                continue

            # Check if it's a login packet (value 2 after handshake packet ID)
            if data[2] == 2:
                wake_up_minecraft()
