from config import SYMBOLS_INFO, FILTER_MIN_AMOUNT_USDT
from models import Params
from utils import round_down_float


class Calculation:
    def __init__(self, params: Params):
        self.TakerFee = params.TakerFee
        self.Forward = params.Forward
        self.Backward = params.Backward
        self.MinDifference = params.MinDifference

    def calc_chains(self, chains, spread):
        fee = 1 - (self.TakerFee / 100)
        best = None

        for chain in chains:
            try:
                # print(chain[0])
                arb = chain[0]
                forward = chain[1]
                symbol_1 = chain[2]
                symbol_2 = chain[3]
                symbol_3 = chain[4]
                spread1 = spread[symbol_1].decode().split(",")
                spread2 = spread[symbol_2].decode().split(",")
                spread3 = spread[symbol_3].decode().split(",")

                if (forward and not self.Forward) or (not forward and not self.Backward):
                    continue

                if forward:
                    price_1 = float(spread1[2])  # buy token/USDT (ask)
                    price_2 = float(spread2[0])  # sell token/BTC (bid)
                    price_3 = float(spread3[0])  # sell BTC/USDT  (bid)

                    efficiency = 1 / price_1 * fee
                    efficiency = efficiency * price_2 * fee
                    efficiency = efficiency * price_3 * fee

                else:
                    price_1 = float(spread1[2])  # buy BTC/USDT    (ask)
                    price_2 = float(spread2[2])  # buy token/BTC   (ask)
                    price_3 = float(spread3[0])  # sell token/USDT (bid)

                    efficiency = 1 / price_1 * fee
                    efficiency = efficiency / price_2 * fee
                    efficiency = efficiency * price_3 * fee

                efficiency = round_down_float((efficiency - 1) * 100, 4)
                if efficiency >= self.MinDifference:
                    # print(arb, efficiency, '%')
                    amount_precision_2 = SYMBOLS_INFO[symbol_2]['amount_precision']
                    amount_precision_3 = SYMBOLS_INFO[symbol_3]['amount_precision']

                    if forward:
                        amount_1 = float(spread1[3])
                        amount_2 = float(spread2[1])
                        amount_3 = float(spread3[1])

                        max_amount_token = amount_3 / price_2
                        max_amount_token = round_down_float(max_amount_token, amount_precision_2)
                        max_amount_token = min(max_amount_token, amount_2, amount_1)
                        max_amount_btc = max_amount_token * price_2
                        max_amount_btc = round_down_float(max_amount_btc, amount_precision_3)
                        max_amount_usdt = max_amount_token * price_1
                    else:
                        amount_1 = float(spread1[1])
                        amount_2 = float(spread2[1])
                        amount_3 = float(spread3[3])
                        amount_precision_1 = SYMBOLS_INFO[symbol_1]['amount_precision']

                        max_amount_token = min(amount_3, amount_2)
                        max_amount_btc = max_amount_token * price_2
                        max_amount_btc = round_down_float(max_amount_btc, amount_precision_1)
                        max_amount_btc = min(max_amount_btc, amount_1)
                        max_amount_token = max_amount_btc / price_2
                        max_amount_token = round_down_float(max_amount_token, amount_precision_2)
                        max_amount_usdt = max_amount_btc * price_1

                    if max_amount_usdt > FILTER_MIN_AMOUNT_USDT:
                        if forward:
                            profit_token = max_amount_token * fee
                            profit_token = round_down_float(profit_token, amount_precision_2)
                            profit_btc = profit_token * price_2 * fee
                            profit_btc = round_down_float(profit_btc, amount_precision_3)
                            profit_usdt = profit_btc * price_3
                            profit_usdt = profit_usdt * fee
                            profit_usdt = round(profit_usdt - max_amount_usdt, 4)
                        else:
                            profit_btc = max_amount_btc * fee
                            profit_token = profit_btc / price_2 * fee
                            profit_token = round_down_float(profit_token, amount_precision_3)
                            profit_usdt = profit_token * price_3 * fee
                            profit_usdt = profit_usdt - max_amount_usdt

                        if best and profit_usdt < best[11]:
                            continue

                        best = (arb, forward, efficiency, symbol_1, symbol_2, symbol_3, price_1, price_2,
                                price_3, max_amount_token, max_amount_btc, profit_usdt)
            except KeyError:
                continue
        return best
