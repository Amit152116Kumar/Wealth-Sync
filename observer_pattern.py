from abc import ABC, abstractmethod


class IEventListener(ABC):
    @abstractmethod
    def update(self, *args):
        pass


class IEventManager(ABC):
    @abstractmethod
    def attachObserver(self, observer: IEventListener):
        pass

    @abstractmethod
    def detachObserver(self, observer: IEventListener):
        pass

    @abstractmethod
    def notifyObserver(self, *args):
        pass
