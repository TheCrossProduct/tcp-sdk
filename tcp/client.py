import platform
import requests
import sys

from slumber.serialize import Serializer, JsonSerializer
from slumber.exceptions import HttpClientError, HttpServerError

from .clientAPI import clientAPI
from . import exceptions
from .text_serializer import PlainTextSerializer
from ._version import __version__


class client(object):
    user_agent = "tcp-sdk/%s Python/%s %s" % (
        __version__,
        " ".join(sys.version.split()),
        platform.platform(),
    )

    def __init__(
        self,
        host: str = None,
        token: str = None,
        user_agent: str = None,
        usermail: str = None,
        passwd: str = None,
        keep_track=False,
    ):
        """
        OOP to TCP API.

        Args:
            host (str): uri of TCP SDK as protocol + ip + port + api version (e.g https://api.thecrossproduct.xyz/v1 or http://127.0.0.1:8080/v1)
            token (str): connection JWT
            user_agent (str): Additional info for logging purposes.
            usermail (str): If no token, then it will connect using credentials.
            passwd (str)
            keep_track (bool): log every requests in a dict (f'{addr}+{method}':integer).

        Exceptions:
            tcp.exceptions.InvalidCredentials

        Notes:
            If neither token nor the pair usermail+passwd are set, then the environment variable TCP_API_TOKEN is tested.
        """

        import os

        if host == None:
            if "TCP_HOST" in os.environ.keys():
                host = os.environ["TCP_HOST"]
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

            resp = clientAPI(
                self.host,
                self.host,
                session=self._make_requests_session(),
                auth=HTTPBasicAuth(usermail, passwd),
                keep_track=keep_track,
            ).auth.login.get()

            self.token = resp["token"]

        if not self.token:
            if "TCP_API_TOKEN" not in os.environ.keys():
                raise exceptions.InvalidCredentials(
                    "No token available: either use BasicAuth or set the env var $TCP_API_TOKEN"
                )

            self.token = os.environ["TCP_API_TOKEN"]

        if keep_track:
            from .track_usage import TrackUsage

            self.keep_track = True
            TrackUsage().init(self)

    def _make_requests_session(self):
        session = requests.Session()

        session.headers.update({"User-Agent": self.user_agent})

        if self.token:
            session.headers.update({"Authorization": f"Bearer {self.token}"})

        return session

    def query(self, **kwargs):
        """
        Use this method to perform a query to TCP API.
        """

        if hasattr(self, "keep_track"):
            kwargs["keep_track"] = self.keep_track

        api = clientAPI(
            self.host,
            self.host,
            session=self._make_requests_session(),
            serializer=Serializer(
                default="json", serializers=[JsonSerializer(), PlainTextSerializer()]
            ),
            **kwargs,
        )

        return api

    def _get_endpoints(self):
        api = clientAPI(
            self.host,
            self.host + "/help",
            session=self._make_requests_session(),
            serializer=Serializer(
                default="json", serializers=[JsonSerializer(), PlainTextSerializer()]
            ),
        )
        routes = api._get_resource(**api._store).get()
        if isinstance(routes, dict):
            return api._get_resource(**api._store).get()["routes"]
        return api._get_resource(**api._store).get()

    def help(self, app=None):
        """
        Provides informations about all methods available to you.

        Args:
            app (str, optional): inquiries help on Application Domain-App

        """

        if app:
            specs = self.query().app.get()

            app_domain = None
            app_name = None

            matches = []
            for domain in specs:
                if app.startswith(domain):
                    matches.append(domain)

            if matches:
                matches.sort(key=lambda x: len(x), reverse=True)
                app_domain = matches[0]
                app_name = app.replace(f"{app_domain}@", "")

            if not app_domain or not app_name:
                print(f"{app} not found")
                return

            print(app_domain, app_name)

            print(self.query().app(app_domain)(app_name).get())
            return

        import textwrap

        resp = self._get_endpoints()

        should_print_license = False

        lines = []
        for endpoint in resp:
            lines.append(
                [
                    " OR ".join(endpoint["methods"]),
                    "query()" + endpoint["endpoint"].replace("/", "."),
                ]
            )

            if "app" in endpoint["endpoint"]:
                should_print_license = True

        print(
            "Python SDK to query TCP's API.\n"
            "\n"
            "You can connect to your TCP account by either setting the environment variable TCP_API_TOKEN\n"
            "Alternatively, you can connect using the following code:\n"
            "\n"
            "import tcp\n"
            'client = tcp.client (usermail="user@mail.co", passwd="passwd")\n'
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

        print("The following endpoints are available:\n")

        for line in lines:
            print("{0:<30}\t{1:<}".format(line[0], line[1]))

        if not lines:
            print("NO ENDPOINT")

        print(
            "\n\nOther methods includes:\n"
            "\n"
            "help\t\t- this message\n"
            "download\t- from TCP S3 storage to your local storage\n"
            "upload\t\t- from your local storage to TCP S3 storage\n"
            "upload_gdrive\t - from your google drive to TCP S3 storage\n"
            #               "metrics\t\t- display %cpu and %rss for a given proces"
        )

        if self.token and should_print_license:
            print("\n\nYou have licenses for the following applications:\n")

            try:
                apps = self.query().app.get()
            except exceptions.InvalidCredentials as err:
                apps = []
                pass

            list_of_apps = []
            for x in apps:
                list_of_apps += [x + "@" + y for y in apps[x]]

            print("\n".join([x for x in list_of_apps]))
            if not apps:
                print("NO APPLICATION")
            print("\n")

            if apps:
                print("Use this line to query help on a specific application:\n")
                print(f"client.help(app='{list_of_apps[0]}')")

    def upload_gdrive(
        self,
        src_gdrive: str,
        dest_s3: str,
        max_part_size: str = None,
        overwrite: bool = False,
        num_tries: int = 3,
        delay_between_tries: float = 1.0,
    ):
        """
        Multipart upload of a file from Google drive to S3 repository.

        Args:
            src_gdrive (str): URL of the Google Drive folder or file. It must be shared as 'Anyone with the link'.
            dest_s3 (str): desired path in TCP S3 bucket
            max_part_size (str): optional. Size of each part to be sent. Either an int (number of bytes) or a human formatted string (example: "1Gb")
            overwrite (bool): optional. If the destination already exists, abort. (false by default).

        Exceptions:
            tcp.exceptions.UploadError
        """
        import gdown
        import tempfile
        import os
        import pathlib

        is_folder = "folders" == src_gdrive.split("/")[4]

        fp = tempfile.TemporaryDirectory()

        if is_folder:
            gdown.download_folder(url=src_gdrive, output=fp.name, remaining_ok=True)

            files = [str(x) for x in list(pathlib.Path(fp.name).iterdir())]

            for file in files:
                rel_path = file[len(fp.name) + 1 :]
                self.upload(
                    file,
                    os.path.join(dest_s3, rel_path),
                    max_part_size,
                    num_tries,
                    delay_between_tries,
                )
        else:
            file = gdown.download(url=src_gdrive, output=fp.name)
            filename = os.path.basename(file)
            self.upload(
                file,
                os.path.join(dest_s3, filename),
                max_part_size,
                overwrite,
                num_tries,
                delay_between_tries,
            )

        fp.cleanup()

    def upload(
        self,
        src_local: str,
        dest_s3: str,
        max_part_size: str = None,
        overwrite: bool = False,
        num_tries: int = 3,
        delay_between_tries: float = 1.0,
        verbose: bool = False,
        compute_md5sum: bool = True,
        md5sum_chunk_size=8192,
    ):
        """
        Multipart upload of a file from local repository to S3 repository.

        Args:
            src_local (str): path to your file on your local computer
            dest_s3 (str): desired path in TCP S3 bucket
            max_part_size (str): optional. Size of each part to be sent. Either an int (number of bytes) or a human formatted string (example: "1Gb")
            overwrite (bool): optional. If the destination already exists, abort. (false by default).

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
        """
        import os
        import slumber
        import time
        import multiprocessing
        from sys import stderr
        import hashlib

        # Uploading directory
        if os.path.isdir(src_local):
            root_in_s3 = os.path.basename(os.path.normpath(src_local))

            for root, dirs, files in os.walk(src_local):
                for file in files:
                    self.upload(
                        os.path.normpath(os.path.join(root, file)),
                        os.path.join(
                            os.path.join(os.path.normpath(dest_s3), root_in_s3),
                            os.path.normpath(
                                os.path.join(
                                    os.path.normpath(root[len(src_local) :]), file
                                )
                            ),
                        ).replace("\\", "/"),
                        max_part_size,
                        overwrite,
                        num_tries,
                        delay_between_tries,
                        verbose,
                        compute_md5sum,
                        md5sum_chunk_size,
                    )
            return


        def check_if_exists ():
            try:
                resp = self.query().data.exists.post({'uri': dest_s3})
            except exceptions.HttpClientError as err:
                return False
            return True

        if not overwrite and check_if_exists():
            raise exceptions.UploadError(f"{dest_s3} already exists. Please set overwrite to True.")

        if verbose:
            stderr.write(
                f"Uploading {src_local} to {dest_s3} (max part size: {max_part_size})"
            )

        file_size = str(os.path.getsize(src_local))
        presigned_body = {"uri": dest_s3, "size": file_size}

        if max_part_size:
            presigned_body.update({"part_size": max_part_size})

        print (presigned_body)

        try:
            resp = self.query().data.upload.multipart.post(presigned_body)
        except slumber.exceptions.SlumberHttpBaseException as err:
            raise exceptions.UploadError(str(err), err.__dict__)

        # 2: File's parts loading
        uploadId = resp["upload_id"]
        urls = resp["parts"]
        part_size = resp["part_size"]
        completed_parts = []

        has_failed = False

        if verbose:
            stderr.write(f"  * part_size: {part_size}")

        completed_parts = []
        todo_parts = [[url, part_no + 1] for part_no, url in enumerate(urls)]

        from .upload import _upload_part

        for try_num in range(num_tries):
            if not todo_parts:
                break

            if try_num > 0:
                time.sleep(delay_between_tries)

            if verbose:
                stderr.write(
                    f"  * Trying {try_num}: {len(todo_parts)} uploads remaining"
                )

            failed_parts = []

            with multiprocessing.Pool() as pool:
                for result in pool.imap_unordered(
                    _upload_part,
                    (
                        [url, part_no, [src_local, part_size]]
                        for url, part_no in todo_parts
                    ),
                ):
                    has_successed, out = result

                    if has_successed:
                        completed_parts.append(out)
                    else:
                        if verbose:
                            stderr.write(f"  * Failed {out}")
                        failed_parts.append([out["url"], out["PartNumber"]])

            todo_parts = failed_parts

        completed_parts.sort(key=lambda x: x["PartNumber"])

        has_failed = len(todo_parts) > 0

        body = {}

        # A part has failed, we abort.
        if has_failed:
            body["upload_id"] = uploadId
            body["uri"] = dest_s3

            stderr.write(f"  * Aborting {src_local}")

            self.query().data.upload.multipart.abort.post(body)

            number_of_parts_done = len(completed_parts)
            total_number_of_parts = len(urls)

            raise exceptions.UploadError(
                f"Part number {number_of_parts_done} failed ({total_number_of_parts} in totals). The multi-part upload was aborted"
            )

        # 3: Parts concatenation and end of upload
        body["upload_id"] = uploadId
        body["parts"] = completed_parts
        body["uri"] = dest_s3

        if compute_md5sum:
            hash_md5 = hashlib.md5()
            with open(src_local, "rb") as f:
                for chunk in iter(lambda: f.read(md5sum_chunk_size), b""):
                    hash_md5.update(chunk)
            body["md5sum"] = hash_md5.hexdigest()

        try:
            self.query().data.upload.multipart.complete.post(body)
        except slumber.exceptions.SlumberHttpBaseException as err:
            raise exceptions.UploadError(str(err), err.__dict__)

    def download(
        self,
        src_s3,
        dest_local,
        chunk_size=8192,
        num_tries: int = 3,
        delay_between_tries: float = 1.0,
        verbose: bool = False,
        md5sum_chunk_size=8192,
    ):
        """
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
        """

        import slumber
        from . import exceptions
        import time
        import sys
        import hashlib

        body = {}
        body["uri"] = src_s3

        try:
            resp = self.query().data.download.post(body)
        except slumber.exceptions.SlumberHttpBaseException as err:
            raise exceptions.DownloadError(str(err), err.__dict__)

        url = resp[src_s3]

        for try_num in range(num_tries):
            if try_num > 0:
                if verbose:
                    sys.stderr.write(
                        f"download {dest_local}: trying again ({try_num+1}/{num_tries})"
                    )
                time.sleep(delay_between_tries)

            try:
                with requests.get(url, stream=True) as r:
                    r.raise_for_status()
                    with open(dest_local, "wb") as f:
                        for chunk in r.iter_content(chunk_size=chunk_size):
                            f.write(chunk)
                return

            except requests.exceptions.HTTPError as err:
                raise exceptions.DownloadError(str(err), err.__dict__)

        if "md5sum" in resp:
            hash_md5 = hashlib.md5()
            with open(dest_local, "rb") as f:
                for chunk in iter(lambda: f.read(md5sum_chunk_size), b""):
                    hash_md5.update(chunk)
            if hash_md5.hexdigest() != resp["md5sum"]:
                raise exceptions.DownloadError("md5sums do not match")

        raise exceptions.DownloadError(str(err), err.__dict__)
