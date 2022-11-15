import time
import traceback

from calculation import Calculation
from config import GENERAL_LOG, SYMBOLS_LOWER
from models import Params
from trading import Trading
from utils import log, mem_get_spread, time_diff_ms, mem_get_settings
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
        # Create structure
        structure = create_structure()

        log(f"Monitoring started", GENERAL_LOG, 'INFO', to_mem=True)

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
                log(f"NEW ARBITRAGE {best[2]}%", GENERAL_LOG, best[0], to_mem=True)
                log(f"GetSpreadSpeed={self.GetSpreadSpeed} CalcSpreadSpeed={self.CalcSpreadSpeed}",
                    GENERAL_LOG, 'INFO', to_mem=True)
                if self.Params.Trading:
                    self.execute(best)


if __name__ == '__main__':
    try:
        Monitoring().run()
    except KeyboardInterrupt:
        exit(0)
    except Exception as err:
        log(f"{str(err)}", GENERAL_LOG, 'ERROR', to_mem=True)
        log(traceback.format_exc(), GENERAL_LOG)
