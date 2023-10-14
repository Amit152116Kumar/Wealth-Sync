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
        db = Firestore.db()
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


if __name__ == "__main__":
    db = Firestore.db()
