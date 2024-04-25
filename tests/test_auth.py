import datetime
import unittest
import tcp
import re
import requests
import time


class AuthTestCase(unittest.TestCase):
    def setUp(self):
        import os

        self._test_account = os.environ["TCP_TEST_ACCOUNT"]
        self._test_passwd = os.environ["TCP_TEST_PASSWD"]

        self._client = tcp.client(
            usermail=self._test_account, passwd=self._test_passwd, keep_track=True
        )

        self._re_jwt = "^[A-Za-z0-9-_]*\.[A-Za-z0-9-_]*\.[A-Za-z0-9-_]*$"
        self._re_uuid4 = (
            "^[0-9a-f]{8}\-[0-9a-f]{4}\-4[0-9a-f]{3}\-[89ab][0-9a-f]{3}\-[0-9a-f]{12}$"
        )
        self._re_mail = "^[\w\.-]+@([\w-]+\.)+[\w-]{2,4}$"
        self._re_url = "^(https?|ftp)://[^\s/$.?#].[^\s]*$"

    def tearDown(self):
        try:
            self._client.query().auth.logout.get()
        except:
            pass

    def test_zz_endpoints_coverage(self):
        uses = tcp.track_usage.TrackUsage().uses
        untested = [x for x in uses if uses[x] == 0 and x.startswith("^\/auth")]
        self.assertListEqual(untested, [], "Those endpoints remains untested")

    def test_login_get(self):
        self.assertIsInstance(self._client.token, str)
        assert len(self._client.token) > 0
        assert re.fullmatch(
            "^[A-Za-z0-9-_]*\.[A-Za-z0-9-_]*\.[A-Za-z0-9-_]*$", self._client.token
        )

    def test_login_post(self):
        body = {"mail": self._test_account, "passwd": self._test_passwd}
        resp = self._client.query().auth.login.post(body)
        token = resp["token"]

        self.assertIsInstance(token, str)
        assert len(token) > 0
        assert re.fullmatch(self._re_jwt, token)

    def test_validate_auth_token_get(self):
        resp = self._client.query().auth.token.get()

        self.assertIsInstance(resp, dict)

        for key in resp.keys():
            assert key in ["id", "user_id", "expires_at", "limit", "uses", "scope"]

        self.assertIsInstance(resp["id"], str)
        assert re.fullmatch(self._re_uuid4, resp["id"])
        self.assertIsInstance(resp["user_id"], str)
        assert re.fullmatch(self._re_uuid4, resp["user_id"])
        self.assertIsInstance(resp["expires_at"], str)
        datetime.datetime.fromisoformat(resp["expires_at"])
        self.assertIsInstance(resp["limit"], int)
        assert resp["limit"] >= 0
        self.assertIsInstance(resp["uses"], int)
        assert resp["uses"] >= 0
        self.assertIsInstance(resp["scope"], type([]))

    def test_get(self):
        resp = self._client.query().auth.get()

        self.assertIsInstance(resp, dict)

        for key in resp:
            assert key in [
                "id",
                "mail",
                "created_on",
                "nbr_activations",
                "last_activation",
                "group",
                "scope",
                "address",
                "company",
                "contact",
            ]

        self.assertIsInstance(resp["id"], str)
        self.assertTrue(re.fullmatch(self._re_uuid4, resp["id"]))
        self.assertIsInstance(resp["mail"], str)
        self.assertTrue(re.fullmatch(self._re_mail, resp["mail"]))
        self.assertIsInstance(resp["created_on"], str)
        datetime.datetime.fromisoformat(resp["created_on"])
        self.assertIsInstance(resp["nbr_activations"], int)
        self.assertGreaterEqual(resp["nbr_activations"], 0)
        self.assertIsInstance(resp["last_activation"], str)
        datetime.datetime.fromisoformat(resp["last_activation"])
        if "group" in resp:
            self.assertIsInstance(resp["group"], list)
            for group in resp["group"]:
                self.assertIsInstance(group, dict)
                for key in group.keys():
                    self.assertIn(key, ["id", "name", "descr"])
                self.assertIsInstance(group["id"], str)
                self.assertTrue(re.fullmatch(self._re_uuid4, group["id"]))
                self.assertIsInstance(group["name"], str)
                self.assertIsInstance(group["descr"], str)

    def test_reset_psw(self):
        from .mail import check_out_mail

        resp = self._client.query().auth.reset_password.post(
            {"mail": self._test_account}
        )

        self.assertIsInstance(resp, dict)
        mail = resp.get("mail")
        self.assertTrue(re.fullmatch(self._re_mail, mail))
        url_reset = resp.get("url_reset")
        self.assertTrue(re.fullmatch(self._re_url, url_reset))
        url_alert = resp.get("url_alert")
        self.assertTrue(re.fullmatch(self._re_url, url_alert))

        x = requests.get(url_reset)
        match = re.search(r'action="(.*?)"', x.text)
        self.assertTrue(match)
        url_form = match.group(1)

        body = {"newpsw": self._test_passwd, "confirmpsw": self._test_passwd}

        self.assertTrue(requests.post(url_form, data=body))

        time.sleep(10)

        mails = check_out_mail(
            mto=self._test_account,
            subject="[TheCrossProduct] Link to reset your password 🔓",
        )

        self.assertGreater(len(mails), 0)

    def test_logout_get(self):
        self._client.query().auth.logout.get()

        try:
            self._client.query().auth.get()
        except tcp.exceptions.InvalidCredentials as err:
            assert err.response.status_code == 401
            pass

    def test_tokens_delete(self):
        nbr_clients = 10

        clients = [
            tcp.client(
                usermail=self._test_account, passwd=self._test_passwd, keep_track=False
            )
            for _x in range(nbr_clients)
        ]

        self._client.query().auth.tokens.delete()

        for client in clients:
            with self.assertRaises(tcp.exceptions.InvalidCredentials):
                client.query().auth.get()


if __name__ == "__main__":
    unittest.main()
