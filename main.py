from keys import *
from functions import *
from googleapiclient.discovery import build
import pandas as pd

TICKER = "AMZN"

# Create service object with API
with build("youtube", "v3", developerKey=API_KEY) as service:

    # Create objects for search query and video query
    search = service.search()
    videos = service.videos()
    channels = service.channels()
    comments = service.commentThreads()

    # Generate Search request object
    request = search.list(part=["snippet"], q=f"{TICKER} stock", order="date", maxResults=50, type="video", videoDuration="long")

    # Call API and obtain response
    search_result = get_data(request)

    # Extract video ID and channel ID for each video in the search result
    vid_ids = list(map(lambda x : x["id"]["videoId"], search_result))
    channel_ids = list(map(lambda x : x["snippet"]["channelId"], search_result))

    # Generate video and channel request objects
    vid_request = videos.list(part=["id","snippet", "statistics", "contentDetails"], id=vid_ids)
    channel_request = channels.list(part=["statistics"], id=channel_ids, maxResults=50)
    comment_request = comments.list(part=["snippet"], id=vid_ids)

    # Call APIs for video, channel info, comments, and transcripts
    print("Fetching video metadata...")
    vid_data = get_data(vid_request)
    print("Fetching subscriber count...")
    channel_data = get_data(channel_request)
    print("Fetching comments...")
    comments_data = list(map(get_comments, vid_ids, [comments]*len(vid_ids)))
    print("Fetching transcripts...")
    transcript_data = list(map(get_transcript, vid_ids))

    # Extract data, collect into a dataframe, and save to csv file
    body = list(map(extract_vid_data, vid_data))
    headers = ["VideoID", "Title", "Description", "Tags", "Publish Date", "Thumbnail", "Duration", "Views", "Likes", "Number of Comments", "Channel Name", "Channel ID"]
    df = pd.DataFrame(data=body, columns=headers)
    df["Comments"] = comments_data
    df["Transcript"] = transcript_data

    # Extract channel data into a separate dataframe and join with main dataframe by channel ID (this is so each of multiple videos from the same channel have subscriber count in the output file)
    body = list(map(extract_channel_data, channel_data))
    headers = ["Channel ID", "Subscriber Count"]
    channel_df = pd.DataFrame(data=body, columns=headers)
    channel_df.set_index("Channel ID", inplace=True)

    df = df.join(channel_df, on="Channel ID")
    df.set_index("VideoID", inplace=True)

    # Output to Excel
    df.to_excel("output.xlsx", engine="xlsxwriter")