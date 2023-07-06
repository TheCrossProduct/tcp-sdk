def main (host="https://api.thecrossproduct.xyz/v1", token=None, test_stelvio=True, test_app=True, test_data=True, test_usr=True):

    from .tcpAPI import tcpAPI

    api = tcpAPI (host, token) 

    api.query().auth.get()
