import socket
import logging
import subprocess
import os
import json
import time

# Setup logging
LOG_FILE_PATH = "/var/www/minecraft/monitor.log"
logging.basicConfig(filename=LOG_FILE_PATH, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filemode='a')
IDLE_THRESHOLD = 60

HOST = '0.0.0.0'
PORT = 25565

def save_last_attempt_time(attempt_time):
    with open('/var/www/minecraft/lastLogin.json', 'w') as f:
        json.dump({"last_attempt_time": attempt_time}, f)

def load_last_attempt_time():
    try:
        with open('/var/www/minecraft/lastLogin.json', 'r') as f:
            data = json.load(f)
            return data["last_attempt_time"]
    except (FileNotFoundError, KeyError):
        return 0

last_attempt_time = load_last_attempt_time()

def wake_up_minecraft():
    logging.info("Waking up the server...")
    subprocess.call(["/bin/bash", "/var/www/minecraft/minecraft-wakeup.sh"])

def check_players_and_shutdown():
    # If the hardcopy file doesn't exist, create it
    if not os.path.exists('/var/www/minecraft/playerMonitor'):
        with open('/var/www/minecraft/playerMonitor', 'w') as f:
            pass  # Just creating the file

    # Send the list command to the server and capture the output
    output = subprocess.getoutput('screen -S minecraft -X stuff "list\n"')
    time.sleep(2)  # give the server a second to respond
    output = subprocess.getoutput('screen -S minecraft -X hardcopy /var/www/minecraft/playerMonitor')
    
    # Read the hardcopy file
    with open('/var/www/minecraft/playerMonitor', 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        if "There are" in line:
            # Extract the number of online players
            players_online = int(line.split()[5])
            logging.info(f"Players online: {players_online}")
            if players_online == 0:
                # If no players online for more than 30 minutes
                if time.time() - last_attempt_time > IDLE_THRESHOLD:
                    logging.info("No players online for more than 30 minutes. Shutting down the server...")
                    subprocess.call(["systemctl", "stop", "minecraft-server.service"])
                    save_last_attempt_time(time.time())

# Check if Minecraft server is already running
if os.system("systemctl is-active --quiet minecraft-server.service") == 0:
    check_players_and_shutdown()
    logging.info("Minecraft server is already running. Exiting monitor.")
    exit()

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
