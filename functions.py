from youtube_transcript_api import YouTubeTranscriptApi as trans
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
import pandas as pd
import bs4 as bs
import requests
import os
from datetime import datetime, timedelta

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

def get_transcript(video_id, index, number_of_videos):
    try:
        print(f"Fetching transcript for video : {index}/{number_of_videos}")
        transcript = trans.list_transcripts(video_id).find_transcript(language_codes=["en"]).fetch()
        transcript_text = " ".join(list(map(lambda x: x["text"], transcript)))
    except (NoTranscriptFound, TranscriptsDisabled):
        return "No transcript"
    return transcript_text

    
def generate_dataframe(vid_data, comments_data, channel_data, tickers, transcript_data=None, index="VideoID", existing_data=False):
    # Extract data, collect into a dataframe, and save to csv file
    headers = ["VideoID", "Title", "Description", "Tags", "Publish Date", "Thumbnail", "Duration", "Views", "Likes", "Number of Comments", "Channel Name", "Channel ID"]
    df = pd.DataFrame(data=vid_data, columns=headers)
    df["Stock"] = tickers

    # If comment retrieval is turned off, the comments data list will be empty, so don't add it to the dataframe
    if comments_data:
        df["Comments"] = comments_data

    if transcript_data != False:
        df["Transcript"] = transcript_data

    # Extract channel data into a separate dataframe and join with main dataframe by channel ID (this is so each of multiple videos from the same channel have subscriber count in the output file)
    headers = ["Channel ID", "Subscriber Count"]
    channel_df = pd.DataFrame(data=channel_data, columns=headers)
    channel_df.set_index("Channel ID", inplace=True)

    df = df.join(channel_df, on="Channel ID").drop_duplicates(subset=[index])

    if type(existing_data) != bool:
        df = pd.concat([df, existing_data]).drop_duplicates(subset=[index])

    return df.set_index(index)


def sp500_tickers():
    resp = requests.get('http://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    soup = bs.BeautifulSoup(resp.text, 'lxml')
    table = soup.find('table', {'class': 'wikitable sortable'})
    tickers = []
    for row in table.findAll('tr')[1:]:
        ticker = row.findAll('td')[0].text
        tickers.append(ticker)
    
    tickers = list(map(lambda x: x[:-1], tickers))
    
    return tickers

def check_for_data(filename):
    if os.path.exists(filename):
        return True
    return False

# If there is a settings file (containing information about how many videos to grab for each stock / whether to grab comments or not), open the file.
# If it has not been > 1 day since the program was last run, display a warning as it is unlikely the API quota will not have refreshed.
# If there is no settings file, the user must select how many videos to grab for each stock / whether to grab comments or not, based on how much quota they want to use.
def get_settings(TICKERS):
    try:
        with open("settings.txt", "r") as f:
            settings = f.readlines()
            reduce_quota_option = int(settings[0])
            last_run_time = datetime.strptime(settings[1], '%d/%m/%y %H:%M:%S')
            api_quota = int(settings[2])
        
            if datetime.now() - timedelta(days=1) < last_run_time:
                print(f"""
                --------------------------------------------------------------------------------------------------------------------------------------------------------------------
                WARNING! This program was last run less than 24 hours ago (at {last_run_time.strftime('%d/%m/%y %H:%M:%S')}).

                It is likely that the API quota will be exceeded the program is run again within 24 hours, no extra data will be collected if the quota is exceeded.
                
                The API quota will be refreshed at {(last_run_time + timedelta(days=1)).strftime('%d/%m/%y %H:%M:%S')}, it is recommended that this program is run after this time.
                --------------------------------------------------------------------------------------------------------------------------------------------------------------------

                """)
                while True:
                    con = input("Would you like to continue? (y/n) : ").lower()
                    if con in ["y", "n"]:
                        if con == "n":
                            quit()
                        else:
                            break
                    else:
                        print("INVALID INPUT : Enter 'y' for yes or 'n' for no\n")
    except Exception:
        while True:
            try:
                api_quota = int(input("Enter the API quota allowance associated with the API key (default = 10,000) : "))
                if api_quota < 10000:
                    api_quota = 10000
                break
            except Exception:
                print("INVALID INPUT : Enter a number between 1 and 4.\n")
        
        if api_quota < 230000:
            print(f"""
            If your YouTube Data API key has a quota limit < 230,000, this program will need to be run over multiple days (if not, press option 1).

            Assuming the default quota limit of 10,000, to run the full program (fetching 150 of the latest videos on each stock and fetching comments for all of the videos)
            the program will need to be run each day for 23 days.

            To reduce the quota cost of running the program, you can reduce the data that the program collects, 4 options are detailed below:
            
            1. The required quota to fetch 150 videos for each remaining stock (with comments) is {456 * len(TICKERS)} ({(456 * len(TICKERS) // 10000) + 1} days of daily program running, assuming default API quota).
            2. The required quota to fetch 150 videos for each remaining stock (without comments) is {306 * len(TICKERS)} ({(306 * len(TICKERS) // 10000) + 1} days of daily program running, assuming default API quota).
            3. The required quota to fetch 50 videos for each remaining stock (with comments) is {152 * len(TICKERS)} ({(152 * len(TICKERS) // 10000) + 1} days of daily program running, assuming default API quota).
            4. The required quota to fetch 50 videos for each remaining stock (without comments) is {102 * len(TICKERS)} ({(102 * len(TICKERS) // 10000) + 1} days of daily program running, assuming default API quota).

            """)
            while True:
                try:
                    reduce_quota_option = int(input("Choose one of the options above (enter number between 1 and 4) : "))
                    if reduce_quota_option in [1, 2, 3, 4]:
                        break
                except Exception:
                    print("INVALID INPUT : Enter a number between 1 and 4.\n")
        else:
            reduce_quota_option = 1
        
        run_time = datetime.now().strftime('%d/%m/%y %H:%M:%S')
    
    return reduce_quota_option, run_time, api_quota

