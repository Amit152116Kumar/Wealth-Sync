import json
import os

import firebase_admin
import pandas as pd
from dotenv import load_dotenv
from firebase_admin import credentials, firestore, initialize_app

from models import Strategy


class Firestore:
    _instance = None

    def initialize(self):
        load_dotenv("config.env")
        encoded_json = os.getenv("FIRESTORE_KEY")
        FIRESTORE_KEY = json.loads(encoded_json)
        credential = credentials.Certificate(FIRESTORE_KEY)
        initialize_app(credential)
        self.db_client = firestore.client()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.initialize()
        return cls._instance

    @classmethod
    def db(cls):
        instance = cls.get_instance()
        return instance.db_client

    @classmethod
    def add_strategy(cls, token: int, strategy: dict):
        db = cls.db()
        df = pd.read_hdf(
            "kotak_data/tokens.hdf5",
            key="cashTokens",
            mode="r",
            where="index==" + str(token),
        )
        print(df)
        documentName = (df["exchange"] + "_" + df["instrumentName"]).values[0]
        print(documentName)
        db.collection("watchlist").document(documentName).collection(
            "strategy"
        ).document().set(strategy)
        return {"status": "success", "message": "Strategy added successfully."}

    @classmethod
    def get_strategy(cls, documentName: str):
        db = cls.db()
        strategy = (
            db.collection("watchlist")
            .document(documentName)
            .collection("strategy")
            .get()[0]
        )
        return strategy

    @classmethod
    def add_watchlist(cls, documentName: str, info: dict):
        db = cls.db()
        db.collection("watchlist").document(documentName).set(info)
        return {
            "status": "success",
            "message": "Watchlist added successfully.",
        }

    @classmethod
    def get_watchlist(cls):
        db = cls.db()
        docs = db.collection("watchlist").stream()
        return docs

    @classmethod
    def add_ohlcv(cls, documentName: str, id: str, info: dict):
        db = cls.db()
        docs = (
            db.collection("livefeed")
            .document(documentName)
            .collection("ohlcv")
            .document(id)
            .set(info)
        )
        return docs

    @classmethod
    def get_ohlcv(cls, documentName: str, size: int):
        db = cls.db()
        docs = (
            db.collection("livefeed")
            .document(documentName)
            .collection("ohlcv")
            .order_by("__name__", direction=firestore.Query.DESCENDING)
            .limit(size)
            .stream()
        )
        return docs

    @classmethod
    def add_livefeed_info(cls, documentName: str, info: dict):
        db = cls.db()
        docs = db.collection("livefeed").document(documentName).set(info)
        return docs

    @classmethod
    def get_livefeed_info(cls, documentName: str):
        db = cls.db()
        docs = db.collection("livefeed").document(documentName).get()
        return docs


if __name__ == "__main__":
    db = Firestore.db()
