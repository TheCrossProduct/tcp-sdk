def main (host="https://api.thecrossproduct.xyz", token=None, test_stelvio=True, test_app=True, test_data=True, test_usr=True):

    import slumber

    if not token:
        import os
        token = os.environ['TCP_API_TOKEN']

    from requests_oauthlib import OAuth2Session

    auth = OAuth2Session (token=token)
    api = slumber.API (host, auth=auth)

    api.auth.get()
