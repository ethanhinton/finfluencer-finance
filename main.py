from keys import *
import csv
import requests
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json


TICKER = "AMZN"

# Create service object with API
with build("youtube", "v3", developerKey=API_KEY) as service:

    # Create objects for search query and video query
    search = service.search()
    videos = service.videos()

    # Generate Search request object
    request = search.list(part=["snippet"], q=f"{TICKER} stock", order="relevance")

    # Call API and obtain response
    try:
        response = request.execute()
    except HttpError as e:
        print(f"Error status code : {e.status_code}, reason : {e.reason}")

    print(response["items"])