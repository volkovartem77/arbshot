from utils import decimal, to_digits, find_filter


def format_symbol_info(data):
    """
        FORMAT
        {
            "price_precision": 0.01,
            "amount_precision": 0.000001,
            "min_amount": 10.0,
            "tick_size": 0.01,
            "base": "LTC",
            "quote": "USDT"
        }
    """
    return {
        "price_precision": int(data['price_precision']),
        "amount_precision": int(data['amount_precision']),
        "min_amount": decimal(data['min_amount']),
        "tick_size": decimal(data['tick_size']),
        "base": str(data['base']),
        "quote": str(data['quote'])
    }


def format_symbols_info(symbols_info):
    return dict((data['symbol'], format_symbol_info(data)) for data in symbols_info.items())


def format_open_limit_order_rest(order):
    """
        INITIAL FORMAT:
        {
            'symbol': 'LTCBTC',
            'orderId': 457925986,
            'orderListId': -1,
            'clientOrderId': 'rOcRBb46GeY5khzTErxKZN',
            'transactTime': 1606928493059,
            'price': '0.00460000',
            'origQty': '0.04000000',
            'executedQty': '0.00000000',
            'cummulativeQuoteQty': '0.00000000',
            'status': 'NEW',
            'timeInForce': 'GTC',
            'type': 'LIMIT',
            'side': 'SELL',
            'fills': [
            ]
        }
    """
    result = {
        'timestamp': int(order['transactTime']),
        'orderId': str(order['orderId']),
        'clientOrderId': str(order['clientOrderId']),
        'symbol': str(order['symbol']),
        'price': decimal(order['price']),
        'side': order['side'].upper(),
        'amount': decimal(order['origQty']),
        'cummulativeQuoteQty': decimal(order['cummulativeQuoteQty']),
        'commission': decimal(0),
        'status': str(order['status']),
        'type': str(order['type'])
    }

    if order['fills']:
        commission = sum([decimal(f['commission']) for f in order['fills']])
        result.update({'commission': commission})

    return result


def format_open_market_order_rest(order):
    """
        INITIAL FORMAT:
        {
            {
              'symbol': 'ETHBTC',
              'orderId': 3277207173,
              'orderListId': -1,
              'clientOrderId': 'testes345-3rtest',
              'transactTime': 1665650792530,
              'price': '0.00000000',
              'origQty': '0.01500000',
              'executedQty': '0.01500000',
              'cummulativeQuoteQty': '0.00100777',
              'status': 'FILLED',
              'timeInForce': 'GTC',
              'type': 'MARKET',
              'side': 'SELL',
              'fills': [
                {
                  'price': '0.06718500',
                  'qty': '0.01500000',
                  'commission': '0.00000101',
                  'commissionAsset': 'BTC',
                  'tradeId': 381353723
                }
              ]
            }
        }
    """
    result = {
        'timestamp': int(order['transactTime']),
        'orderId': str(order['orderId']),
        'clientOrderId': str(order['clientOrderId']),
        'symbol': str(order['symbol']),
        'price': decimal(order['price']),
        'side': order['side'].upper(),
        'amount': decimal(order['origQty']),
        'cummulativeQuoteQty': decimal(order['cummulativeQuoteQty']),
        'commission': decimal(0),
        'status': str(order['status']),
        'type': str(order['type'])
    }

    if order['fills']:
        price = sum([decimal(f['price']) for f in order['fills']]) / len(order['fills'])
        commission = sum([decimal(f['commission']) for f in order['fills']])
        result.update({'price': price, 'commission': commission})

    return result


def format_limit_order_rest(order):
    """
        INITIAL FORMAT:
        {
            'symbol': 'VGXETH',
            'orderId': 19936451,
            'orderListId': -1,
            'clientOrderId': 'ac5e131685b045a7834a12fd74b2a9d9',
            'price': '0.00032600',
            'origQty': '46.40000000',
            'executedQty': '46.40000000',
            'cummulativeQuoteQty': '0.01512640',
            'status': 'FILLED',
            'timeInForce': 'GTC',
            'type': 'LIMIT',
            'side': 'BUY',
            'stopPrice': '0.00000000',
            'icebergQty': '0.00000000',
            'time': 1665662687851,
            'updateTime': 1665662687851,
            'isWorking': True,
            'origQuoteOrderQty': '0.00000000'
        }
    """
    if order:
        return {
            'timestamp': int(order['updateTime']),
            'orderId': str(order['orderId']),
            'clientOrderId': str(order['clientOrderId']),
            'symbol': str(order['symbol']),
            'price': decimal(order['price']),
            'side': order['side'].upper(),
            'amount': decimal(order['origQty']),
            'exec_amount': decimal(order['executedQty']),
            'quote_amount': decimal(order['cummulativeQuoteQty']),
            'status': str(order['status']),
            'type': str(order['type'])
        }

