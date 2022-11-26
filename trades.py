import time
import traceback

import simplejson

from config import GENERAL_LOG, ORDER_STATUS_NEW, ORDER_STATUS_CANCELED, ORDER_STATUS_FILLED
from utils import log, mem_get_order, mem_get_raw_orders, mem_add_trade, timestamp_to_datetime_str, \
    scientific_to_str, datetime_diff, time_now_ms, mem_remove_raw_order


def run():
    log(f"Trades started", GENERAL_LOG, 'INFO', to_mem=True)

    while True:
        raw_orders = mem_get_raw_orders()
        if raw_orders:
            for order_id, raw_order in raw_orders.items():
                raw_order = simplejson.loads(raw_order)

                send_time = timestamp_to_datetime_str(int(raw_order['send_time'])).split(' ')[1]
                amount = f"{scientific_to_str(raw_order['amount'])} {raw_order['token']}"
                price = f"{scientific_to_str(raw_order['price'])}"
                status = raw_order['status']
                placing_speed = (int(raw_order['recv_time']) - int(raw_order['send_time'])) / 1000
                creation_time = ""
                update_time = ""
                recv_time = timestamp_to_datetime_str(int(raw_order['recv_time'])).split(' ')[1]
                holding_time = ""

                ws_order = mem_get_order(order_id)
                if ws_order:
                    status = ws_order['status']
                    creation_time = timestamp_to_datetime_str(int(ws_order['creation_time'])).split(' ')[1]
                    update_time = timestamp_to_datetime_str(int(ws_order['transact_time'])).split(' ')[1]

                    if status in [ORDER_STATUS_FILLED, ORDER_STATUS_CANCELED]:
                        holding_time = datetime_diff(int(ws_order['creation_time']), int(ws_order['transact_time']))
                        mem_remove_raw_order(order_id)
                    elif status == ORDER_STATUS_NEW:
                        holding_time = datetime_diff(int(ws_order['creation_time']), time_now_ms())

                mem_add_trade(order_id, {
                    'send_time': send_time,
                    'order_id': order_id,
                    'arb': raw_order['arb'],
                    'time_in_force': raw_order['time_in_force'],
                    'symbol': raw_order['symbol'],
                    'side': raw_order['side'],
                    'amount': amount,
                    'token': raw_order['token'],
                    'price': price,
                    'status': status,
                    'placing_speed': placing_speed,
                    'creation_time': creation_time,
                    'update_time': update_time,
                    'recv_time': recv_time,
                    'holding_time': holding_time,
                    'timestamp': int(raw_order['send_time'])
                })
        time.sleep(1)


if __name__ == '__main__':
    try:
        run()
    except KeyboardInterrupt:
        pass

    except Exception as e:
        log(f"{str(e)}", GENERAL_LOG, 'ERROR', to_mem=True)
        log(traceback.format_exc(), GENERAL_LOG, 'ERROR', to_mem=True)

# TODO:
#  send_time | order_id | arb | time_in_force | symbol | side | amount (token) | price | status | PlacingSpeed | CreationTime| UpdateTime | ReceiveTime | HoldingTime
#  11:19:11.543 | arb_2dbe21f576 | USDT-WRX-BTC-USDT | FOK | WRXUSDT | BUY | 126.2 WRX | 0.1594 | FILLED | 17.032 | 11:19:11.549 | 11:19:11.549 | 11:19:11.554 | 1d 14h 12m 26.074

# raw_order = {
#     'send_time',
#     'arb',
#     'time_in_force',
#     'symbol',
#     'side',
#     'amount',
#     'token',
#     'status',
#     'recv_time'
# }
