import platform
import requests
import sys
import os

__version__ = '0.0.1'

from .common import SlumberAPI
from slumber.serialize import Serializer
from slumber.exceptions import HttpServerError

class API (object):

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
                resp = SlumberAPI (self.get_api_url (), 
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

        api = SlumberAPI (self.get_api_url (),
                          session=self.make_requests_session(),
                          serializer=Serializer(default="json"),
                          **kwargs)

        return api


    def upload (self, local_file_path:str, dest_to_s3:str, max_part_size:str="50Mb"):

        # TODO: CMA. Finished that.
        #1: S3 target space definition
        presigned_body={"uri": dest_to_s3,"size": file_size, "part_size":max_part_size}
        response=self.query().data.generate-presigned-multipart-post.post(presigned_body)

        #2: File's parts loading
        uploadId=response.json()["upload_id"]
        url=response.json()["parts"]
        part_size = response.json()["part_size"]
        files=[('file',(os.path.basename(local_file_path),open(local_file_path,'rb'),'application/octet-stream'))]
        completed_parts=[]

        with open(local_file_path, 'rb') as f:
            for part_no,url in enumerate(url):
                file_data = f.read(int(part_size))
                #Lancement de la requête put sur une partition
                response=self.query().data.generate-presigned-multipart-post.put(file_data)
                #resu = requests.put(url, data=file_data)
                #récupération des etags des partitions (nécessaire pour la commande de concaténation)
                completed_parts.append({'ETag': response.headers['ETag'], 'PartNumber': part_no+1})

        #3: Parts concatenation and end of upload
        response= self.query().data.complete-multipart-post.post({"upload_id": uploadId, "parts": completed_parts,"uri" : dest_to_s3})



#    def download (self, ):

