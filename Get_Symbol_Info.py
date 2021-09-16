import datetime
import os

import pandas as pd
from binance.client import Client

import main as ws
from strategies import strutcnow


def get_file_names(dir):  # 1.Get file names from directory
    file_list = os.listdir(dir)
    for index, item in enumerate(file_list):
        file_list[index] = item[:-4]

    return file_list


def TsToStrgCsvFormat(time):
    t = datetime.datetime.utcfromtimestamp(time / 1000.0)
    return t.strftime('%Y.%m.%d %H:%M:%S')


async def get_symbol_info(client, semanal_symbol_list, directory):

    binance_client = client
    # print("%s - Programa iniciado" % strutcnow())

    # 2.To rename files
    files = get_file_names(directory)
    # print(files)

    minutes_15 = pd.to_timedelta(15, unit='m')
    days_60 = pd.to_timedelta(62, unit='D')
    time_now = datetime.datetime.utcnow() - minutes_15

    for week_symbols in semanal_symbol_list:
        # print('%s - mining new values from %s' % (strutcnow(), s))
        df = pd.read_csv('%s/%s.csv' % (directory, week_symbols), header=None)
        last_rec_date = datetime.datetime.strptime(df[0].iloc[-1], '%Y.%m.%d %H:%M:%S') + minutes_15
        # print('%s < %s' % (last_rec_date, time_now))
        if last_rec_date < time_now:
            """print('%s - last mined candle was at: %s. Mining more.' % (strutcnow(),
                                                                       datetime.datetime.strptime(
                                                                           df[0].iloc[-1],
                                                                           '%Y.%m.%d %H:%M:%S')))"""
            candles_dataset = await binance_client.get_historical_klines(week_symbols,
                                                                         Client.KLINE_INTERVAL_15MINUTE,
                                                                         last_rec_date.strftime(
                                                                             "%m/%d/%Y %H:%M:%S"),
                                                                         time_now.strftime(
                                                                             "%m/%d/%Y %H:%M:%S"))
            if candles_dataset != []:
                df = pd.DataFrame(candles_dataset)
                df = df.iloc[:, :-7]
                df[0] = [TsToStrgCsvFormat(time) for time in df[0]]
                if ws.get_last_csv_candle_time(directory, week_symbols) != df[0].iloc[-1]:
                    print('%s - %s -> update from: %s to time: %s' %
                          (strutcnow(),
                           week_symbols,
                           ws.get_last_csv_candle_time(directory, week_symbols),
                           df[0].iloc[-1]))

                    df.to_csv('%s/%s.csv' % (directory, week_symbols), mode='a', header=False, index=False)
            else:
                print("{} - Algo errado com o {}, binance não foi capaz de enviar dados.".format(
                    strutcnow(), week_symbols))
        else:
            print('%s - %s já atualizado' % (strutcnow(), week_symbols))


if __name__ == "__main__":
    get_symbol_info(semanal_symbol_list=['BTCUSD', 'ETHUSD'], directory=r'/Symbols', client=None)


