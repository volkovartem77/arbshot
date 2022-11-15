import asyncio
import threading
import time

import simplejson
import websockets
from requests import ReadTimeout
from websockets.exceptions import ConnectionClosedError

from config import STREAM_LOG
from exceptions import NoConnectionException
from rest.restBinanceSpot import RestBinanceSpot
from utils import mem_set_balance, mem_get_settings, log, time_now_ms, mem_get_balance, retrying


async def on_message(msg):
    try:
        msg = simplejson.loads(msg)
        # print(time.time(), msg)

        if 'e' in msg:
            # Update balances
            if msg['e'] == 'outboundAccountPosition':
                balance = mem_get_balance()
                if balance is not None:
                    for balance_info in msg['B']:
                        balance.update({balance_info['a']: balance_info['f']})
                    balance.update({'updateTime': time_now_ms()})
                    mem_set_balance(balance)
                    log(f"Update balance {balance}", log_file_name, 'STREAM')

    except Exception as e:
        log(f'stream: {e}', log_file_name, 'ERROR')


async def on_open(listen_key):
    def keepalive():
        ts = time.time()
        while True:
            try:
                if time.time() > ts + 30 * 60:
                    rest.stream_keepalive(listen_key)
                    ts = time.time()
                time.sleep(30)
            except NoConnectionException:
                log(f"NoConnectionException", STREAM_LOG, 'ERROR')
                time.sleep(1)

    x = threading.Thread(target=keepalive)
    x.start()

    log(f'stream: Connected', log_file_name, 'STREAM')

    # Update balance
    balance = retrying(rest.get_all_balances, {}, ReadTimeout, 5, 2)
    balance.update({'updateTime': time_now_ms()})
    mem_set_balance(balance)
    log(f"Update balance {balance}", log_file_name, 'STREAM')


async def run():
    while True:
        try:
            listen_key = retrying(rest.stream_get_listen_key, {}, ReadTimeout, 5, 2)
            log(f'stream: listen key {listen_key}', log_file_name, 'STREAM')
            endpoint = f"wss://stream.binance.com:9443/ws/{listen_key}"

            async with websockets.connect(endpoint) as websocket:
                await on_open(listen_key)
                while True:
                    msg = await websocket.recv()
                    await on_message(msg)
        except (ConnectionClosedError, NoConnectionException):
            log(f'stream: Connection closed. Reconnecting..', log_file_name, 'STREAM')
            time.sleep(1)

if __name__ == '__main__':
    try:
        # Init
        log_file_name = STREAM_LOG
        mem_set_balance({})

        mem_settings = mem_get_settings()
        rest = RestBinanceSpot(mem_settings['api_key'], mem_settings['api_secret'])

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        asyncio.run(run())
    except KeyboardInterrupt:
        exit()
