from msilib.schema import AppId


class APIError(Exception):
    pass

class QuotaExceededError(APIError):
    pass