import datetime
import logging
import os
from collections import defaultdict

import pandas as pd

from demoOrder import OrderClient
from models import OptionType, OrderType, PositionType, TransactionType
from mylogger import logging_handler
from observer_pattern import IEventListener
from option_geeks import OptionGeeks

logging.basicConfig(level=logging.DEBUG, handlers=[logging_handler])


class Portfolio(IEventListener):
    def __init__(self):
        self.order_client = OrderClient()
        self.startfund = self.order_client.get_funds()
        self.strike_token = defaultdict(int)
        self.strike_price = defaultdict(int)
        self.optionType = defaultdict(OptionType)
        self.quantity = 25

    def __del__(self):
        open_position = self.order_client.get_position(
            position_Type=PositionType.open
        )

        for position in open_position:
            # Finding the Token of the position from the strike_token dictionary
            strike_token = position["instrumentToken"]
            keys = list(self.strike_token.keys())
            values = list(self.strike_token.values())
            idx = values.index(strike_token)
            self.sell(keys[idx])

        orderbook = self.order_client.get_order_report()
        funds = self.order_client.get_funds()
        pnl = funds - self.startfund
        logging.info(f"Orderbook : {orderbook}")
        logging.info(f"PnL : {pnl}")

    def update(self, *args):
        token = args[0]

        if type(args[1]) == pd.DataFrame:
            df = args[1]
            price = df["close"].values[-1]
            if price >= self.strike_price[token]:
                self.sell(token)
                strike_price = self.strike_price[token] + 100
                self.buy(token, self.optionType[token],strike_price,price)
                return

            optionGeek = OptionGeeks(token, OptionType.call,underlying_price=price)
            optionGeek2 = OptionGeeks(token, OptionType.put,underlying_price=price)

            logging.debug(f"Price : {price}")
            logging.debug(
                f"Token : {token} - Call : [ Strike Price : {optionGeek.strike_price} - Option Price : {optionGeek.option_price} - IV : {optionGeek.iv}]"
            )
            logging.debug(optionGeek.find_all())
            logging.debug(
                f"Token : {token} - Put : [ Strike Price : {optionGeek2.strike_price} - Option Price : {optionGeek2.option_price} - IV : {optionGeek2.iv}]"
            )
            logging.debug(optionGeek2.find_all())

        else:
            transactionType = args[1]
            if transactionType == TransactionType.buy:
                optionType = args[2]
                self.buy(token, optionType)
            else:
                self.sell(token)

        return

    def buy(self, token, optionType,strike_price=None,underlying_price=None):
        """
        The function `buy` is used to place a buy order for a specific option contract, and it logs
        relevant information about the option before placing the order.
        
        :param token: The "token" parameter is used to identify the specific option contract. It is
        typically a unique identifier assigned to each option contract by the exchange
        :param optionType: The `optionType` parameter represents the type of option to buy. It can be
        either "CE" (Call Option) or "PE" (Put Option)
        :param strike_price: The strike_price parameter is the price at which the option contract can be
        exercised. It represents the predetermined price at which the underlying asset can be bought or
        sold when the option is exercised
        :param underlying_price: The underlying_price parameter represents the current price of the
        underlying asset on which the option is based
        :return: nothing.
        """
        optionGeek = OptionGeeks(token, optionType,strike_price,underlying_price)
        logging.info(
            f"Token : {token} - {optionType} : [ Strike Price : {optionGeek.strike_price} - Option Price : {optionGeek.option_price} - IV : {optionGeek.iv}]"
        )
        logging.debug(optionGeek.find_all())

        self.strike_token[token] = optionGeek.strike_token
        self.strike_price[token] = optionGeek.strike_price
        self.optionType[token] = optionType

        response = self.order_client.placeOrder(
            orderType=OrderType.mis_order,
            instrumentToken=optionGeek.strike_token,
            transactionType=TransactionType.buy,
            qty=self.quantity,
        )
        logging.info(response)
        return

    def sell(self, token):
        """
        The `sell` function places a sell order for a option of the given token and logs the response.

        :param token: The `token` parameter is used to specify the instrument token for the order.
        """
        response = self.order_client.placeOrder(
            orderType=OrderType.mis_order,
            instrumentToken=self.strike_token[token],
            transactionType=TransactionType.sell,
            qty=self.quantity,
        )
        logging.info(response)
        return


if __name__ == "__main__":
    portfolio = Portfolio()
