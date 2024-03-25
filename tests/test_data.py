import datetime
import unittest
import tcp
import re

def check_resp (resp):
    self.assertIsInstance (resp, dict)

class DataTestCase (unittest.TestCase):

    def setUp (self):

        import os

        self._test_dir = '.'

        if "TCP_TEST_TOKEN" in os.environ.keys ():
            self._client = tcp.client (token=os.environ["TCP_TEST_TOKEN"])
            return

        self._test_account = os.environ["TCP_TEST_ACCOUNT"]
        self._test_passwd = os.environ["TCP_TEST_PASSWD"]
        self._client = tcp.client (usermail=self._test_account,
                                   passwd= self._test_passwd,
                                   keep_track=True)

        self._re_mem = "^[1-9][0-9]{0,32}(|.[0-9]+)(|b|Kb|Mb|Gb|Tb|Pb)$"

    def test_z_check_uses (self):
        uses = tcp.track_usage.TrackUsage().uses

        for key in uses:
            if key.startswith("^\/data"):
                self.assertGreater(uses[key], 0, f'Endpoint {key} has not been tested')

    def test_get (self):

        resp = self._client.query().data.get()

        self.assertIn('paging', resp)
        self.assertIsInstance(resp, dict)
        self.assertIn('files', resp)
        self.assertIsInstance(resp['files'], list)

    def test_post (self):

        body={
            'items_per_page':2,
            'hierarchy':True,
            'suffix':['.txt'],
            'prefix':['test'],
            'since':'2020-01-01T00:00:00',
            'expands_info':True,
            'groups':['internal']
        }
        resp = self._client.query().data.post(body)

        body={
            'expands_info':True,
        }
        resp = self._client.query().data.post(body)
        self.assertIn('paging', resp)
        self.assertIsInstance(resp, dict)
        self.assertIn('files', resp)
        self.assertIsInstance(resp['files'], list)

        self.assertIn('user_id', resp['files'][0])

        self.assertIn('path', resp['files'][0])
        self.assertIsInstance(resp['files'][0]['path'],str)

        self.assertIn('created', resp['files'][0])
        self.assertIsInstance(resp['files'][0]['created'],str)
        datetime.datetime.fromisoformat (resp['files'][0]['created'])

        self.assertIn('last_modified', resp['files'][0])
        self.assertIsInstance(resp['files'][0]['last_modified'],str)
        datetime.datetime.fromisoformat (resp['files'][0]['last_modified'])

        self.assertIn('size', resp['files'][0])
        self.assertIsInstance(resp['files'][0]['size'],int)

        self.assertIn('md5sum', resp['files'][0])
        self.assertIsInstance(resp['files'][0]['md5sum'],str)

        self.assertIn('download_count', resp['files'][0])
        self.assertIsInstance(resp['files'][0]['download_count'],int)

    def test_get_next_previous (self):

        import requests,json
        resp = self._client.query().data.post({'items_per_page':2})
        # This test suppose to have more than 2 files in this account
        self.assertIn('paging', resp)
        self.assertIn('next', resp['paging'])

        url=resp['paging']['next']
        response=requests.get(url,headers={'authorization':'bearer '+self._client.token})
        resp=json.loads(response.text)

        self.assertTrue('files' in resp or 'dirs' in resp)
        if "files" in resp:
            self.assertIsInstance(resp['files'], list)
        if 'dirs' in resp:
            self.assertIsInstance(resp['dirs'], list)

        self.assertIn('previous', resp['paging'])
        url=resp['paging']['previous']
        response=requests.get(url,headers={'authorization':'bearer '+self._client.token})
        resp=json.loads(response.text)

        self.assertTrue('files' in resp or 'dirs' in resp)
        if "files" in resp:
            self.assertIsInstance(resp['files'], list)
        if 'dirs' in resp:
            self.assertIsInstance(resp['dirs'], list)

    def test_move (self) :
        import time
        self._client.query().data.move.post({'src':'filetest.txt','dest':'filetest-move.txt'})
        time.sleep(2)
        self._client.query().data.move.post({'src':'filetest-move.txt','dest':'filetest.txt'})

    def test_download_upload_delete (self):
        import os
        import filecmp
        import time

        file_src = os.path.join (self._test_dir, 'test.txt')
        file_dest = os.path.join (self._test_dir, 'test-downloaded.txt')

        with open(file_src, 'w') as f:
            f.write ("This is a test. You can safely remove this file.")

        self._client.upload (file_src, 'test.txt')
        time.sleep(2)

        self.assertEqual(self._client.query().data.exists.post({"uri":"test.txt"}),b'')

        self._client.download ('test.txt', file_dest)
        time.sleep(2)
        self.assertTrue(os.path.exists(file_dest))

        filecmp.cmp (file_src, file_dest)
        os.remove (file_src)
        os.remove (file_dest)

        self._client.query().data.remove.post({'uri':"test.txt"})
        time.sleep(2)

        with self.assertRaises(tcp.exceptions.HttpClientError):
           self._client.query().data.exists.post({"uri":"test.txt"})

    def test_single_part (self):

        import requests
        import os
        import time
        import filecmp

        file_src = os.path.join (self._test_dir, 'test.txt')
        file_dest = os.path.join (self._test_dir, 'test-downloaded.txt')

        resp=self._client.query().data.upload.singlepart.post({'uri':'test-singlepart.txt'})
        self.assertIn('url', resp)

        with open(file_src, 'w') as f:
            f.write ("This is a test. You can safely remove this file.")

        requests.put(resp['url'], file_src)
        self._client.query().data.upload.singlepart.complete.post({'uri':'test-singlepart.txt'})

        time.sleep(2)

        self.assertEqual(self._client.query().data.exists.post({"uri":"test-singlepart.txt"}),b'')

        self._client.download ('test-singlepart.txt', file_dest)
        time.sleep(2)
        self.assertTrue(os.path.exists(file_dest))

        filecmp.cmp (file_src, file_dest)
        os.remove (file_src)
        os.remove (file_dest)

        self._client.query().data.remove.post({'uri':"test-singlepart.txt"})
        time.sleep(2)

        with self.assertRaises(tcp.exceptions.HttpClientError):
             self._client.query().data.exists.post({"uri":"test-singlepart.txt"})

    def test_summary (self):

        resp=self._client.query().data.summary.get()

        for field in ['users', 'groups']:
            self.assertIn(field, resp)
            for key in resp[field]:
                self.assertTrue(re.fullmatch (self._re_mem, resp[field][key]))

        self.assertIn("uploads", resp)
        self.assertIn("from", resp["uploads"])
        datetime.datetime.fromisoformat (resp["uploads"]["from"])
        self.assertIn("to", resp["uploads"])
        datetime.datetime.fromisoformat (resp["uploads"]["to"])

        self.assertIn("files", resp["uploads"])

    def test_dir_creation_removal (self):
        import time

        resp=self._client.query().data.dir.post({"uri":"test_dir/"})

        self.assertEqual(resp, b'')

        self.assertEqual(self._client.query().data.exists.post({"uri":"test_dir/"}),b'')

        self._client.query().data.remove.post({"uri":"test_dir/"})

        time.sleep(2)

        with self.assertRaises(tcp.exceptions.HttpClientError):
             self._client.query().data.exists.post({"uri":"test_dir/"})


if __name__ == '__main__':
    unittest.main()
