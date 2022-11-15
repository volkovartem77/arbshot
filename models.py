
class Params:
    def __init__(self, params):
        self.APIKey = str(params['api_key'])
        self.APISecret = str(params['api_secret'])
        self.TakerFee = float(params['taker_fee'])
        self.MinDifference = float(params['min_difference'])
        self.OrderAmountPrc = float(params['order_amount_prc'])
        self.Forward = bool(params['forward'])
        self.Backward = bool(params['backward'])
        self.Trading = bool(params['trading'])

    def upd_params(self, params: dict):
        if 'api_key' in params:
            self.APIKey = str(params['api_key'])
        if 'api_secret' in params:
            self.APISecret = str(params['api_secret'])
        if 'taker_fee' in params:
            self.TakerFee = float(params['taker_fee'])
        if 'min_difference' in params:
            self.MinDifference = float(params['min_difference'])
        if 'order_amount_prc' in params:
            self.OrderAmountPrc = float(params['order_amount_prc'])
        if 'forward' in params:
            self.Forward = bool(params['forward'])
        if 'backward' in params:
            self.Backward = bool(params['backward'])
        if 'trading' in params:
            self.Trading = bool(params['trading'])

    def get_dict(self):
        return {
            "api_key": self.APIKey,
            "api_secret": self.APISecret,
            "taker_fee": self.TakerFee,
            "min_difference": self.MinDifference,
            "order_amount_prc": self.OrderAmountPrc,
            "trade_forward": self.Forward,
            "trade_backward": self.Backward,
            "trading": self.Trading
        }
