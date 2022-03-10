from msilib.schema import AppId


class APIError(Exception):
    pass

class QuotaExceededError(APIError):
    pass

class CommentsDisabledError(APIError):
    pass

# When an error is raised internally with the YouTube API, it does not throw an HTTP error on the request, instead it returns a response with the error cause as a
# dictionary. This will cause a KeyError to be raised later on in the code in most circumstances
# This function can be run whenever there is a KeyError to diagnose the problem and raise the correct error.
def check_keyerror_cause(response):
    if type(response) == list:
        response = response[0]
    if "errors" in response.keys():
        reason = response["error"]["errors"][0]["reason"]
        if reason == "quotaExceeded":
            raise QuotaExceededError("The daily API quota has been exceeded")
        elif reason == "commentsDisabled":
            raise CommentsDisabledError("Comments are disabled on this video")
        else:
            raise APIError(reason)
    else:
        raise KeyError
