from youtube_transcript_api import YouTubeTranscriptApi as trans
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from googleapiclient.errors import HttpError
import asyncio

# Changes video duration from PTxMxS to MM:SS       
def format_duration(duration):
    split = duration[2:].split("M")
    minutes = split[0]

    seconds = split[1][:-1]
    if len(seconds) == 0:
        seconds = "00"
    elif len(seconds) == 1:
        seconds = f"0{seconds}"

    return f"{minutes}:{seconds}"


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
        (int(video["statistics"]["likeCount"]) if "likeCount" in video["statistics"].keys() else ""),
        int(video["statistics"]["commentCount"]),
        video["snippet"]["channelTitle"],
        video["snippet"]["channelId"]
    ]
    return out

def extract_channel_data(channel):
    out = [
        channel["id"],
        int(channel["statistics"]["subscriberCount"]) if channel["statistics"]["hiddenSubscriberCount"] == False else "Hidden"
    ]
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
    

