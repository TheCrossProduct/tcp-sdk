import datetime
import unittest
import tcp
import re

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

    def test_get (self):

        resp = self._client.query().data.get()

        assert 'paging' in resp
        for field in ['count', 'items_per_page', 'next', 'previous']:
            assert field in resp['paging']
        assert isinstance (resp['paging']['count'], int)
        assert isinstance (resp['paging']['items_per_page'], int)
        assert isinstance (resp['paging']['next'], str)
        assert isinstance (resp['paging']['previous'], str)

        assert isinstance(resp, dict)
        assert 'files' in resp
        assert isinstance(resp['files'], list)

    def test_download_upload_delete (self):

        import os
        import filecmp

        file_src = os.path.join (self._test_dir, 'test.txt')
        file_dest = os.path.join (self._test_dir, 'test-downloaded.txt')

        with open(file_src, 'w') as f:
            f.write ("This is a test. You can safely remove this file.")

        self._client.upload (file_src, 'test.txt')
        self._client.download ('test.txt', file_dest)

        assert os.path.exists (file_dest)

        filecmp.cmp (file_src, file_dest)

        os.remove (file_src)
        os.remove (file_dest)

        self._client.query().data.delete_file.post ({'uri':"test.txt"})

        resp = self._client.query().data.get()
        assert 'test.txt' not in resp['files']

if __name__ == '__main__':
    unittest.main()
