import asyncio

from pandas import reset_option
import aiohttp
from keys import API_KEY

class AsyncYoutube:
    
    def __init__(self, session, api_key):
        self.session = session
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"

    async def search(self, queries, max_results=50, order="date", video_duration="any"):
        tasks = [self.session.get(f"{self.base_url}/search?part=snippet&maxResults={max_results}&q={query.replace(' ', '%20')}&type=video&order={order}&videoDuration={video_duration}&key={self.api_key}") for query in queries]
        responses = await asyncio.gather(*tasks)
        results = [await response.json() for response in responses]
        return results

    async def get_comments(self, vid_ids):
        pass

async def main():
    async with aiohttp.ClientSession() as session:
        api = AsyncYoutube(session, API_KEY)
        tickers = ["AMZN", "GOOGL", "AAPL"]
        queries = [ticker+" stock" for ticker in tickers]
        print(await api.search(queries))


asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())

    