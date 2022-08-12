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

## main.py

This file contains the main code for the program, located inside the main() function. This function is executed each time the program is run.

### Prerequisite Requirements

1. The program must be run in a virtual environment with all of the required packages installed. The environment.yml file can be used to create this environment using Anaconda, follow this link for details: https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html

2. A file named keys.py must be in the same directory as the main.py file. This file must contain a variable called API_KEYS, this should be a list of API keys for the YouTube Data API.

### How does the Program Work?

At the top of the function, there are some variables that can be changed by the user to change certain parts of the program (e.g. input filename, output filename, number of pages retrieved per search query, etc.). Please DO NOT change the include_comments variable to True, as comments are not outputted well to Excel so will be truncated.

In the next section, data from the input Excel file is loaded in, please make sure the Excel file is in the same format as the one I have provided (including a unique ID for each query and EA date in the format (dd/mm/yyyy) (you can ignore that the formatting gets changed to yyyy-mm-dd HH:MM:SS, the program does this itself)).

Existing output data from previous runs is then checked for as we want to maintain this in the output file for when a search requires multiple runs of the program. If you do not want this to happen, delete the output file or specific results in the output file.

The previous run time of the program is then checked. This is because it is highly likely that if the program was run in the last 24 hours, the API quota will be exceeded on the next run, if this happens with the API keys that are used to retrieve video data, the program will fail. The user will be prompted whether or not they want to continue if the program has been run in the past 24 hours. Once this stage is passed, the current time is stored in a file named "settings.txt" to be referenced as the previous run time the next time the program is run.

The next stage of the program splits the available API keys into two groups (search and video), these are used for two different purposes: to search for videos and to gather video data. The number of API keys assigned to these tasks changes based on whether include_commments is True or False (it should be False though, as mentioned earlier).

Search queries are then performed sequentially, and video/channel queries are performed asynchronously. Data is added to various lists to be processed into a pandas DataFrame before exporting.

If the transcripts variable is set to True, the program will search sequentially though the video IDs and gather English transcrips if available. This will take time! as each video (of potentially 1000s!) is processed one-by-one.

The pandas DataFrame is then created with all of the results, this is exported to the output Excel file. The input Excel file is then updated to change the "Done?" column to True for completed queries.
