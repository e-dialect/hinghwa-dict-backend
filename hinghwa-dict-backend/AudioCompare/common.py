class BaseResult(object):
    """Used to report results of operations
    performed in our algorithms."""
    def __init__(self, success, message):
        self.success = success
        self.message = message

    def __str__(self):
        return self.message

class FileErrorResult(BaseResult):
    """A result that indicates there was an error
    operating on a file."""
    def __init__(self, message):
        super(FileErrorResult, self).__init__(False, message)
