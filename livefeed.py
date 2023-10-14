import datetime
import logging
import sys
import time
from collections import defaultdict
from threading import Thread

import pandas as pd

from firestore import Firestore
from kotakclient import KotakClient
from models import IST
from mylogger import logging_handler
from observer_pattern import IEventListener, IEventManager

logging.basicConfig(level=logging.DEBUG, handlers=[logging_handler])


class LiveFeed(IEventManager):
    dataList = defaultdict(list)
    __columns = ["datetime", "open", "high", "low", "close", "volume", "OI"]
    __instance = None
    Threads = []
    count = 0
    stockName = defaultdict(str)

    df_incomplete = defaultdict(pd.DataFrame)
    startTime = None

    def __new__(cls):
        if not cls.__instance:
            cls.__instance = super(LiveFeed, cls).__new__(cls)
        return cls.__instance

    def __init__(self) -> None:
        self._observers = set()
        self.db = Firestore.db()
        self.watchlist = self.__get_watchlist()

    def __del__(self):
        pass

    def __get_watchlist(self) -> list:
        watchlist = []
        docs = self.db.collection("watchlist").get()
        for doc in docs:
            details = doc.to_dict()
            self.stockName[details["instrumentToken"]] = doc.id
            watchlist.append(details)
        df = pd.DataFrame(watchlist)
        return df

    @property
    def get_tokens(self) -> str:
        tokens = self.watchlist["instrumentToken"].to_list()
        for _, row in self.watchlist.iterrows():
            documentName = self.stockName[row["instrumentToken"]]
            self.db.collection("livefeed").document(documentName).set(
                row.to_dict()
            )
        return (
            tokens.__str__().replace("[", "").replace("]", "").replace(" ", "")
        )

    async def subscribe(self):
        sys.stderr = logging_handler.stream

        time_now = datetime.datetime.now(tz=IST)
        if time_now.strftime("%a") == ("Sun" or "Sat"):
            return {"status": "error", "message": "Today is Weekend."}

        holiday = pd.read_csv(
            "kotak_data/holiday.csv", index_col="Date"
        ).index.to_list()
        if time_now.strftime("%d-%b-%Y") in holiday:
            return {"status": "error", "message": "Today is Market Holiday."}

        if time_now.hour < 9:
            return {
                "status": "error",
                "message": "Market will open at 9:15 AM.",
            }

        if time_now.hour > 15 or (
            time_now.hour == 15 and time_now.minute > 30
        ):
            return {
                "status": "error",
                "message": "Market is Closed for Today.",
            }

        # Subscribe to live feed
        try:
            KotakClient.get_client.subscribe(
                self.get_tokens,
                callback=self.callback_method,
                broadcast_host="https://wstreamer.kotaksecurities.com/feed",
                disconnect_event=self.disconnect_event,
                connect_event=self.connect_event,
                error_event=self.error_event,
            )
        except Exception as e:
            return {"status": "error", "message": f"{e}"}
        return {
            "status": "success",
            "message": "Successfully Subscribed to Live feed 👍",
        }

    def unsubscribe(self):
        try:
            KotakClient.get_client.unsubscribe()
        except Exception as e:
            logging.debug(e)
            return {"status": "error", "message": f"{e}"}
        logging.debug("Successfully Unsubscribed from Live feed 👍")
        return {
            "status": "success",
            "message": "Successfully Unsubscribed from Live feed 👍",
        }

    def attachObserver(self, observer: IEventListener):
        self._observers.add(observer)
        return super().attachObserver(observer)

    def detachObserver(self, observer: IEventListener):
        if observer in self._observers:
            self._observers.remove(observer)
        return super().detachObserver(observer)

    def notifyObserver(self, *args):
        logging.debug("livefeed -> notify Observers")
        for observer in self._observers:
            observer.update(*args)
        return super().notifyObserver()

    @classmethod
    def updatedb(cls, token, data):
        df = pd.DataFrame(data, columns=cls.__columns)
        cls.dataList[token].clear()
        df["datetime"] = pd.to_datetime(
            df["datetime"], format="%d/%m/%Y %H:%M:%S"
        )
        df = df.resample(f"1T", on="datetime").agg(
            {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "last",
                "OI": "last",
            }
        )
        df = pd.concat([cls.df_incomplete[token], df])
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
            df.index < current_time - datetime.timedelta(minutes=1)
        ]
        cls.df_incomplete[token] = df[
            df.index >= current_time - datetime.timedelta(minutes=1)
        ]
        if completed_df.shape[0] == 0:
            return

        data = completed_df.iloc[-1].to_dict()
        token_time = completed_df.index[-1].strftime("%Y-%m-%d %H:%M:%S")
        cls.__instance.db.collection("livefeed").document(
            cls.__instance.stockName[token]
        ).collection("ohlcv").document(token_time).set(data)
        cls.__instance.notifyObserver(token, completed_df)
        return

    # Callback method to receive live feed
    @staticmethod
    def callback_method(message):
        LiveFeed.count += 1
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
        logging.debug("Disconnected from Live feed. Reconnecting...")
        LiveFeed.startTime = time.perf_counter()
        logging.debug(f"count :  {LiveFeed.count}")
        LiveFeed.count = 0
        for thread in LiveFeed.Threads:
            thread.join()
            logging.debug(f"Thread-{thread.getName} joined")
        LiveFeed.Threads.clear()

        for token, data in LiveFeed.dataList.items():
            thread = Thread(target=LiveFeed.updatedb, args=(token, data))
            logging.debug(
                f"Thread-{thread.getName} created for token : {token}"
            )
            LiveFeed.Threads.append(thread)
            thread.start()

        return

    @staticmethod
    def connect_event():
        if LiveFeed.startTime is not None:
            logging.debug(
                f"Connected to Live feed.\tTime taken to reconnect : {time.perf_counter() - LiveFeed.startTime}"
            )
        return

    @staticmethod
    def error_event(data):
        logging.error("Error in Live feed : {}".format(data))
        return
