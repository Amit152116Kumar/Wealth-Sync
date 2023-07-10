import datetime
import os

import pandas as pd

from demoOrder import OrderClient
from observer_pattern import IEventListener


class Portfolio(IEventListener):
    def __init__(self):
        self.order_client = OrderClient()
        self.startfund = self.order_client.get_funds()


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
        print(args)
        return


if __name__ == "__main__":
    portfolio = Portfolio()
