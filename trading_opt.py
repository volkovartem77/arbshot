import asyncio
import time
import traceback
from decimal import Decimal

import simplejson
from pynats import NATSClient

from config import GENERAL_LOG, SYMBOLS_INFO, ORDER_SIDE_BUY, ORDER_STATUS_FILLED, ORDER_SIDE_SELL
from exceptions import TimestampError, NoBalanceException
from models import Params
from rest.restBinanceSpot import RestBinanceSpot
from utils import mem_get_balance, quote_to_base, decimal, round_up, round_down, datetime_str_ms, log, \
    datetime_str, mem_add_raw_stats, make_chain_id, make_client_order_id, time_now_mcs


class TradingOpt:
    def __init__(self, params: Params):
        self.rest = RestBinanceSpot(params.APIKey, params.APISecret)
        self.OrderAmountPrc = params.OrderAmountPrc
        self.TakerFee = params.TakerFee
        self.AmountBTCLock = params.AmountBTCLock
        self.RecvWindow = params.RecvWindow

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
    def amount_to_precision_up(symbol, amount: Decimal, price: Decimal, balance_token_remain: Decimal):
        amount_precision = int(SYMBOLS_INFO[symbol]['amount_precision'])
        conv = decimal(SYMBOLS_INFO[symbol]['min_amount']) / price
        min_amount = round_up(conv, amount_precision)

        balance_token = amount + balance_token_remain
        my_amount = round_up(amount, amount_precision)
        if my_amount > balance_token:
            my_amount = round_down(amount, amount_precision)

        return my_amount if my_amount >= min_amount else 0

    def amount_to_precision_btc(self, symbol, amount: Decimal, price: Decimal, balance_btc_remain: Decimal):
        amount_precision = int(SYMBOLS_INFO[symbol]['amount_precision'])
        conv = decimal(SYMBOLS_INFO[symbol]['min_amount']) / price
        min_amount = round_up(conv, amount_precision)

        balance_btc = balance_btc_remain - decimal(self.AmountBTCLock)
        my_amount = round_up(amount, amount_precision)
        if my_amount > balance_btc:
            my_amount = round_down(amount, amount_precision)

        return my_amount if my_amount >= min_amount else 0

    def get_amount_token(self, symbol_1, price_1, symbol_2, price_2, max_amount_token, balance_usdt, balance_btc):
        max_amount_token = self.amount_to_precision(symbol_1, max_amount_token, price_1)
        amount_usdt = balance_usdt * decimal(self.OrderAmountPrc / 100)
        amount_token = quote_to_base(amount_usdt, price_1)
        amount_token = self.amount_to_precision(symbol_1, amount_token, price_1)

        max_amount_token_from_btc = self.amount_to_precision(symbol_2, balance_btc / price_2, price_2)
        max_amount_token_from_btc = self.amount_to_precision(symbol_1, max_amount_token_from_btc, price_1)
        return min(amount_token, max_amount_token, max_amount_token_from_btc)

    def place_limit_order(self, order_id, symbol, amount, price, side):
        try:
            send_time = time_now_mcs()
            order = self.rest.place_limit(symbol, amount, price, side, time_in_force='GTC', client_order_id=order_id)
            return order, send_time, time_now_mcs()
        except NoBalanceException:
            return None

    def place_limit_fok_order(self, order_id, symbol, amount, price, side):
        try:
            send_time = time_now_mcs()
            order = self.rest.place_limit(symbol, amount, price, side, time_in_force='FOK', client_order_id=order_id,
                                          recv_window=self.RecvWindow)
            return order, send_time, time_now_mcs()
        except TimestampError:
            return None

    async def place_limit_order_async(self, order_id, symbol, amount, price, side):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.place_limit_order, order_id, symbol, amount, price, side)

    async def place_limit_fok_order_async(self, symbol, amount, price, side, base):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.place_limit_fok_order, symbol, amount, price, side, base)

    def place_orders_async(self, params1, params2):
        async def place():
            task_fok = asyncio.create_task(self.place_limit_fok_order_async(*params1))
            task_gtc_1 = asyncio.create_task(self.place_limit_order_async(*params2))
            task_gtc_2 = asyncio.create_task(self.place_limit_order_async(*params2))
            task_gtc_3 = asyncio.create_task(self.place_limit_order_async(*params2))
            task_gtc_4 = asyncio.create_task(self.place_limit_order_async(*params2))
            task_gtc_5 = asyncio.create_task(self.place_limit_order_async(*params2))

            order_fok = await task_fok
            order_gtc_1 = await task_gtc_1
            if order_gtc_1:
                return order_fok, order_gtc_1
            order_gtc_2 = await task_gtc_2
            if order_gtc_2:
                return order_fok, order_gtc_2
            order_gtc_3 = await task_gtc_3
            if order_gtc_3:
                return order_fok, order_gtc_3
            order_gtc_4 = await task_gtc_4
            if order_gtc_4:
                return order_fok, order_gtc_4
            order_gtc_5 = await task_gtc_5
            if order_gtc_5:
                return order_fok, order_gtc_5
            return order_fok, None

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
            fee = decimal(self.TakerFee / 100)
            token = SYMBOLS_INFO[symbol_1]['base']

            # Update balance
            balance = mem_get_balance()
            balance_usdt = balance['USDT']
            balance_token = balance[token] if token in balance else 0
            balance_btc = balance['BTC']

            if forward:
                amount_token_buy = self.get_amount_token(symbol_1, price_1, symbol_2, price_2, max_amount_token,
                                                         balance_usdt, balance_btc)
                if amount_token_buy == 0:
                    # self.log(f"SKIPPED Not enough balance USDT or low amount in orderbook", GENERAL_LOG, arb)
                    return

                # self.log(f"Balance {balance_usdt} USDT "
                #          f"{balance_token} {token} {balance_btc} BTC", GENERAL_LOG, 'INFO')

                # Order 1: LIMIT (FOK) BUY TOKEN/USDT
                order_id_1 = make_client_order_id()
                order_params_1 = (order_id_1, symbol_1, amount_token_buy, price_1, ORDER_SIDE_BUY)

                # Order 2: LIMIT (GTC) SELL TOKEN/BTC
                commission_token = round_up(amount_token_buy * fee, 8)
                amount_recv_token = amount_token_buy - commission_token
                amount_token_sell = self.amount_to_precision_up(symbol_2, amount_recv_token, price_2, balance_token)
                order_id_2 = make_client_order_id()
                order_params_2 = (order_id_2, symbol_2, amount_token_sell, price_2, ORDER_SIDE_SELL)

                # Order 3: LIMIT (GTC) SELL BTC/USDT
                amount_recv_btc = amount_token_sell * price_2
                commission_btc = round_up(amount_recv_btc * fee, 8)
                amount_recv_btc = amount_recv_btc - commission_btc
                amount_btc_sell = self.amount_to_precision_btc(symbol_3, amount_recv_btc, price_3, balance_btc)
                order_id_3 = make_client_order_id()
                order_params_3 = (order_id_3, symbol_3, amount_btc_sell, price_3, ORDER_SIDE_SELL)

                # Placing
                order_1, order_2 = self.place_orders_async(order_params_1, order_params_2)
                if order_1:
                    if order_1['status'] == ORDER_STATUS_FILLED:
                        amount_spent_usdt = decimal(order_1[0]['cummulativeQuoteQty'])

                        if order_2:
                            order_3 = self.place_limit_order(*order_params_3)
                            if order_3:
                                self.log(f"ARBITRAGE HOLDING TradeSize {amount_spent_usdt} USDT", GENERAL_LOG, 'INFO')

                                # Statistic
                                amount_token_left = amount_recv_token - amount_token_sell
                                p_speed_1 = (order_1[2] - order_1[1]) / 1000
                                p_speed_2 = (order_2[2] - order_2[1]) / 1000
                                p_speed_3 = (order_3[2] - order_3[1]) / 1000
                                self.raw_stat(arb, amount_spent_usdt, efficiency, order_1, order_2, order_3, p_speed_1,
                                              p_speed_2, p_speed_3, amount_token_left, get_spread_speed,
                                              calc_spread_speed)
                            else:
                                self.log(f"ARBITRAGE BROKEN {amount_recv_btc} BTC left", GENERAL_LOG, arb)
                        else:
                            self.log(f"ARBITRAGE BROKEN {amount_recv_token} {token} left", GENERAL_LOG, arb)
                    else:
                        self.log(f"ARBITRAGE CANCELLED", GENERAL_LOG, arb)
                else:
                    self.log(f"ARBITRAGE CANCELLED recvWindow={self.RecvWindow}", GENERAL_LOG, arb)

                # Rate-limit: 50 orders / 10 sec
                time.sleep(5)
            else:
                self.log(f"Backward not implemented", GENERAL_LOG, arb)

        except Exception as e:
            log(str(e), GENERAL_LOG, 'ERROR', to_mem=True)
            log(str(chain), GENERAL_LOG, 'ERROR', to_mem=True)
            log(traceback.format_exc(), GENERAL_LOG, 'ERROR', to_mem=True)
