import logging
import time
from datetime import datetime, timedelta

import pandas as pd
from py_vollib.black_scholes.greeks.analytical import *
from py_vollib.black_scholes.implied_volatility import implied_volatility

from orderclient import get_quote
from utils import IST, OptionType, QuoteType, logging_handler

DATASTORE = "kotak_data/tokens.hdf5"
logging.basicConfig(level=logging.DEBUG, handlers=[logging_handler])


class OptionGeeks:
    def __init__(
        self,
        token: str,
        option_type: OptionType,
        strike_price: int = None,
        underlying_price: float = None,
    ):
        self.start = time.perf_counter()
        self._interest_rate = 0.1

        if not underlying_price:
            response = get_quote(token, QuoteType.ltp)
            if type(response) == dict:
                logging.error(response)
                raise Exception(response)
            underlying_price = float(response)

        self.strike_token = self.__find_strike_tokens__(
            token, option_type, underlying_price, strike_price
        )
        self.strike_token["optionType"] = option_type.value[0].lower()
        self.__find_expiry__()
        self.__find_option_price__()
        self.__find_iv__()
        self.__find_delta__()
        # ! Check if below works or not
        self.strike_token["optionType"] = option_type
        logging.info(
            f"Initializing OptionGeeks: {time.perf_counter() - self.start}"
        )

    def __del__(self):
        logging.info(
            f"Deleting OptionGeeks : {time.perf_counter() - self.start}"
        )

    def __find_strike_tokens__(
        self,
        token: str,
        option_type: OptionType,
        underlying_price: float,
        strike_price: int = None,
    ):
        token_name = pd.read_hdf(
            DATASTORE, "cashTokens", mode="r", where=f"index=='{token}'"
        )["instrumentName"].values[0]
        if strike_price:  # If strike price is given then find the exact strike
            strike_token = pd.read_hdf(
                DATASTORE,
                "fnoTokens",
                mode="r",
                where=f"instrumentName == '{token_name}' & optionType=='{option_type.value}' & strike == {strike_price}",
            )
        else:  # If strike price is not given then find the strike price within 3% of underlying price
            if option_type == OptionType.call:
                upper_limit = underlying_price * 1.03
                lower_limit = underlying_price * 1
            elif option_type == OptionType.put:
                upper_limit = underlying_price * 1
                lower_limit = underlying_price * 0.97

            strike_token = pd.read_hdf(
                DATASTORE,
                "fnoTokens",
                mode="r",
                where=f"instrumentName == '{token_name}' & optionType=='{option_type.value}' & strike >= {lower_limit} & strike <= {upper_limit}",
            )

        # First convert the expiry date to datetime object with tzinfo
        strike_token["expiry"] = pd.to_datetime(
            strike_token["expiry"], format="%d%b%y"
        ).dt.tz_localize(IST) + timedelta(hours=15, minutes=30)
        # Filter the data which are within next 1 week expiry
        strike_token = strike_token[
            (strike_token["expiry"] - datetime.now(IST)).dt.days <= 7
        ]
        strike_token = strike_token[
            ["strike", "expiry", "lotSize", "optionType"]
        ].sort_values("strike")
        strike_token["underlyingPrice"] = underlying_price
        return strike_token

    def __find_option_price__(self):
        for token in self.strike_token.index:
            response = get_quote(token, QuoteType.ltp)
            if type(response) == dict:
                logging.error(response)
                raise Exception(response)
            option_price = float(response)
            # Add the option price to the dataframe
            self.strike_token.loc[token, "optionPrice"] = option_price
        return

    def __find_expiry__(self):
        expiry = self.strike_token["expiry"]
        time_now = datetime.now(IST)

        duration_left = (expiry - time_now).dt.seconds / 3600 / 24 / 365
        self.strike_token["expiry"] = duration_left
        return

    def __find_iv__(self):
        for token, row in self.strike_token.iterrows():
            iv = implied_volatility(
                row["optionPrice"],
                row["underlyingPrice"],
                row["strike"],
                row["expiry"],
                self._interest_rate,
                row["optionType"],
            )
            self.strike_token.loc[token, "iv"] = iv

        return self.strike_token

    def __find_delta__(self):
        for token, row in self.strike_token.iterrows():
            d = delta(
                row["optionType"],
                row["underlyingPrice"],
                row["strike"],
                row["expiry"],
                self._interest_rate,
                row["iv"],
            )
            self.strike_token.loc[token, "delta"] = d

        return self.strike_token

    def find_all(self):
        for token, row in self.strike_token.iterrows():
            r = rho(
                row["optionType"],
                row["underlyingPrice"],
                row["strike"],
                row["expiry"],
                self._interest_rate,
                row["iv"],
            )
            g = gamma(
                row["optionType"],
                row["underlyingPrice"],
                row["strike"],
                row["expiry"],
                self._interest_rate,
                row["iv"],
            )
            t = theta(
                row["optionType"],
                row["underlyingPrice"],
                row["strike"],
                row["expiry"],
                self._interest_rate,
                row["iv"],
            )
            v = vega(
                row["optionType"],
                row["underlyingPrice"],
                row["strike"],
                row["expiry"],
                self._interest_rate,
                row["iv"],
            )
            self.strike_token.loc[token, "rho"] = r
            self.strike_token.loc[token, "gamma"] = g
            self.strike_token.loc[token, "theta"] = t
            self.strike_token.loc[token, "vega"] = v

        return self.strike_token


if __name__ == "__main__":
    nifty_call = OptionGeeks(11717, OptionType.call)
    print(nifty_call.strike_token)
    nifty_put = OptionGeeks(11717, OptionType.put)
    print(nifty_put.strike_token)

    banknifty_call = OptionGeeks(11721, OptionType.call)
    print(banknifty_call.strike_token)
    banknifty_put = OptionGeeks(11721, OptionType.put)
    print(banknifty_put.strike_token)
