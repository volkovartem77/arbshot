import asyncio
import time
import traceback
from decimal import Decimal

import simplejson
from pynats import NATSClient

from config import GENERAL_LOG, SYMBOLS_INFO, ORDER_SIDE_BUY, ORDER_STATUS_FILLED, ORDER_SIDE_SELL
from exceptions import TimestampError
from models import Params
from rest.restBinanceSpot import RestBinanceSpot
from utils import mem_get_balance, quote_to_base, decimal, round_up, round_down, time_diff_ms, datetime_str_ms, log, \
    datetime_str, mem_add_raw_stats, make_chain_id, make_client_order_id, time_now_mcs


class Trading:
    def __init__(self, params: Params):
        self.rest = RestBinanceSpot(params.APIKey, params.APISecret)
        self.OrderAmountPrc = params.OrderAmountPrc
        self.TakerFee = params.TakerFee
        self.AmountBTCLock = params.AmountBTCLock
        self.RecvWindow = params.RecvWindow

        self.Balance = {}

        # Init NATSConnection
        self.NATS = NATSClient()
        self.NATS.connect()

    def log(self, text, module, mark=''):
        dt = datetime_str_ms()
        payload = dt + ' ' + mark + ' ' + text + '\n'
        try:
            self.NATS.publish(subject=module, payload=payload.encode())
        except BrokenPipeError:
            self.NATS.connect()
            self.NATS.publish(subject=module, payload=payload.encode())

    @staticmethod
    def raw_stat(arb, size_usdt, efficiency, order_1, order_2, order_3, placing_speed_1, placing_speed_2,
                 placing_speed_3, amount_token_left, get_spread_speed, calc_spread_speed):
        chain_id = make_chain_id()
        payload = simplejson.dumps({
            'datetime': datetime_str(),
            'arb': arb,
            'size_usdt': size_usdt,
            'efficiency': efficiency,
            'order_1': order_1['clientOrderId'],
            'order_2': order_2['clientOrderId'],
            'order_3': order_3['clientOrderId'],
            'placing_speed_1': placing_speed_1,
            'placing_speed_2': placing_speed_2,
            'placing_speed_3': placing_speed_3,
            'amount_token_left': amount_token_left,
            'get_spread_speed': get_spread_speed,
            'calc_spread_speed': calc_spread_speed,
            'timestamp': time_now_mcs()
        })
        mem_add_raw_stats(chain_id, payload)

    @staticmethod
    def price_to_precision(symbol, price: Decimal):
        return round(price, decimal(SYMBOLS_INFO[symbol]['price_precision']))

    @staticmethod
    def amount_to_precision(symbol, amount: Decimal, price: Decimal):
        amount_precision = int(SYMBOLS_INFO[symbol]['amount_precision'])
        conv = decimal(SYMBOLS_INFO[symbol]['min_amount']) / price
        min_amount = round_up(conv, amount_precision)
        my_amount = round_down(amount, amount_precision)
        # log(f'Min {min_amount} My {my_amount} ({symbol} {price})', GENERAL_LOG, 'TEST')
        return my_amount if my_amount >= min_amount else 0

    @staticmethod
    def amount_to_precision_2(symbol, amount: Decimal, price: Decimal, balance_token_remain: Decimal):
        amount_precision = int(SYMBOLS_INFO[symbol]['amount_precision'])
        conv = decimal(SYMBOLS_INFO[symbol]['min_amount']) / price
        min_amount = round_up(conv, amount_precision)

        balance_token = amount + balance_token_remain
        my_amount = round_up(amount, amount_precision)
        if my_amount > balance_token:
            my_amount = round_down(amount, amount_precision)

        return my_amount if my_amount >= min_amount else 0

    def amount_to_precision_3(self, symbol, amount: Decimal, price: Decimal, balance_btc_remain: Decimal):
        amount_precision = int(SYMBOLS_INFO[symbol]['amount_precision'])
        conv = decimal(SYMBOLS_INFO[symbol]['min_amount']) / price
        min_amount = round_up(conv, amount_precision)

        balance_btc = balance_btc_remain - decimal(self.AmountBTCLock)
        my_amount = round_up(amount, amount_precision)
        if my_amount > balance_btc:
            my_amount = round_down(amount, amount_precision)

        return my_amount if my_amount >= min_amount else 0

    def get_amount_btc(self, symbol, price):
        balance_usdt = self.Balance['USDT']
        amount_usdt = balance_usdt * decimal(self.OrderAmountPrc / 100)
        amount_btc = self.amount_to_precision(symbol, quote_to_base(amount_usdt, price), price)
        return amount_btc

    def get_amount_token(self, symbol_1, symbol_2, price_1, price_2, max_amount_token):
        balance_usdt = self.Balance['USDT']
        balance_btc = self.Balance['BTC']

        if self.amount_to_precision(symbol_1, max_amount_token, price_1) == 0:
            return 0

        max_amount_token = self.amount_to_precision(symbol_1, max_amount_token, price_1)
        amount_usdt = balance_usdt * decimal(self.OrderAmountPrc / 100)
        amount_token = quote_to_base(amount_usdt, price_1)
        amount_token = self.amount_to_precision(symbol_1, amount_token, price_1)

        max_amount_token_from_btc = self.amount_to_precision(symbol_2, balance_btc / price_2, price_2)
        max_amount_token_from_btc = self.amount_to_precision(symbol_1, max_amount_token_from_btc, price_1)
        return min(amount_token, max_amount_token, max_amount_token_from_btc)

    def place_limit_order(self, symbol, amount, price, side, base):
        self.log(f"Send LIMIT {symbol} {side} {amount} {base} @{price}", GENERAL_LOG, 'INFO')
        client_order_id = make_client_order_id()
        t = time.time()
        order = self.rest.place_limit(symbol, amount, price, side, time_in_force='GTC', client_order_id=client_order_id)
        placing_speed = time_diff_ms(t)
        self.log(f"Order {order['clientOrderId'][:14]} {order['type']} {order['symbol']} {order['side']} "
                 f"{order['origQty']} {base} @{order['price']} {order['status']}", GENERAL_LOG, 'INFO')
        self.log(f"Order {order['clientOrderId'][:14]} PlacingSpeed={placing_speed} ms "
                 f"TransactTime={order['transactTime']}", GENERAL_LOG, 'INFO')
        return order, placing_speed

    def place_limit_fok_order(self, symbol, amount, price, side, base):
        self.log(f"Send LIMIT {symbol} {side} {amount} {base} @{price}", GENERAL_LOG, 'INFO')
        client_order_id = make_client_order_id()
        t = time.time()
        order = self.rest.place_limit(symbol, amount, price, side, time_in_force='FOK', client_order_id=client_order_id,
                                      recv_window=self.RecvWindow)
        placing_speed = time_diff_ms(t)
        self.log(f"Order {order['clientOrderId'][:14]} {order['type']} {order['symbol']} {order['side']} "
                 f"{order['origQty']} {base} @{order['price']} {order['status']}", GENERAL_LOG, 'INFO')
        self.log(f"Order {order['clientOrderId'][:14]} PlacingSpeed={placing_speed} ms "
                 f"TransactTime={order['transactTime']}", GENERAL_LOG, 'INFO')
        return order, placing_speed

    async def place_limit_order_async(self, symbol, amount, price, side, base):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.place_limit_order, symbol, amount, price, side, base)

    def place_orders_async(self, params1, params2):
        async def place():
            task_1 = asyncio.create_task(self.place_limit_order_async(*params1))
            task_2 = asyncio.create_task(self.place_limit_order_async(*params2))

            order_1 = await task_1
            order_2 = await task_2
            return order_1[0], order_2[0], order_1[1], order_2[1]

        return asyncio.run(place())

    def execute(self, chain, get_spread_speed, calc_spread_speed):
        try:
            arb = chain[0]
            forward = chain[1]
            efficiency = decimal(chain[2])
            symbol_1 = chain[3]
            symbol_2 = chain[4]
            symbol_3 = chain[5]
            price_1 = decimal(chain[6])
            price_2 = decimal(chain[7])
            price_3 = decimal(chain[8])
            max_amount_token = decimal(chain[9])
            fee = decimal(1 - (self.TakerFee / 100))
            token = SYMBOLS_INFO[symbol_1]['base']

            # Update balance
            self.Balance = mem_get_balance()

            if forward:
                amount_token = self.get_amount_token(symbol_1, symbol_2, price_1, price_2, max_amount_token)
                if amount_token == 0:
                    # self.log(f"SKIPPED Not enough balance USDT or BTC", GENERAL_LOG, arb)
                    return

                self.log(f"Balance now {self.Balance['USDT']} USDT  {self.Balance['BTC']} BTC", GENERAL_LOG, 'INFO')

                # Step 1: Place LIMIT (FOK) BUY TOKEN/USDT
                balance_token_remain = self.Balance[token] if token in self.Balance else 0
                balance_btc_remain = self.Balance['BTC']
                try:
                    order_1, p_speed_1 = self.place_limit_fok_order(symbol_1, amount_token, price_1,
                                                                    ORDER_SIDE_BUY, token)
                    if order_1['status'] == ORDER_STATUS_FILLED:
                        amount_spent_usdt = decimal(order_1['cummulativeQuoteQty'])
                        commission_token = sum([decimal(fill['commission']) for fill in order_1['fills']])
                        amount_received_token = amount_token - commission_token
                        amount_token_2 = self.amount_to_precision_2(symbol_2, amount_received_token, price_2,
                                                                    balance_token_remain)
                        if amount_token_2 == 0:
                            self.log(f"ARBITRAGE BROKEN {amount_token - commission_token} {token} left",
                                     GENERAL_LOG, arb)
                            return
                        params1 = (symbol_2, amount_token_2, price_2, ORDER_SIDE_SELL, token)

                        amount_received_btc = amount_token_2 * price_2 * fee
                        amount_received_btc = self.amount_to_precision_3(symbol_3, amount_received_btc, price_3,
                                                                         balance_btc_remain)
                        if amount_received_btc == 0:
                            self.log(f"ARBITRAGE BROKEN {amount_token_2 * price_2 * fee} BTC left",
                                     GENERAL_LOG, arb)
                            return
                        params2 = (symbol_3, amount_received_btc, price_3, ORDER_SIDE_SELL, 'BTC')

                        # Step 2: Place LIMIT LIMIT (GTC) TOKEN/BTC BTC/USDT
                        order_2, order_3, p_speed_2, p_speed_3 = self.place_orders_async(params1, params2)
                        self.log(f"ARBITRAGE HOLDING TradeSize {amount_spent_usdt} USDT", GENERAL_LOG, arb)

                        # Statistic
                        amount_token_left = amount_received_token - amount_token_2
                        self.raw_stat(arb, amount_spent_usdt, efficiency, order_1, order_2, order_3, p_speed_1,
                                      p_speed_2, p_speed_3, amount_token_left, get_spread_speed, calc_spread_speed)
                    else:
                        self.log(f"ARBITRAGE CANCELLED", GENERAL_LOG, arb)
                except TimestampError:
                    self.log(f"ARBITRAGE CANCELLED recvWindow={self.RecvWindow}", GENERAL_LOG, arb)
            else:
                self.log(f"Backward not implemented", GENERAL_LOG, arb)

        except Exception as e:
            log(str(e), GENERAL_LOG, 'ERROR', to_mem=True)
            log(str(chain), GENERAL_LOG, 'ERROR', to_mem=True)
            log(traceback.format_exc(), GENERAL_LOG, 'ERROR', to_mem=True)
