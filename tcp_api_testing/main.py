def main (host="https://api.thecrossproduct.xyz/v1", token=None, test_stelvio=True, test_app=True, test_data=True, test_usr=True):

    from .tcpAPI import tcpAPI

    if not token:
        import os
        token = os.environ['TCP_API_TOKEN']

    api = tcpAPI (host, token) 

    api.query().auth.get()
