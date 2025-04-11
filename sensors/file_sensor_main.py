"""
Minimal file sensor main
"""
import time
import logging

# Basic logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/file_sensor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

def main():
    """Just print a message and stay alive."""
    logger.info("file sensor initialized")
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main() 