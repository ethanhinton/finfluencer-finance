from keys import *
from functions import *
from async_youtube2 import AsyncYoutube
import asyncio
import aiohttp
from sys import platform

# async def main():
#     TICKERS = ["AMZN", "GOOGL"]
#     queries = [ticker+" stock" for ticker in TICKERS]

#     # Retrieve video and channel IDs asynchronously for all tickers using 
#     async with aiohttp.ClientSession() as session:
#         api = AsyncYoutube(session, API_KEY)
#         vid_ids, channel_ids, tickers = await api.get_ids(queries, video_duration=["short", "medium", "long"])
#         comments = await api.get_comments_multi_videos(vid_ids)
#         vid_data = await api.get_video_data(vid_ids)
#         channel_data = await api.get_subscribers(channel_ids)

#     print("Fetching transcripts...")
#     transcript_data = list(map(get_transcript, vid_ids))

#     # Extract data, collect into a dataframe, and save to csv file
#     df = generate_dataframe(vid_data, comments, transcript_data, channel_data)

#     # Output to Excel
#     df.to_excel("output.xlsx", engine="xlsxwriter")


async def main():
    TICKERS = ["AMZN", "GOOGL"]
    queries = [ticker+" stock" for ticker in TICKERS]

    # Retrieve video and channel IDs asynchronously for all tickers using 
    async with aiohttp.ClientSession() as session:
        api = AsyncYoutube(session, API_KEY)

        print("Fetching video data...")
        vid_ids, channel_ids, vid_data, channel_data, comments, tickers = await get_output_all_queries(api, queries)

    # print("Fetching transcripts...")
    # transcript_data = list(map(get_transcript, vid_ids))

    print("Generating Spreadsheet...")
    # Extract data, collect into a dataframe, and save to csv file
    df = generate_dataframe(vid_data, comments, channel_data, tickers, transcript_data=False)

    # Output to Excel
    df.to_excel("output.xlsx", engine="xlsxwriter")

async def get_output_all_queries(api, queries):
    tasks = [asyncio.create_task(api.get_info_for_query(query)) for query in queries]

    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
    
    if pending:
        print(f"{len(pending)} results pending")

    for p in pending:
        p.cancel()

    v_ids = []
    c_ids = []
    vid_data = []
    channel_data = []
    comment_data = []
    tickers = []

    for d in done:
        try:
            vid_ids, channel_ids, ticker, vids, subs, comments = d.result()
            v_ids.extend(vid_ids)
            c_ids.extend(channel_ids) 
            vid_data.extend(vids)
            channel_data.extend(subs)
            comment_data.extend(comments)
            tickers.extend(ticker)
        except Exception as e:
            print(f"Error retrieving data for query {e}")

    return v_ids, c_ids, vid_data, channel_data, comment_data, tickers

if __name__ == '__main__':
    if platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
