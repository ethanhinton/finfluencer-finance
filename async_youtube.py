import asyncio
from exceptions import QuotaExceededError, APIError, CommentsDisabledError, check_keyerror_cause
from functions import extract_channel_data, extract_vid_data

class AsyncYoutube:
    
    def __init__(self, session, api_key):
        self.session = session
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"

    # Gets video and channel ids for a list of queries and video duration filters
    async def get_ids(self, queries, max_results=50, order="date", video_duration=["any"]):
        # Call API for multiple duration filters for each query in the query input list (returns a list of lists of video ids)
        tasks = [self.ids_multi_duration(query, max_results=max_results, order=order, durations=video_duration) for query in queries]
        responses = await asyncio.gather(*tasks)

        # Unpack lists and output two lists of video and channel ids for all videos in all queries 
        vid_ids = []
        channel_ids = []
        tickers = []

        for i, response in enumerate(responses):
            ticker = queries[i].split(" ")[0]
            tickers.extend([ticker]*len(response[0]))
            vid_ids.extend(response[0])
            channel_ids.extend(response[1])
        return vid_ids, channel_ids, tickers

    # Gets video and channel ids for a list of duration filters
    async def ids_multi_duration(self, query, max_results=50, order="date", durations=["short", "medium", "long"]):
        # Call API to search for query with each duration filter
        tasks = [self.session.get(f"{self.base_url}/search?part=snippet&maxResults={max_results}&q={query.replace(' ', '%20')}&type=video&order={order}&videoDuration={duration}&key={self.api_key}") for duration in durations]
    
        responses = await asyncio.gather(*tasks)
        results = [await response.json() for response in responses]

        # Cut out useless response metadata from json response leaving a list of lists of videos for each duration filter
        try:
            cut_down = list(map(lambda x: x["items"], results))
        except KeyError:
            check_keyerror_cause(results)

        # Create one long list of videos (reducing dimension of list of lists)
        videos = []
        for i in cut_down:
            videos.extend(i)
        
        # Extract the video/channel ID of each video in the list and return the list of id tuples
        vid_ids = list(map(lambda x : x["id"]["videoId"], videos))
        channel_ids = list(map(lambda x : x["snippet"]["channelId"], videos))
        return vid_ids, channel_ids

    # Gets top level comments for one video
    async def get_comments(self, vid_id):
        try:
            response = await self.session.get(f"{self.base_url}/commentThreads?part=snippet&maxResults=10000&videoId={vid_id}&key={self.api_key}")
        except Exception as e:
            return f"{e.status_code} :: {e.message}"
        
        response = await response.json()

        try:
            items = response["items"]
        except KeyError as e:
            try:
                check_keyerror_cause(response)
            except CommentsDisabledError:
                return []
            except QuotaExceededError:
                return ["Comments could not be retrieved: API Quota Exceeded"]

        return list(map(lambda x: x['snippet']['topLevelComment']['snippet']['textOriginal'], items))
    
    async def get_comments_multi_videos(self, vid_ids):
        tasks = [self.get_comments(vid_id) for vid_id in vid_ids]

        responses = await asyncio.gather(*tasks)

        return responses
    
    # Takes in a list of channel ids and outputs a list containing [channel id, number of subscribers] for each channel
    async def get_subscribers(self, channel_ids):
        # One API call can only process 50 channel IDs at a time, split the list of channel IDs into a list of lists w/ max length = 50 
        packets = [channel_ids[i:i+50] for i in range(0, len(channel_ids), 50)]

        # For each list of lists of channel ids, stitch the 50 channel ids together into one string with "&id=" between them. This string can be put into the request URL
        stitch = lambda x: "&id=".join(x)
        req_strings = list(map(stitch, packets))

        tasks = [self.session.get(f"{self.base_url}/channels?part=id&part=statistics&maxResults=50&id={ids}&key={self.api_key}") for ids in req_strings]

        responses = await asyncio.gather(*tasks)

        results = [await response.json() for response in responses]

        # Get rid of useless metadata about the API calls and add individual channel information to a list "items"
        items = []
        for result in results:
            try:
                items.extend(result["items"])
            except KeyError as e:
                check_keyerror_cause(result)

        # The API removes duplicate channel info outputs for duplicate channel ids in a single call, however this does not happen when the API is called multiple times
        # therefore we must remove duplicate channel data before we return it
        uniques = list(set(map(extract_channel_data, items)))

        # Data for each channel is in tuple form (so the unique filtering would work), change this back to list form for output
        return list(map(lambda x: list(x), uniques))


    async def get_video_data(self, vid_ids):
        # One API call can only process 50 video IDs at a time, split the list of video IDs into a list of lists w/ max length = 50 
        packets = [vid_ids[i:i+50] for i in range(0, len(vid_ids), 50)]

        # For each list of lists of video ids, stitch the 50 video ids together into one string with "&id=" between them. This string can be put into the request URL
        stitch = lambda x: "&id=".join(x)
        req_strings = list(map(stitch, packets))

        tasks = [self.session.get(f"{self.base_url}/videos?part=id&part=statistics&part=snippet&part=contentDetails&maxResults=50&id={ids}&key={self.api_key}") for ids in req_strings]

        responses = await asyncio.gather(*tasks)

        results = [await response.json() for response in responses]

        # Get rid of useless metadata about the API calls and add individual video information to a list "items"
        items = []
        for result in results:
            try:
                items.extend(result["items"])
            except KeyError as e:
                check_keyerror_cause(result)

        # Extract the data that we want from the set of all video data for each video and return as a list of lists of single video data
        return list(map(extract_vid_data, items))
