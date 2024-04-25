import datetime
import unittest
import tcp
import re


class LicsTestCase(unittest.TestCase):
    def setUp(self):
        import os

        self._test_account = os.environ["TCP_TEST_ACCOUNT"]
        self._test_passwd = os.environ["TCP_TEST_PASSWD"]

        self._client = tcp.client(
            usermail=self._test_account, passwd=self._test_passwd, keep_track=True
        )

        self._re_uuid4 = (
            "^[0-9a-f]{8}\-[0-9a-f]{4}\-4[0-9a-f]{3}\-[89ab][0-9a-f]{3}\-[0-9a-f]{12}$"
        )
        self._re_datetime = "^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[ ]+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[ ]+([1-9]|[1-2][0-9]|3[0-1])[ ]+([0-1][0-9]|2[0-4]):([0-5][0-9]|60):([0-5][0-9]|60)[ ]+(1|[0-9]{4})$"

    def tearDown(self):
        self._client.query().auth.logout.get()

    def test_z_endpoints_coverage(self):
        uses = tcp.track_usage.TrackUsage().uses
        untested = [x for x in uses if uses[x] == 0 and x.startswith("^\/lics")]
        self.assertListEqual(untested, [], "Those endpoints remains untested")

    def test_lics(self):
        # TEST lics_licenses_get_post
        #      lics_licenses_next_get
        #      lics_licenses_previous_get
        #      lics_license_get

        def check_resp(resp):
            self.assertIsInstance(resp, dict)

            self.assertIn("licenses", resp)
            self.assertIsInstance(resp["licenses"], list)

            for lic in resp["licenses"]:
                self.assertIsInstance(lic, dict)

                for key in lic:
                    self.assertIn(
                        key,
                        [
                            "token",
                            "name",
                            "scope",
                            "created",
                            "until",
                            "last_used",
                            "last_failed",
                            "active",
                            "uses",
                            "limit",
                            "failed_attempts",
                        ],
                    )

                self.assertIsInstance(lic["token"], str)
                self.assertTrue(re.fullmatch(self._re_uuid4, lic["token"]))
                self.assertIsInstance(lic["name"], str)
                self.assertIsInstance(lic["scope"], type([]))
                self.assertIsInstance(lic["created"], str)
                datetime.datetime.fromisoformat(lic["created"])
                self.assertIsInstance(lic["until"], str)
                datetime.datetime.fromisoformat(lic["until"])
                self.assertIsInstance(lic["last_used"], str)
                datetime.datetime.fromisoformat(lic["last_used"])
                self.assertIsInstance(lic["last_failed"], str)
                datetime.datetime.fromisoformat(lic["last_failed"])
                self.assertIsInstance(lic["active"], bool)
                self.assertIsInstance(lic["uses"], float)
                self.assertGreaterEqual(lic["uses"], 0)
                self.assertIsInstance(lic["limit"], float)
                self.assertGreaterEqual(lic["limit"], 0)
                self.assertIsInstance(lic["failed_attempts"], int)
                self.assertGreaterEqual(lic["failed_attempts"], 0)

            self.assertIn("paging", resp)
            self.assertIsInstance(resp["paging"], dict)

            for key in resp["paging"]:
                self.assertIn(key, ["count", "items_per_page", "next", "previous"])

        # Without filters.
        resp = self._client.query().lics.licenses.get()
        check_resp(resp)

        # Filtering number of items per page.
        resp = self._client.query().lics.licenses.post({"items_per_page": 1})

        check_resp(resp)

        lic = resp["licenses"][0]

        if "next" not in resp["paging"]:
            return

        token = resp["paging"]["next"].split("/")[-1]

        resp = self._client.query().lics.licenses.next(token).get()

        check_resp(resp)

        self.assertIn("previous", resp["paging"])

        token = resp["paging"]["previous"].split("/")[-1]

        resp = self._client.query().lics.licenses.previous(token).get()

        check_resp(resp)

        self.assertEqual(resp["licenses"][0], lic)

        resp = self._client.query().lics.license(lic["token"]).get()

        self.assertEqual(resp, lic)


if __name__ == "__main__":
    unittest.main()
