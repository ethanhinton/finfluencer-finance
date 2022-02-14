from youtube_transcript_api import YouTubeTranscriptApi as trans

def extract_vid_data(video):
    out = [
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
    transcript = trans.list_transcripts(video_id).find_transcript(language_codes=["en"]).fetch()

    transcript_text = " ".join(list(map(lambda x: x["text"], transcript)))

    return transcript_text
