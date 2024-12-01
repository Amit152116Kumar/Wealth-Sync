import json
import logging
from collections import defaultdict

import pandas as pd

from demoOrder import OrderClient
from observer_pattern import IEventListener
from option_geeks import OptionGeeks
from utils import (
    OptionType,
    OrderType,
    PositionType,
    TransactionType,
    logging_handler,
)

logging.basicConfig(level=logging.DEBUG, handlers=[logging_handler])


class Portfolio(IEventListener):
    def __init__(self, delta: float, quantity: int = 1):
        logging.info("Initializing Portfolio")
        self.order_client = OrderClient()
        self.startfund = self.order_client.get_funds()
        self.strike_token = defaultdict(int)
        self.optionType = defaultdict(OptionType)
        self.df = defaultdict(pd.DataFrame)
        self.quantity = quantity
        self.delta = delta

    def __del__(self):
        logging.info("Deleting Portfolio")
        open_position = self.order_client.get_position(
            position_Type=PositionType.open
        )

        for position in open_position:
            strike_token = position["instrumentToken"]
            # Find the underlying token of the strike token
            keys = list(self.strike_token.keys())
            values = list(self.strike_token.values())
            idx = values.index(strike_token)
            self.update(keys[idx], TransactionType.sell)

        orderbook = self.order_client.get_order_report()
        funds = self.order_client.get_funds()
        pnl = funds - self.startfund
        logging.info(f"Open Position : {self.order_client.open_positions}")
        logging.info(f"Orderbook : {orderbook}")
        logging.info(f"PnL : {pnl}")

    """UPDATE ABOUT THE UNDERLYING PRICE OF THE ASSET"""

    def update(self, token: str, df: pd.DataFrame):
        price = df["close"].values[-1]
        # ! Roll the contract if the option price delta increase by 0.1 or decrease by 0.1
        if token in self.optionType and price >= self.strike_price[token]:
            logging.info("Rolling Option contract")
            self.update(token, TransactionType.sell)
            strike_price = self.strike_price[token] + 100
            self.update(
                token,
                TransactionType.buy,
                self.optionType[token],
                strike_price,
                price,
            )
        return

    """For Selling the Option of the Stock"""

    def update(self, token: str, transactionType: TransactionType):
        if self.strike_token[token] == 0:
            logging.error("No Open Position")
            return "error"
        # ! There is problem in placeOrder for the sell order. Check and Solve it
        qty = self.df[token]["lotSize"].values[0] * self.quantity
        response = self.order_client.placeOrder(
            orderType=OrderType.mis_order,
            instrumentToken=self.strike_token[token],
            transactionType=transactionType,
            qty=qty,
        )
        logging.info(json.dumps(response, indent=4))
        if response["status"] == "success":
            self.strike_token.pop(token)
            self.optionType.pop(token)
            self.strike_price.pop(token)
        return response["status"]

    """For Buying the Option of the Stock"""

    def update(
        self,
        token: str,
        transactionType: TransactionType,
        optionType: OptionType,
        strike_price: int = None,
        underlying_price: float = None,
    ):
        optionGeek = OptionGeeks(
            token, optionType, strike_price, underlying_price
        )

        self.df[token] = optionGeek.strike_token
        qty = self.df[token]["lotSize"].values[0] * self.quantity
        # ! Solve the problem of optionPrice
        response = self.order_client.placeOrder(
            orderType=OrderType.mis_order,
            instrumentToken=optionToken,
            transactionType=transactionType,
            qty=qty,
            price=optionPrice,
        )
        # ! Check if these are required or not
        if response["status"] == "success":
            self.strike_token[token] = optionGeek.strike_token
            self.strike_price[token] = optionGeek.strike_price
            self.optionType[token] = optionType
        logging.info(json.dumps(response, indent=4))
        return


if __name__ == "__main__":
    portfolio = Portfolio()
