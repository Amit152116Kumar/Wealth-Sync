import datetime
import logging
import time
from collections import defaultdict

import numpy as np
import pandas as pd
import pandas_ta as ta
from numba import njit

from firestore import Firestore
from models import IST, OptionType, TransactionType
from mylogger import logging_handler
from observer_pattern import IEventListener, IEventManager

logging.basicConfig(level=logging.DEBUG, handlers=[logging_handler])


class Indicator(IEventManager, IEventListener):
    df_incomplete = defaultdict(pd.DataFrame)

    def __init__(self):
        self._observers = set()
        self.df_complete = defaultdict(pd.DataFrame)
        self.strategy = defaultdict(dict)
        self.window = defaultdict(int)
        self.timeframe = defaultdict(int)
        self.db = Firestore.db()
        docs = self.db.collection("watchlist").stream()

        for doc in docs:
            id = doc.id
            token = doc.get("instrumentToken")
            try:
                strategy = (
                    self.db.collection("watchlist")
                    .document(id)
                    .collection("strategy")
                    .get()[0]
                )

                self.timeframe[token] = strategy.get("timeframe")
                data_dict = strategy.to_dict()
                data_dict.pop("timeframe")

                for key in data_dict.keys():
                    data_dict[key] = int(data_dict[key])
                self.strategy[token] = data_dict
                self.window[token] = max(data_dict.values()) + 2

                df = []
                livefeed_ref = (
                    self.db.collection("livefeed")
                    .document(id)
                    .collection("ohlcv")
                )
                size = self.window[token] * self.timeframe[token]
                livefeed_stream = livefeed_ref.limit(size).stream()

                for livefeed in livefeed_stream:
                    dict_data = livefeed.to_dict()
                    dict_data["datetime"] = livefeed.id
                    df.append(dict_data)
                df = pd.DataFrame(df)
                df["datetime"] = pd.to_datetime(df["datetime"])
                df = (
                    df.resample(f"{self.timeframe[token]}T", on="datetime")
                    .agg(
                        {
                            "open": "first",
                            "high": "max",
                            "low": "min",
                            "close": "last",
                            "volume": "last",
                            "OI": "last",
                        }
                    )
                    .dropna()
                )
                self.df_complete[token] = df.tail(self.window[token])
                logging.debug(
                    f"Initial Shape of the token {token, self.df_complete[token].shape}"
                )
            except Exception as e:
                logging.error(f"Error in Indicator init: {e}")

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

    def data_handler(self, token, df: pd.DataFrame):
        TIMEFRAME = self.timeframe[token]
        STRATEGY = self.strategy[token]
        WINDOW = self.window[token]
        df = df.resample(f"{TIMEFRAME}T").agg(
            {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "last",
                "OI": "last",
            }
        )

        df = pd.concat([self.df_incomplete[token], df])
        df = df.groupby(df.index).agg(
            {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "last",
                "OI": "last",
            }
        )

        current_time = datetime.datetime.now(IST).replace(tzinfo=None)
        completed_df = df[
            df.index < current_time - datetime.timedelta(minutes=TIMEFRAME)
        ]
        self.df_incomplete[token] = df[
            df.index >= current_time - datetime.timedelta(minutes=TIMEFRAME)
        ]

        if completed_df.shape[0] == 0:
            return

        self.df_complete[token] = pd.concat(
            [self.df_complete[token], completed_df]
        )
        if self.df_complete[token].shape[0] == WINDOW + 1:
            self.df_complete[token].drop(
                self.df_complete[token].index[:1], inplace=True
            )

        if self.df_complete[token].shape[0] < WINDOW:
            return

        sma = self.SMA(self.df_complete[token], STRATEGY["sma"]).values
        rsi = self.RSI(self.df_complete[token], STRATEGY["rsi"]).values
        (fast_trend, fast_direction) = self.SUPERTREND(
            self.df_complete[token],
            STRATEGY["fast_period"],
            STRATEGY["fast_multiplier"],
        )
        (slow_trend, slow_direction) = self.SUPERTREND(
            self.df_complete[token],
            STRATEGY["slow_period"],
            STRATEGY["slow_multiplier"],
        )

        logging.debug(
            f"token: {token}, sma: {sma[-1]}, rsi: {rsi[-1]}, fast_trend: {fast_trend[-1]}, slow_trend: {slow_trend[-1]}, fast_direction: {fast_direction[-1]}, slow_direction: {slow_direction[-1]}"
        )

        if (
            sma[-1]
            and rsi[-1]
            and fast_trend[-1]
            and slow_trend[-1]
            and fast_direction[-1]
            and slow_direction[-1]
        ):
            self.notifyObserver(token, TransactionType.buy, OptionType.call)
            logging.debug(f"token: {token} BUY call")

        elif (
            not sma[-1]
            and not rsi[-1]
            and not fast_trend[-1]
            and not slow_trend[-1]
            and not fast_direction[-1]
            and not slow_direction[-1]
        ):
            self.notifyObserver(token, TransactionType.buy, OptionType.put)
            logging.debug(f"token: {token} BUY put")

        else:
            self.notifyObserver(token, TransactionType.sell)
            logging.debug(f"token: {token} SELL call/put")

        return

    def update(self, *args):
        token = args[0]
        df: pd.DataFrame = args[1]
        if self.timeframe[token] == 0:
            return
        self.data_handler(token, df)
        return

    def SMA(self, data: pd.DataFrame, period: int = 20):
        data = data.tail(period + 1)
        return ta.sma(data["close"], timeperiod=period) < data["close"]

    def RSI(self, data: pd.DataFrame, period: int = 14):
        data = data.tail(period + 1)
        return ta.rsi(data["close"], timeperiod=period) >= 50

    def SUPERTREND(
        self, data: pd.DataFrame, period: int = 7, multiplier: int = 3
    ):
        data = data.tail(period + 1)
        high = data["high"]
        low = data["low"]
        close = data["close"]

        avg_price = ta.midprice(high, low)
        atr = ta.atr(high, low, close, period)
        matr = multiplier * atr
        upper = avg_price + matr
        lower = avg_price - matr
        trend, direction = _get_final_bands_nb(
            close.values, upper.values, lower.values
        )
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
