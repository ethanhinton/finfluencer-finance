from keys import *
from functions import *
from async_youtube import AsyncYoutube
import asyncio
import aiohttp
from sys import platform


async def main():
    # Grabs list of S&P500 tickers from wikipedia
    # TICKERS = sp500_tickers()[:2]
    TICKERS = ["AMZN", "GOOGL", "AAPL"]

    while True:
        transcripts = input("Fetch transcripts for all compatible videos? (NOTE: This will increase computation time significantly) (y/n) : ").lower()
        if transcripts in ["y", "n"]:
            break
        else:
            print("INVALID INPUT : Enter 'y' for yes or 'n' for no\n")

    # Checks if an excel file already exists, if so, check which stocks have already been done, and remove these from the ticker list
    if check_for_data("output.xlsx"):
        existing_data = pd.read_excel("output.xlsx")
        known_tickers = existing_data["Stock"].unique()
        TICKERS = list(set(TICKERS) - set(known_tickers))
    else:
        existing_data = False
    

    # Create the queries
    queries = [ticker+" stock" for ticker in TICKERS]

    # Retrieve video and channel IDs asynchronously for all tickers using 
    async with aiohttp.ClientSession() as session:
        api = AsyncYoutube(session, API_KEY)

        print(f"Fetching video data for {len(TICKERS)} companies...")
        vid_ids, channel_ids, vid_data, channel_data, comments, tickers = await get_output_all_queries(api, queries)

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

async def get_output_all_queries(api, queries):
    tasks = [asyncio.create_task(api.get_info_for_query(query)) for query in queries]

    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
    
    if pending:
        print(f"Number of queries retrieved : {len(done) - 1}")

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
