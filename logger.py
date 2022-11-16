import time
import traceback

from pynats import NATSClient
from pynats.exceptions import NATSReadSocketError

from config import GENERAL_LOG, PRINT_LOG
from utils import log, log_to_file, mem_add_to_log


def general_log(msg):
    msg = msg.payload.decode()
    log_to_file(msg, GENERAL_LOG)
    mem_add_to_log(GENERAL_LOG, msg)
    if PRINT_LOG:
        print(msg.replace('\n', ''))


def run():
    log(f"Logger started", GENERAL_LOG, 'INFO', to_mem=True)
    while True:
        try:
            with NATSClient() as client:

                # Connect
                client.connect()

                # Subscribe
                client.subscribe(subject=GENERAL_LOG, callback=general_log)

                # Listen
                while True:
                    client.wait(count=1)
        except NATSReadSocketError:
            log(f"NATSReadSocketError. Reconnect", GENERAL_LOG, "ERROR", to_mem=True)
            time.sleep(1)


if __name__ == '__main__':
    try:
        run()
    except KeyboardInterrupt:
        pass

    except Exception as e:
        log(f"{str(e)}", GENERAL_LOG, 'ERROR', to_mem=True)
        log(traceback.format_exc(), GENERAL_LOG, 'ERROR', to_mem=True)

