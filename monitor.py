import socket
import logging
import subprocess
import os
import json
import time

# Setup logging
LOG_FILE_PATH = "/var/www/minecraft/monitor.log"
logging.basicConfig(filename=LOG_FILE_PATH, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filemode='a')
IDLE_THRESHOLD = 30 * 60 #seconds

HOST = '0.0.0.0'
PORT = 25565

def save_last_login_time(login_time):
    with open('/var/www/minecraft/lastLogin.json', 'w') as f:
        json.dump({"last_login_time": login_time}, f)

def load_last_login_time():
    try:
        with open('/var/www/minecraft/lastLogin.json', 'r') as f:
            data = json.load(f)
            return data["last_login_time"]
    except (FileNotFoundError, KeyError):
        return 0

last_login_time = load_last_login_time()

def wake_up_minecraft():
    logging.info("Waking up the server...")
    subprocess.call(["/bin/bash", "/var/www/minecraft/minecraft-wakeup.sh"])

def check_players():
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
            logging.info("Current time: " + str(time.time()))
            logging.info("Last login time: " + str(last_login_time))
            if players_online == 0:
                logging.info("No players online. Checking if we should shut down the server...")
                # If no players online for more than 30 minutes
                if time.time() - last_login_time > IDLE_THRESHOLD:
                    
                    logging.info("No players online for more than 30 minutes. Shutting down the server...")
                    subprocess.call(["systemctl", "stop", "minecraft-server.service"])
                    
            elif players_online > 0:
                save_last_login_time(time.time())

def main():
    while True:
        # Check if Minecraft server is already running
        if os.system("systemctl is-active --quiet minecraft-server.service") == 0:
            check_players()
            logging.info("Minecraft server is already running. Sleeping for a while before checking again.")
            time.sleep(30)
            continue

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
                break  # Exit from the inner while loop to start player-checking again.


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"An error occurred: {e}")