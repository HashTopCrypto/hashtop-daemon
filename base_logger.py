from datetime import datetime
import logging
import os
import sys

logger = logging
LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO').upper()
print(LOGLEVEL)

log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
timestamp = datetime.now().strftime("%m-%d-%Y_%H:%M")

# noinspection PyArgumentList
logger.basicConfig(level=LOGLEVEL,
                   format='%(asctime)s %(levelname)s %(name)s %(message)s',
                   handlers=[
                       logging.FileHandler(f"{log_dir}/{timestamp}.log"),
                       logging.StreamHandler()
                   ])
#log_dir = os.path.dirname(os.path.abspath(__file__)) + "/logs/"

