import platform
import requests
import sys
import os

from .clientAPI import clientAPI
from slumber.serialize import Serializer
from slumber.exceptions import HttpServerError

from datetime import datetime

__version__ = datetime.today().strftime ("%Y-%m-%d")

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
                resp = clientAPI (self.get_api_url (), 
                                  self.get_api_url (),
                                  session=self.make_requests_session(),
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

    def make_requests_session (self):

        session = requests.Session ()

        session.headers.update({'User-Agent': self.user_agent})

        if self.token:

            session.headers.update ({'Authorization': f'Bearer {self.token}'})

        return session

    def get_api_url (self):

        return self.host

    def query (self, **kwargs):

        api = clientAPI (self.host,
                         self.get_api_url (),
                         session=self.make_requests_session(),
                         serializer=Serializer(default="json"),
                         **kwargs)

        return api

    def help (self):

        import textwrap

        api = clientAPI (self.host,
                         self.get_api_url () + '/help',
                         session=self.make_requests_session(),
                         serializer=Serializer(default="json"))

        resp = api._get_resource(**api._store).get()

        lines = []
        for endpoint in resp:
            lines.append ([" OR ".join(endpoint['methods']), endpoint["endpoint"]])

        max_first = max([len(x[0]) for x in lines])

        for line in lines:
            print ('{0:<30}\t{1:<}'.format(line[0], line[1]))

    def upload (self, local_file_path:str, dest_to_s3:str, max_part_size:str=None):
        '''Multipart upload for a file from local repository to S3 repository.
        Works accordingly to the following sequence:
        1- Defining the target space in the S3 repository.
        2- Partionning the file and sending each part to the target space
        3- Merging files and completing the upload
        '''
        #TODO adding multithread and retry process when error
        #1: S3 target space definition
        file_size = str(os.path.getsize(local_file_path))
        presigned_body={"uri": dest_to_s3,"size": file_size}

        if max_part_size:
            presigned_body.update({"part_size":max_part_size})
        
        response=self.query().data.generate_presigned_multipart_post.post(presigned_body)

        #2: File's parts loading
        uploadId=response["upload_id"]
        urls=response["parts"]
        part_size = response["part_size"]
        completed_parts=[]

        with open(local_file_path, 'rb') as f:
            for part_no,url in enumerate(urls):
                file_data = f.read(int(part_size))
           
                response=requests.put(url, data=file_data)
                                
                completed_parts.append({'ETag': response.headers['ETag'].replace('"',''), 'PartNumber': part_no+1})

        #3: Parts concatenation and end of upload
        response= self.query().data.complete_multipart_post.post({"upload_id": uploadId, "parts": completed_parts,"uri" : dest_to_s3})

#    def download (self, ):

