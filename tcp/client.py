import platform
import requests
import sys
import os

from .clientAPI import clientAPI
from slumber.serialize import Serializer
from slumber.exceptions import HttpServerError

from datetime import datetime

from . import __version__

class client (object):

    base_url = None
    user_agent = 'scw-sdk/%s Python/%s %s' % (__version__, ' '.join(sys.version.split()), platform.platform())

    def __init__ (self, host="https://api.thecrossproduct.xyz/v1", token=None, user_agent=None, usermail=None, passwd=None):

        self.host = host

        if user_agent:
            self.user_agent = user_agent

        self.token = None

        if token:
            self.token = token

        elif usermail and passwd:

            from requests.auth import HTTPBasicAuth
            import json

            has_login = True

            try:
                resp = clientAPI (self.host, 
                                  self.host,
                                  session=self._make_requests_session(),
                                  auth=HTTPBasicAuth(usermail,passwd),
                               ).auth.login.get()
            except HttpServerError as err:
                has_login = False

            if has_login:
                self.token = resp['token']

        if not token:
            import os
            if 'TCP_API_TOKEN' not in os.environ.keys():
                exit (1)
            self.token = os.environ['TCP_API_TOKEN']

    def _make_requests_session (self):

        session = requests.Session ()

        session.headers.update({'User-Agent': self.user_agent})

        if self.token:

            session.headers.update ({'Authorization': f'Bearer {self.token}'})

        return session

    def query (self, **kwargs):

        api = clientAPI (self.host,
                         self.host,
                         session=self._make_requests_session(),
                         serializer=Serializer(default="json"),
                         **kwargs)

        return api

    def _get_endpoints (self):
        api = clientAPI (self.host,
                         self.host + '/help',
                         session=self._make_requests_session(),
                         serializer=Serializer(default="json"))

        return api._get_resource(**api._store).get()

    def help (self):

        import textwrap

        resp = self._get_endpoints ()

        lines = []
        for endpoint in resp:
            lines.append ([" OR ".join(endpoint['methods']), 'query()'+endpoint["endpoint"].replace('/', '.')])

        max_first = max([len(x[0]) for x in lines])

        print ("Python SDK to query TCP's API.\n"
               "\n"
               "You can connect to your TCP account by either setting the environment variable TCP_API_TOKEN\n"
               "Alternatively, you can connect using the following code:\n"
               "\n"
               "client = tcpSDK.client (usermail=\"user@mail.co\", passwd=\"passwd\")"
               "\n"
               "If you're looking to send a GET HTTP request against our API, like:\n"
               "\n"
               " GET https://{hostname}/{vX}/auth\n"
               "\n"
               "you only need to call the following pythonic code:\n"
               "\n"
               "import tcpSDK\n"
               "client = tcpSDK.client ()\n"
               "client.query().auth.get()\n"
               "\n"
               "The query method returns a slumber.API object.\n"
               "The latter handles all the excruciating details of the requests.\n"
               "\n"
              )

        print ("The following endpoints are available:\n")

        for line in lines:
            print ('{0:<30}\t{1:<}'.format(line[0], line[1]))

        print ("\n\nOther methods includes:\n"
               "\n"
               "help\t\t- this message\n"
               "download\t - from TCP S3 storage to your local storage\n"
               "upload\t\t - from your local storage to TCP S3 storage\n")

    def upload (self, src_local:str, dest_s3:str, max_part_size:str=None):
        '''
        Multipart upload of a file from local repository to S3 repository.

        Args:
            src_local (str): path to your file on your local computer
            dest_s3 (str): desired path in TCP S3 bucket
            max_part_size (str): optional. Size of each part to be sent. Either an int (number of bytes) or a human formatted string (example: "10Gb") 

        Returns:
            bool: True if it has successed

        Notes:

            Works accordingly to the following sequence:
                1. Defining the target space in the S3 repository.
                2. Partionning the file and sending each part to the target space
                3. Merging files and completing the upload

            Internally it uses the following TCP endpoints:
                - POST generate_presigned_multipart_post 
                - POST complete_multipart_post
        '''
        #TODO adding multithread and retry process when error
        #1: S3 target space definition
        file_size = str(os.path.getsize(src_local))
        presigned_body={"uri": dest_s3,"size": file_size}

        if max_part_size:
            presigned_body.update({"part_size":max_part_size})
        
        try:
            resp=self.query().data.generate_presigned_multipart_post.post(presigned_body)
        except slumber.exceptions.SlumberHttpBaseException as err:
            return False

        #2: File's parts loading
        uploadId=resp["upload_id"]
        urls=resp["parts"]
        part_size = resp["part_size"]
        completed_parts=[]

        has_failed = False

        with open(src_local, 'rb') as f:
            for part_no,url in enumerate(urls):
                file_data = f.read(int(part_size))
           
                resp=requests.put(url, data=file_data)

                if resp.status_code != 200:
                    has_failed = True
                    break
                                
                completed_parts.append({'ETag': response.headers['ETag'].replace('"',''), 'PartNumber': part_no+1})

        body = {}

        # A part has failed, we abort.
        if has_failed:
            body['upload_id'] = uploadId
            body['uri'] = dest_s3
            self.query().data.abort_multipart_post.delete (body)
            return False

        #3: Parts concatenation and end of upload
        body["upload_id"] = uploadId
        body["parts"] = completed_parts
        body["uri"] = dest_s3
        self.query().data.complete_multipart_post.post(body)

        return True

    def download (self, src_s3, dest_local, chunk_size=8192):
        '''
        Download of a file from local repository to S3 repository.

        Args:
            src_s3 (str): path in TCP S3 bucket 
            dest_local (str): desired path in your local computer 
            chunk_size (int): desired chunk size for streaming download

        Returns:
            bool: True if it has successed

        Notes:

            Works accordingly to the following sequence:
                1. Get a temporary link to our S3 
                2. Download file from that link using a stream 

            Internally it uses the following TCP endpoints:
                - POST generate_presigned_get
        '''

        body = {} 
        body['uri'] = src_s3

        try:
            resp = self.query ().data.generate_presigned_get.post (body)
        except slumber.exceptions.SlumberHttpBaseException as err:
            return False

        url = resp['url']

        try: 
            with requests.get(url, stream=True) as r:
                r.raise_for_status ()
                with open (dest_local, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=chunk_size):
                        f.write (chunk)
        except requests.exceptions.HTTPError as err:
            return False

        return True

