import datetime
import json

from models import IST, OrderType, PositionType, QuoteType, TransactionType
from order_interface import IOrderClient
from orderclient import get_quote


class OrderClient(IOrderClient):
    gst = 0.18
    stt_charges = 0.000625
    transaction_charges = 0.0005
    sebi_charges = 0.000001
    buy_stamp_charges = 0.00003

    def __init__(self):
        self.orderbook = []
        self.open_positions = []
        self.funds = 100000

    def get_funds(self):
        return self.funds

    def get_order_report(self):
        return self.orderbook

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
        if price == 0:
            response = get_quote(instrumentToken, quote_type=QuoteType.ltp)
            if type(response) == dict:
                return response
            else:
                price = float(response)

        amount = qty * price
        orderinfo = {
            "timestamp": datetime.datetime.now(IST),
            "orderType": orderType.value,
            "instrumentToken": instrumentToken,
            "transactionType": transactionType.value,
            "qty": qty,
            "trigger_price": price,
            "variety": variety,
            "tag": tag,
        }

        if transactionType == TransactionType.buy:
            gst_amount = (amount * self.sebi_charges) + (
                amount * self.transaction_charges
            )
            gst_charges = gst_amount * self.gst
            total_charges = (
                gst_amount + gst_charges + (amount * self.buy_stamp_charges)
            )
            if amount > self.funds:
                return {"status": "error", "message": "Insufficient Funds"}
            else:
                self.funds -= amount + total_charges
                orderinfo["total_charges"] = total_charges
                self.open_positions.append(orderinfo)

        else:
            if len(self.open_positions) == 0:
                return {"status": "error", "message": "No Open Positions"}
            gst_amount = (amount * self.sebi_charges) + (
                amount * self.transaction_charges
            )
            gst_charges = gst_amount * self.gst
            total_charges = (
                gst_amount + gst_charges + (amount * self.stt_charges)
            )
            orderinfo["total_charges"] = total_charges
            self.funds += amount - total_charges
            self.open_positions.pop()

        self.orderbook.append(orderinfo)

        return {"status": "success", "message": orderinfo}

    def get_position(self, position_Type: PositionType):
        return self.open_positions
