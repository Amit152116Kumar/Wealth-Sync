from abc import ABC, abstractmethod

import pandas as pd

from utils import OptionType, TransactionType


class IEventListener(ABC):
    @abstractmethod
    def update(self, token: str, df: pd.DataFrame):
        pass

    @abstractmethod
    def update(self, token: str, transactionType: TransactionType):
        pass

    @abstractmethod
    def update(
        self,
        token: str,
        transactionType: TransactionType,
        optionType: OptionType,
        strike_price: int = 0,
        underlying_price: float = 0,
    ):
        pass


class IEventManager(ABC):
    @abstractmethod
    def attachObserver(self, observer: IEventListener):
        pass

    @abstractmethod
    def detachObserver(self, observer: IEventListener):
        pass

    @abstractmethod
    def notifyObserver(self, token: str, df: pd.DataFrame):
        pass

    @abstractmethod
    def notifyObserver(self, token: str, transactionType: TransactionType):
        pass

    @abstractmethod
    def notifyObserver(
        self,
        token: str,
        transactionType: TransactionType,
        optionType: OptionType,
    ):
        pass
