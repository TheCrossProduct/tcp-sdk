import platform
import requests
import sys

from slumber.serialize import Serializer
from slumber.exceptions import HttpClientError, HttpServerError

from .clientAPI import clientAPI
from . import exceptions 
from ._version import __version__

class client (object):

    user_agent = 'scw-sdk/%s Python/%s %s' % (__version__, ' '.join(sys.version.split()), platform.platform())

    def __init__ (self, host:str=None, token:str=None, user_agent:str=None, usermail:str=None, passwd:str=None):

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

        print ("\n\nOther methods includes:\n"
               "\n"
               "help\t\t- this message\n"
               "download\t- from TCP S3 storage to your local storage\n"
               "upload\t\t- from your local storage to TCP S3 storage\n"
               "overview\t\t- interactive overview of your ongoing processes, remotes and instances")

    def upload (self, src_local:str, dest_s3:str, max_part_size:str=None):
        '''
        Multipart upload of a file from local repository to S3 repository.

        Args:
            src_local (str): path to your file on your local computer
            dest_s3 (str): desired path in TCP S3 bucket
            max_part_size (str): optional. Size of each part to be sent. Either an int (number of bytes) or a human formatted string (example: "10Gb") 

        Exceptions:
            tcp.exceptions.tcpUploadException

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

        #TODO adding multithread and retry process when error
        #1: S3 target space definition
        file_size = str(os.path.getsize(src_local))
        presigned_body={"uri": dest_s3,"size": file_size}

        if max_part_size:
            presigned_body.update({"part_size":max_part_size})
        
        try:
            resp=self.query().data.generate_presigned_multipart_post.post(presigned_body)
        except slumber.exceptions.SlumberHttpBaseException as err:
            raise exceptions.UploadException (str(err), err.__dict__)

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
                                
                completed_parts.append({'ETag': resp.headers['ETag'].replace('"',''), 'PartNumber': part_no+1})

        body = {}

        # A part has failed, we abort.
        if has_failed:
            body['upload_id'] = uploadId
            body['uri'] = dest_s3
            self.query().data.abort_multipart_post.post (body)

            number_of_parts_done = len(completed_parts)
            total_number_of_parts = len(urls)

            raise exceptions.UploadException (f"Part number {number_of_parts_done} failed ({total_number_of_parts} in totals). The multi-part upload was aborted")

        #3: Parts concatenation and end of upload
        body["upload_id"] = uploadId
        body["parts"] = completed_parts
        body["uri"] = dest_s3

        try:
            self.query().data.complete_multipart_post.post(body)
        except slumber.exceptions.SlumberHttpBaseException as err:
            raise exceptions.UploadException (str(err), err.__dict__)

    def download (self, src_s3, dest_local, chunk_size=8192):
        '''
        Download of a file from local repository to S3 repository.

        Args:
            src_s3 (str): path in TCP S3 bucket 
            dest_local (str): desired path in your local computer 
            chunk_size (int): desired chunk size for streaming download

        Exceptions:
            tcp.exceptions.tcpDownloadException

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
            raise exceptions.DownloadException (str(err), err.__dict__)

        url = resp['url']

        try: 
            with requests.get(url, stream=True) as r:
                r.raise_for_status ()
                with open (dest_local, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=chunk_size):
                        f.write (chunk)
        except requests.exceptions.HTTPError as err:
            raise exceptions.DownloadException (str(err), err.__dict__)

    def overview (self, refresh_delay=5):
        '''
        Print an overview of all processes.

        Args:
            refresh_delay (int): refresh every X seconds
        '''

        import prettytable
        import time
        import curses
        import traceback
        import threading, queue

        ignores_fields = {'Process':['user_id', 'endpoint', 'terminated', 'expires'],
                          'Remote':['user_id', 'usr', 'input_path', 'output_path', 'working_path'],
                          'Instance':['user_id', 'expires', 'ip', 'ssh_usr', 'input_path', 'working_path', 'output_path', 'num_cores', 'mem_required', 'ram_required']}

        models = ["Process", "Instance", "Remote"]

        text = { "Process": ["No Process"],
                 "Instance": ["No Instance"],
                 "Remote": ["No Remote"] }

        current = "Process"
        current_line = 0

        text_queue = queue.Queue()
        text_queue.put (text)

        dims = [80, 80]

        stop_updating = threading.Event ()

        def update_tables (text_queue):

            def get_table (model):

                entries = self.query().app.list(model).get()

                out = [f"No {model}"]

                if entries:

                    filtered = [{key: entry[key] for key in entry if key not in ignores_fields[model]} for entry in entries]

                    table = prettytable.PrettyTable()
                    #table.max_table_width = table.min_table_width = dims[1]
                    #table.max_table_heigth = table.min_table_heigth = dims[0]-5

                    table.field_names = filtered[0].keys ()
                    table.add_rows ([x.values() for x in filtered])

                    out = table.get_string ().split('\n')
                
                return out

            while True:

                text_queue.put ( { "Process": get_table("Process"),
                         "Instance": get_table("Instance"),
                         "Remote": get_table("Remote") } )

                if stop_updating.is_set ():
                   break 

                time.sleep (refresh_delay)

        th = threading.Thread (target=update_tables, args=(text_queue,))
        th.start ()

        try:
            stdscr = curses.initscr()
            curses.noecho ()
            curses.cbreak ()
            curses.halfdelay(10*refresh_delay)
            stdscr.keypad(1)

            should_exit = False

            current_pos = 0

            while not should_exit:
    
                dims = stdscr.getmaxyx()

                if dims[0] < 40 and dims[1] < 40:
                    stdscr.addstr (0, 0, "screen should be at least 40x40...")
                    continue

                sections = []
                for model in models:
                    if model == current:
                        sections.append (f'<{model}>')
                    else:
                        sections.append (model)

                footnote = '|'.join(sections)+'\n'
                footnote += 'Press q to quit. Press up and down arrow to scroll. Press left and right to select which table.'

                if text_queue.qsize() > 0:
                    text = text_queue.get ()
    
                stdscr.clear ()
                stdscr.addstr(0, 0, '\n'.join(text[current][current_line:min(len(text[current]), dims[0]-5)]))
                stdscr.addstr(dims[0]-2, 0, footnote)

                stdscr.refresh ()

                try:
                    ch = stdscr.getch ()
                except:
                    pass                 

                if ch == curses.KEY_LEFT:
                    index_current = models.index(current)
                    index_current = max(0, index_current-1)
                    current = models[index_current]
                    current_line = 0
                elif ch == curses.KEY_RIGHT:
                    index_current = models.index(current)
                    index_current = min (len(models)-1, index_current+1)
                    current = models[index_current]
                    current_line = 0
                elif ch == curses.KEY_UP:
                    current_line = max(0, current_line-1)
                elif ch == curses.KEY_DOWN:
                    current_line = min(max(0,(len(text[current])-dims[0]+5)), current_line+1)
                elif ch == ord('q'):
                    should_exit = True

                curses.flushinp()
            stdscr.clear ()
            stdscr.addstr ("Exiting...")
            stdscr.refresh ()

        finally:

            stop_updating.set ()
            th.join()

            stdscr.keypad(0)
            curses.echo(); curses.nocbreak()
            curses.endwin()
            traceback.print_exc()

