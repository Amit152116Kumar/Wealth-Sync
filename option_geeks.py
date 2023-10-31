import logging
import math
import re
import time
from datetime import datetime, timedelta

import pandas as pd
from py_vollib.black_scholes.greeks.analytical import *
from py_vollib.black_scholes.implied_volatility import implied_volatility

from models import IST, OptionType, QuoteType, upcoming_expiry
from mylogger import logging_handler
from orderclient import OrderClient, get_quote

DATASTORE = "kotak_data/tokens.hdf5"
logging.basicConfig(level=logging.DEBUG, handlers=[logging_handler])


class OptionGeeks:
    def __init__(
        self,
        token,
        option_type: OptionType,
        strike_price=None,
        underlying_price=None,
    ) -> None:
        self.underlying_price = self.find_underlying_price(token,underlying_price)
        self.strike_price = self.find_strike_price(strike_price,option_type)

        strike_token = self.find_strike_token(token,option_type)
        self.strike_token = strike_token.index[0].item()

        self._expiry_date = self.find_expiry(strike_token)
        
        response = get_quote(self.strike_token, QuoteType.ltp)
        if type(response) == dict:
            raise Exception(response)
        self.option_price = float(response)

        self._option_type = option_type.value[0].lower()
        self._interest_rate = 0.1
        self.iv = self.find_IV()
    
    def find_underlying_price(self,token,underlying_price):
        if underlying_price:
            return underlying_price
        else:
            response = get_quote(token, QuoteType.ltp)
            if type(response) == dict:
                raise Exception(response)
            return float(response)
        
    def find_strike_price(self,strike_price,option_type):
        if strike_price:
            return strike_price
        else:
            if option_type == OptionType.call:
                otm = math.ceil(self.underlying_price / 100) * 100
                diff = otm - self.underlying_price
                if diff < 10:
                    return otm + 100
                else:
                    return otm

            elif option_type == OptionType.put:
                otm = math.floor(self.underlying_price / 100) * 100
                diff = self.underlying_price - otm
                if diff < 10:
                    return otm - 100
                else:
                    return otm

    def find_strike_token(self,token,option_type):
        token_name = pd.read_hdf(
            DATASTORE, "cashTokens", mode="r", where=f"index=='{token}'"
        )["instrumentName"].values[0]

        strike_token = pd.read_hdf(
            DATASTORE,
            "fnoTokens",
            mode="r",
            where=f"instrumentName == '{token_name}' & strike=='{self.strike_price}' & optionType=='{option_type.value}' ",
        )
        return strike_token.head(1)

    def find_expiry(self,strike_token):
        expiry = strike_token["expiry"].values[0]
        expiry = datetime.strptime(expiry, "%d%b%y").astimezone(IST)+timedelta(hours=15,minutes=30)
        
        time_now = datetime.now(IST)
        if time_now.hour>15 or (time_now.hour>=15 and time_now.minute>30):
            curr_time = time_now.replace(hour=15,minute=30)
        else :
            curr_time = time_now

        expiry_time = (expiry- curr_time).total_seconds()/(3600*24*365)
        return expiry_time
    
    def find_IV(self):
        iv = implied_volatility(
            self.option_price,
            self.underlying_price,
            self.strike_price,
            self._expiry_date,
            self._interest_rate,
            self._option_type,
        )
        return round(iv, 5)

    def find_delta(self):
        d = delta(
            self._option_type,
            self.underlying_price,
            self.strike_price,
            self._expiry_date,
            self._interest_rate,
            self.iv,
        )
        return round(d, 5)

    def find_gamma(self):
        g = gamma(
            self._option_type,
            self.underlying_price,
            self.strike_price,
            self._expiry_date,
            self._interest_rate,
            self.iv,
        )
        return round(g, 5)

    def find_theta(self):
        t = theta(
            self._option_type,
            self.underlying_price,
            self.strike_price,
            self._expiry_date,
            self._interest_rate,
            self.iv,
        )
        return round(t, 5)

    def find_vega(self):
        v = vega(
            self._option_type,
            self.underlying_price,
            self.strike_price,
            self._expiry_date,
            self._interest_rate,
            self.iv,
        )
        return round(v, 5)

    def find_rho(self):
        r = rho(
            self._option_type,
            self.underlying_price,
            self.strike_price,
            self._expiry_date,
            self._interest_rate,
            self.iv,
        )
        return round(r, 5)

    def find_all(self):
        """
        The function "find_all" returns a dictionary containing the values of various financial metrics
        such as implied volatility, delta, gamma, theta, vega, and rho.
        :return: a dictionary with keys "iv", "delta", "gamma", "theta", "vega", and "rho". The values
        associated with these keys are the results of calling the corresponding methods `find_delta()`,
        `find_gamma()`, `find_theta()`, `find_vega()`, and `find_rho()`.
        """
        iv = self.iv
        d = self.find_delta()
        g = self.find_gamma()
        t = self.find_theta()
        v = self.find_vega()
        r = self.find_rho()
        return {
            "iv": iv,
            "delta": d,
            "gamma": g,
            "theta": t,
            "vega": v,
            "rho": r,
        }


if __name__ == "__main__":
    start = time.perf_counter()
    og = OptionGeeks(11717, OptionType.call)
    print(
        og.find_all(),
        og.strike_price,
        og.iv,
        og._expiry_date,
        og.underlying_price,
        og.option_price,
        sep="\n",
    )
