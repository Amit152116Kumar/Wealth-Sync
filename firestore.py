import json
import os

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials, firestore

load_dotenv("firestore.env")
encoded_json = os.getenv("FIRESTORE_KEY")
FIRESTORE_KEY = json.loads(encoded_json)
cred = credentials.Certificate(FIRESTORE_KEY)
firebase_admin.initialize_app(cred)
db = firestore.client()
