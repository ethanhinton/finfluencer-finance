from exceptions import QuotaExceededError
from keys import API_KEYS
from functions import *
from async_youtube import AsyncYoutube
import asyncio
import aiohttp
from sys import platform
import os
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

async def main():

    include_comments = False
    transcripts = False
    pages_per_query = 4
    input_filename = "stocks_and_dates.xlsx"
    output_filename = "output.xlsx"

    # Open Excel file with instructions for searches
    excel_sheet = pd.read_excel(input_filename, index_col="ID")
    instructions = excel_sheet[excel_sheet["Done?"] != "Yes"]
    TICKERS = list(map(lambda x: x.upper(), instructions.Stock))
    dates = [earnings_announcement_period(x) for x in instructions["EA Date"]]
    ids = list(instructions.index)

    # Checks if an output excel file already exists, if not, remove the settings.txt file as settings need to be re entered
    if check_for_data(output_filename):
        print("Existing Data Found")
        existing_data = pd.read_excel(output_filename)
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
    # number_stocks = calculate_number_stocks(api_quota)

    # Create the queries
    queries = [ticker+" stock" for ticker in TICKERS]

    # If fetching comments is enabled, significantly more API quota needs to be allocated to fetching these comments
    # 5 API keys are allocated to fetching video data in this case, as opposed to 1 key in the case where comments are not collected
    if include_comments:
        VID_DATA_API_KEYS = [API_KEYS.pop() for i in range(5)]
    else:
        VID_DATA_API_KEYS = API_KEYS.pop()

    # Fetch video/channel ids, tickers, and ids of queries that have been processed
    vid_ids, channel_ids, tickers, ids_done = search_queries(API_KEYS, queries, dates, ids, pages_per_query)

    # Set up async session object
    async with aiohttp.ClientSession() as session:
        print(VID_DATA_API_KEYS)
        api = AsyncYoutube(session, VID_DATA_API_KEYS.pop())
        print(VID_DATA_API_KEYS)
        print(f"Fetching video data for {len(vid_ids)} videos...")
        vid_data = await api.get_video_data(vid_ids)
        channel_data = await api.get_subscribers(channel_ids)

        comments = False
        if include_comments:
            comments = []
            segment_lengths = len(vid_ids) // len(VID_DATA_API_KEYS)
            vid_ids_for_comments = [vid_ids[i*segment_lengths:(i+1)*segment_lengths] if i+1 != len(VID_DATA_API_KEYS) else vid_ids[i*segment_lengths:] for i in range(len(VID_DATA_API_KEYS))]
            print(list(map(len, vid_ids_for_comments)))
            for i, API_KEY in enumerate(VID_DATA_API_KEYS):
                vid_ids_segement = vid_ids_for_comments[i]
                api = AsyncYoutube(session, API_KEY)
                comments.extend(await api.get_comments_multi_videos(vid_ids_segement))

    if transcripts:
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
    df.to_excel(output_filename, engine="xlsxwriter")

    # Change "Done?" column to "Yes" for queries that have been completed
    excel_sheet.loc[ids_done, "Done?"] = "Yes"
    excel_sheet.to_excel(input_filename)


if __name__ == '__main__':
    if platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
