import os

import pandas as pd
import requests
from dotenv import load_dotenv

from firestore import db

DATASTORE = "kotak_data/tokens.hdf5"


class Watchlist:
    def __init__(self) -> None:
        load_dotenv("config.env")
        self._access_token = os.getenv("access_token")
        self._consumer_key = os.getenv("consumer_key")
        self._host = os.getenv("host")
        # self.__fetch_tokens()

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
            cash_token.drop(["expiry","OptionType","strike"], axis=1, inplace=True)
            cash_token.to_hdf(
                DATASTORE,
                "/cashTokens",
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
            fno_token.drop(['isin'], axis=1, inplace=True)
            fno_token.to_hdf(
                DATASTORE,
                "/fnoTokens",
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
        dataStore = DATASTORE
        if is_fno:
            key = "/fnoTokens"
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
        else:
            key = "/cashTokens"
            keys = list(kwargs.keys())
            values = tuple(kwargs.values())
            token_list = pd.read_hdf(dataStore, key, mode="r", where=f"{keys[0]}=='{values[0]}' & {keys[1]}=='{values[1]}'")
        token_list = token_list.reset_index()
        print(token_list)
        ans = input("Update Watchlist (y/n) : ")

        if ans in ["n", "N"]:
            print("Watchlist not updated")
            return

        elif ans in ["y", "Y"]:
            # Update watchlist
            for index, row in token_list.iterrows():
                stockName = row["exchange"] + "_" + row["instrumentName"]
                db.collection("watchlist").document(stockName).set(row.to_dict())
            return {"status": "success", "message": "Watchlist Updated 👍👍"}

        return

    # Get Watchlist
    @classmethod
    def get_watchlist(self) -> pd.DataFrame:
        hdf = pd.HDFStore(DATASTORE, mode="r")
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
        df = pd.read_hdf(DATASTORE, "/watchlist", mode="r")
        print(df)
        tokenID = int(input("Enter Token ID to delete : "))
        if tokenID not in df["instrumentToken"].values:
            print("Token ID not in Watchlist")
            return {"status": "error", "message": "Token ID not in Watchlist"}
        df = df.drop(df[df["instrumentToken"] == tokenID].index)
        df.to_hdf(
            DATASTORE,
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
    watchlist.add_to_watchlist(is_fno=False, instrumentType="IN", instrumentName="NIFTY 50")
