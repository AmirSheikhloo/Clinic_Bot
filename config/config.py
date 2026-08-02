# config/config.py

import os

from dotenv import load_dotenv


load_dotenv()


BALE_TOKEN = os.getenv(
    "BALE_TOKEN"
)


if not BALE_TOKEN:
    raise RuntimeError(
        "BALE_TOKEN is not configured"
    )