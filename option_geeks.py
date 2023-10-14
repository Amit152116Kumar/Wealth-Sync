import math
import re
import time
from datetime import datetime, timedelta

import pandas as pd
from py_vollib.black_scholes.greeks.analytical import *
from py_vollib.black_scholes.implied_volatility import implied_volatility

from models import IST, OptionType, QuoteType, upcoming_expiry
from orderclient import OrderClient, get_quote

DATASTORE = "kotak_data/tokens.hdf5"


class OptionGeeks:
    def __init__(
        self,
        token,
        option_type: OptionType,
        strike_price=None,
        expiry=None,
        underlying_price=None,
    ) -> None:
        if underlying_price:
            self.underlying_price = underlying_price
        else:
            self.underlying_price = float(get_quote(token, QuoteType.ltp))

        if strike_price:
            self.strike_price = strike_price
        else:
            if option_type == OptionType.call:
                otm = math.ceil(self.underlying_price / 100) * 100
                diff = otm - self.underlying_price
                if diff < 10:
                    self.strike_price = otm + 100
                else:
                    self.strike_price = otm

            elif option_type == OptionType.put:
                otm = math.floor(self.underlying_price / 100) * 100
                diff = self.underlying_price - otm
                if diff < 10:
                    self.strike_price = otm - 100
                else:
                    self.strike_price = otm

        print(self.strike_price)
        if expiry is None:
            expiry = upcoming_expiry()
        print(expiry)
        token_info = pd.read_hdf(
            DATASTORE, "cashTokens", mode="r", where=f"index=='{token}'"
        )["instrumentName"].values[0]
        token_info = token_info.split()
        strike_token = pd.read_hdf(
            DATASTORE,
            "fnoTokens",
            mode="r",
            where=f"strike=='{self.strike_price}' & optionType=='{option_type.value}' "
        )
        
        print(strike_token)

        self.strike_token = strike_token.index.values[0]
        print(self.strike_token)
        self._expiry_date = (
            datetime.strptime(expiry, "%d%b%y").astimezone(IST)
            - datetime.now(IST)
        ).days / 365
        self.option_price = get_quote(strike_token, QuoteType.ltp)
        print(self.option_price)
        self._option_type = option_type.value[0].lower()
        self._interest_rate = 0.1
        self.iv = self.find_IV()

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
    og = OptionGeeks(11717, OptionType.call, underlying_price=44500)
    print(
        og.find_all(),
        og.strike_price,
        og.iv,
        og._expiry_date,
        og.underlying_price,
        og.option_price,
        sep="\n",
    )
