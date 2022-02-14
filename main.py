from keys import *
from functions import *
import csv
from googleapiclient.discovery import build




TICKER = "AMZN"

# Create service object with API
with build("youtube", "v3", developerKey=API_KEY) as service:

    # Create objects for search query and video query
    search = service.search()
    videos = service.videos()
    channels = service.channels()

    # Generate Search request object
    request = search.list(part=["snippet"], q=f"{TICKER} stock", order="relevance", maxResults=50)

    # Call API and obtain response
    search_result = get_data(request)

    # Extract video ID and channel ID for each video in the search result
    vid_ids = list(map(lambda x : x["id"]["videoId"], search_result))
    channel_ids = list(map(lambda x : x["snippet"]["channelId"], search_result))
    # print(f"Channel IDs: {len(channel_ids)}")
    # print(channel_ids)
    
    # Generate video and channel request objects
    vid_request = videos.list(part=["snippet", "statistics", "contentDetails"], id=vid_ids)
    channel_request = channels.list(part=["statistics"], id=channel_ids, maxResults=50)

    # Call APIs for video and channel info
    vid_data = get_data(vid_request)
    channel_data = get_data(channel_request)

    # Extract data and save to csv file
    body = list(map(extract_vid_data, vid_data))
    headers = ["Title", "Description", "Tags", "Publish Date", "Thumbnail", "Duration", "Views", "Likes", "Comments", "Channel Name"]
    
    with open("output.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(body)
