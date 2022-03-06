import asyncio
import aiohttp
from keys import API_KEY

class AsyncYoutube:
    
    def __init__(self, session, api_key):
        self.session = session
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"

    async def get_vid_ids(self, queries, max_results=50, order="date", video_duration=["any"]):
        # Call API for multiple duration filters for each query in the query input list (returns a list of lists of video ids)
        tasks = [self.vid_ids_multi_duration(query, max_results=max_results, order=order, durations=video_duration) for query in queries]
        responses = await asyncio.gather(*tasks)

        # Unpack lists and output one single list of video ids for all videos in all queries 
        out = []
        for response in responses:
            out.extend(response)
        return out
        

    async def vid_ids_multi_duration(self, query, max_results=50, order="date", durations=["short", "medium", "long"]):
        # Call API to search for query with each duration filter
        tasks = [self.session.get(f"{self.base_url}/search?part=snippet&maxResults={max_results}&q={query.replace(' ', '%20')}&type=video&order={order}&videoDuration={duration}&key={self.api_key}") for duration in durations]
        responses = await asyncio.gather(*tasks)
        results = [await response.json() for response in responses]

        # Cut out useless response metadata from json response leaving a list of lists of videos for each duration filter
        cut_down = list(map(lambda x: x["items"], results))

        # Create one long list of videos (reducing dimension of list of lists)
        videos = []
        for i in cut_down:
            videos.extend(i)
        
        # Extract the video ID of each video in the list and return the list of ids
        vid_ids = list(map(lambda x : x["id"]["videoId"], videos))
        return vid_ids

    async def get_comments(self, vid_ids):
        # tasks = [self.session.get(f"{self.base_url}/search?part=snippet&maxResults={max_results}&q={query.replace(' ', '%20')}&type=video&order={order}&videoDuration={video_duration}&key={self.api_key}") for query in queries]
        # responses = await asyncio.gather(*tasks)
        # results = [await response.json() for response in responses]
        # return results
        pass

async def main():
    async with aiohttp.ClientSession() as session:
        api = AsyncYoutube(session, API_KEY)
        tickers = ["AMZN", "GOOGL"]
        queries = [ticker+" stock" for ticker in tickers]
        output = await api.get_vid_ids(queries, video_duration=["short", "medium", "long"])
        print(output)

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())

    