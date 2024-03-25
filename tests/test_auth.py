import datetime
import unittest
import tcp
import re

class AuthTestCase (unittest.TestCase):

    def setUp (self):

        import os

        self._test_account = os.environ["TCP_TEST_ACCOUNT"]
        self._test_passwd = os.environ["TCP_TEST_PASSWD"]

        self._client = tcp.client (usermail=self._test_account, passwd= self._test_passwd, keep_track=True)

        self._re_jwt = "^[A-Za-z0-9-_]*\.[A-Za-z0-9-_]*\.[A-Za-z0-9-_]*$"
        self._re_uuid4 = "^[0-9a-f]{8}\-[0-9a-f]{4}\-4[0-9a-f]{3}\-[89ab][0-9a-f]{3}\-[0-9a-f]{12}$"
        self._re_mail = "^[\w\.-]+@([\w-]+\.)+[\w-]{2,4}$"

    def test_z_endpoints_coverage (self):
        uses = tcp.track_usage.TrackUsage().uses

        for key in uses:
            if key.startswith("^\/auth"):
                self.assertGreater(uses[key], 0, f'Endpoint {key} has not been tested')

    def test_login_get (self):

        self.assertIsInstance(self._client.token, str)
        assert len(self._client.token)>0
        assert re.fullmatch("^[A-Za-z0-9-_]*\.[A-Za-z0-9-_]*\.[A-Za-z0-9-_]*$", self._client.token)

    def test_login_post (self):

        body = {"mail":self._test_account, "passwd":self._test_passwd}
        resp = self._client.query().auth.login.post(body)
        token = resp['token']

        self.assertIsInstance(token, str)
        assert len(token)>0
        assert re.fullmatch(self._re_jwt, token)

    def test_validate_auth_token_get (self):

        resp = self._client.query().auth.token.get()

        self.assertIsInstance (resp, dict)

        for key in resp.keys():
            assert key in ["id", "user_id", "expires_at", "limit", "uses", "scope"]

        self.assertIsInstance(resp["id"], str)
        assert re.fullmatch(self._re_uuid4, resp["id"])
        self.assertIsInstance(resp["user_id"], str)
        assert re.fullmatch(self._re_uuid4, resp["user_id"])
        self.assertIsInstance(resp["expires_at"], str)
        datetime.datetime.fromisoformat (resp['expires_at'])
        self.assertIsInstance(resp["limit"], int)
        assert resp["limit"] >= 0
        self.assertIsInstance(resp["uses"], int)
        assert resp["uses"] >= 0
        self.assertIsInstance(resp["scope"], type([]))

    def test_get (self):

        resp = self._client.query().auth.get ()

        self.assertIsInstance (resp, dict)

        for key in resp:
            assert key in ['id',
                           'mail',
                           'created_on',
                           'nbr_activations',
                           'last_activation',
                           'group',
                           'scope',
                           'address',
                           'company',
                           'contact']

        self.assertIsInstance(resp["id"], str)
        assert re.fullmatch(self._re_uuid4, resp["id"])
        self.assertIsInstance(resp["mail"], str)
        assert re.fullmatch(self._re_mail, resp["mail"])
        self.assertIsInstance(resp["created_on"], str)
        datetime.datetime.fromisoformat (resp['created_on'])
        self.assertIsInstance(resp["nbr_activations"], int)
        assert resp["nbr_activations"] >= 0
        self.assertIsInstance(resp["last_activation"], str)
        datetime.datetime.fromisoformat (resp['last_activation'])
        self.assertIsInstance(resp["group"], list)
        for group in resp["group"]:
            self.assertIsInstance(group, dict)
            for key in group.keys():
                assert key in ["id", "name", "descr"]
            self.assertIsInstance(group["id"], str)
            assert re.fullmatch(self._re_uuid4, group["id"])
            self.assertIsInstance(group["name"], str)
            self.assertIsInstance(group["descr"], str)

    def test_logout_get (self):

        self._client.query().auth.logout.get()

        try:
            self._client.query().auth.get()
        except tcp.exceptions.InvalidCredentials as err:
            assert err.response.status_code == 401
            pass

if __name__ == '__main__':
    unittest.main()
