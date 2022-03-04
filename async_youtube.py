import asyncio
import aiohttp
from keys import API_KEY

class AsyncYoutube:
    
    def __init__(self, session, api_key):
        self.session = session
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"

    async def search(self, queries, max_results=50, order="date", video_duration=["any"]):
        tasks = [self.search_multi_duration(query, max_results=max_results, order=order, durations=video_duration) for query in queries]
        responses = await asyncio.gather(*tasks)
        # out = []
        # for response in responses:
        #     out.extend(response)
        # return out
        return responses

    async def search_multi_duration(self, query, max_results=50, order="date", durations=["short", "medium", "long"]):
        tasks = [self.session.get(f"{self.base_url}/search?part=snippet&maxResults={max_results}&q={query.replace(' ', '%20')}&type=video&order={order}&videoDuration={duration}&key={self.api_key}") for duration in durations]
        responses = await asyncio.gather(*tasks)
        results = [await response.json() for response in responses]
        out = list(map(lambda x: x["items"], results))
        return out

    async def get_comments(self, vid_ids):
        # tasks = [self.session.get(f"{self.base_url}/search?part=snippet&maxResults={max_results}&q={query.replace(' ', '%20')}&type=video&order={order}&videoDuration={video_duration}&key={self.api_key}") for query in queries]
        # responses = await asyncio.gather(*tasks)
        # results = [await response.json() for response in responses]
        # return results
        pass

async def main():
    async with aiohttp.ClientSession() as session:
        api = AsyncYoutube(session, API_KEY)
        tickers = ["AMZN", "GOOGL", "AAPL", "MSFT"]
        queries = [ticker+" stock" for ticker in tickers]
        output = await api.search(queries, video_duration=["short", "medium", "long"])
        print(len(output))

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())

    