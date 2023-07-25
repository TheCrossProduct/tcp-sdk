import unittest
import tcp
import re

class LicsTestCase (unittest.TestCase):

    def setUp (self):

        import os

        self._test_account = os.environ["TCP_TEST_ACCOUNT"]
        self._test_passwd = os.environ["TCP_TEST_PASSWD"]

        self._client = tcp.client (usermail=self._test_account, passwd= self._test_passwd)

        self._re_uuid4 = "^[0-9a-f]{8}\-[0-9a-f]{4}\-4[0-9a-f]{3}\-[89ab][0-9a-f]{3}\-[0-9a-f]{12}$"
        self._re_datetime = "^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[ ]+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[ ]+([1-9]|[1-2][0-9]|3[0-1])[ ]+([0-1][0-9]|2[0-4]):([0-5][0-9]|60):([0-5][0-9]|60)[ ]+[0-9]{4}$"

    def test_get (self):

        resp = self._client.query().lics.get()

        assert isinstance (resp, list)

        for lic in resp:
            assert isinstance (lic, dict)

            for key in lic:
                assert key in ['token',
                               'name',
                               'user_id',
                               'scope',
                               'created',
                               'until',
                               'last_used',
                               'last_failed',
                               'active',
                               'uses',
                               'limit',
                               'failed_attempts']

            assert isinstance (lic['token'], str)
            assert re.fullmatch (self._re_uuid4, lic['token'])
            assert isinstance (lic['name'], str)
            assert isinstance (lic['user_id'], str)
            assert re.fullmatch (self._re_uuid4, lic['user_id'])
            assert isinstance (lic['scope'], str)
            assert isinstance (lic['created'], str)
            assert re.fullmatch (self._re_datetime, lic['created'])
            assert isinstance (lic['until'], str)
            assert re.fullmatch (self._re_datetime, lic['until'])
            assert isinstance (lic['last_used'], str)
            assert re.fullmatch (self._re_datetime, lic['last_used'])
            assert isinstance (lic['last_failed'], str)
            assert re.fullmatch (self._re_datetime, lic['last_failed'])
            assert isinstance (lic['active'], bool)
            assert isinstance (lic['uses'], float)
            assert lic['uses'] >= 0
            assert isinstance (lic['limit'], float)
            assert lic['limit'] >= 0
            assert isinstance (lic['failed_attempts'], int)
            assert lic['failed_attempts'] >= 0

if __name__ == '__main__':
    unittest.main()