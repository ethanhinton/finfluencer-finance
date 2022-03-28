from keys import *
from functions import *
# from async_youtube import AsyncYoutube
from async_youtube2 import AsyncYoutube
import asyncio
import aiohttp
from sys import platform
from datetime import datetime, timedelta
import os


async def main():
    # Grabs list of S&P500 tickers from wikipedia
    TICKERS = sp500_tickers()

    # Checks if an excel file already exists, if so, check which stocks have already been done, and remove these from the ticker list
    if check_for_data("output.xlsx"):
        existing_data = pd.read_excel("output.xlsx")
        known_tickers = existing_data["Stock"].unique()
        TICKERS = list(set(TICKERS) - set(known_tickers))
    else:
        existing_data = False
        try:
            os.remove("settings.txt")
        except Exception as e:
            print(e)

    # Grab settings that determine how many videos are collected per stock (and whether or not comments are fetched), also grabs the API quota and date and time of program run.
    reduce_quota_option, run_time, api_quota = get_settings(TICKERS)

    # Write the settings to settings file
    with open("settings.txt", "w") as f:
        f.write(str(reduce_quota_option))
        f.write("\n")
        f.write(run_time)
        f.write("\n")
        f.write(str(api_quota))

    # Based on the api quota and the settings the user has chosen, calculate the number of stocks that can be retrieved in one run of the program
    # Shorten the ticker list to contain only that number of stocks
    number_stocks = calculate_number_stocks(reduce_quota_option, api_quota)
    TICKERS = TICKERS[:number_stocks]

    # Ask user if they would like transcripts to be collected for videos or not
    while True:
        transcripts = input("Fetch transcripts for all compatible videos? (NOTE: This will increase computation time significantly) (y/n) : ").lower()
        if transcripts in ["y", "n"]:
            break
        else:
            print("INVALID INPUT : Enter 'y' for yes or 'n' for no\n")
    
    # Create the queries
    queries = [ticker+" stock" for ticker in TICKERS]

    # Set up async session object
    async with aiohttp.ClientSession() as session:
        api = AsyncYoutube(session, API_KEY)

        if reduce_quota_option in [1, 3]:
            include_comments = True
        else:
            include_comments = False
        
        if reduce_quota_option in [1, 2]:
            video_duration = ["short", "medium", "long"]
        else:
            video_duration = ["any"]

        print(f"Fetching video data for {len(TICKERS)} companies...")
        # vid_ids, channel_ids, vid_data, channel_data, comments, tickers = await api.get_output_all_queries(queries, include_comments=include_comments, video_duration=video_duration)
        vid_ids, channel_ids, tickers = api.get_ids(queries, video_duration=video_duration)
        vid_data = api.get_video_data(vid_ids)
        channel_data = api.get_subscribers(channel_ids)
        if include_comments:
            comments = api.get_comments_multi_videos(vid_ids)

    if transcripts == "y":
        print("Fetching transcripts...")
        number = [x+1 for x in range(len(vid_ids))]
        number_vids = [len(number) for x in range(len(number))]
        transcript_data = list(map(get_transcript, vid_ids, number, number_vids))
    else:
        transcript_data = False

    print("Generating Spreadsheet...")
    # Extract data, collect into a dataframe, and save to csv file
    df = generate_dataframe(vid_data, comments, channel_data, tickers, transcript_data=transcript_data, existing_data=existing_data)

    # Output to Excel
    df.to_excel("output.xlsx", engine="xlsxwriter")


if __name__ == '__main__':
    if platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
