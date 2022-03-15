from keys import *
from functions import *
from async_youtube import AsyncYoutube
import asyncio
import aiohttp
from sys import platform

async def main():
    TICKERS = ["AMZN", "GOOGL"]
    queries = [ticker+" stock" for ticker in TICKERS]

    # Retrieve video and channel IDs asynchronously for all tickers using 
    async with aiohttp.ClientSession() as session:
        api = AsyncYoutube(session, API_KEY)
        vid_ids, channel_ids, tickers = await api.get_ids(queries, video_duration=["short", "medium", "long"])
        comments = await api.get_comments_multi_videos(vid_ids)
        vid_data = await api.get_video_data(vid_ids)
        channel_data = await api.get_subscribers(channel_ids)

    print("Fetching transcripts...")
    transcript_data = list(map(get_transcript, vid_ids))

    # Extract data, collect into a dataframe, and save to csv file
    df = generate_dataframe(vid_data, comments, transcript_data, channel_data)

    # Output to Excel
    df.to_excel("output.xlsx", engine="xlsxwriter")

if __name__ == '__main__':
    if platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
