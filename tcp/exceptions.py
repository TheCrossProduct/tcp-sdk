class tcpBaseException (Exception):
    """
    All TCP exceptions inherit from this exception.
    """

class tcpHttpBaseException (tcpBaseException):
    """
    All tcp HTTP Exceptions inherit from this exception.
    """

    def __init__ (self, *args, **kwargs):
        for key, val in kwargs.iteritems():
            setattr(self, key, value)
        super(tcpHttpBaseException, self).__init__(*args)

class HttpClientException (tcpHttpBaseException):
    """
    Called when the server tells us there was a client error (4xx)
    """

class HttpServerException (tcpHttpBaseException):
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

class DownloadException (tcpHttpBaseException):
    """
    Download has failed somehow.
    """

class UploadException (tcpHttpBaseException):
    """
    Upload has failed somehow.
    """
