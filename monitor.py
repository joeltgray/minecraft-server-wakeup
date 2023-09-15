import socket
import time
import subprocess
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Socket setup to monitor port 25565
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(("0.0.0.0", 25565))
s.listen(5)
logging.info("Started listening on port 25565")

# Debounce function
def debounce(seconds):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            if hasattr(wrapper, '_last_called'):
                elapsed = time.time() - wrapper._last_called
                if elapsed < seconds:
                    return
            wrapper._last_called = time.time()
            return fn(*args, **kwargs)
        return wrapper
    return decorator

@debounce(5)  # ensures the function can't be called more than once every 5 seconds
def wakeup_server():
    logging.info("Waking up the server...")
    subprocess.run(["/var/www/minecraft/minecraft-wakeup.sh"])

while True:
    connection, address = s.accept()
    logging.info(f"Connection received from {address}")
    wakeup_server()
    connection.close()
