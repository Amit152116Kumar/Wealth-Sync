from collections import defaultdict

import pandas as pd

from observer_pattern import IEventListener, IEventManager


class Handler(IEventManager, IEventListener):
    def __init__(self) -> None:
        self._listOfObservers = defaultdict(set)
        self._listOfTags = set()

    def attachObserver(self, observer: IEventListener, tag: str):
        self._listOfObservers[tag].add(observer)
        self._listOfTags.add(tag)
        return

    def detachObserver(self, observer: IEventListener, tag: str):
        if observer in self._listOfObservers[tag]:
            self._listOfObservers[tag].remove(observer)

            if len(self._listOfObservers[tag]) == 0:
                self._listOfObservers.pop(tag)
                self._listOfTags.remove(tag)
        return

    def notifyObserver(self, token: str, df: pd.DataFrame):
        for tag in self._listOfObservers:
            for observer in self._listOfObservers[tag]:
                observer.update(token, df)
        return

    def update(self, token: str, df: pd.DataFrame):
        df["datetime"] = pd.to_datetime(
            df["datetime"], format="%d/%m/%Y %H:%M:%S"
        )
        df = df.resample("1T", on="datetime").agg(
            {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "last",
                "OI": "last",
            }
        )
        self.notifyObserver(token, df)
        return
