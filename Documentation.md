# Documentation

This document will detail each file included in the project and the functions/classes/logic inside.

## async_youtube.py

This file contains the AsyncYoutube class which is used to make calls to the YouTube data API asynchronously. This speeds up the retrieval of data from the API significantly as API calls are processed simultaneously. NOTE: Search requests that retrieve video/channel ids etc. are not performed asynchronously due to needing to utilise multiple API keys as a workaround for the lack of available API quota.

### AsyncYoutube (*Class*)
Used to make YouTube Data API calls asynchronously.


#### self.session (*Attribute*)
Stores the HTTP session object from the aiohttp module.


#### self.api_key (*Attribute*)
Stores the YouTube Data API key.


#### self.base_url (*Attribute*)
Stores the base URL for YouTube Data API calls.


#### get_ids (*Method*) (**Args**: queries(*list*), max_results(*int*, default=50), order(*str*, options="relevance", "date", default="date"), video_duration(*list*, default=["any"])) (Quota Cost = 100 per query and video duration) (REDUNDANT)
Method to call a search query for multiple queries. Returns a list of video/channel ids and a list of tickers.


#### ids_multi_duration (*Method*) (**Args**: query(*str*), max_results(*int*, default=50), order(*str*, options="relevance", "date", default="date"), video_duration(*list*, default=["short", "medium", "long"])) (REDUNDANT)
Method to call a search query for multiple durations. Returns a list of video/channel ids and a list of tickers. Called by get_ids method.


#### get_comments(*Method*) (**Args**: vid_id(*str*)) (Quota Cost = 1 per video)
Method to get all comments for a single YouTube video.


#### get_comments_multi_videos (*Method*) (**Args**: vid_ids(*list*))
Calls get_comments for a list of multiple video ids.


#### get_subscribers (*Method*) (**Args**: channel_ids(*list*)) (Quota Cost = 1 per 50 channels)
Retrieves the number of subscribers for each channel in a list of channel ids. Raw API repsonse is cleaned using extract_channel_data function from functions.py and returned.


#### get_vid_data (*Method*) (**Args**: vid_ids(*list*)) (Quota Cost = 1 per 50 videos)
Retrieves data from the YouTube Data API about each video in a list of video ids. Raw API response is cleaned using the extract_vid_data function from functions.py and returned.


## functions.py

This file stores all functions that are used in the main program and in other modules.

### format_duration (*Function*) (Args: duration(*str*))
Changes the format the video duration metric returned by the YouTube Data API for a video from PTxMxS to the more standard HH:MM:SS.

### extract_vid_data (*Function*) (Args: video(*api_response["item"]*))
Function to reformat output from API response into list of desired metrics. Input is the output from the video API call indexed with the ["item"] key.

### extract_channel_data (*Function*) (Args: channel(*api_response["item"]*))
Function to reformat output from API response into list of desired metrics. Input is the output from the channel API call indexed with the ["item"] key.

### get_transcript (*Function*) (Args: video_id(*str*), index(*int*), number_of_videos(*int*))
Fetches English transcript of a specified video ID. Other arguments are used to print the video number and total number of videos to process when function is called in a map function for multiple videos in main.py.

### check_multi_tickers (*Function*) (Args: df(*Pandas DataFrame*), filename(*str*, default="all_tickers.csv"))
Checks the title of videos in a .csv file for the presence of other stock tickers. Notes these stock tickers and returns them. Video titles are split on spaces/punctuation defined in the argument to the re.split function in the code; change/add text to split title on by modifying this.

### generate_dataframe (*Function*) (Args: vid_data(*list*), comments_data(*list*), channel_data(*list*), tickers(*list*), transcript_data(*list*, default=None), index(*str*, default="VideoID"), exisiting_data(*bool*/*Pandas DataFrame*, defaul=False))
Generates a Pandas DataFrame from the retrieved data. Stitches together outputs from extract_vid_data, extract_channel_data, comments data, and transcript data to one DataFrame which can then be outputted to an Excel file. If a DataFrame is passed as the existing_data argument, the function will extend the existing DataFrame with the new data.

### check_for_data (*Function*) (Args: filename(*str*))
Checks for the presence of a file in the current working directory.

### get_run_time (*Function*)
Retrieves the time of last run for the program from the settings.txt file. If the program was run <24 hours ago, a message is presented to the user stating that the program may not work as the API quotas might not be full (although the program might still work fine depending on how much quota was used in the previous program run(s)). The user is then given the option whether to continue running the program or not. If the program is run, the current time is returned to be added to the settings.txt file.

### date_to_RFC (*Function*) (Args: date(*datetime*))
Converts a datetime object to RFC format for use as input to the Data API.

### paginated_results (*Function*) (Args: search_obj(*YouTube Data API search object*), request(*YouTube Data API search request object*), limit_requests(*int*, default=4))
Retrieves responses for a specified number of pages for a search api request. This limit is specified by the limit_requests argument.

### search_request (*Function*) (Args: service(*YouTube Data API service object*), query(*str*), start_date(*str*), end_date(*str*), order(*str*), pages(*int*), max_results(*int*, default=50))
Generates search object for a specific query, date range, and order and passes this to the paginated_results function. Returns a list of video/channel IDs and a list of tickers.

### earnings_announcement_period (*Function*) (Args: ea_date(*datetime*), width(*int*, default=10))
Returns a start and end date a specified number of days (*width*) either side of an earnings announcement date.

### search_queries (*Function*) (Args: API_KEYS(*list*), queries(*list*), dates(*list), ids(*list*), pages_per_query(*int*))
Calls search_request function for a list of queries, dates, etc. Returns a list of video/channel IDs, tickers, and ids of queries completed. This function dynamically changes API keys used for queries when quota is exceeded on an API key, this greatly increases capacity for query processing using multiple API keys.





