from youtube_transcript_api import YouTubeTranscriptApi as trans
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from googleapiclient.errors import HttpError


def extract_vid_data(video):
    out = [
        video["id"],
        video["snippet"]["title"],
        video["snippet"]["description"],
        (video["snippet"]["tags"] if "tags" in video["snippet"].keys() else ""),
        video["snippet"]["publishedAt"],
        video["snippet"]["thumbnails"]["high"]["url"],
        video["contentDetails"]["duration"],
        video["statistics"]["viewCount"],
        (video["statistics"]["likeCount"] if "likeCount" in video["statistics"].keys() else ""),
        video["statistics"]["commentCount"],
        video["snippet"]["channelTitle"],
        # channel["statistics"]["subscriberCount"]
    ]
    return out

def get_transcript(video_id):
    print(f"Fetching transcript for {video_id}...")
    try:
        transcript = trans.list_transcripts(video_id).find_transcript(language_codes=["en"]).fetch()
        transcript_text = " ".join(list(map(lambda x: x["text"], transcript)))
        print("Done")
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
