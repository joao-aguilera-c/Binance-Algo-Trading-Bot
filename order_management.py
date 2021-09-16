"""This file is responsible for doing everything order related"""

import binance.exceptions as exceptions
import pandas as pd
from binance.enums import *

import send_email as email
import strategies as strats


def generate_stoch_brackets(time, strategy, symbol, entry, sl, tp, size, id):
    filename = "active_orders.csv"

    order_list = pd.read_csv(filename)
    # print(order_list)

    df = pd.DataFrame(columns=['time_of_creation',
                               'strategy',
                               'symbol',
                               'name',
                               'status',
                               'side',
                               'type',
                               'quantity',
                               'stopPrice',
                               'price',
                               'timeInForce',
                               'newClientOrderId',
                               'isIsolated',
                               'sideEffectType'])
    """creating main order"""
    df.at['0', 'time_of_creation'] = time
    df.at['0', 'strategy'] = strategy
    df.at['0', 'symbol'] = symbol
    df.at['0', 'name'] = 'mainside'
    df.at['0', 'status'] = 'open'
    df.at['0', 'side'] = SIDE_BUY
    df.at['0', 'type'] = ORDER_TYPE_STOP_LOSS_LIMIT
    df.at['0', 'quantity'] = size
    df.at['0', 'stopPrice'] = entry
    df.at['0', 'price'] = entry
    df.at['0', 'timeInForce'] = TIME_IN_FORCE_GTC
    df.at['0', 'newClientOrderId'] = 's_%s_n_mainside' % id
    df.at['0', 'isIsolated'] = 'TRUE'
    df.at['0', 'sideEffectType'] = 'MARGIN_BUY'

    """creating sl order"""
    df.at['1', 'time_of_creation'] = time
    df.at['1', 'strategy'] = strategy
    df.at['1', 'symbol'] = symbol
    df.at['1', 'name'] = 'stoploss'
    df.at['1', 'status'] = 'open'
    df.at['1', 'side'] = SIDE_SELL
    df.at['1', 'type'] = ORDER_TYPE_STOP_LOSS_LIMIT
    df.at['1', 'quantity'] = size
    df.at['1', 'stopPrice'] = sl
    df.at['1', 'price'] = entry
    df.at['1', 'timeInForce'] = TIME_IN_FORCE_GTC
    df.at['1', 'newClientOrderId'] = 's_%s_n_sl' % id
    df.at['1', 'isIsolated'] = 'TRUE'
    df.at['1', 'sideEffectType'] = 'AUTO_REPAY'

    """creating tp order"""
    df.at['2', 'time_of_creation'] = time
    df.at['2', 'strategy'] = strategy
    df.at['2', 'symbol'] = symbol
    df.at['2', 'name'] = 'takeprofit'
    df.at['2', 'status'] = 'open'
    df.at['2', 'side'] = SIDE_SELL
    df.at['2', 'type'] = ORDER_TYPE_TAKE_PROFIT_LIMIT
    df.at['2', 'quantity'] = size
    df.at['2', 'stopPrice'] = tp
    df.at['2', 'price'] = entry
    df.at['2', 'timeInForce'] = TIME_IN_FORCE_GTC
    df.at['2', 'newClientOrderId'] = 's_%s_n_tp' % id
    df.at['2', 'isIsolated'] = 'TRUE'
    df.at['2', 'sideEffectType'] = 'AUTO_REPAY'

    # print(df)

    result = order_list.append(df)

    result.to_csv(filename, index=False)

    tittle = ('%s - New order on %s' % (strats.strutcnow(), symbol))
    message = ("{} - data on the order is: entry: {} // sl: {} // tp: {}".format(strats.strutcnow(),
                                                                                 entry,
                                                                                 sl,
                                                                                 tp))
    email.send_email(tittle.encode('utf-8'), message.encode('utf-8'))
    return


