import datetime
import uuid
import unittest
import tcp
import re
import os
import json
import tempfile
import filecmp
import requests
import socketio
from .retry import retry, retry_until_resp
from .pagination import check_pagination


class DataTestCase(unittest.TestCase):
    def setUp(self):
        self._test_account = os.environ["TCP_TEST_ACCOUNT"]
        self._test_passwd = os.environ["TCP_TEST_PASSWD"]

        self._client = tcp.client(
            usermail=self._test_account, passwd=self._test_passwd, keep_track=True
        )

        self._sock = socketio.SimpleClient()
        self._sock.connect(
            os.environ["TCP_WEBSOCKET_HOST"],
            transports=["websocket"],
            headers={"Authorization": f"Bearer {self._client.token}"},
        )

        self._re_mem = "^[1-9][0-9]{0,32}(|.[0-9]+)(|b|Kb|Mb|Gb|Tb|Pb)$"

        self.default_files = ["cloud.e57", "cloud.laz", "hello.txt"]
        self.default_dirs = []

    def tearDown(self):
        self._client.query().auth.logout.get()
        self._sock.disconnect()

    def construct_ref(self, files, dirs):
        from functools import cmp_to_key

        ref = {
            "paging": {
                "count": len(files) + len(dirs),
                "items_per_page": len(files) + len(dirs),
            },
        }

        def cmp_uris(a, b):
            if "@" in a:
                a = a.split("@")[1]
            if "@" in b:
                b = b.split("@")[1]
            if a > b:
                return 1
            elif a < b:
                return -1
            return 0

        ref["files"] = sorted(files, key=cmp_to_key(cmp_uris))
        ref["dirs"] = sorted(dirs, key=cmp_to_key(cmp_uris))

        return ref

    def test_z_endpoints_coverage(self):
        uses = tcp.track_usage.TrackUsage().uses
        untested = [x for x in uses if uses[x] == 0 and x.startswith("^\/data")]
        self.assertListEqual(untested, [], "Those endpoints remains untested")

    def test_a_initial_state(self):
        resp = self._client.query().data.get()

        uris = []
        if "files" in resp:
            uris += resp["files"]
        if "dirs" in resp:
            uris += resp["dirs"]

        resp = self._client.query().data.post(
            {"group": "unit_tests", "personal": False}
        )

        if "files" in resp:
            uris += resp["files"]
        if "dirs" in resp:
            uris += resp["dirs"]

        # CLEANING UP if in dirty state
        for ff in uris:
            if ff in ["cloud.e57", "cloud.laz", "hello.txt"]:
                continue
            print(f"removing {ff}")
            self._client.query().data.remove.post({"uri": ff})
        # END CLEANING UP

        ref = self.construct_ref(self.default_files, self.default_dirs)
        retry_until_resp(self, self._client.query().data.get, ref)

        resp = self._client.query().data.post(
            {"groups": ["unit_tests"], "personal": False}
        )
        self.assertDictEqual(resp, self.construct_ref([], []))

    def test_dir(self):
        self._client.query().data.dir.post({"uri": "toto/"})

        ref = self.construct_ref(self.default_files, self.default_dirs + ["toto/"])

        retry_until_resp(self, self._client.query().data.get, ref)

        self._client.query().data.dir.post({"uri": "toto/toto"})
        self._client.query().data.dir.post({"uri": "toto/tata"})
        self._client.query().data.dir.post({"uri": "tata/tata"})
        self._client.query().data.dir.post(
            {"uri": "this/is/a/very/nested/directory/with/a/long/name/"}
        )

        dirs_that_should_exists = [
            "tata/",
            "tata/tata/",
            "this/",
            "this/is/",
            "this/is/a/",
            "this/is/a/very/",
            "this/is/a/very/nested/",
            "this/is/a/very/nested/directory/",
            "this/is/a/very/nested/directory/with/",
            "this/is/a/very/nested/directory/with/a/",
            "this/is/a/very/nested/directory/with/a/long/",
            "this/is/a/very/nested/directory/with/a/long/name/",
            "toto/",
            "toto/tata/",
            "toto/toto/",
        ]

        ref = self.construct_ref(
            self.default_files, self.default_dirs + dirs_that_should_exists
        )
        retry_until_resp(self, self._client.query().data.get, ref)

        for dd in dirs_that_should_exists:
            self._client.query().data.remove.post({"uri": dirs_that_should_exists})

        ref = self.construct_ref(self.default_files, self.default_dirs)
        retry_until_resp(self, self._client.query().data.get, ref)

        # GROUPS
        self._client.query().data.dir.post({"uri": "unit_tests@toto/"})

        ref = self.construct_ref([], ["unit_tests@toto/"])
        retry_until_resp(
            self,
            self._client.query().data.post,
            ref,
            {"group": "unit_tests", "personal": False},
        )

        self._client.query().data.dir.post({"uri": "unit_tests@toto/toto"})
        self._client.query().data.dir.post({"uri": "unit_tests@toto/tata"})
        self._client.query().data.dir.post({"uri": "unit_tests@tata/tata"})
        self._client.query().data.dir.post(
            {"uri": "unit_tests@this/is/a/very/nested/directory/with/a/long/name/"}
        )

        dirs_that_should_exists = [f"unit_tests@{x}" for x in dirs_that_should_exists]

        ref = self.construct_ref([], dirs_that_should_exists)
        retry_until_resp(
            self,
            self._client.query().data.post,
            ref,
            {"group": "unit_tests", "personal": False},
        )

        for dd in dirs_that_should_exists:
            self._client.query().data.remove.post({"uri": dirs_that_should_exists})

        ref = self.construct_ref([], [])
        resp = retry_until_resp(
            self,
            self._client.query().data.post,
            ref,
            {"group": "unit_tests", "personal": False},
        )

    def test_exists(self):
        # Original setup and root
        self._client.query().data.exists.post(
            {"uri": ["hello.txt", "cloud.laz", "cloud.e57"]}
        )

        # Group root
        self._client.query().data.copy.post(
            {"src": "hello.txt", "dest": "unit_tests@hello.txt"}
        )
        retry(
            self, self._client.query().data.exists.post, {"uri": "unit_tests@hello.txt"}
        )

        # Dir
        self._client.query().data.move.post(
            {"src": "unit_tests@hello.txt", "dest": "dir/hello.txt"}
        )
        retry(self, self._client.query().data.exists.post, {"uri": "dir/hello.txt"})

        # Subdir
        self._client.query().data.move.post(
            {"src": "dir/hello.txt", "dest": "dir/subdir/hello.txt"}
        )
        retry(
            self, self._client.query().data.exists.post, {"uri": "dir/subdir/hello.txt"}
        )

        # Group dir
        self._client.query().data.move.post(
            {"src": "dir/subdir/hello.txt", "dest": "unit_tests@dir/hello.txt"}
        )
        retry(
            self,
            self._client.query().data.exists.post,
            {"uri": "unit_tests@dir/hello.txt"},
        )

        # Group subdir
        self._client.query().data.move.post(
            {
                "src": "unit_tests@dir/hello.txt",
                "dest": "unit_tests@dir/subdir/hello.txt",
            }
        )
        retry(
            self,
            self._client.query().data.exists.post,
            {"uri": "unit_tests@dir/subdir/hello.txt"},
        )

        self._client.query().data.remove.post(
            {
                "uri": [
                    "dir/",
                    "dir/subdir/",
                    "unit_tests@dir/subdir/hello.txt",
                    "unit_tests@dir/",
                    "unit_tests@dir/subdir/",
                ]
            }
        )

    def test_move(self):
        # Empty src
        with self.assertRaises(tcp.exceptions.HttpClientError):
            self._client.query().data.copy.post({"src": "", "dest": "test.txt"})
        retry_until_resp(
            self,
            self._client.query().data.post,
            self.construct_ref(self.default_files, self.default_dirs),
            {"group": "unit_tests"},
        )

        # Empty dest
        with self.assertRaises(tcp.exceptions.HttpClientError):
            self._client.query().data.copy.post({"src": "hello.txt", "dest": ""})
        retry_until_resp(
            self,
            self._client.query().data.post,
            self.construct_ref(self.default_files, self.default_dirs),
            {"group": "unit_tests"},
        )

        # Root
        with self.assertRaises(tcp.exceptions.HttpClientError):
            self._client.query().data.copy.post({"src": "hello.txt", "dest": "/"})
        retry_until_resp(
            self,
            self._client.query().data.post,
            self.construct_ref(self.default_files, self.default_dirs),
            {"group": "unit_tests"},
        )

        # File to file

        ##### P to P
        self._client.query().data.copy.post({"src": "hello.txt", "dest": "test.txt"})
        retry_until_resp(
            self,
            self._client.query().data.post,
            self.construct_ref(self.default_files + ["test.txt"], self.default_dirs),
            {"group": "unit_tests"},
        )

        self._client.query().data.move.post({"src": "test.txt", "dest": "dir/test.txt"})
        retry_until_resp(
            self,
            self._client.query().data.post,
            self.construct_ref(
                self.default_files + ["dir/test.txt"], self.default_dirs + ["dir/"]
            ),
            {"group": "unit_tests"},
        )

        ##### P to group
        self._client.query().data.move.post(
            {"src": "dir/test.txt", "dest": "unit_tests@test.txt"}
        )
        retry_until_resp(
            self,
            self._client.query().data.post,
            self.construct_ref(
                self.default_files + ["unit_tests@test.txt"],
                self.default_dirs + ["dir/"],
            ),
            {"group": "unit_tests"},
        )
        self._client.query().data.remove.post({"uri": "dir/"})
        retry_until_resp(
            self,
            self._client.query().data.post,
            self.construct_ref(
                self.default_files + ["unit_tests@test.txt"], self.default_dirs
            ),
            {"group": "unit_tests"},
        )

        ##### Group to group
        self._client.query().data.move.post(
            {"src": "unit_tests@test.txt", "dest": "unit_tests@dir/test.txt"}
        )
        retry_until_resp(
            self,
            self._client.query().data.post,
            self.construct_ref(
                self.default_files + ["unit_tests@dir/test.txt"],
                self.default_dirs + ["unit_tests@dir/"],
            ),
            {"group": "unit_tests"},
        )

        ##### Group to P
        self._client.query().data.move.post(
            {"src": "unit_tests@dir/test.txt", "dest": "test.txt"}
        )
        retry_until_resp(
            self,
            self._client.query().data.post,
            self.construct_ref(
                self.default_files + ["test.txt"],
                self.default_dirs + ["unit_tests@dir/"],
            ),
            {"group": "unit_tests"},
        )

        self._client.query().data.remove.post({"uri": "unit_tests@dir/"})
        retry_until_resp(
            self,
            self._client.query().data.post,
            self.construct_ref(self.default_files + ["test.txt"], self.default_dirs),
            {"group": "unit_tests"},
        )

        # File to dir

        ##### Dir that does not exist
        with self.assertRaises(tcp.exceptions.HttpClientError):
            self._client.query().data.exists.post({"uri": "dir/"})
        self._client.query().data.move.post({"src": "test.txt", "dest": "dir/"})
        retry_until_resp(
            self,
            self._client.query().data.post,
            self.construct_ref(
                self.default_files + ["dir/test.txt"], self.default_dirs + ["dir/"]
            ),
            {"group": "unit_tests"},
        )

        self._client.query().data.move.post({"src": "dir/test.txt", "dest": "test.txt"})
        retry_until_resp(
            self,
            self._client.query().data.post,
            self.construct_ref(
                self.default_files + ["test.txt"], self.default_dirs + ["dir/"]
            ),
            {"group": "unit_tests"},
        )
        self._client.query().data.remove.post({"uri": "dir/"})
        retry_until_resp(
            self,
            self._client.query().data.post,
            self.construct_ref(self.default_files + ["test.txt"], self.default_dirs),
            {"group": "unit_tests"},
        )

        ##### Dir that exists
        self._client.query().data.dir.post({"uri": "dir/"})
        retry_until_resp(
            self,
            self._client.query().data.post,
            self.construct_ref(
                self.default_files + ["test.txt"], self.default_dirs + ["dir/"]
            ),
            {"group": "unit_tests"},
        )
        self._client.query().data.move.post({"src": "test.txt", "dest": "dir/"})
        retry_until_resp(
            self,
            self._client.query().data.post,
            self.construct_ref(
                self.default_files + ["dir/test.txt"], self.default_dirs + ["dir/"]
            ),
            {"group": "unit_tests"},
        )

        # Dir to File
        ##### It should create a dir with the same name as the file
        self._client.query().data.move.post({"src": "dir/", "dest": "test.txt"})
        retry_until_resp(
            self,
            self._client.query().data.post,
            self.construct_ref(
                self.default_files + ["test.txt/test.txt"],
                self.default_dirs + ["test.txt/"],
            ),
            {"group": "unit_tests"},
        )
        self._client.query().data.move.post(
            {"src": "test.txt/test.txt", "dest": "test.txt"}
        )
        retry_until_resp(
            self,
            self._client.query().data.post,
            self.construct_ref(
                self.default_files + ["test.txt"], self.default_dirs + ["test.txt/"]
            ),
            {"group": "unit_tests"},
        )
        self._client.query().data.remove.post({"uri": "test.txt/"})
        retry_until_resp(
            self,
            self._client.query().data.post,
            self.construct_ref(self.default_files + ["test.txt"], self.default_dirs),
            {"group": "unit_tests"},
        )

        # Dir to Dir

        ###### Default (overwrite:False, merge:True) NOP
        self._client.query().data.copy.post(
            {
                "src": ["test.txt", "test.txt", "test.txt"],
                "dest": ["dira/testa.txt", "dirb/testa.txt", "dirb/testb.txt"],
            }
        )

        retry_until_resp(
            self,
            self._client.query().data.post,
            self.construct_ref(
                self.default_files
                + ["test.txt", "dira/testa.txt", "dirb/testa.txt", "dirb/testb.txt"],
                self.default_dirs + ["dira/", "dirb/"],
            ),
            {"group": "unit_tests"},
        )
        self._client.query().data.move.post({"src": "dira/", "dest": "dirb/"})
        retry_until_resp(
            self,
            self._client.query().data.post,
            self.construct_ref(
                self.default_files
                + ["test.txt", "dira/testa.txt", "dirb/testa.txt", "dirb/testb.txt"],
                self.default_dirs + ["dira/", "dirb/"],
            ),
            {"group": "unit_tests"},
        )

        ##### (overwrite:True, merge:True)
        self._client.query().data.move.post(
            {"src": "dira/", "dest": "dirb/", "overwrite": True}
        )
        retry_until_resp(
            self,
            self._client.query().data.post,
            self.construct_ref(
                self.default_files + ["test.txt", "dirb/testa.txt", "dirb/testb.txt"],
                self.default_dirs + ["dirb/"],
            ),
            {"group": "unit_tests"},
        )

        ##### (overwrite:True, merge:False)
        self._client.query().data.copy.post(
            {"src": "test.txt", "dest": "dira/testa.txt"}
        )
        retry_until_resp(
            self,
            self._client.query().data.post,
            self.construct_ref(
                self.default_files
                + ["test.txt", "dira/testa.txt", "dirb/testa.txt", "dirb/testb.txt"],
                self.default_dirs + ["dira/", "dirb/"],
            ),
            {"group": "unit_tests"},
        )
        self._client.query().data.move.post(
            {"src": "dira/", "dest": "dirb/", "overwrite": True, "merge": False}
        )
        retry_until_resp(
            self,
            self._client.query().data.post,
            self.construct_ref(
                self.default_files + ["test.txt", "dirb/testa.txt"],
                self.default_dirs + ["dirb/"],
            ),
            {"group": "unit_tests"},
        )

        ##### (overwrite:False, merge:False)
        self._client.query().data.copy.post(
            {
                "src": ["test.txt", "test.txt"],
                "dest": ["dira/testa.txt", "dirb/testb.txt"],
            }
        )

        retry_until_resp(
            self,
            self._client.query().data.post,
            self.construct_ref(
                self.default_files
                + ["test.txt", "dira/testa.txt", "dirb/testa.txt", "dirb/testb.txt"],
                self.default_dirs + ["dira/", "dirb/"],
            ),
            {"group": "unit_tests"},
        )
        self._client.query().data.move.post(
            {"src": "dira/", "dest": "dirb/", "overwrite": False, "merge": False}
        )
        retry_until_resp(
            self,
            self._client.query().data.post,
            self.construct_ref(
                self.default_files + ["test.txt", "dirb/testa.txt"],
                self.default_dirs + ["dirb/"],
            ),
            {"group": "unit_tests"},
        )

        # Array
        self._client.query().data.copy.post(
            {
                "src": ["test.txt", "test.txt"],
                "dest": ["dira/testa.txt", "dirb/testb.txt"],
            }
        )
        retry_until_resp(
            self,
            self._client.query().data.post,
            self.construct_ref(
                self.default_files
                + ["test.txt", "dira/testa.txt", "dirb/testa.txt", "dirb/testb.txt"],
                self.default_dirs + ["dira/", "dirb/"],
            ),
            {"group": "unit_tests"},
        )

        self._client.query().data.move.post(
            {
                "src": ["dira/", "dirb/"],
                "dest": ["dirc/", "dird/"],
                "overwrite": False,
                "merge": False,
            }
        )
        retry_until_resp(
            self,
            self._client.query().data.post,
            self.construct_ref(
                self.default_files
                + ["test.txt", "dirc/testa.txt", "dird/testa.txt", "dird/testb.txt"],
                self.default_dirs + ["dirc/", "dird/"],
            ),
            {"group": "unit_tests"},
        )

        self._client.query().data.remove.post({"uri": ["test.txt", "dirc/", "dird/"]})
        retry_until_resp(
            self,
            self._client.query().data.post,
            self.construct_ref(self.default_files, self.default_dirs),
            {"group": "unit_tests"},
        )

    def test_list(self):
        # Setup
        self._client.query().data.copy.post({"src": "hello.txt", "dest": "test.txt"})
        retry_until_resp(
            self,
            self._client.query().data.post,
            self.construct_ref(self.default_files + ["test.txt"], self.default_dirs),
            {"group": "unit_tests"},
        )

        self._client.query().data.copy.post(
            {
                "src": ["test.txt", "test.txt", "test.txt", "test.txt"],
                "dest": [
                    "dira/test.txt",
                    "dirb/test.txt",
                    "dirb/dirc/testa.txt",
                    "dirb/dirc/testb.txt",
                ],
            }
        )

        # Normal
        retry_until_resp(
            self,
            self._client.query().data.post,
            self.construct_ref(
                self.default_files
                + [
                    "test.txt",
                    "dira/test.txt",
                    "dirb/test.txt",
                    "dirb/dirc/testa.txt",
                    "dirb/dirc/testb.txt",
                ],
                self.default_dirs + ["dira/", "dirb/", "dirb/dirc/"],
            ),
            {"group": "unit_tests"},
        )

        # Hierarchy
        self.assertDictEqual(
            self._client.query().data.post({"hierarchy": True}),
            self.construct_ref(
                self.default_files + ["test.txt"],
                self.default_dirs + ["dira/", "dirb/"],
            ),
        )
        self.assertDictEqual(
            self._client.query().data.post({"hierarchy": True, "prefix": ["dirb/"]}),
            self.construct_ref(["dirb/test.txt"], ["dirb/", "dirb/dirc/"]),
        )
        self.assertDictEqual(
            self._client.query().data.post(
                {"hierarchy": True, "prefix": ["dirb/dirc/"]}
            ),
            self.construct_ref(
                ["dirb/dirc/testa.txt", "dirb/dirc/testb.txt"], ["dirb/dirc/"]
            ),
        )

        self._client.query().data.remove.post({"uri": ["test.txt", "dira/", "dirb/"]})

        retry_until_resp(
            self,
            self._client.query().data.post,
            self.construct_ref(self.default_files, self.default_dirs),
            {"group": "unit_tests"},
        )

        try:
            check_pagination(self, self._client.query().data, {"expands_info": True})
        except tcp.exceptions.HttpClientError as err:
            print(err.content)

    def create_temp_file(self):
        import uuid

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write("This is a test. You can safely remove this file.".encode())
            f.write(str(uuid.uuid4()).encode())
            f.close()

            return f.name

    def create_empty_temp_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.close()
            return f.name

    def destroy_temp_file(self, name):
        os.unlink(name)
        self.assertFalse(os.path.exists(name))

    def test_download(self):
        path = self.create_empty_temp_file()

        self._client.download("hello.txt", path)

        with open(path, "r") as f:
            self.assertEqual("\n".join(f.readlines()), "Hello world!\n")

        self.destroy_temp_file(path)

    def test_ws_download(self):
        action = "data_download_post"
        body = {"uri": "hello.txt"}

        msg_id = str(uuid.uuid4())

        self._sock.emit(
            "backend_message", {"action": action, "id": msg_id, "body": body}
        )

        resp = self._sock.receive(10)
        self.assertListEqual(resp, ["info", {"message": "Connection to TCP Websocket"}])

        resp = self._sock.receive(10)
        event_name, data = resp[0], json.loads(resp[1])

        self.assertEqual(event_name, "json")
        self.assertIsInstance(data, dict)
        self.assertListEqual(list(data.keys()), ["action", "state", "response", "id"])
        self.assertEqual(data["action"], "data_download_post")
        self.assertEqual(data["state"], "done")
        self.assertEqual(data["id"], msg_id)
        self.assertIn("hello.txt", data["response"])
        self.assertIn("md5sum", data["response"])

        self._sock.disconnect()

    def test_multipart_upload(self):
        file_src = self.create_temp_file()
        self._client.upload(file_src, "test.txt")

        retry_until_resp(
            self,
            self._client.query().data.post,
            self.construct_ref(self.default_files + ["test.txt"], self.default_dirs),
            {"group": "unit_tests"},
        )

        file_dest = self.create_empty_temp_file()
        self._client.download("test.txt", file_dest)

        self.assertTrue(os.path.exists(file_dest))

        filecmp.cmp(file_src, file_dest)
        self.destroy_temp_file(file_src)
        self.destroy_temp_file(file_dest)
        self._client.query().data.remove.post({"uri": "test.txt"})

        retry_until_resp(
            self,
            self._client.query().data.post,
            self.construct_ref(self.default_files, self.default_dirs),
            {"group": "unit_tests"},
        )

    def test_singlepart_upload(self):
        file_src = self.create_temp_file()

        resp = self._client.query().data.upload.singlepart.post({"uri": "test.txt"})
        self.assertIn("url", resp)
        requests.put(resp["url"], data=file_src)
        self._client.query().data.upload.singlepart.complete.post({"uri": "test.txt"})

        retry_until_resp(
            self,
            self._client.query().data.post,
            self.construct_ref(self.default_files + ["test.txt"], self.default_dirs),
            {"group": "unit_tests"},
        )

        file_dest = self.create_empty_temp_file()
        self._client.download("test.txt", file_dest)

        self.assertTrue(os.path.exists(file_dest))

        filecmp.cmp(file_src, file_dest)
        self.destroy_temp_file(file_src)
        self.destroy_temp_file(file_dest)
        self._client.query().data.remove.post({"uri": "test.txt"})

        retry_until_resp(
            self,
            self._client.query().data.post,
            self.construct_ref(self.default_files, self.default_dirs),
            {"group": "unit_tests"},
        )

    def test_multipart_upload_(self):
        file_src = self.create_temp_file()
        file_size = os.path.getsize(file_src)

        resp = self._client.query().data.upload.multipart.post(
            {"uri": "test.txt", "size": file_size}
        )
        self.assertIn("upload_id", resp)
        self.assertIn("parts", resp)
        self.assertIn("part_size", resp)

        completed_parts = []

        with open(file_src, "rb") as f:
            for part_no, part_url in enumerate(resp["parts"]):
                file_data = f.read(resp["part_size"])
                part_resp = requests.put(part_url, data=file_data)
                self.assertEqual(200, part_resp.status_code)
                completed_parts.append(
                    {
                        "ETag": part_resp.headers["ETag"].replace('"', ""),
                        "PartNumber": part_no + 1,
                    }
                )

        self._client.query().data.upload.multipart.complete.post(
            {
                "uri": "test.txt",
                "upload_id": resp["upload_id"],
                "parts": completed_parts,
            }
        )

        retry_until_resp(
            self,
            self._client.query().data.post,
            self.construct_ref(self.default_files + ["test.txt"], self.default_dirs),
            {"group": "unit_tests"},
        )

        file_dest = self.create_empty_temp_file()
        self._client.download("test.txt", file_dest)

        self.assertTrue(os.path.exists(file_dest))

        filecmp.cmp(file_src, file_dest)
        self.destroy_temp_file(file_src)
        self.destroy_temp_file(file_dest)
        self._client.query().data.remove.post({"uri": "test.txt"})

        retry_until_resp(
            self,
            self._client.query().data.post,
            self.construct_ref(self.default_files, self.default_dirs),
            {"group": "unit_tests"},
        )

    def test_multipart_upload_abort(self):
        file_src = self.create_temp_file()
        file_size = os.path.getsize(file_src)

        resp = self._client.query().data.upload.multipart.post(
            {"uri": "test.txt", "size": file_size}
        )
        self.assertIn("upload_id", resp)
        self.assertIn("parts", resp)
        self.assertIn("part_size", resp)

        self._client.query().data.upload.multipart.abort.post(
            {
                "uri": "test.txt",
                "upload_id": resp["upload_id"],
            }
        )

        with self.assertRaises(tcp.exceptions.HttpClientError):
            self._client.query().data.exists.post({"uri": "test.txt"})


if __name__ == "__main__":
    unittest.main()
