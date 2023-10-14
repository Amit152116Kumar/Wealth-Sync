import datetime
import logging
import sys

import pytz

IST = pytz.timezone("Asia/Kolkata")

date_now = datetime.datetime.now(tz=IST).strftime("%Y-%m-%d")
logging_handler = logging.FileHandler(f"logs/mylogger_{date_now}.log")
logging_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s - [%(module)s] - [%(funcName)s] - %(levelname)s - %(message)s"
    )
)
logging_handler.setLevel(logging.DEBUG)
