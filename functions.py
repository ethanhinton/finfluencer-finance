from youtube_transcript_api import YouTubeTranscriptApi as trans
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from googleapiclient.errors import HttpError
import pandas as pd

# Changes video duration from PTxMxS to MM:SS       
def format_duration(duration):
    cropped = duration[2:-1]
    cropped = cropped.replace("H", ":").replace("M", ":")
    parts = cropped.split(":")

    if len(parts) == 3:
        pass
    else:
        symbols = ["H", "M", "S"]
        for i, symbol in enumerate(symbols):
            if symbol not in duration:
                parts.insert(i, "00")
    
    out = []
    for val in parts:
        if len(val) != 2:
            val = "0" + val
        out.append(val)
    
    return ":".join(out)

def extract_vid_data(video):
    out = [
        video["id"],
        video["snippet"]["title"],
        video["snippet"]["description"],
        (video["snippet"]["tags"] if "tags" in video["snippet"].keys() else ""),
        video["snippet"]["publishedAt"],
        video["snippet"]["thumbnails"]["high"]["url"],
        format_duration(video["contentDetails"]["duration"]),
        int(video["statistics"]["viewCount"]),
        (int(video["statistics"]["likeCount"]) if "likeCount" in video["statistics"].keys() else "Likes Disabled"),
        (int(video["statistics"]["commentCount"]) if "commentCount" in video["statistics"].keys() else "Comments Disabled"),
        video["snippet"]["channelTitle"],
        video["snippet"]["channelId"]
    ]
    return out

def extract_channel_data(channel):
    out = (
        channel["id"],
        int(channel["statistics"]["subscriberCount"]) if channel["statistics"]["hiddenSubscriberCount"] == False else "Hidden"
    )
    return out    

def get_transcript(video_id):
    try:
        transcript = trans.list_transcripts(video_id).find_transcript(language_codes=["en"]).fetch()
        transcript_text = " ".join(list(map(lambda x: x["text"], transcript)))
    except (NoTranscriptFound, TranscriptsDisabled):
        print("No English transcript available")
        return "No transcript"
    return transcript_text

def get_data(request):
    try:
        response = request.execute()
        result = response["items"]
    except HttpError as e:
        print(f"Error status code : {e.status_code}, reason : {e.reason}")
        quit()
    return result

# Takes in comment service object and a list of video ids and returns a list containing a list of comments for each video
def get_comments(video_id, service):
    comment_request = service.list(part=["snippet"], videoId=video_id, maxResults=10000)
    try:
        response = comment_request.execute()
        comments = response["items"]
        return list(map(lambda x: x['snippet']['topLevelComment']['snippet']['textOriginal'], comments))
    except HttpError as e:
        print(f"Error status code : {e.status_code}, reason : {e.reason}")
        return [f"Error when retrieving comments : {e.reason}"]
    
def generate_dataframe(vid_data, comments_data, transcript_data, channel_data, index="VideoID"):
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

    return df.set_index(index, inplace=True)


