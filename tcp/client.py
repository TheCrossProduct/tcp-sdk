import platform
import requests
import sys

from slumber.serialize import Serializer, JsonSerializer
from slumber.exceptions import HttpClientError, HttpServerError

from .clientAPI import clientAPI
from . import exceptions 
from .text_serializer import PlainTextSerializer        
from ._version import __version__

class client (object):

    user_agent = 'tcp-sdk/%s Python/%s %s' % (__version__, ' '.join(sys.version.split()), platform.platform())

    def __init__ (self, host:str=None, token:str=None, user_agent:str=None, usermail:str=None, passwd:str=None):
        '''
        OOP to TCP API.

        Args:
            host (str): uri of TCP SDK as protocol + ip + port + api version (e.g https://api.thecrossproduct.xyz/v1 or http://127.0.0.1:8080/v1) 
            token (str): connection JWT
            user_agent (str): Additional info for logging purposes.
            usermail (str): If no token, then it will connect using credentials.
            passwd (str)

        Exceptions:
            tcp.exceptions.InvalidCredentials

        Notes:
            If neither token nor the pair usermail+passwd are set, then the environment variable TCP_API_TOKEN is tested.
        '''


        import os

        if host == None:
            if 'TCP_HOST' in os.environ.keys ():
                host = os.environ['TCP_HOST']
            else:
                host = "https://api.thecrossproduct.xyz/v1"

        self.host = host

        if user_agent:
            self.user_agent = user_agent

        self.token = None

        if token:
            self.token = token

        elif usermail and passwd:

            from requests.auth import HTTPBasicAuth
            import json
            from .logs import warning

            resp = clientAPI (self.host, 
                              self.host,
                              session=self._make_requests_session(),
                              auth=HTTPBasicAuth(usermail,passwd),
                           ).auth.login.get()

            self.token = resp['token']

        if not self.token:
            if 'TCP_API_TOKEN' not in os.environ.keys():
                raise exceptions.InvalidCredentials ("No token available: either use BasicAuth or set the env var $TCP_API_TOKEN") 

            self.token = os.environ['TCP_API_TOKEN']

    def _make_requests_session (self):

        session = requests.Session ()

        session.headers.update({'User-Agent': self.user_agent})

        if self.token:

            session.headers.update ({'Authorization': f'Bearer {self.token}'})

        return session

    def query (self, **kwargs):
        '''
        Use this method to perform a query to TCP API.
        '''

        api = clientAPI (self.host,
                         self.host,
                         session=self._make_requests_session(),
                         serializer=Serializer(default="json",
                                               serializers=[JsonSerializer(), 
                                                            PlainTextSerializer()]),
                         **kwargs)

        return api

    def _get_endpoints (self):

        api = clientAPI (self.host,
                         self.host + '/help',
                         session=self._make_requests_session(),
                         serializer=Serializer(default="json",
                                               serializers=[JsonSerializer(), 
                                                            PlainTextSerializer()]))

        return api._get_resource(**api._store).get()

    def help (self, app=None):
        '''
        Provides informations about all methods available to you.

        Args:
            app (str, optional): inquiries help on Application Domain-App

        '''

        if app:
            specs = self.query().app.get ()

            app_domain = None
            app_name = None

            matches = []
            for domain in specs:
                if app.startswith(domain):
                    matches.append (domain)

            if matches:
                matches.sort (key=lambda x: len(x), reverse=True)
                app_domain = matches[0]
                app_name = app.replace (f'{app_domain}@', '')

            if not app_domain or not app_name:
                print (f"{app} not found")
                return

            print (app_domain, app_name)

            print(self.query().app(app_domain)(app_name).get())
            return

        import textwrap

        resp = self._get_endpoints ()

        should_print_license = False

        lines = []
        for endpoint in resp:
            lines.append ([" OR ".join(endpoint['methods']), 'query()'+endpoint["endpoint"].replace('/', '.')])

            if 'app' in endpoint["endpoint"]:
                should_print_license = True

        print ("Python SDK to query TCP's API.\n"
               "\n"
               "You can connect to your TCP account by either setting the environment variable TCP_API_TOKEN\n"
               "Alternatively, you can connect using the following code:\n"
               "\n"
               "import tcp\n"
               "client = tcp.client (usermail=\"user@mail.co\", passwd=\"passwd\")\n"
               "\n"
               "If you're looking to send a GET HTTP request against our API, like:\n"
               "\n"
               " GET https://{hostname}/{vX}/auth\n"
               "\n"
               "You only need to call the following pythonic code:\n"
               "\n"
               "import tcp\n"
               "client = tcp.client ()\n"
               "client.query().auth.get()\n"
               "\n"
               "The query method returns a slumber.API object.\n"
               "The latter handles all the excruciating details of the requests.\n"
               "\n"
              )

        print ("The following endpoints are available:\n")

        for line in lines:
            print ('{0:<30}\t{1:<}'.format(line[0], line[1]))

        if not lines:
            print ("NO ENDPOINT")

        print ("\n\nOther methods includes:\n"
               "\n"
               "help\t\t- this message\n"
               "download\t- from TCP S3 storage to your local storage\n"
               "upload\t\t- from your local storage to TCP S3 storage\n"
               "metrics\t\t- display %cpu and %rss for a given proces")
            

        if self.token and should_print_license:

            print ("\n\nYou have licenses for the following applications:\n")
    
            try:
                apps = self.query().app.get ()
            except exceptions.InvalidCredentials as err:
                apps = []
                pass

            list_of_apps = []
            for x in apps:
                list_of_apps += [x + '@' + y for y in apps[x]]

            print ('\n'.join([x for x in list_of_apps]))
            if not apps:
                print ('NO APPLICATION')
            print ('\n')

            if apps: 
                print ('Use this line to query help on a specific application:\n')
                print (f'client.help(app=\'{list_of_apps[0]}\')')

    def upload (self, src_local:str, dest_s3:str, max_part_size:str=None, num_tries:int=3, delay_between_tries:float=1.):
        '''
        Multipart upload of a file from local repository to S3 repository.

        Args:
            src_local (str): path to your file on your local computer
            dest_s3 (str): desired path in TCP S3 bucket
            max_part_size (str): optional. Size of each part to be sent. Either an int (number of bytes) or a human formatted string (example: "1Gb") 

        Exceptions:
            tcp.exceptions.UploadError

        Notes:

            Works accordingly to the following sequence:
                1. Defining the target space in the S3 repository.
                2. Partionning the file and sending each part to the target space
                3. Merging files and completing the upload

            Internally it uses the following TCP endpoints:
                - POST generate_presigned_multipart_post 
                - POST complete_multipart_post
        '''
        import os
        import slumber
        import time
        import multiprocessing

        # Uploading directory
        if os.path.isdir (src_local):
            root_in_s3 = os.path.basename (src_local)

            for root, dirs, files in os.walk (src_local):
                for file in files:
                    self.upload (os.path.join(root,file), 
                                 os.path.normpath(os.path.join(
                                     os.path.join(dest_s3,root_in_s3), 
                                     os.path.join(root[len(src_local):],file)
                                     )).replace('\\','/'),
                                 max_part_size
                                 )
            return

        print (f"Uploading {src_local} to {dest_s3} (max part size: {max_part_size})")

        #TODO adding multithread and retry process when error
        #1: S3 target space definition
        file_size = str(os.path.getsize(src_local))
        presigned_body={"uri": dest_s3,"size": file_size}

        if max_part_size:
            presigned_body.update({"part_size":max_part_size})
        
        try:
            resp=self.query().data.upload.multipart.post(presigned_body)
        except slumber.exceptions.SlumberHttpBaseException as err:
            raise exceptions.UploadError (str(err), err.__dict__)

        #2: File's parts loading
        uploadId=resp["upload_id"]
        urls=resp["parts"]
        part_size = resp["part_size"]
        completed_parts=[]

        has_failed = False

        print (f"  * part_size: {part_size}")

        completed_parts = []
        todo_parts = [[url, part_no+1] for part_no, url in enumerate(urls)]

        from .upload import _upload_part

        for try_num in range(num_tries): 

            if not todo_parts:
                break

            if try_num > 0:
                time.sleep (delay_between_tries)

            print (f"  * Trying {try_num}: {len(todo_parts)} uploads remaining")

            failed_parts = []

            with multiprocessing.Pool () as pool:

                for result in pool.imap_unordered (_upload_part, 
                                                   ([url, part_no, [src_local, part_size]] for url, part_no in todo_parts)):

                    has_successed, out = result

                    if has_successed:
                        completed_parts.append (out)
                    else:
                        print (f"  * Failed {out}")
                        failed_parts.append ([out['url'], out['PartNumber']])

            todo_parts = failed_parts

        completed_parts.sort (key=lambda x: x['PartNumber']) 

        has_failed = (len(todo_parts) > 0)

        body = {}

        # A part has failed, we abort.
        if has_failed:
            body['upload_id'] = uploadId
            body['uri'] = dest_s3

            print (f"  * Aborting {src_local}")

            self.query().data.upload.multipart.abort.post (body)

            number_of_parts_done = len(completed_parts)
            total_number_of_parts = len(urls)

            raise exceptions.UploadError (f"Part number {number_of_parts_done} failed ({total_number_of_parts} in totals). The multi-part upload was aborted")

        #3: Parts concatenation and end of upload
        body["upload_id"] = uploadId
        body["parts"] = completed_parts
        body["uri"] = dest_s3

        try:
            self.query().data.upload.multipart.complete.post(body)
        except slumber.exceptions.SlumberHttpBaseException as err:
            raise exceptions.UploadError (str(err), err.__dict__)

    def download (self, src_s3, dest_local, chunk_size=8192):
        '''
        Download of a file from local repository to S3 repository.

        Args:
            src_s3 (str): path in TCP S3 bucket 
            dest_local (str): desired path in your local computer 
            chunk_size (int): desired chunk size for streaming download

        Exceptions:
            tcp.exceptions.DownloadError

        Notes:

            Works accordingly to the following sequence:
                1. Get a temporary link to our S3 
                2. Download file from that link using a stream 

            Internally it uses the following TCP endpoints:
                - POST generate_presigned_get
        '''

        import slumber
        from . import exceptions

        body = {} 
        body['uri'] = src_s3

        try:
            resp = self.query ().data.download.post (body)
        except slumber.exceptions.SlumberHttpBaseException as err:
            raise exceptions.DownloadError (str(err), err.__dict__)

        url = resp['url']

        try: 
            with requests.get(url, stream=True) as r:
                r.raise_for_status ()
                with open (dest_local, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=chunk_size):
                        f.write (chunk)
        except requests.exceptions.HTTPError as err:
            raise exceptions.DownloadError (str(err), err.__dict__)

    def metrics (self, process_id, filter_state=None):
        '''
        Display metrics about your process. 

        Args:
            process_id (uuid4): your process id 

        Notes:
            needs an active graphical session
        '''


        resp = self.query().app.status.get (Process=process_id)

        if 'metrics' in resp:

            import numpy as np
            import matplotlib
            matplotlib.use('TkAgg', force=True)
            import matplotlib.pyplot as plt
            from datetime import datetime, timedelta
            import math

            ts = {}
            pcpu = {}
            prss = {}
            states = []


            for state in resp['metrics']:

                if filter_state and filter_state not in state:
                    continue

                data = resp['metrics'][state]

                sampling_rate = data['rate']
                pcpu[state] = [float(x[0]) for x in data['metrics'] if x]
                prss[state] = [float(x[1]) for x in data['metrics'] if x]
                ts[state] = [datetime.fromisoformat (data['datetime'])] 
                ts[state] += [ts[state][0] + timedelta(seconds=sampling_rate*(ii+1)) for ii in range(len(pcpu[state])-1)]

                has_at_least_one_entry = len(pcpu[state]) != 0

                if has_at_least_one_entry:
                    states.append (state)

            plt.style.use("dark_background")
            fig = plt.figure ()
            ax = fig.gca ()
            parax = ax.twinx()

            ax.tick_params (axis='x', labelsize='small', rotation=45)


            series = []
            for state in states:
                series.append (ts[state])
                series.append (pcpu[state])

            plot_pcpu = ax.plot (*series, c=(0.451,0.749,0.412))

            series = []
            for state in states:
                series.append (ts[state])
                series.append (prss[state])

            plot_prss = parax.plot (*series, c=(0.949,0.800,0.047))

            leg = ax.legend(plot_pcpu, ["%cpu"], bbox_to_anchor=(0., 1.05), loc='lower left')
            leg = parax.legend(plot_prss, ["%rss"], bbox_to_anchor=(1., 1.05), loc='lower right')

            max_cpu = max([max(pcpu[state]) for state in states])

            for state in states:
                ax.text (ts[state][0], max_cpu, state)
                ax.axvspan (ts[state][0], ts[state][-1], facecolor='0.15')

            fig.tight_layout ()
            plt.show ()

        else:
            print ("No metrics available.")