def stoch_manage_open_orders(symbol):
    """This Function sees and cancels old open orders who are not suposed to exist anymore"""
    filename = "active_orders.csv"

    '''Get all orders in this symbol and strategy'''
    order_list = pd.read_csv(filename)
    # print(order_list)
    order_list_symbol = order_list.loc[order_list['symbol'] == symbol]
    order_list_list_strategy = order_list_symbol.loc[order_list['strategy'] == 'stoch']

    '''See if there is more than one open main order, if so, exclude the old one and its childrens'''
    mainside_df = order_list_list_strategy.loc[order_list_list_strategy['name'] == 'mainside']
    mainside_df = mainside_df.loc[mainside_df['status'] == 'open']
    while len(mainside_df) > 1:
        '''Remover o mainside mais antigo, bem como seus filhos
            ou seja: pega a data do mais antigo, e exclue todas as ordens com aquela data'''
        older_date = mainside_df['time_of_creation'].min()
        i = -1
        while i < len(order_list) - 1:
            i += 1
            # print(len(order_list))
            # print(i)
            # print(order_list['time_of_creation'].iloc[i])

            # print(order_list)

            if order_list['time_of_creation'].iloc[i] == older_date:
                order_list = order_list.drop(i)
                order_list = order_list.reset_index(drop=True)
                i = -1
        mainside_df = order_list_list_strategy.loc[order_list_list_strategy['name'] == 'mainside']
        mainside_df = mainside_df.loc[mainside_df['status'] == 'open']

    order_list.to_csv(filename, index=False)
    print('%s - Order List Refreshed.' % strats.utcnow())
    return None


def there_is_open_order():
    filename = "active_orders.csv"

    order_list = pd.read_csv(filename)
    if len(order_list) != 0:
        i = -1
        while i < len(order_list) - 1:
            i += 1
            if order_list['status'].iloc[i] == 'open':
                return True

    return False


