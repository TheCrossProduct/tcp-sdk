import datetime
import unittest
import tcp
import re

class AuthTestCase (unittest.TestCase):

    def setUp (self):

        import os

        self._test_account = os.environ["TCP_TEST_ACCOUNT"]
        self._test_passwd = os.environ["TCP_TEST_PASSWD"]

        self._client = tcp.client (usermail=self._test_account, passwd= self._test_passwd)

        self._re_jwt = "^[A-Za-z0-9-_]*\.[A-Za-z0-9-_]*\.[A-Za-z0-9-_]*$"
        self._re_uuid4 = "^[0-9a-f]{8}\-[0-9a-f]{4}\-4[0-9a-f]{3}\-[89ab][0-9a-f]{3}\-[0-9a-f]{12}$"
        self._re_mail = "^[\w\.-]+@([\w-]+\.)+[\w-]{2,4}$"

    def test_login_get (self):

        client = tcp.client (usermail=self._test_account, passwd= self._test_passwd)

        assert isinstance(client.token, str)
        assert len(client.token)>0
        assert re.fullmatch("^[A-Za-z0-9-_]*\.[A-Za-z0-9-_]*\.[A-Za-z0-9-_]*$", client.token)

    def test_login_post (self):

        body = {"mail":self._test_account, "passwd":self._test_passwd}
        resp = self._client.query().auth.login.post(body)
        token = resp['token']

        assert isinstance(token, str)
        assert len(token)>0
        assert re.fullmatch(self._re_jwt, token)

    def test_validate_auth_token_get (self):

        resp = self._client.query().auth.validate_auth_token.get()

        assert isinstance (resp, dict)

        for key in resp.keys():
            assert key in ["id", "user_id", "expires_at", "limit", "uses", "scope"]

        assert isinstance(resp["id"], str)
        assert re.fullmatch(self._re_uuid4, resp["id"]) 
        assert isinstance(resp["user_id"], str)
        assert re.fullmatch(self._re_uuid4, resp["user_id"])
        assert isinstance(resp["expires_at"], str)
        datetime.datetime.fromisoformat (resp['expires_at'])
        assert isinstance(resp["limit"], int)
        assert resp["limit"] >= 0
        assert isinstance(resp["uses"], int)
        assert resp["uses"] >= 0
        assert isinstance(resp["scope"], str)

    def test_get (self):

        resp = self._client.query().auth.get ()

        assert isinstance (resp, dict)

        for key in resp:
            assert key in ['id',
                           'mail',
                           'created_on',
                           'nbr_activations',
                           'last_activation',
                           'group',
                           'vat',
                           'address',
                           'company',
                           'contact']

        assert isinstance(resp["id"], str)
        assert re.fullmatch(self._re_uuid4, resp["id"]) 
        assert isinstance(resp["mail"], str)
        assert re.fullmatch(self._re_mail, resp["mail"])
        assert isinstance(resp["created_on"], str)
        datetime.datetime.fromisoformat (resp['created_on'])
        assert isinstance(resp["nbr_activations"], int)
        assert resp["nbr_activations"] >= 0
        assert isinstance(resp["last_activation"], str)
        datetime.datetime.fromisoformat (resp['last_activation'])
        assert isinstance(resp["group"], list)
        for group in resp["group"]:
            assert isinstance(group, dict)
            for key in group.keys():
                assert key in ["id", "name", "descr"]
            assert isinstance(group["id"], str)
            assert re.fullmatch(self._re_uuid4, group["id"])
            assert isinstance(group["name"], str)
            assert isinstance(group["descr"], str)
        assert resp["vat"] is None
        assert resp["address"] is None
        assert resp["company"] is None
        assert resp["contact"] is None

    def test_logout_get (self):

        client = tcp.client (usermail=self._test_account, passwd= self._test_passwd)
        client.query().auth.logout.get()

        try:
            client.query().auth.get()
        except tcp.exceptions.InvalidCredentials as err:
            assert err.response.status_code == 401
            pass

if __name__ == '__main__':
    unittest.main()
