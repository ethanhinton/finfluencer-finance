from msilib.schema import InstallUISequence
from keys import *
from functions import *
from async_youtube import AsyncYoutube
import asyncio
import aiohttp
from sys import platform
import os
import pandas as pd
from googleapiclient.discovery import build

async def main():

    api_quota = 10000
    include_comments = False
    transcripts = False

    # Open Excel file with instructions for searches
    excel_sheet = pd.read_excel("stocks_and_dates.xlsx", index_col="ID")
    instructions = excel_sheet[excel_sheet["Done?"] != "Yes"]
    TICKERS = list(map(lambda x: x.upper(), instructions.Stock))
    dates = [earnings_announcement_period(x) for x in instructions["EA Date"]]
    ids = list(instructions.index)

    # Checks if an output excel file already exists, if not, remove the settings.txt file as settings need to be re entered
    if check_for_data("output.xlsx"):
        print("Existing Data Found")
        existing_data = pd.read_excel("output.xlsx")
    else:
        existing_data = False
        try:
            os.remove("settings.txt")
        except Exception as e:
            print(e)

    # Fetch the date + time of last run of the program (if program run in last 24 hours, there could be errors due to API quota breaches)
    run_time = get_run_time()

    # Write the settings to settings file
    with open("settings.txt", "w") as f:
        f.write(run_time)
    
    # Based on the api quota and the settings the user has chosen, calculate the number of stocks that can be retrieved in one run of the program
    # Shorten the ticker list to contain only that number of stocks
    number_stocks = calculate_number_stocks(api_quota)
    TICKERS = TICKERS[:number_stocks]

    # Create the queries
    queries = [ticker+" stock" for ticker in TICKERS]
    print(TICKERS)

    # Get video, channel ids from search queries
    # Each query retrieves a specified number of pages of search results (each page is 50 videos)
    # IDEA: You know when to be careful with searches when you get to the last API key.
    # Count the number of searches done (perhaps using 2 lists with pop()?) and when on last API key, use only for video and channel queries as these are guaranteed to be below quota
    with build("youtube", "v3", developerKey=API_KEY) as service:
        print("Fetching Search Results...")
        vid_ids = []
        channel_ids = []
        tickers = []
        ids_done = []
        for i, query in enumerate(queries):
            print(query)
            print(type(dates[i][0]))
            v, c, t = search_videos(service, query, date_to_RFC(dates[i][0]), date_to_RFC(dates[i][1]), order="date", pages=4)
            vid_ids.extend(v)
            channel_ids.extend(c)
            tickers.extend(t)
            # Add id to ids_done list to determine which queries have been completed
            ids_done.append(ids[i])

    # Set up async session object
    async with aiohttp.ClientSession() as session:
        api = AsyncYoutube(session, API_KEY)

        print(f"Fetching video data for {len(vid_ids)} videos...")
        vid_data = await api.get_video_data(vid_ids)
        channel_data = await api.get_subscribers(channel_ids)

        comments = False
        if include_comments:
            comments = await api.get_comments_multi_videos(vid_ids)

    if transcripts:
        print("Fetching transcripts...")
        number = [x+1 for x in range(len(vid_ids))]
        number_vids = [len(number) for x in range(len(number))]
        transcript_data = list(map(get_transcript, vid_ids, number, number_vids))
    else:
        transcript_data = False

    # Change "Done?" column to "Yes" for queries that have been completed
    excel_sheet.loc[ids_done, "Done?"] = "Yes"
    excel_sheet.to_excel("stocks_and_dates.xlsx")

    print("Generating Spreadsheet...")
    # Extract data, collect into a dataframe, and save to csv file
    df = generate_dataframe(vid_data, comments, channel_data, tickers, transcript_data=transcript_data, existing_data=existing_data)

    # Output to Excel
    df.to_excel("output.xlsx", engine="xlsxwriter")


if __name__ == '__main__':
    if platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
