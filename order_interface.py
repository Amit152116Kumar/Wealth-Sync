from abc import ABC, abstractmethod

from models import OrderType, PositionType, TransactionType


class IOrderClient(ABC):
    @abstractmethod
    def get_order_report(self):
        pass

    @abstractmethod
    def placeOrder(
        self,
        orderType: OrderType,
        instrumentToken: str,
        transactionType: TransactionType,
        qty: int,
        trigger_price: int = 0,
        price: int = 0,
        variety: str = "REGULAR",
        tag: str = "fno",
    ):
        pass

    @abstractmethod
    def get_funds(self):
        pass
    
    @abstractmethod
    def get_position(self, position_Type: PositionType):
        pass
