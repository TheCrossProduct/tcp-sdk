import datetime
import unittest
import tcp
import re
from .retry import retry, retry_until_resp

class DataTestCase (unittest.TestCase):

    def setUp (self):

        import os

        self._test_dir = '.'

        self._test_account = os.environ["TCP_TEST_ACCOUNT"]
        self._test_passwd = os.environ["TCP_TEST_PASSWD"]

        self._client = tcp.client (usermail=self._test_account,
                                   passwd= self._test_passwd,
                                   keep_track=True)

        self._re_mem = "^[1-9][0-9]{0,32}(|.[0-9]+)(|b|Kb|Mb|Gb|Tb|Pb)$"

        self.default_files = ['cloud.e57', 'cloud.laz', 'hello.txt']
        self.default_dirs = []

    def tearDown (self):

        self._client.query().auth.logout.get()

    def construct_ref (self, files, dirs):
        from functools import cmp_to_key
        if not files and not dirs:
            return []

        ref = {
            'paging': {
                'count':len(files)+len(dirs),
                'items_per_page':len(files)+len(dirs)
            },
        }

        def cmp_uris(a,b):
            if '@' in a:
                a = a.split('@')[1]
            if '@'in b:
                b = b.split('@')[1]
            if a > b:
                return 1
            elif a < b:
                return -1
            return 0

        if files:
            ref['files'] = sorted(files, key=cmp_to_key(cmp_uris))
        if dirs:
            ref['dirs'] = sorted(dirs, key=cmp_to_key(cmp_uris))

        return ref

    def test_z_endpoints_coverage (self):

        uses = tcp.track_usage.TrackUsage().uses
        untested = [x for x in uses if uses[x]==0 and x.startswith("^\/data")]
        self.assertListEqual(untested, [], "Those endpoints remains untested")

    def test_a_initial_state (self):

        resp = self._client.query().data.get()

        uris = []
        if 'files' in resp:
            uris += resp['files']
        if 'dirs' in resp:
            uris += resp['dirs']

        resp = self._client.query().data.post({'group':'unit_tests', 'personal':False})

        if 'files' in resp:
            uris += resp['files']
        if 'dirs' in resp:
            uris += resp['dirs']

        #CLEANING UP if in dirty state
        for ff in uris:
            if ff in ["cloud.e57","cloud.laz","hello.txt"]:
                continue
            print(f"removing {ff}")
            self._client.query().data.remove.post({'uri':ff})
        #END CLEANING UP

        ref = self.construct_ref(self.default_files, self.default_dirs)
        retry_until_resp(self, self._client.query().data.get, ref)

        resp = self._client.query().data.post({'groups':['unit_tests'], "personal":False})
        self.assertListEqual(resp, [])

    def test_dir (self):

        self._client.query().data.dir.post({"uri":"toto/"})

        ref=self.construct_ref(self.default_files, self.default_dirs+['toto/'])

        retry_until_resp(self, self._client.query().data.get, ref)

        self._client.query().data.dir.post({"uri":"toto/toto"})
        self._client.query().data.dir.post({"uri":"toto/tata"})
        self._client.query().data.dir.post({"uri":"tata/tata"})
        self._client.query().data.dir.post({"uri":"this/is/a/very/nested/directory/with/a/long/name/"})

        dirs_that_should_exists = ['tata/',
                                   'tata/tata/',
                                   'this/',
                                   'this/is/',
                                   'this/is/a/',
                                   'this/is/a/very/',
                                   'this/is/a/very/nested/',
                                   'this/is/a/very/nested/directory/',
                                   'this/is/a/very/nested/directory/with/',
                                   'this/is/a/very/nested/directory/with/a/',
                                   'this/is/a/very/nested/directory/with/a/long/',
                                   "this/is/a/very/nested/directory/with/a/long/name/",
                                   'toto/',
                                   'toto/tata/',
                                   'toto/toto/']

        ref = self.construct_ref(self.default_files, self.default_dirs+dirs_that_should_exists)
        retry_until_resp(self, self._client.query().data.get, ref)

        for dd in dirs_that_should_exists:
            self._client.query().data.remove.post({'uri':dirs_that_should_exists})

        ref = self.construct_ref(self.default_files, self.default_dirs)
        retry_until_resp(self, self._client.query().data.get, ref)

        # GROUPS
        self._client.query().data.dir.post({"uri":"unit_tests@toto/"})

        ref = self.construct_ref([],['unit_tests@toto/'])
        retry_until_resp(self, self._client.query().data.post, ref, {"group":'unit_tests', "personal":False})

        self._client.query().data.dir.post({"uri":"unit_tests@toto/toto"})
        self._client.query().data.dir.post({"uri":"unit_tests@toto/tata"})
        self._client.query().data.dir.post({"uri":"unit_tests@tata/tata"})
        self._client.query().data.dir.post({"uri":"unit_tests@this/is/a/very/nested/directory/with/a/long/name/"})

        dirs_that_should_exists = [f"unit_tests@{x}" for x in dirs_that_should_exists]

        ref = self.construct_ref([],dirs_that_should_exists)
        retry_until_resp(self, self._client.query().data.post, ref, {"group":'unit_tests', "personal":False})

        for dd in dirs_that_should_exists:
            self._client.query().data.remove.post({'uri':dirs_that_should_exists})

        ref = self.construct_ref([],[])
        resp = retry_until_resp(self, self._client.query().data.post, ref, {"group":'unit_tests', "personal":False})

    def test_exists (self):

        # Original setup and root
        self._client.query().data.exists.post({"uri":["hello.txt", "cloud.laz", "cloud.e57"]})

        # Group root
        self._client.query().data.copy.post({"src":"hello.txt", "dest":"unit_tests@hello.txt"})
        retry(self, self._client.query().data.exists.post,{"uri":"unit_tests@hello.txt"})

        # Dir
        self._client.query().data.move.post({"src":"unit_tests@hello.txt", "dest":"dir/hello.txt"})
        retry(self, self._client.query().data.exists.post,{"uri":"dir/hello.txt"})

        # Subdir
        self._client.query().data.move.post({"src":"dir/hello.txt", "dest":"dir/subdir/hello.txt"})
        retry(self, self._client.query().data.exists.post,{"uri":"dir/subdir/hello.txt"})

        # Group dir
        self._client.query().data.move.post({"src":"dir/subdir/hello.txt", "dest":"unit_tests@dir/hello.txt"})
        retry(self, self._client.query().data.exists.post,{"uri":"unit_tests@dir/hello.txt"})

        # Group subdir
        self._client.query().data.move.post({"src":"unit_tests@dir/hello.txt", "dest":"unit_tests@dir/subdir/hello.txt"})
        retry(self, self._client.query().data.exists.post,{"uri":"unit_tests@dir/subdir/hello.txt"})

        self._client.query().data.remove.post({'uri':['dir/',
                                                      'dir/subdir/',
                                                      'unit_tests@dir/subdir/hello.txt',
                                                      'unit_tests@dir/',
                                                      'unit_tests@dir/subdir/']})

    def test_move (self):

        # Empty src
        with self.assertRaises(tcp.exceptions.HttpClientError):
            self._client.query().data.copy.post({"src":"", "dest":"test.txt"})
        retry_until_resp(self,
            self._client.query().data.post,
            self.construct_ref(self.default_files,
                            self.default_dirs),
            {'group':'unit_tests'})

        # Empty dest
        with self.assertRaises(tcp.exceptions.HttpClientError):
            self._client.query().data.copy.post({"src":"hello.txt", "dest":""})
        retry_until_resp(self,
            self._client.query().data.post,
            self.construct_ref(self.default_files,
                            self.default_dirs),
            {'group':'unit_tests'})

        # Root
        with self.assertRaises(tcp.exceptions.HttpClientError):
            self._client.query().data.copy.post({"src":"hello.txt", "dest":"/"})
        retry_until_resp(self,
            self._client.query().data.post,
            self.construct_ref(self.default_files,
                            self.default_dirs),
            {'group':'unit_tests'})

        # File to file

        ##### P to P
        self._client.query().data.copy.post({"src":"hello.txt", "dest":"test.txt"})
        retry_until_resp(self,
            self._client.query().data.post,
            self.construct_ref(self.default_files+['test.txt'],
                            self.default_dirs),
            {'group':'unit_tests'})

        self._client.query().data.move.post({"src":"test.txt", "dest":"dir/test.txt"})
        retry_until_resp(self,
            self._client.query().data.post,
            self.construct_ref(self.default_files+['dir/test.txt'],
                            self.default_dirs+['dir/']),
                            {'group':'unit_tests'})

        ##### P to group
        self._client.query().data.move.post({"src":"dir/test.txt", "dest":"unit_tests@test.txt"})
        retry_until_resp(self,
            self._client.query().data.post,
            self.construct_ref(self.default_files+['unit_tests@test.txt'],
                            self.default_dirs+['dir/']),
            {'group':'unit_tests'})
        self._client.query().data.remove.post({'uri':'dir/'})
        retry_until_resp(self,
            self._client.query().data.post,
            self.construct_ref(self.default_files+['unit_tests@test.txt'],
                            self.default_dirs),
            {'group':'unit_tests'})

        ##### Group to group
        self._client.query().data.move.post({"src":"unit_tests@test.txt", "dest":"unit_tests@dir/test.txt"})
        retry_until_resp(self,
            self._client.query().data.post,
            self.construct_ref(self.default_files+['unit_tests@dir/test.txt'],
                            self.default_dirs+['unit_tests@dir/']),
            {'group':'unit_tests'})

        ##### Group to P
        self._client.query().data.move.post({"src":"unit_tests@dir/test.txt", "dest":"test.txt"})
        retry_until_resp(self,
            self._client.query().data.post,
            self.construct_ref(self.default_files+['test.txt'],
                            self.default_dirs+['unit_tests@dir/']),
            {'group':'unit_tests'})

        self._client.query().data.remove.post({'uri':'unit_tests@dir/'})
        retry_until_resp(self,
            self._client.query().data.post,
            self.construct_ref(self.default_files+['test.txt'],
                            self.default_dirs),
            {'group':'unit_tests'})

        # File to dir

        ##### Dir that does not exist
        with self.assertRaises(tcp.exceptions.HttpClientError):
            self._client.query().data.exists.post({"uri":"dir/"})
        self._client.query().data.move.post({"src":"test.txt", "dest":"dir/"})
        retry_until_resp(self,
            self._client.query().data.post,
            self.construct_ref(self.default_files+['dir/test.txt'],
                            self.default_dirs+['dir/']),
            {'group':'unit_tests'})

        self._client.query().data.move.post({"src":"dir/test.txt", "dest":"test.txt"})
        retry_until_resp(self,
            self._client.query().data.post,
            self.construct_ref(self.default_files+['test.txt'],
                               self.default_dirs+['dir/']),
            {'group':'unit_tests'})
        self._client.query().data.remove.post({'uri':'dir/'})
        retry_until_resp(self,
            self._client.query().data.post,
            self.construct_ref(self.default_files+['test.txt'],
                            self.default_dirs),
            {'group':'unit_tests'})

        ##### Dir that exists
        self._client.query().data.dir.post({'uri':'dir/'})
        retry_until_resp(self,
            self._client.query().data.post,
            self.construct_ref(self.default_files+['test.txt'],
                               self.default_dirs+['dir/']),
            {'group':'unit_tests'})
        self._client.query().data.move.post({"src":"test.txt", "dest":"dir/"})
        retry_until_resp(self,
            self._client.query().data.post,
            self.construct_ref(self.default_files+['dir/test.txt'],
                            self.default_dirs+['dir/']),
            {'group':'unit_tests'})

        # Dir to File
        ##### It should create a dir with the same name as the file
        self._client.query().data.move.post({"src":"dir/", "dest":"test.txt"})
        retry_until_resp(self,
            self._client.query().data.post,
            self.construct_ref(self.default_files+['test.txt/test.txt'],
                               self.default_dirs+['test.txt/']),
            {'group':'unit_tests'})
        self._client.query().data.move.post({"src":"test.txt/test.txt", "dest":"test.txt"})
        retry_until_resp(self,
            self._client.query().data.post,
            self.construct_ref(self.default_files+['test.txt'],
                               self.default_dirs+['test.txt/']),
            {'group':'unit_tests'})
        self._client.query().data.remove.post({'uri':'test.txt/'})
        retry_until_resp(self,
            self._client.query().data.post,
            self.construct_ref(self.default_files+['test.txt'],
                            self.default_dirs),
            {'group':'unit_tests'})

        # Dir to Dir

        ###### Default (overwrite:False, merge:True) NOP
        self._client.query().data.copy.post({"src":["test.txt",
                                                    "test.txt",
                                                    "test.txt"],
                                             "dest":["dira/testa.txt",
                                                     "dirb/testa.txt",
                                                     "dirb/testb.txt"]})

        retry_until_resp(self,
            self._client.query().data.post,
            self.construct_ref(self.default_files+['test.txt',
                                                   'dira/testa.txt',
                                                   'dirb/testa.txt',
                                                   'dirb/testb.txt'],
                               self.default_dirs+['dira/', 'dirb/']),
            {'group':'unit_tests'})
        self._client.query().data.move.post({"src":"dira/", "dest":"dirb/"})
        retry_until_resp(self,
            self._client.query().data.post,
            self.construct_ref(self.default_files+['test.txt',
                                                   'dira/testa.txt',
                                                   'dirb/testa.txt',
                                                   'dirb/testb.txt'],
                               self.default_dirs+['dira/', 'dirb/']),
            {'group':'unit_tests'})

        ##### (overwrite:True, merge:True)
        self._client.query().data.move.post({"src":"dira/", "dest":"dirb/", "overwrite":True})
        retry_until_resp(self,
            self._client.query().data.post,
            self.construct_ref(self.default_files+['test.txt',
                                                   'dirb/testa.txt',
                                                   'dirb/testb.txt'],
                               self.default_dirs+['dirb/']),
            {'group':'unit_tests'})

        ##### (overwrite:True, merge:False)
        self._client.query().data.copy.post({"src":"test.txt",
                                             "dest":"dira/testa.txt"})
        retry_until_resp(self,
            self._client.query().data.post,
            self.construct_ref(self.default_files+['test.txt',
                                                   'dira/testa.txt',
                                                   'dirb/testa.txt',
                                                   'dirb/testb.txt'],
                               self.default_dirs+['dira/', 'dirb/']),
            {'group':'unit_tests'})
        self._client.query().data.move.post({"src":"dira/", "dest":"dirb/", "overwrite":True, "merge":False})
        retry_until_resp(self,
            self._client.query().data.post,
            self.construct_ref(self.default_files+['test.txt',
                                                   'dirb/testa.txt'],
                               self.default_dirs+['dirb/']),
            {'group':'unit_tests'})

        ##### (overwrite:False, merge:False)
        self._client.query().data.copy.post({"src":["test.txt",
                                                    "test.txt"],
                                             "dest":["dira/testa.txt",
                                                     "dirb/testb.txt"]})

        retry_until_resp(self,
            self._client.query().data.post,
            self.construct_ref(self.default_files+['test.txt',
                                                   'dira/testa.txt',
                                                   'dirb/testa.txt',
                                                   'dirb/testb.txt'],
                               self.default_dirs+['dira/', 'dirb/']),
            {'group':'unit_tests'})
        self._client.query().data.move.post({"src":"dira/", "dest":"dirb/", "overwrite":False, "merge":False})
        retry_until_resp(self,
            self._client.query().data.post,
            self.construct_ref(self.default_files+['test.txt',
                                                   'dira/testa.txt',
                                                   'dirb/testa.txt',
                                                   'dirb/testb.txt'],
                               self.default_dirs+['dira/', 'dirb/']),
            {'group':'unit_tests'})

        # Array
        self._client.query().data.move.post({"src":["dira/","dirb/"], "dest":["dirc/","dird/"], "overwrite":False, "merge":False})
        retry_until_resp(self,
            self._client.query().data.post,
            self.construct_ref(self.default_files+['test.txt',
                                                   'dirc/testa.txt',
                                                   'dird/testa.txt',
                                                   'dird/testb.txt'],
                               self.default_dirs+['dirc/', 'dird/']),
            {'group':'unit_tests'})


    def test_list(self):
        self.assertTrue(True)
        # Normal

        # Hierarchy

    def test_singlepart_upload(self):
        self.assertTrue(True)

    def test_multipart_upload(self):
        self.assertTrue(True)