async def order_executioner(res, client):
    kline_data = res.get('data')
    kline_price = kline_data.get('k')

    symbol = kline_data.get('s')
    last_price = kline_price.get('c')
    filename = "active_orders.csv"

    '''Get all orders in this symbol and strategy'''
    order_list = pd.read_csv(filename)
    # print(len(order_list))
    there_is_change = False
    if len(order_list) != 0:
        i = -1
        while i < len(order_list) - 1:
            i += 1
            if order_list['symbol'].iloc[i] == symbol:
                if order_list['status'].iloc[i] == 'open':
                    if order_list['name'].iloc[i] == 'mainside':
                        if float(last_price) >= float(order_list['stopPrice'].iloc[i]):
                            '''Position Starting'''
                            try:
                                there_is_change = True
                                order_list.at[i, 'status'] = 'completed'
                                order_list.to_csv(filename, index=False)

                                await client.create_margin_order(symbol=symbol,
                                                                 side=order_list['side'].iloc[i],
                                                                 type=ORDER_TYPE_MARKET,
                                                                 quantity=order_list['quantity'].iloc[i],
                                                                 price=order_list['stopPrice'].iloc[i],
                                                                 newClientOrderId=
                                                                 order_list['newClientOrderId'].iloc[i],
                                                                 isIsolated=order_list['isIsolated'].iloc[i],
                                                                 sideEffectType=
                                                                 order_list['sideEffectType'].iloc[i])

                                tittle = ('%s - New position taken on %s - ' % (strats.strutcnow(), symbol))
                                message = ("Data on the order is: entry: {} // sl: {} // tp: {}".format(
                                    order_list['stopPrice'].iloc[i],
                                    order_list['stopPrice'].iloc[i + 1],
                                    order_list['stopPrice'].iloc[i + 2]))
                                print(tittle, message)
                                email.send_email(tittle.encode('utf-8'), message.encode('utf-8'))
                            except exceptions.BinanceAPIException as e:
                                there_is_change = False
                                order_list.at[i, 'status'] = 'open'
                                order_list.to_csv(filename, index=False)

                                tittle = ('%s ERROR ON %s MAIN ORDER: %s' % (strats.strutcnow(), symbol, e.message))
                                message = ("{} - data on the order is: entry: {} // sl: {} // tp: {} //// {}".format(
                                    strats.strutcnow(),
                                    order_list['stopPrice'].iloc[i],
                                    order_list['stopPrice'].iloc[i + 1],
                                    order_list['stopPrice'].iloc[i + 2],
                                    e.message))
                                print(tittle)
                                email.send_email(tittle.encode('utf-8'), message.encode('utf-8'))

                    if order_list['name'].iloc[i] == 'stoploss' and order_list['status'].iloc[i-1] == 'completed':
                        if float(last_price) <= float(order_list['stopPrice'].iloc[i]):
                            '''Position closening in loss'''
                            try:
                                order_list.at[i, 'status'] = 'completed'
                                there_is_change = True
                                order_list.to_csv(filename, index=False)

                                await client.create_margin_order(symbol=symbol,
                                                                 side=order_list['side'].iloc[i],
                                                                 type=ORDER_TYPE_MARKET,
                                                                 quantity=order_list['quantity'].iloc[i],
                                                                 price=order_list['stopPrice'].iloc[i],
                                                                 newClientOrderId=
                                                                 order_list['newClientOrderId'].iloc[i],
                                                                 isIsolated=order_list['isIsolated'].iloc[i],
                                                                 sideEffectType=
                                                                 order_list['sideEffectType'].iloc[i])
                                tittle = ('%s - New exiting position in loss on %s - ' %
                                          (strats.strutcnow(), symbol))
                                message = ("Data on the exit is: price: {}".format(
                                    order_list['stopPrice'].iloc[i]))


                                order_list = order_list.drop(i + 1)
                                order_list = order_list.reset_index(drop=True)

                                print(tittle, message)

                                email.send_email(tittle.encode('utf-8'), message.encode('utf-8'))
                            except exceptions.BinanceAPIException as e:
                                order_list.at[i, 'status'] = 'open'
                                there_is_change = False
                                order_list.to_csv(filename, index=False)

                                tittle = ('%s ERROR ON %s STOP ORDER: %s' % (strats.strutcnow(), symbol, e.message))
                                message = ("{} - data on the order is: entry: {} // sl: {} // tp: {} //// {}".format(
                                    strats.strutcnow(),
                                    order_list['stopPrice'].iloc[i - 1],
                                    order_list['stopPrice'].iloc[i],
                                    order_list['stopPrice'].iloc[i + 1],
                                    e.message))
                                print(tittle)
                                email.send_email(tittle.encode('utf-8'), message.encode('utf-8'))

                    if order_list['name'].iloc[i] == 'takeprofit' and order_list['status'].iloc[i-2] == 'completed':
                        if float(last_price) >= float(order_list['stopPrice'].iloc[i]):
                            '''Position closening in profit!'''
                            try:
                                order_list.at[i, 'status'] = 'completed'
                                there_is_change = True
                                order_list.to_csv(filename, index=False)

                                await client.create_margin_order(symbol=symbol,
                                                                 side=order_list['side'].iloc[i],
                                                                 type=ORDER_TYPE_MARKET,
                                                                 quantity=order_list['quantity'].iloc[i],
                                                                 price=order_list['stopPrice'].iloc[i],
                                                                 newClientOrderId=
                                                                 order_list['newClientOrderId'].iloc[i],
                                                                 isIsolated=order_list['isIsolated'].iloc[i],
                                                                 sideEffectType=
                                                                 order_list['sideEffectType'].iloc[i])
                                tittle = ('%s - New exiting position in profit on %s - ' %
                                          (strats.strutcnow(), symbol))
                                message = ("Data on the exit is: price: {}".format(
                                    order_list['stopPrice'].iloc[i]))


                                order_list = order_list.drop(i - 1)
                                order_list = order_list.reset_index(drop=True)
                                i -= 1

                                print(tittle, message)

                                email.send_email(tittle.encode('utf-8'), message.encode('utf-8'))
                            except exceptions.BinanceAPIException as e:
                                order_list.at[i, 'status'] = 'open'
                                there_is_change = False
                                order_list.to_csv(filename, index=False)

                                tittle = ('%s ERROR ON %s TAKE PROFIT ORDER: %s' %
                                          (strats.strutcnow(), symbol, e.message))
                                message = ("{} - data on the order is: entry: {} // sl: {} // tp: {} //// {}".format(
                                    strats.strutcnow(),
                                    order_list['stopPrice'].iloc[i - 2],
                                    order_list['stopPrice'].iloc[i - 1],
                                    order_list['stopPrice'].iloc[i],
                                    e.message))
                                print(tittle)
                                email.send_email(tittle.encode('utf-8'), message.encode('utf-8'))
        if there_is_change:
            order_list.to_csv(filename, index=False)



if __name__ == '__main__':
    print('%s - Start' % strats.strutcnow())
    # order_executioner(client=None, last_price=61000, symbol='BTCUSDT')
    print('%s - End' % strats.strutcnow())


