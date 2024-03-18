import datetime
import unittest
import tcp
import re

def check_resp (resp):
    assert isinstance (resp, dict)

class DataTestCase (unittest.TestCase):

    def setUp (self):

        import os

        self._test_dir = '.'

        if "TCP_TEST_TOKEN" in os.environ.keys ():
            self._client = tcp.client (token=os.environ["TCP_TEST_TOKEN"])
            return

        self._test_account = os.environ["TCP_TEST_ACCOUNT"]
        self._test_passwd = os.environ["TCP_TEST_PASSWD"]
        self._client = tcp.client (usermail=self._test_account, passwd= self._test_passwd)

        self._re_mem = "^[1-9][0-9]{0,32}(|.[0-9]+)(|b|Kb|Mb|Gb|Tb|Pb)$"


    def test_get (self):

        resp = self._client.query().data.get()

        assert 'paging' in resp
        assert isinstance(resp, dict)
        assert 'files' in resp
        assert isinstance(resp['files'], list)

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
        assert 'paging' in resp
        assert isinstance(resp, dict)
        assert 'files' in resp
        assert isinstance(resp['files'], list)

        assert 'user_id' in resp['files'][0]

        assert 'path' in resp['files'][0]
        assert isinstance(resp['files'][0]['path'],str)

        assert 'created' in resp['files'][0]
        assert isinstance(resp['files'][0]['created'],str)
        datetime.datetime.fromisoformat (resp['files'][0]['created'])

        assert 'last_modified' in resp['files'][0]
        assert isinstance(resp['files'][0]['last_modified'],str)
        datetime.datetime.fromisoformat (resp['files'][0]['last_modified'])

        assert 'size' in resp['files'][0]
        assert isinstance(resp['files'][0]['size'],int)

        assert 'md5sum' in resp['files'][0]
        assert isinstance(resp['files'][0]['md5sum'],str)

        assert 'download_count' in resp['files'][0]
        assert isinstance(resp['files'][0]['download_count'],int)


    def test_get_next_previous (self):

        import requests,json
        resp = self._client.query().data.post({'items_per_page':2})
        # This test suppose to have more than 2 files in this account
        assert 'paging' in resp
        assert 'next' in resp['paging']

        url=resp['paging']['next']
        response=requests.get(url,headers={'authorization':'bearer '+self._client.token})
        resp=json.loads(response.text)
        assert 'files' in resp
        assert isinstance(resp['files'], list)

        assert 'previous' in resp['paging']
        url=resp['paging']['previous']
        response=requests.get(url,headers={'authorization':'bearer '+self._client.token})
        resp=json.loads(response.text)
        assert 'files' in resp
        assert isinstance(resp['files'], list)

    def test_exists(self):
        self._client.query().data.exists({"uri":"filetest.txt"})

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

        resp = self._client.query().data.get()
        assert 'test.txt' in resp['files']

        self._client.download ('test.txt', file_dest)
        time.sleep(2)
        assert os.path.exists(file_dest)

        filecmp.cmp (file_src, file_dest)
        os.remove (file_src)
        os.remove (file_dest)

        self._client.query().data.remove.post({'uri':"test.txt"})
        time.sleep(4)

        resp = self._client.query().data.get()
        assert 'test.txt' not in resp['files']

    def test_single_part (self):

        import requests,os,time
        resp=self._client.query().data.upload.singlepart.post({'uri':'test-singlepart.txt'})
        assert 'url' in resp

        file_src = os.path.join (self._test_dir, 'test.txt')
        with open(file_src, 'w') as f:
            f.write ("This is a test. You can safely remove this file.")

        requests.put(resp['url'],file_src)
        self._client.query().data.upload.singlepart.complete.post({'uri':'test-singlepart.txt'})

        time.sleep(2)
        resp = self._client.query().data.get()
        assert 'test-singlepart.txt' in resp['files']
        self._client.query().data.remove.post({'uri':"test-singlepart.txt"})

    def test_summary (self):

        resp=self._client.query().data.summary.get()

        for field in ['users', 'groups']:
            assert field in resp
            for key in resp[field]:
                assert re.fullmatch (self._re_mem, resp[field][key])

        assert "uploads" in resp
        assert "from" in resp["uploads"]
        datetime.datetime.fromisoformat (resp["uploads"]["from"])
        assert "to" in resp["uploads"]
        datetime.datetime.fromisoformat (resp["uploads"]["to"])

        assert "files" in resp["uploads"]

if __name__ == '__main__':
    unittest.main()
