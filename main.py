from keys import *
import csv
import requests
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json


TICKER = "AMZN"

with build("youtube", "v3", developerKey=API_KEY) as service:
    search = service.search()
    videos = service.videos()

    request = search.list(part=["snippet"], q=f"{TICKER} stock", order="relevance")

    try:
        response = request.execute()
    except HttpError as e:
        print(f"Error status code : {e.status_code}, reason : {e.reason}")

    print(response["items"])