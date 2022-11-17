import time
import traceback

from calculation import Calculation
from config import GENERAL_LOG, SYMBOLS_LOWER
from models import Params
from trading import Trading
from utils import mem_get_spread, time_diff_ms, mem_get_settings, mem_set_log, log, mem_get_balance
from utils_arb import create_structure


class Monitoring(Calculation, Trading):
    def __init__(self):
        self.Params = Params(mem_get_settings())
        Calculation.__init__(self, self.Params)
        Trading.__init__(self, self.Params)

        # Speed milliseconds
        self.GetSpreadSpeed = None
        self.CalcSpreadSpeed = None

    def run(self):
        # Clear Log
        mem_set_log(GENERAL_LOG, [])

        # Create structure
        structure = create_structure()

        self.log(f"Monitoring started", GENERAL_LOG, 'INFO')

        while True:
            # Load Spread
            t = time.time()
            spread = mem_get_spread(SYMBOLS_LOWER)
            self.GetSpreadSpeed = time_diff_ms(t)

            # Calc Spread
            t = time.time()
            best = self.calc_chains(structure, spread)
            self.CalcSpreadSpeed = time_diff_ms(t)

            # Execute Best
            if best:
                self.log(f"NEW ARBITRAGE {'{:.4f}'.format(best[2])}%", GENERAL_LOG, best[0])
                if self.Params.Trading:
                    self.execute(best, self.GetSpreadSpeed, self.CalcSpreadSpeed)
                    # self.log(f"GetSpreadSpeed={self.GetSpreadSpeed} CalcSpreadSpeed={self.CalcSpreadSpeed}",
                    #          GENERAL_LOG, best[0])


if __name__ == '__main__':
    try:
        Monitoring().run()
    except KeyboardInterrupt:
        exit(0)
    except Exception as err:
        log(f"{str(err)}", GENERAL_LOG, 'ERROR', to_mem=True)
        log(traceback.format_exc(), GENERAL_LOG, to_mem=True)

# TODO:
#  2. стратегия:
#       Limit (FOK), Limit Limit (GTC). Если первый прошел, разместить 2й и 3й одновременно и оставить в стакане.
#       Иметь буфер BTC
#       Для backward: Limit (FOK) на 2й ордер (token/BTC) и если он прошел - Limit Limit (GTC)
