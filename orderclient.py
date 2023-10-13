import json

from kotakclient import KotakClient
from models import *
from order_interface import IOrderClient


class OrderClient(IOrderClient):
    def __init__(self) -> None:
        self._client = KotakClient.get_client

    def __del__(self):
        pass

    def get_order_report(self):
        try:
            orders = self._client.order_report()
        except Exception as e:
            return {"status": "error", "message": str(e)}
        return OrderBookResponse(**orders)

    # Get Trade Report
    def get_trade_report(self):
        try:
            trades = self._client.trade_report()
        except Exception as e:
            return {"status": "error", "message": str(e)}
        return TradeBookResponse(**trades)

    # Place All Types of Orders
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
        validity = OrderValidity.gfd.value
        try:
            response = self._client.place_order(
                order_type=orderType.value,
                instrument_token=int(instrumentToken),
                transaction_type=transactionType.value,
                quantity=qty,
                price=price,
                trigger_price=trigger_price,
                validity=validity,
                tag=tag,
                variety=variety,
            )

        except Exception as e:
            return {"status": "error", "message": str(e)}
        response = json.dumps(response, indent=4)
        return response

    def cancelOrder(self, order_id: str):
        try:
            response = self._client.cancel_order(order_id=order_id)
        except Exception as e:
            return {"status": "error", "message": str(e)}
        return response

    # Get Available Funds in Account
    def get_funds(self):
        try:
            response = self._client.margin()["Success"]["derivatives"][0]["options"]  # type: ignore
        except Exception as e:
            return {"status": "error", "message": str(e)}
        return FundsResponse(**response)

    # Get Required Margin for Order to be placed
    def get_required_margin(self, transactionType: TransactionType, order_info: OrderParams):
        order_info = [order.__dict__() for order in order_info]
        try:
            margin = self._client.margin_required(transaction_type=transactionType.value, order_info=order_info)
        except Exception as e:
            return {"status": "error", "message": str(e)}
        return MarginReqResponse(**margin).Success  # type: ignore

    # Get Open Positions for given position type
    def get_position(self, position_Type: PositionType):
        try:
            positions = self._client.positions(position_Type.value)  # type: ignore
        except Exception as e:
            return {"status": "error", "message": str(e)}
        positions = json.dumps(positions, indent=4)

        return positions


# Get Quote for given token ID
def get_quote(instrumentToken: str, quote_type: QuoteType):
    try:
        quote = KotakClient.get_client.quote(instrumentToken, quote_type.value)["success"]  # type: ignore
    except Exception as e:
        return {"status": "error", "message": str(e)}
    if quote_type == QuoteType.ltp:
        return quote[0]["lastPrice"]
    elif quote_type == QuoteType.ohlc:
        return QuoteOHLCResponse(**quote[0])
    else:
        return QuoteDepthResponse(**quote)


if __name__ == "__main__":
    print("Order Client")
