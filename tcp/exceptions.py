class tcpBaseException (Exception):
    """
    All TCP exceptions inherit from this exception.
    """

class tcpHttpBaseException (tcpBaseException):
    """
    All tcp HTTP Exceptions inherit from this exception.
    """

    def __init__ (self, *args, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)
        super(tcpHttpBaseException, self).__init__(*args)

class HttpClientError (tcpHttpBaseException):
    """
    Called when the server tells us there was a client error (4xx)
    """

class HttpServerError (tcpHttpBaseException):
    """
    Called when the server tells us there was a server error (5xx)
    """

class InvalidCredentials (tcpHttpBaseException):
    """
    Invalid or no credentials were provided.
    """

class NoDocumentation (tcpHttpBaseException):
    """
    No documentation is available for this endpoint.
    """

class DownloadError (tcpHttpBaseException):
    """
    Download has failed somehow.
    """

class UploadError (tcpHttpBaseException):
    """
    Upload has failed somehow.
    """
