from youtube_transcript_api import YouTubeTranscriptApi as trans
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
import pandas as pd
import bs4 as bs
import requests
import os
from datetime import datetime, timedelta
import re
from exceptions import check_keyerror_cause, QuotaExceededError
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

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

def check_multi_tickers(df, filename="all_tickers.csv"):
    tickers = pd.read_csv(filename)
    tickers = list(tickers.iloc[:,0])

    titles = list(df.Title)

    number_stocks = []
    stocks_in_title = []

    for title in titles:
        n = 0
        s = []
        words = re.split(r",|!|\$| |\||\.|\?|\:|\(|\)|/|#", title)
        for word in words:
            if word.upper() in tickers:
                n += 1
                s.append(word.upper())
        number_stocks.append(n)
        stocks_in_title.append(s)

    return number_stocks, stocks_in_title

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

    number_stocks, stocks_in_title = check_multi_tickers(df)
    df["Number of Stocks in Title"] = number_stocks
    df["Stocks in Title"] = stocks_in_title

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
def get_run_time():
    try:
        with open("settings.txt", "r") as f:
            settings = f.readlines()
            last_run_time = datetime.strptime(settings[0], '%d/%m/%y %H:%M:%S')
        
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
    except FileNotFoundError:
        print("No previous run time available. Assuming full API quota.")

    run_time = datetime.now().strftime('%d/%m/%y %H:%M:%S')
    
    return run_time

def calculate_number_stocks(api_quota):
    cost_per_stock = 102
    return int(api_quota // cost_per_stock)

def date_to_RFC(date):
    return date.isoformat("T") + "Z"

def paginated_results(search_obj, request, limit_requests=4):
    remaining = -1 if limit_requests is None else limit_requests

    while request and remaining != 0:
        response = request.execute()
        yield response
        request = search_obj.list_next(request, response)
        remaining -= 1


def search_request(service, query, start_date, end_date, order, pages, max_results=50):
    print(start_date, end_date)
    search = service.search()
    search_request = search.list(
        part="snippet",
        q=query,
        publishedAfter=start_date,
        publishedBefore=end_date,
        order=order,
        maxResults=max_results
    )

    responses = paginated_results(search, search_request, limit_requests=pages)

    videos = []
    for response in responses:
        videos.extend(response["items"])

    vid_ids = list(map(lambda x : x["id"]["videoId"], videos))
    channel_ids = list(map(lambda x : x["snippet"]["channelId"], videos))
    tickers = [query.split(" ")[0]] * len(vid_ids)

    return vid_ids, channel_ids, tickers

# Returns a start date and end date a specified number of days around an earnings announcement date
def earnings_announcement_period(ea_date, width=10):
    end_date = ea_date + timedelta(days=width)
    start_date = ea_date - timedelta(days=width)

    return start_date, end_date

def search_queries(API_KEYS, queries, dates, ids, pages_per_query):
    # Set empty lists to be filled in following loop
    vid_ids = []
    channel_ids = []
    tickers = []
    ids_done = []

    
    # Loop through API keys allocated to search requests
    for i, API_KEY in enumerate(API_KEYS):
        print(f"API Key {i+1} of {len(API_KEYS)}")
        try:
            # Build the YouTube API search object (this must be done each time there is a new API key used)
            with build("youtube", "v3", developerKey=API_KEY) as service:
                print("Fetching Search Results...")
                # Loop through queries
                for i, query in enumerate(queries):
                    print(query)
                    print(ids[i])
                    print(type(dates[i][0]))
                    try:
                        # Fetch video + channel IDs and the ticker of the stock in question
                        v, c, t = search_request(service, query, date_to_RFC(dates[i][0]), date_to_RFC(dates[i][1]), order="date", pages=pages_per_query)
                    # Catches instances where API quota has been exceeded, saves the index of the query currently being processed
                    # Stores this so query can be processed using the next API key
                    except HttpError as e:
                        if repr(e)[-18:-5] == "quotaExceeded":
                            print("API Quota Exceeded! Trying a different API Key...")
                            query_index = i
                            raise QuotaExceededError
                    # If no error occurs, add video/channel ids and tickers to relevant lists
                    else:
                        vid_ids.extend(v)
                        channel_ids.extend(c)
                        tickers.extend(t)
                        # Add id to ids_done list to determine which queries have been completed
                        ids_done.append(ids[i])
                # If we get to this point in the loop with no quota-related errors, all queries must have been processed, so break from outer loop
                print("Queries complete! Breaking from loop...")
                break
        except QuotaExceededError:
            queries = queries[query_index:]
    
    return vid_ids, channel_ids, tickers, ids_done