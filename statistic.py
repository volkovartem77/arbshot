import time
import traceback

import simplejson

from config import GENERAL_LOG, ORDER_STATUS_NEW, ORDER_STATUS_CANCELED, ORDER_STATUS_FILLED, ORDER_SIDE_SELL
from rest.restBinanceSpot import RestBinanceSpot
from utils import log, mem_get_raw_stats, mem_get_order, decimal, mem_remove_raw_stats, mem_add_history, \
    mem_get_settings


def place_market_sell(rest, symbol, amount):
    log(f"Place MARKET {symbol} SELL {amount}", 'test', 'TEST')
    order = rest.place_market(symbol, amount, ORDER_SIDE_SELL)
    log(f"Market order {order}", 'test', 'TEST')
    return order


def run():
    mem_settings = mem_get_settings()
    rest = RestBinanceSpot(mem_settings['api_key'], mem_settings['api_secret'])

    log(f"Statistic started", GENERAL_LOG, 'INFO', to_mem=True)

    while True:
        raw_stats = mem_get_raw_stats()
        if raw_stats:
            for chain_id, raw_stat in raw_stats.items():
                raw_stat = simplejson.loads(raw_stat)
                order_1 = mem_get_order(raw_stat['order_1'])
                order_2 = mem_get_order(raw_stat['order_2'])
                order_3 = mem_get_order(raw_stat['order_3'])
                timestamp = raw_stat['timestamp']

                if order_1 and order_2 and order_3:
                    statuses = [order_1['status'], order_2['status'], order_3['status']]
                    size_usdt = decimal(raw_stat['size_usdt'])
                    profit_usdt = None
                    amount_token_left = None
                    amount_token_left_in_usdt = None

                    if ORDER_STATUS_NEW in statuses:
                        chain_status = 'HOLDING'
                    elif ORDER_STATUS_CANCELED in statuses:
                        chain_status = 'CANCELED'
                        mem_remove_raw_stats(chain_id)
                        log(f"order_2['status']={order_2['status']}; order_3['status']={order_3['status']}",
                            'test', 'INFO', to_mem=True)

                        # Execute at Market
                        if order_2['status'] == ORDER_STATUS_CANCELED and order_3['status'] == ORDER_STATUS_FILLED:
                            market_order = place_market_sell(rest, order_2['symbol'], decimal(order_2['amount']))
                            amount_btc_received = decimal(market_order['cummulativeQuoteQty'])
                            amount_usdt_received_1 = decimal(order_3['amount_received'])
                            amount_usdt_received_2 = amount_btc_received * decimal(order_3['price'])
                            amount_usdt_diff = amount_usdt_received_1 - amount_usdt_received_2

                            amount_token_left = decimal(raw_stat['amount_token_left'])
                            amount_token_left_in_usdt = amount_token_left * decimal(order_1['price'])
                            profit_usdt = decimal(order_3['amount_received']) - size_usdt
                            profit_usdt = profit_usdt - amount_token_left_in_usdt
                            profit_usdt = profit_usdt - amount_usdt_diff
                            profit_usdt = round(profit_usdt, 4)

                            # log(f"amount_btc_received={amount_btc_received}\n"
                            #     f"amount_usdt_received_1={amount_usdt_received_1}\n"
                            #     f"order_3_price={order_3['price']}\n"
                            #     f"amount_usdt_received_2={amount_usdt_received_2}\n"
                            #     f"amount_token_left={amount_token_left}\n"
                            #     f"order_1_price={order_1['price']}\n"
                            #     f"amount_token_left_in_usdt={amount_token_left_in_usdt}\n"
                            #     f"profit_usdt={profit_usdt}",
                            #     'test', 'TEST')
                    else:
                        chain_status = 'COMPLETED'
                        amount_token_left = decimal(raw_stat['amount_token_left'])
                        amount_token_left_in_usdt = amount_token_left * decimal(order_1['price'])
                        profit_usdt = decimal(order_3['amount_received']) - size_usdt
                        profit_usdt = profit_usdt - amount_token_left_in_usdt
                        profit_usdt = round(profit_usdt, 4)
                        mem_remove_raw_stats(chain_id)

                    mem_add_history(chain_id, {
                        'datetime': raw_stat['datetime'],
                        'arb': raw_stat['arb'],
                        'size_usdt': size_usdt,
                        'status': chain_status,
                        'diff': '{:.4f}'.format(raw_stat['efficiency']),
                        'profit_usdt': profit_usdt,
                        'amount_token_left': amount_token_left,
                        'amount_token_left_in_usdt': amount_token_left_in_usdt,
                        'timestamp': timestamp
                    })
        time.sleep(0.5)


if __name__ == '__main__':
    try:
        run()
    except KeyboardInterrupt:
        pass

    except Exception as e:
        log(f"{str(e)}", GENERAL_LOG, 'ERROR', to_mem=True)
        log(traceback.format_exc(), GENERAL_LOG, 'ERROR', to_mem=True)
