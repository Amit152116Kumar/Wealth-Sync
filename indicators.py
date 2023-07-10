import datetime
import time
from abc import ABC, abstractmethod
from collections import defaultdict

import numpy as np
import pandas as pd
import pandas_ta as ta
from numba import njit

from models import DATASTORE, OptionType, TransactionType
from observer_pattern import IEventListener, IEventManager

TIMEFRAME = 2

WINDOWS = {
    "sma": 50,
    "rsi": 40,
    "fast_multiplier": 4,
    "fast_period": 14,
    "slow_multiplier": 4,
    "slow_period": 48,
}


class Indicator(IEventManager, IEventListener):
    df_incomplete = defaultdict(pd.DataFrame)

    def __init__(self):
        self._observers = set()
        self.data = defaultdict(pd.DataFrame)
        self.window = max(WINDOWS.values()) + 1

        watchlist = pd.read_hdf(DATASTORE, "/watchlist", mode="r")
        for item in watchlist.itertuples():
            filename = item.filename
            token = item.Index
            try:
                df = pd.read_hdf(DATASTORE, f"/{filename}", mode="r").tail(self.window * TIMEFRAME)
                df = (
                    df.resample(f"{TIMEFRAME}T")
                    .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "last", "OI": "last"})
                    .dropna()
                )
                self.data[token] = df.tail(self.window)
                print(token, self.data[token].shape)

            except KeyError:
                print(f"KeyError: {filename}")
                continue

    def attachObserver(self, observer: IEventListener):
        self._observers.add(observer)
        return super().attachObserver(observer)

    def detachObserver(self, observer: IEventListener):
        if observer in self._observers:
            self._observers.remove(observer)
        return super().detachObserver(observer)

    def notifyObserver(self, *args):
        for observer in self._observers:
            observer.update(*args)
        return super().notifyObserver()

    def data_handler(self, token, df):
        df = df.resample(f"{TIMEFRAME}T").agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "last", "OI": "last"})

        df = pd.concat([self.df_incomplete[token], df])
        df = df.groupby(df.index).agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "last", "OI": "last"})

        completed_df = df[df.index < datetime.datetime.now() - datetime.timedelta(minutes=TIMEFRAME)]
        self.df_incomplete[token] = df[df.index >= datetime.datetime.now() - datetime.timedelta(minutes=TIMEFRAME)]

        if completed_df.shape[0] == 0:
            return

        self.data[token] = pd.concat([self.data[token], completed_df])
        if self.data[token].shape[0] == self.window + 1:
            self.data[token].drop(self.data[token].index[:1], inplace=True)

        if self.data[token].shape[0] < self.window:
            return

        start = time.perf_counter()
        sma = self.SMA(self.data[token], WINDOWS["sma"]).values < self.data[token]["close"].values
        rsi = self.RSI(self.data[token], WINDOWS["rsi"]).values > 50
        (fast_trend, fast_direction) = self.SUPERTREND(self.data[token], WINDOWS["fast_period"], WINDOWS["fast_multiplier"])
        (slow_trend, slow_direction) = self.SUPERTREND(self.data[token], WINDOWS["slow_period"], WINDOWS["slow_multiplier"])

        # print(sma[-3:], rsi[-3:], fast_trend[-3:], slow_trend[-3:], fast_direction[-3:], slow_direction[-3:], sep="\n")
        # end = time.perf_counter()
        # print(f"Time taken: {end - start:.4f} seconds")

        # sma = calculate_sma(self.data[token]["close"].values, WINDOWS['sma'])
        # rsi = self.RSI(self.data[token], WINDOWS['rsi']).values
        # fast_trend = calculate_supertrend(self.data[token]["close"].values, self.data[token]["high"].values, self.data[token]["low"].values, WINDOWS['fast_period'], WINDOWS["fast_multiplier"])
        # slow_trend = calculate_supertrend(self.data[token]["close"].values, self.data[token]["high"].values, self.data[token]["low"].values, WINDOWS['slow_period'], WINDOWS["slow_multiplier"])

        # print(sma[-3:], rsi[-3:], fast_trend[-3:], slow_trend[-3:], sep="\n")
        # print(f"Time taken: { time.perf_counter()- end:.4f} seconds")
        # if last values of sma, rsi, fast_trend, slow_trend are True, then buy

        if sma[-1] and rsi[-1] and fast_trend[-1] and slow_trend[-1] and fast_direction[-1] and slow_direction[-1]:
            self.notifyObserver(token, TransactionType.buy, OptionType.call)

        elif not sma[-1] and not rsi[-1] and not fast_trend[-1] and not slow_trend[-1] and not fast_direction[-1] and not slow_direction[-1]:
            self.notifyObserver(token, TransactionType.buy, OptionType.put)

        else:
            self.notifyObserver(token, TransactionType.sell)

        return

    def update(self, *args):
        for token, df in args[0].items():
            self.data_handler(token, df)
        return

    def SMA(self, data, period: int = 20):
        return ta.sma(data["close"], timeperiod=period)

    def RSI(self, data, period: int = 14):
        return ta.rsi(data["close"], timeperiod=period)

    def SUPERTREND(self, data, period: int = 7, multiplier: int = 3):
        high = data["high"]
        low = data["low"]
        close = data["close"]

        avg_price = ta.midprice(high, low)
        atr = ta.atr(high, low, close, period)
        matr = multiplier * atr
        upper = avg_price + matr
        lower = avg_price - matr
        trend, direction = _get_final_bands_nb(close.values, upper.values, lower.values)
        return trend, direction == 1


@njit
def _get_final_bands_nb(close, upper, lower):
    trend = np.full(close.shape, np.nan)
    direction = np.full(close.shape, 1)

    for i in range(1, close.shape[0]):
        if close[i] > upper[i - 1]:
            direction[i] = 1
        elif close[i] < lower[i - 1]:
            direction[i] = -1
        else:
            direction[i] = direction[i - 1]
            if direction[i] > 0 and lower[i] < lower[i - 1]:
                lower[i] = lower[i - 1]
            if direction[i] < 0 and upper[i] > upper[i - 1]:
                upper[i] = upper[i - 1]

        if direction[i] > 0:
            trend[i] = lower[i]
        else:
            trend[i] = upper[i]

    return trend, direction


@njit
def calculate_sma(prices, window=14):
    sma = np.zeros_like(prices)
    sma[:window] = np.mean(prices[:window])

    for i in range(window, len(prices)):
        sma[i] = np.mean(prices[i - window + 1 : i + 1])

    return sma
