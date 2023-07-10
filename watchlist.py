import datetime
import json
import os

import pandas as pd
import requests
from dotenv import load_dotenv, set_key


class Watchlist:
    __dataStore = "financial_data.h5"

    def __init__(self) -> None:
        load_dotenv("config.env")
        self._access_token = os.getenv("access_token")
        self._consumer_key = os.getenv("consumer_key")
        self._host = os.getenv("host")
        date_today = datetime.date.today().strftime("%d%b%y")
        if date_today != os.getenv("date_today"):
            res = self.__fetch_tokens()
            if res == True:
                set_key("config.env", "date_today", date_today)

    def __fetch_tokens(self):
        token_url = self._host + "/scripmaster/1.1/filename"  # type: ignore
        header = {"accept": "application/json", "Authorization": f"Bearer {self._access_token}", "consumerKey": f"{self._consumer_key}"}
        res = requests.get(token_url, headers=header)
        if res.status_code != 200:
            print("Error in fetching tokens")
            return False
        res = res.json()

        # Read and save Cash token IDs
        try:
            cash_token = pd.read_csv(res["Success"]["cash"], sep="|", index_col="instrumentToken")
            cash_token.drop(["nudge", "tickSize", "isin", "multiplier", "exchangeToken"], axis=1, inplace=True)
            cash_token["expiry"].replace({0: pd.NaT}, inplace=True)
            cash_token.rename(columns={"OptionType": "optionType"}, inplace=True)
            cash_token.to_hdf(
                self.__dataStore,
                "/tokens/cashTokens",
                mode="a",
                append=False,
                index=True,
                complevel=9,
                format="table",
                complib="blosc:lz4",
                data_columns=True,
            )

            # Read and save FNO token IDs
            fno_token = pd.read_csv(res["Success"]["fno"], sep="|", index_col="instrumentToken")
            fno_token.drop(["tickSize", "isin", "multiplier", "exchangeToken"], axis=1, inplace=True)
            fno_token.to_hdf(
                self.__dataStore,
                "/tokens/fnoTokens",
                mode="a",
                append=False,
                index=True,
                complevel=9,
                format="table",
                complib="blosc:lz4",
                data_columns=True,
            )
        except Exception as e:
            print("Error in fetching tokens : ", e)
            return False

        return True

    def add_to_watchlist(self, is_fno=False, **kwargs):
        dataStore = self.__dataStore
        if is_fno:
            key = "/tokens/fnoTokens"
            try:
                strikeRange = kwargs.pop("strikeRange")
                keys = list(kwargs.keys())
                values = tuple(kwargs.values())
                token_list = pd.read_hdf(
                    dataStore,
                    key,
                    mode="r",
                    where=f"{keys[0]}=='{values[0]}' & {keys[1]}=='{values[1]}' & strike>='{strikeRange[0]}' & strike<='{strikeRange[1]}'",
                )

            except Exception as e:
                print(e)
                keys = list(kwargs.keys())
                values = tuple(kwargs.values())
                token_list = pd.read_hdf(
                    dataStore, key, mode="r", where=f"{keys[0]}=='{values[0]}' & {keys[1]}=='{values[1]}' & {keys[2]}=='{values[2]}'"
                )
            token_list["filename"] = (
                token_list["segment"]
                + "/"
                + token_list["instrumentName"]
                + "_"
                + token_list["optionType"]
                + "_"
                + token_list["strike"].astype(str)
                + "_"
                + token_list["expiry"]
            )
        else:
            key = "/tokens/cashTokens"
            keys = list(kwargs.keys())
            values = tuple(kwargs.values())
            token_list = pd.read_hdf(dataStore, key, mode="r", where=f"{keys[0]}=='{values[0]}' & {keys[1]}=='{values[1]}'")
            token_list["filename"] = token_list["instrumentType"] + "/" + token_list["instrumentName"].str.replace(" ", "_")
        print(token_list)
        ans = input("Update Watchlist (y/n) : ")

        if ans in ["n", "N"]:
            print("Watchlist not updated")
            return

        elif ans in ["y", "Y"]:
            # Update watchlist
            hdf = pd.HDFStore(dataStore, mode="a")
            key = "/watchlist"
            if key in hdf.keys():
                df = hdf.get(key)
                unique_df = pd.concat([df, token_list])  # type: ignore
                unique_df = unique_df.drop_duplicates()
                unique_df["expiry"] = pd.to_datetime(unique_df["expiry"])
                unique_df = unique_df.sort_values(
                    by=["segment", "instrumentType", "instrumentName", "expiry", "strike", "optionType"], ascending=True
                )
                unique_df["expiry"] = unique_df["expiry"].dt.strftime("%d%b%y")
                hdf.put(key, unique_df, format="table", data_columns=["instrumentToken"], index=False, complevel=9)
            else:
                hdf.append(key, token_list, format="table", data_columns=["instrumentToken"], index=False, complevel=9)

            hdf.close()
            print("Watchlist Updated 👍👍 \n")
            return {"status": "success", "message": "Watchlist Updated 👍👍"}

        return

    # Get Watchlist
    @classmethod
    def get_watchlist(self) -> pd.DataFrame:
        hdf = pd.HDFStore(self.__dataStore, mode="r")
        key = "/watchlist"
        if key in hdf.keys():
            df = hdf.get(key)
            hdf.close()
            json_data = df.T.to_json(orient="index")
            return json_data
        else:
            hdf.close()
            return {"status": "success", "message": "Watchlist is Empty !"}

    # Delete Token from Watchlist

    def remove_from_watchlist(self):
        df = pd.read_hdf(self.__dataStore, "/watchlist", mode="r")
        print(df)
        tokenID = int(input("Enter Token ID to delete : "))
        if tokenID not in df["instrumentToken"].values:
            print("Token ID not in Watchlist")
            return {"status": "error", "message": "Token ID not in Watchlist"}
        df = df.drop(df[df["instrumentToken"] == tokenID].index)
        df.to_hdf(
            self.__dataStore,
            "/watchlist",
            mode="a",
            append=False,
            format="table",
            data_columns=["instrumentToken"],
            index=False,
            complevel=9,
            complib="blosc:lz4",
        )
        return {"status": "success", "message": "Token ID deleted from Watchlist"}


if __name__ == "__main__":
    watchlist = Watchlist()
    watchlist.add_to_watchlist(is_fno=False, instrumentType="IN", instrumentName="NIFTY BANK")
