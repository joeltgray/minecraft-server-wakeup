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

def wake_up_minecraft():
    logging.info("Waking up the server...")
    subprocess.call(["/bin/bash", "/var/www/minecraft/minecraft-wakeup.sh"])

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    logging.info("Minecraft server is NOT already running. Continuing monitor.")
    s.bind((HOST, PORT))
    s.listen()
    logging.info(f"Started listening on port {PORT}")

    while True:
        conn, addr = s.accept()
        with conn:
            remote_ip, remote_port = addr
            local_ip, local_port = conn.getsockname()
            
            logging.info(f"Connection received from IP: {remote_ip}, Port: {remote_port}")
            logging.info(f"Accepted on local IP: {local_ip}, Port: {local_port}")

        logging.info(f"Connection received from {addr}")
        conn.close()  # Close the connection immediately after accepting it
        wake_up_minecraft()
        exit()
