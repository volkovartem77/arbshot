import argparse
import asyncio
import time

import simplejson
import websockets
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

from exceptions import NoConnectionException
from utils import log, time_now_ms


fastest = 999
longest = 0
all_ms = []


async def on_message(msg):
    global fastest, longest, all_ms

    t = time_now_ms()
    msg = simplejson.loads(msg)
    ms = t - msg['E']

    if ms < fastest:
        fastest = ms
    if ms > longest:
        longest = ms
    all_ms.append(ms)
    avg = round(sum(all_ms) / len(all_ms), 3)
    print(f"{ms}ms   min: {fastest}ms   max: {longest}ms   avg: {avg}ms")


async def on_open():
    log(f'WS {symbol}: Connected', log_file_name, 'INFO')


async def run():
    while True:
        try:
            endpoint = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@trade"

            async with websockets.connect(endpoint) as websocket:
                await on_open()
                while True:
                    msg = await websocket.recv()
                    await on_message(msg)
        except (ConnectionClosedError, NoConnectionException, ConnectionClosedOK):
            log(f'WS {symbol}: Connection closed. Reconnecting..', log_file_name, 'INFO')
            time.sleep(1)

if __name__ == "__main__":
    try:
        # Parse arguments
        parser = argparse.ArgumentParser()
        parser.add_argument('--symbol', help='example: BTCUSDT')
        args = parser.parse_args()
        if args.symbol:
            symbol = str(args.symbol)
            log_file_name = f"ws_test"

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            asyncio.run(run())
        else:
            raise Exception('Empty arguments')

    except KeyboardInterrupt:
        exit()
