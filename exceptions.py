
class MarketsNotLoaded(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return f'MarketsNotLoaded: {self.message}'


# ----------------------------------------------------------------
# ------------------------ Binance Spot --------------------------
# ----------------------------------------------------------------

class InvalidAPIKeyException(Exception):
    def __init__(self):
        self.message = 'Invalid API Key'

    def __str__(self):
        return f'InvalidAPIKeyException: {self.message}'


class NoBalanceException(Exception):
    def __init__(self):
        self.message = 'Not enough balance for this order'

    def __str__(self):
        return f'NoBalanceException: {self.message}'


class TimestampError(Exception):
    def __init__(self):
        self.message = 'Timestamp for this request is outside of the recvWindow.'

    def __str__(self):
        return f'TimestampError: {self.message}'


class LimitPriceException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return f'LimitPriceException: {self.message}'


class NoConnectionException(Exception):
    def __init__(self):
        self.message = 'No connection with server'

    def __str__(self):
        return f'NoConnectionException: {self.message}'


class TimeoutWaitingException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return f'TimeoutWaitingException: Timout for function {self.message}'


class UnknownOrderException(Exception):
    def __init__(self):
        self.message = 'Unknown order sent.'

    def __str__(self):
        return f'UnknownOrderException: {self.message}'


class UnknownBinanceException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return f'UnknownBinanceException: {self.message}'
