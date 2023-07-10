import datetime
import os
import random
import time
from collections import defaultdict

import pandas as pd

from indicators import Indicator
from kotakclient import KotakClient
from observer_pattern import IEventListener, IEventManager
from portfolio import Portfolio


class LiveFeed(IEventManager):
    dataList = defaultdict(list)
    __broadcast_live = "https://wstreamer.kotaksecurities.com/feed"
    __dataStore = "financial_data.h5"
    __columns = ["datetime", "open", "high", "low", "close", "volume", "OI"]
    __watchlist = None
    __instance = None
    df_incomplete = defaultdict(pd.DataFrame)
    df_notify = defaultdict(pd.DataFrame)

    def __new__(cls):
        if not cls.__instance:
            cls.__instance = super(LiveFeed, cls).__new__(cls)
        return cls.__instance

    def __init__(self) -> None:
        self._observers = set()
        self.__watchlist = self.__get_watchlist

    def __del__(self):
        pass

    @property
    def __get_watchlist(self) -> pd.DataFrame:
        df = pd.read_hdf(self.__dataStore, "/watchlist", mode="r")
        return df

    @property
    def __get_tokens(self) -> str:
        return self.__watchlist.index.to_list().__str__().replace("[", "").replace("]", "").replace(" ", "")

    def subscribe(self):
        self._client = KotakClient.get_client
        time_now = datetime.datetime.now()
        if time_now.strftime("%a") == ("Sun" or "Sat"):
            print("Today is Weekend.")
            return {"status": "success", "message": "Today is Weekend."}

        holiday = pd.read_csv("kotak_data/holiday.csv", index_col="Date").index.to_list()
        if time_now.strftime("%d-%b-%Y") in holiday:
            print("Today is Market Holiday.")
            return {"status": "success", "message": "Today is Market Holiday."}

        if time_now.hour < 9 or (time_now.hour == 9 and time_now.minute < 14):
            print("Market will open at 9:15 AM.")
            return {"status": "success", "message": "Market will open at 9:15 AM."}

        if time_now.hour > 15 or (time_now.hour == 15 and time_now.minute > 30):
            print("Market is Closed for Today.")
            return {"status": "success", "message": "Market is Closed for Today."}

        print(
            f"\tTime Now : {time_now.strftime('%H:%M:%S')} \
            \n\tMarket will close at 3:30 PM. \n\tTime left : \
                {datetime.timedelta(hours=15-time_now.hour,minutes=30-time_now.minute)}"
        )

        # Subscribe to live feed
        try:
            self._client.subscribe(
                self.__get_tokens,
                callback=self.callback_method,
                broadcast_host=self.__broadcast_live,
                disconnect_event=self.disconnect_event,
                connect_event=self.connect_event,
            )
        except Exception as e:
            return {"status": "error", "message": f"{e}"}

        print("Successfully Subscribed to Live feed 👍👍 \n")
        return {"status": "success", "message": "Successfully Subscribed to Live feed 👍👍 \n"}

    def unsubscribe(self):
        try:
            self._client.unsubscribe()
        except Exception as e:
            return {"status": "error", "message": f"{e}"}

        print("Successfully Unsubscribed from Live feed 👍👍 \n")
        return {"status": "success", "message": "Successfully Unsubscribed from Live feed 👍👍 \n"}

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

    @classmethod
    def updatedb(cls):
        print("Disconnected from Live feed. Reconnecting...")
        flag = False
        df_watchlist = cls.__instance.__watchlist

        for token, data in cls.dataList.items():
            df = pd.DataFrame(data, columns=cls.__columns)
            df["datetime"] = pd.to_datetime(df["datetime"],format="%d/%m/%Y %H:%M:%S")
            df = df.resample(f"1T", on="datetime").agg(
                {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "last", "OI": "last"}
            )
            df = pd.concat([cls.df_incomplete[token], df])
            df = df.groupby(df.index).agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "last", "OI": "last"})

            completed_df = df[df.index < datetime.datetime.now() - datetime.timedelta(minutes=1)]
            cls.df_incomplete[token] = df[df.index >= datetime.datetime.now() - datetime.timedelta(minutes=1)]

            if completed_df.shape[0] == 0:
                continue
            
            filename = df_watchlist._get_value(token, "filename")
            completed_df.to_hdf(
                cls.__dataStore, key=filename, mode="a", append=True, format="table", complevel=9, complib="blosc:lz4", data_columns=True
            )
            cls.df_notify[token] = pd.concat([cls.df_notify[token], completed_df])
            flag = True

        cls.dataList.clear()
        if flag:
            cls.__instance.notifyObserver(cls.df_notify)
            cls.df_notify.clear()
        return

    # Callback method to receive live feed
    @staticmethod
    def callback_method(message):
        token = int(message[1])
        ltp = float(message[6])
        total_qty = message[15]
        open_Interest = message[16]
        datetime = message[19]
        series = (datetime, ltp, ltp, ltp, ltp, total_qty, open_Interest)
        LiveFeed.dataList[token].append(series)
        return

    @staticmethod
    def disconnect_event():
        LiveFeed.updatedb()
        return

    @staticmethod
    def connect_event():
        pass


if __name__ == "__main__":
    livefeed = LiveFeed()
    livefeed.subscribe()
    ques = input("Press any key to unsubscribe : ")
    if ques:
        livefeed.unsubscribe()
    # counter = 0
    # while True:
    #     livefeed.connect_event()
    #     price = random.randint(18000, 19000)
    #     data = ("NIFTY", 11721, 0, 0, 0, 0, price, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, datetime.datetime.now())
    #     time.sleep(1)
    #     livefeed.callback_method(data)
    #     price = random.randint(42000, 43000)
    #     data = ("NIFTY", 11717, 0, 0, 0, 0, price, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, datetime.datetime.now())
    #     livefeed.callback_method(data)
    #     counter += 1
    #     if counter == 27:
    #         start = time.perf_counter()
    #         livefeed.disconnect_event()
    #         print("--------------------")
    #         counter = 0
    #         time.sleep(3)