#
#    def test_post (self):
#
#        body={
#            'items_per_page':2,
#            'hierarchy':True,
#            'suffix':['.txt'],
#            'prefix':['test'],
#            'since':'2020-01-01T00:00:00',
#            'expands_info':True,
#            'groups':['internal']
#        }
#        resp = self._client.query().data.post(body)
#
#        body={
#            'expands_info':True,
#        }
#        resp = self._client.query().data.post(body)
#        self.assertIn('paging', resp)
#        self.assertIsInstance(resp, dict)
#        self.assertIn('files', resp)
#        self.assertIsInstance(resp['files'], list)
#
#        self.assertIn('user_id', resp['files'][0])
#
#        self.assertIn('path', resp['files'][0])
#        self.assertIsInstance(resp['files'][0]['path'],str)
#
#        self.assertIn('created', resp['files'][0])
#        self.assertIsInstance(resp['files'][0]['created'],str)
#        datetime.datetime.fromisoformat (resp['files'][0]['created'])
#
#        self.assertIn('last_modified', resp['files'][0])
#        self.assertIsInstance(resp['files'][0]['last_modified'],str)
#        datetime.datetime.fromisoformat (resp['files'][0]['last_modified'])
#
#        self.assertIn('size', resp['files'][0])
#        self.assertIsInstance(resp['files'][0]['size'],int)
#
#        self.assertIn('md5sum', resp['files'][0])
#        self.assertIsInstance(resp['files'][0]['md5sum'],str)
#
#        self.assertIn('download_count', resp['files'][0])
#        self.assertIsInstance(resp['files'][0]['download_count'],int)
#
#    def test_get_next_previous (self):
#
#        import requests,json
#        resp = self._client.query().data.post({'items_per_page':2})
#        # This test suppose to have more than 2 files in this account
#        self.assertIn('paging', resp)
#        self.assertIn('next', resp['paging'])
#
#        url=resp['paging']['next']
#        response=requests.get(url,headers={'authorization':'bearer '+self._client.token})
#        resp=json.loads(response.text)
#
#        self.assertTrue('files' in resp or 'dirs' in resp)
#        if "files" in resp:
#            self.assertIsInstance(resp['files'], list)
#        if 'dirs' in resp:
#            self.assertIsInstance(resp['dirs'], list)
#
#        self.assertIn('previous', resp['paging'])
#        url=resp['paging']['previous']
#        response=requests.get(url,headers={'authorization':'bearer '+self._client.token})
#        resp=json.loads(response.text)
#
#        self.assertTrue('files' in resp or 'dirs' in resp)
#        if "files" in resp:
#            self.assertIsInstance(resp['files'], list)
#        if 'dirs' in resp:
#            self.assertIsInstance(resp['dirs'], list)
#
#    def test_move (self) :
#        import time
#        self._client.query().data.move.post({'src':'filetest.txt','dest':'filetest-move.txt'})
#        time.sleep(2)
#        self._client.query().data.move.post({'src':'filetest-move.txt','dest':'filetest.txt'})
#
#    def test_download_upload_delete (self):
#        import os
#        import filecmp
#        import time
#
#        file_src = os.path.join (self._test_dir, 'test.txt')
#        file_dest = os.path.join (self._test_dir, 'test-downloaded.txt')
#
#        with open(file_src, 'w') as f:
#            f.write ("This is a test. You can safely remove this file.")
#
#        self._client.upload (file_src, 'test.txt')
#        time.sleep(2)
#
#        self.assertEqual(self._client.query().data.exists.post({"uri":"test.txt"}),b'')
#
#        self._client.download ('test.txt', file_dest)
#        time.sleep(2)
#        self.assertTrue(os.path.exists(file_dest))
#
#        filecmp.cmp (file_src, file_dest)
#        os.remove (file_src)
#        os.remove (file_dest)
#
#        self._client.query().data.remove.post({'uri':"test.txt"})
#        time.sleep(2)
#
#        with self.assertRaises(tcp.exceptions.HttpClientError):
#           self._client.query().data.exists.post({"uri":"test.txt"})
#
#    def test_single_part (self):
#
#        import requests
#        import os
#        import time
#        import filecmp
#
#        file_src = os.path.join (self._test_dir, 'test.txt')
#        file_dest = os.path.join (self._test_dir, 'test-downloaded.txt')
#
#        resp=self._client.query().data.upload.singlepart.post({'uri':'test-singlepart.txt'})
#        self.assertIn('url', resp)
#
#        with open(file_src, 'w') as f:
#            f.write ("This is a test. You can safely remove this file.")
#
#        requests.put(resp['url'], file_src)
#        self._client.query().data.upload.singlepart.complete.post({'uri':'test-singlepart.txt'})
#
#        time.sleep(2)
#
#        self.assertEqual(self._client.query().data.exists.post({"uri":"test-singlepart.txt"}),b'')
#
#        self._client.download ('test-singlepart.txt', file_dest)
#        time.sleep(2)
#        self.assertTrue(os.path.exists(file_dest))
#
#        filecmp.cmp (file_src, file_dest)
#        os.remove (file_src)
#        os.remove (file_dest)
#
#        self._client.query().data.remove.post({'uri':"test-singlepart.txt"})
#        time.sleep(2)
#
#        with self.assertRaises(tcp.exceptions.HttpClientError):
#             self._client.query().data.exists.post({"uri":"test-singlepart.txt"})
#
#    def test_summary (self):
#
#        resp=self._client.query().data.summary.get()
#
#        for field in ['users', 'groups']:
#            self.assertIn(field, resp)
#            for key in resp[field]:
#                self.assertTrue(re.fullmatch (self._re_mem, resp[field][key]))
#
#        self.assertIn("uploads", resp)
#        self.assertIn("from", resp["uploads"])
#        datetime.datetime.fromisoformat (resp["uploads"]["from"])
#        self.assertIn("to", resp["uploads"])
#        datetime.datetime.fromisoformat (resp["uploads"]["to"])
#
#        self.assertIn("files", resp["uploads"])
#
#    def test_dir_creation_removal (self):
#        import time
#
#        resp=self._client.query().data.dir.post({"uri":"test_dir/"})
#
#        self.assertEqual(resp, b'')
#
#        self.assertEqual(self._client.query().data.exists.post({"uri":"test_dir/"}),b'')
#
#        self._client.query().data.remove.post({"uri":"test_dir/"})
#
#        time.sleep(2)
#
#        with self.assertRaises(tcp.exceptions.HttpClientError):
#             self._client.query().data.exists.post({"uri":"test_dir/"})


if __name__ == '__main__':
    unittest.main()
