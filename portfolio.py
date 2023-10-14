import datetime
import os
from collections import defaultdict

import pandas as pd

from demoOrder import OrderClient
from models import OptionType, OrderType
from observer_pattern import IEventListener
from option_geeks import OptionGeeks


class Portfolio(IEventListener):
    def __init__(self):
        self.order_client = OrderClient()
        self.startfund = self.order_client.get_funds()
        self.signal = defaultdict(set)

    def __del__(self):
        pass
        # print(self.startfund)
        # endfund = self.order_client.get_funds()
        # # end fund to the txt file
        # with open("funds.txt", "w") as f:
        #     f.write(endfund)

        # if endfund > self.startfund:
        #     with open("profit.txt", "a") as f:
        #         f.write(f"Date : {datetime.date.today}\nProfit: {endfund - self.startfund}")
        # else:
        #     with open("loss.txt", "a") as f:
        #         f.write(f"Date : {datetime.date.today}\nLoss: {self.startfund - endfund}")

    def update(self, *args):
        token = args[0]

        if type(args[1]) == pd.DataFrame:
            df = args[1]
            price = df["close"].values[-1]
            print(price)
            optionGeek = OptionGeeks(token, OptionType.call)
            optionGeek2 = OptionGeeks(token, OptionType.put)
            print(
                "Call : ",
                optionGeek.strike_price,
                optionGeek.option_price,
                optionGeek.iv,
            )
            print(
                "Put : ",
                optionGeek2.strike_price,
                optionGeek2.option_price,
                optionGeek2.iv,
            )

        else:
            flag = ~self.signal.keys().__contains__(token)
            if flag or args != self.signal[token]:
                print(args)
                self.signal[token] = args
                response = self.order_client.placeOrder(
                    orderType=OrderType.mis_order,
                    instrumentToken=token,
                    transactionType=args[1],
                    qty=1,
                )
                print(response)
                if len(args) == 3:
                    optionGeeks = OptionGeeks(token, args[2])
                    print(
                        optionGeeks.strike_price,
                        optionGeeks.option_price,
                        optionGeeks.iv,
                    )
                    print(optionGeeks.find_all())
        return


if __name__ == "__main__":
    portfolio = Portfolio()
