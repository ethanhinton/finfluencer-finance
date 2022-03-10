import asyncio
import aiohttp
from keys import API_KEY
from exceptions import QuotaExceededError, APIError

class AsyncYoutube:
    
    def __init__(self, session, api_key):
        self.session = session
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"

    # Gets video ids for a list of queries and video duration filters
    async def get_vid_ids(self, queries, max_results=50, order="date", video_duration=["any"]):
        # Call API for multiple duration filters for each query in the query input list (returns a list of lists of video ids)
        tasks = [self.vid_ids_multi_duration(query, max_results=max_results, order=order, durations=video_duration) for query in queries]
        responses = await asyncio.gather(*tasks)

        # Unpack lists and output one single list of video ids for all videos in all queries 
        out = []
        for response in responses:
            out.extend(response)
        return out

    # Gets video ids for a list of duration filters
    async def vid_ids_multi_duration(self, query, max_results=50, order="date", durations=["short", "medium", "long"]):
        # Call API to search for query with each duration filter
        tasks = [self.session.get(f"{self.base_url}/search?part=snippet&maxResults={max_results}&q={query.replace(' ', '%20')}&type=video&order={order}&videoDuration={duration}&key={self.api_key}") for duration in durations]
        

        responses = await asyncio.gather(*tasks)
        results = [await response.json() for response in responses]

        # Cut out useless response metadata from json response leaving a list of lists of videos for each duration filter
        try:
            cut_down = list(map(lambda x: x["items"], results))
        except KeyError:
            try:
                if "error" in results[0].keys():
                    reason = results[0]["error"]["errors"][0]["reason"]
                    if reason == "quotaExceeded":
                        raise QuotaExceededError
                    else:
                        raise APIError(reason)
            except QuotaExceededError:
                print("Daily API quota exceeded, wait 24 hours for the quota to replenish")
                quit()
            except APIError:
                print("There was an error with the YouTube Data API")
                quit()
        

        # Create one long list of videos (reducing dimension of list of lists)
        videos = []
        for i in cut_down:
            videos.extend(i)
        
        # Extract the video ID of each video in the list and return the list of ids
        vid_ids = list(map(lambda x : x["id"]["videoId"], videos))
        return vid_ids

    # Gets top level comments for one video --FINISH--
    async def get_comments(self, vid_id):
        try:
            response = await self.session.get(f"{self.base_url}/commentThreads?part=snippet&maxResults=10000&videoId={vid_id}&key={self.api_key}")
        except Exception as e:
            return f"{e.status_code} :: {e.message}"
        
        response = await response.json()

        items = response["items"]

        return list(map(lambda x: x['snippet']['topLevelComment']['snippet']['textOriginal'], items))

async def main():
    async with aiohttp.ClientSession() as session:
        api = AsyncYoutube(session, API_KEY)
        tickers = ["GOOGL"]
        queries = [ticker+" stock" for ticker in tickers]
        vid_ids = await api.get_vid_ids(queries, video_duration=["short", "medium", "long"])

        for vid_id in vid_ids:
            comments = await api.get_comments(vid_id)
            print(comments)
        
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())

    