import email
import os
import time
from imaplib import IMAP4_SSL

from dotenv import load_dotenv, set_key

from ks_api_client import ks_api


class KotakClient:
    __instance = None
    __client = None

    def __new__(cls):
        if not cls.__instance:
            cls.__instance = super(KotakClient, cls).__new__(cls)
        return cls.__instance

    def __init__(self) -> None:
        load_dotenv("config.env")
        self.__host = os.getenv("HOST")
        self.__consumer_key = os.getenv("CONSUMER_KEY")
        self.__access_token = os.getenv("ACCESS_TOKEN")
        self.__secret_key = os.getenv("SECRET_KEY")
        self.__client = self.__client_login()

    def __del__(self):
        pass

    @classmethod
    @property
    def get_client(cls):
        if not cls.__client:
            cls.__client = KotakClient().__client
        return cls.__client

    def __client_login(self):
        # Fetch access code from txt file
        user_id = os.getenv("USERID")
        password = os.getenv("PASSWORD")

        try:
            client = ks_api.KSTradeApi(
                access_token=self.__access_token,
                userid=user_id,
                consumer_key=self.__consumer_key,
                ip="127.0.0.1",
                app_id="1",
                consumer_secret=self.__secret_key,
                host=self.__host,
            )
        except Exception as e:
            exit(code="Not Connected to Internet : {}".format(e))

        # Get session for user
        login_response = client.login(password=password)
        message = login_response["Success"]["message"]  # type: ignore
        if message == "Your access code is generated successfully.":
            print("Waiting for 2FA authentication...")
            time.sleep(5)

        # Get session for 2FA authentication if doesn't exist then fetch
        # access code from mail and login
        access_code = self.__fetch_access_code()

        try:
            response = client.session_2fa(access_code=access_code)

        except Exception as e:
            print("Error in Login : ", e)

        return client

    @staticmethod
    def __fetch_access_code():
        username = os.getenv("GMAIL_USERNAME")
        password = os.getenv("GMAIL_PASSWORD")
        mail = IMAP4_SSL("imap.gmail.com")
        mail.login(username, password)  # type: ignore
        mail.select("inbox")
        _, messages = mail.search(None, f'FROM "accesscode@kotaksecurities.com"')
        msg_id = messages[0].split(b" ")[-1]

        _, message = mail.fetch(msg_id, "(RFC822)")
        for response in message:
            if isinstance(response, tuple):
                msg = email.message_from_bytes(response[1])
                access_code = msg["Subject"].split(" ")[-1]
                return str(access_code)
        return None


if __name__ == "__main__":
    client = KotakClient.get_client
    print(client)
