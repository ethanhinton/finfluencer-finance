# Documentation

This document will detail each file included in the project and the functions/classes/logic inside.

## async_youtube.py

This file contains the AsyncYoutube class which is used to make calls to the YouTube data API asynchronously. This speeds up the retrieval of data from the API significantly as API calls are processed simultaneously. NOTE: Search requests that retrieve video/channel ids etc. are not performed asynchronously due to needing to utilise multiple API keys as a workaround for the lack of available API quota.

### AsyncYoutube (*Class*)
Used to make YouTube Data API calls asynchronously.


**self.session** (*Attribute*)
Stores the HTTP session object from the aiohttp module.


**self.api_key** (*Attribute*)
Stores the YouTube Data API key.


**self.base_url** (*Attribute*)
Stores the base URL for YouTube Data API calls.


**get_ids** (*Method*) (**Args**: queries(*list*), max_results(*int*, default=50), order(*str*, options="relevance", "date", default="date"), video_duration(*list*, default=["any"])) (Quota Cost = 100 per query and video duration) (REDUNDANT)
Method to call a search query for multiple queries. Returns a list of video/channel ids and a list of tickers.


**ids_multi_duration** (*Method*) (**Args**: query(*str*), max_results(*int*, default=50), order(*str*, options="relevance", "date", default="date"), video_duration(*list*, default=["short", "medium", "long"])) (REDUNDANT)
Method to call a search query for multiple durations. Returns a list of video/channel ids and a list of tickers. Called by get_ids method.


**get_comments** (*Method*) (**Args**: vid_id(*str*)) (Quota Cost = 1 per video)
Method to get all comments for a single YouTube video.


**get_comments_multi_videos** (*Method*) (**Args**: vid_ids(*list*))
Calls get_comments for a list of multiple video ids.


**get_subscribers** (*Method*) (**Args**: channel_ids(*list*)) (Quota Cost = 1 per 50 channels)
Retrieves the number of subscribers for each channel in a list of channel ids. Raw API repsonse is cleaned using extract_channel_data function from functions.py and returned.


**get_vid_data** (*Method*) (**Args**: vid_ids(*list*)) (Quota Cost = 1 per 50 videos)
Retrieves data from the YouTube Data API about each video in a list of video ids. Raw API response is cleaned using the extract_vid_data function from functions.py and returned.


## functions.py

This file stores all functions that are used in the main program and in other modules.

### format_duration (*Function*) (Args: duration(*str*))
Changes the format the video duration metric returned by the YouTube Data API for a video from PTxMxS to the more standard HH:MM:SS.

### extract_vid_data (*Function*) (Args: video(*api_response["item"]*))
Function to reformat output from API response into list of desired metrics. Input is the output from the video API call indexed with the ["item"] key.

### extract_channel_data (*Function*) (Args: channel(*api_response["item"]*))
Function to reformat output from API response into list of desired metrics. Input is the output from the channel API call indexed with the ["item"] key.


