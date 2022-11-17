import traceback

import simplejson

from config import GENERAL_LOG, ORDER_STATUS_NEW, ORDER_STATUS_CANCELED
from utils import log, mem_get_raw_stats, mem_get_order, decimal, mem_remove_raw_stats, mem_rm_order, mem_add_history


def clear_orders(oid1, oid2, oid3):
    mem_rm_order(oid1)
    mem_rm_order(oid2)
    mem_rm_order(oid3)


def run():
    log(f"Statistic started", GENERAL_LOG, 'INFO', to_mem=True)

    while True:
        raw_stats = mem_get_raw_stats()
        if raw_stats:
            for chain_id, raw_stat in raw_stats.items():
                raw_stat = simplejson.loads(raw_stat)
                order_1 = mem_get_order(raw_stat['order_1'])
                order_2 = mem_get_order(raw_stat['order_2'])
                order_3 = mem_get_order(raw_stat['order_3'])

                if order_1 and order_2 and order_3:
                    statuses = [order_1['status'], order_2['status'], order_3['status']]
                    size_usdt = decimal(raw_stat['size_usdt'])
                    profit_usdt = None

                    if ORDER_STATUS_NEW in statuses:
                        chain_status = 'HOLDING'
                    elif ORDER_STATUS_CANCELED in statuses:
                        chain_status = 'CANCELED'
                        mem_remove_raw_stats(chain_id)
                        clear_orders(raw_stat['order_1'], raw_stat['order_2'], raw_stat['order_3'])
                    else:
                        chain_status = 'COMPLETED'
                        profit_usdt = round(decimal(order_3['amount_received']) - size_usdt, 4)
                        mem_remove_raw_stats(chain_id)
                        clear_orders(raw_stat['order_1'], raw_stat['order_2'], raw_stat['order_3'])

                    mem_add_history(chain_id, {
                        'datetime': raw_stat['datetime'],
                        'arb': raw_stat['arb'],
                        'size_usdt': size_usdt,
                        'status': chain_status,
                        'diff': '{:.4f}'.format(raw_stat['efficiency']),
                        'profit_usdt': profit_usdt
                    })


if __name__ == '__main__':
    try:
        run()
    except KeyboardInterrupt:
        pass

    except Exception as e:
        log(f"{str(e)}", GENERAL_LOG, 'ERROR', to_mem=True)
        log(traceback.format_exc(), GENERAL_LOG, 'ERROR', to_mem=True)
