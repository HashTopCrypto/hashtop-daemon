from datetime import datetime
import logging
import os


def setup_logger():
    log_dir = os.path.dirname(os.path.abspath(__file__)) + "/daemon-logs/"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    timestamp = datetime.now().strftime("%m-%d-%Y_%H:%M")
    logging.basicConfig(filename=log_dir + f"{timestamp}", filemode='w', level=logging.WARNING,
                        format='%(asctime)s %(levelname)s %(name)s %(message)s')
    logger = logging.getLogger(__name__)

    return logger


logger = setup_logger()
