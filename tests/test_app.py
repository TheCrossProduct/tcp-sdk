import datetime
import unittest
import tcp
import re


class AppTestCase(unittest.TestCase):
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
        self._re_ip = (
            "^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.){3}(25[0-5]|(2[0-4]|1\d|[1-9]|)\d)$"
        )
        self._re_usr = "^[a-z_]([a-z0-9_-]{0,31}|[a-z0-9_-]{0,30}\$)$"
        self._re_path = "^([^ !$`&*()+]|(\\[ !$`&*()+]))+$"
        self._re_mem = "^[1-9][0-9]{0,32}(|.[0-9]+)(|b|Kb|Mb|Gb|Tb|Pb)$"
        self._re_remote_cp = "^(scw|aws):[a-zA-Z0-9_-]+:[\.a-zA-Z0-9_-]+$"
        self._re_remote_id = (
            "^(scw|aws):[a-zA-Z0-9_-]+:[\.a-zA-Z0-9_-]+:[\.a-zA-Z0-9_-]+$"
        )
        self._re_instance_id = "^[0-9]+\-[0-9a-f]{8}\-[0-9a-f]{4}\-4[0-9a-f]{3}\-[89ab][0-9a-f]{3}\-[0-9a-f]{12}$"

    def tearDown(self):
        self._client.query().auth.logout.get()

    def test_z_endpoints_coverage(self):
        uses = tcp.track_usage.TrackUsage().uses
        untested = [x for x in uses if uses[x] == 0 and x.startswith("^\/app")]
        self.assertListEqual(untested, [], "Those endpoints remains untested")

    def test_get(self):
        resp = self._client.query().app.get()

        self.assertIsInstance(resp, dict)

        for key in resp:
            self.assertIsInstance(resp[key], list)
            for el in resp[key]:
                self.assertIsInstance(el, str)

    def test_get_inputs(self):
        resp = self._client.query().app.test.helloworld.inputs.get()
        self.assertIsInstance(resp, dict)

    def test_processes_get(self):
        resp = self._client.query().app.processes.get()

        if not resp:
            return

        self.assertIsInstance(resp, dict)

        assert "processes" in resp
        self.assertIsInstance(resp["processes"], list)

        for el in resp["processes"]:
            for key in el:
                self.assertIn(
                    key,
                    [
                        "id",
                        "app",
                        "domain",
                        "endpoint",
                        "launched",
                        "terminated",
                        "expires",
                        "body",
                        "state",
                        "quote",
                        "errors",
                        "agent",
                        "tags",
                    ],
                )

            self.assertIsInstance(el, dict)
            self.assertIsInstance(el["id"], str)
            assert re.fullmatch(self._re_uuid4, el["id"])
            self.assertIsInstance(el["app"], str)
            self.assertIsInstance(el["domain"], str)
            self.assertIsInstance(el["endpoint"], str)
            self.assertIn(el["endpoint"], ["run", "test", "quotation"])
            self.assertIsInstance(el["launched"], str)
            datetime.datetime.fromisoformat(el["launched"])
            self.assertIsInstance(el["terminated"], str)
            datetime.datetime.fromisoformat(el["terminated"])
            self.assertIsInstance(el["expires"], str)
            datetime.datetime.fromisoformat(el["expires"])
            self.assertIsInstance(el["body"], dict)
            self.assertIsInstance(el["state"], str)

    def test_instances_get(self):
        resp = self._client.query().app.instances.get()

        if not resp:
            return

        self.assertIsInstance(resp, dict)

        assert "instances" in resp
        self.assertIsInstance(resp["instances"], list)

        for el in resp["instances"]:
            for key in el:
                self.assertIn(
                    key,
                    [
                        "id",
                        "ext_id",
                        "process_id",
                        "pool",
                        "launched",
                        "expires",
                        "state",
                        "ip",
                        "ssh_usr",
                        "input_path",
                        "working_path",
                        "output_path",
                        "num_cores",
                        "mem_required",
                        "ram_required",
                    ],
                )

            self.assertIsInstance(el, dict)
            self.assertIsInstance(el["id"], str)
            assert re.fullmatch(self._re_instance_id, el["id"])
            self.assertIsInstance(el["ext_id"], str)
            assert (
                re.fullmatch("^remote:" + self._re_uuid4[1:], el["ext_id"])
                or re.fullmatch(self._re_remote_id, el["ext_id"])
                or not el["ext_id"]
            )
            self.assertIsInstance(el["process_id"], str)
            assert re.fullmatch(self._re_uuid4, el["process_id"])
            self.assertIsInstance(el["launched"], str)
            datetime.datetime.fromisoformat(el["launched"])
            self.assertIsInstance(el["pool"], type([]))
            self.assertIsInstance(el["expires"], str)
            datetime.datetime.fromisoformat(el["expires"])
            self.assertIsInstance(el["state"], str)
            self.assertIsInstance(el["ip"], str)
            assert re.fullmatch(self._re_ip, el["ip"]) or not el["ip"]
            self.assertIsInstance(el["ssh_usr"], str)
            assert re.fullmatch(self._re_usr, el["ssh_usr"]) or not el["ssh_usr"]
            self.assertIsInstance(el["input_path"], str)
            assert re.fullmatch(self._re_path, el["input_path"]) or not el["input_path"]
            self.assertIsInstance(el["working_path"], str)
            assert (
                re.fullmatch(self._re_path, el["working_path"])
                or not el["working_path"]
            )
            self.assertIsInstance(el["output_path"], str)
            assert (
                re.fullmatch(self._re_path, el["output_path"]) or not el["output_path"]
            )
            self.assertIsInstance(el["num_cores"], int)
            assert el["num_cores"] > 0
            self.assertIsInstance(el["mem_required"], str)
            self.assertIsInstance(el["ram_required"], str)

    def test_remotes_get(self):
        resp = self._client.query().app.remotes.get()

        if not resp:
            return

        self.assertIsInstance(resp, dict)

        assert "remotes" in resp
        self.assertIsInstance(resp["remotes"], list)

        for el in resp["remotes"]:
            for key in el:
                self.assertIn(
                    key,
                    [
                        "id",
                        "name",
                        "ip",
                        "usr",
                        "num_cores",
                        "mem",
                        "ram",
                        "input_path",
                        "working_path",
                        "output_path",
                        "instanciated",
                    ],
                )

            self.assertIsInstance(el, dict)
            self.assertIsInstance(el["id"], str)
            assert re.fullmatch(
                "^remote:" + self._re_uuid4[1:], el["id"]
            ) or re.fullmatch(self._re_remote_id, el["id"])
            self.assertIsInstance(el["ip"], str)
            assert re.fullmatch(self._re_ip, el["ip"])
            self.assertIsInstance(el["usr"], str)
            assert re.fullmatch(self._re_usr, el["usr"])
            self.assertIsInstance(el["num_cores"], int)
            self.assertGreater(el["num_cores"], 0)
            self.assertIsInstance(el["mem"], str)
            self.assertIsInstance(el["ram"], str)
            self.assertIsInstance(el["input_path"], str)
            assert re.fullmatch(self._re_path, el["input_path"])
            self.assertIsInstance(el["working_path"], str)
            assert re.fullmatch(self._re_path, el["working_path"])
            self.assertIsInstance(el["output_path"], str)
            assert re.fullmatch(self._re_path, el["output_path"])
            self.assertIsInstance(el["instanciated"], bool)

    def test_postmortems_get(self):
        resp = self._client.query().app.postmortems.get()

        if not resp:
            return

        self.assertIsInstance(resp, dict)

        assert "postmortems" in resp
        self.assertIsInstance(resp["postmortems"], list)

        for el in resp["postmortems"]:
            for key in el:
                self.assertIn(
                    key,
                    [
                        "id",
                        "ext_id",
                        "process_id",
                        "launched",
                        "terminated",
                        "state",
                        "num_cores",
                        "mem",
                        "ram",
                    ],
                )

            self.assertIsInstance(el, dict)
            self.assertIsInstance(el["id"], str)
            assert re.fullmatch(self._re_instance_id, el["id"])
            self.assertIsInstance(el["ext_id"], str)
            assert (
                re.fullmatch("^remote:" + self._re_uuid4[1:], el["ext_id"])
                or re.fullmatch(self._re_remote_id, el["ext_id"])
            ) or el["ext_id"] == ""
            self.assertIsInstance(el["process_id"], str)
            assert re.fullmatch(self._re_uuid4, el["process_id"])
            self.assertIsInstance(el["launched"], str)
            datetime.datetime.fromisoformat(el["launched"])
            self.assertIsInstance(el["terminated"], str)
            datetime.datetime.fromisoformat(el["terminated"])
            self.assertIsInstance(el["state"], str)
            self.assertIsInstance(el["num_cores"], int)
            self.assertGreater(el["num_cores"], 0)
            self.assertIsInstance(el["mem"], str)
            self.assertIsInstance(el["ram"], str)

    def test_remote_create_get_delete(self):
        import uuid

        first = "test_remote_" + str(uuid.uuid4()).replace("-", "_")
        second = "test_remote_" + str(uuid.uuid4()).replace("-", "_")

        ids = []

        for ii, name in enumerate([first, second]):
            body = {
                "name": name,
                "ip": "127.0.0.1",
                "usr": "test_user",
                "mem": "10Gb",
                "ram": "10Gb",
                "num_cores": ii + 1,
                "input_path": "/home/test_user/data/input",
                "working_path": "/home/test_user/data/working",
                "output_path": "/home/test_user/data/output",
            }

            resp = self._client.query().app.remote.post(body)

            self.assertIsInstance(resp, dict)
            for key in resp:
                self.assertIn(key, ["id", "pub"])

            self.assertIsInstance(resp["id"], str)
            assert re.fullmatch("^remote:" + self._re_uuid4[1:], resp["id"])
            self.assertIsInstance(resp["pub"], str)
            assert re.fullmatch("^ssh-ed25519 [a-zA-Z0-9\/+]+$", resp["pub"])

            ids.append(resp["id"])

        resp = self._client.query().app.remotes.get()

        self.assertIsInstance(resp, dict)

        for remote_id in ids:
            resp = self._client.query().app.remote(remote_id).get()
            remote = resp

            for key in remote:
                self.assertIn(
                    key,
                    [
                        "id",
                        "name",
                        "ip",
                        "usr",
                        "input_path",
                        "working_path",
                        "output_path",
                        "num_cores",
                        "mem",
                        "ram",
                        "instanciated",
                    ],
                )

            self.assertIsInstance(remote["id"], str)
            assert re.fullmatch("^remote:" + self._re_uuid4[1:], remote["id"])
            self.assertIsInstance(remote["num_cores"], int)
            assert remote["num_cores"] > 0
            self.assertIsInstance(remote["mem"], str)
            assert re.fullmatch(self._re_mem, remote["mem"])
            self.assertIsInstance(remote["ram"], str)
            assert re.fullmatch(self._re_mem, remote["ram"])
            self.assertIsInstance(remote["instanciated"], bool)
            self.assertFalse(remote["instanciated"])

        resp = [
            xx["name"]
            for xx in self._client.query().app.remotes.post({"num_cores": 2})["remotes"]
        ]

        self.assertNotIn(first, resp)
        self.assertIn(second, resp)

        # delete by name
        self.assertTrue(self._client.query().app.remote(first).delete())
        # delete by id
        self.assertTrue(self._client.query().app.remote(ids[1]).delete())

        resp = self._client.query().app.remotes.get()["remotes"]

        self.assertNotIn(first, resp)
        self.assertNotIn(second, resp)

    def check_remote_cp_get_post(self, cloud_providor, creds=None):
        if not creds:
            resp = self._client.query().app.remotes(cloud_providor).get()
        else:
            resp = self._client.query().app.remotes(cloud_providor).post(creds)

        self.assertIsInstance(resp, dict)

        # Asserting only the first tenth elements
        max_element = min(len(resp), 10)
        keys = list(resp.keys())[:max_element]
        remotes = {}
        for ii in range(max_element):
            remotes[keys[ii]] = resp[keys[ii]]

        for key in remotes:
            remote = remotes[key]
            assert re.fullmatch(self._re_remote_cp, key)
            self.assertIsInstance(remote, dict)
            for kk in remote:
                assert kk in ["cp", "price", "ram", "cores"]
            assert remote["cp"] in ["scw", "aws"]
            self.assertIsInstance(remote["price"], dict)
            for key in remote["price"]:
                self.assertIn(
                    key,
                    [
                        "AUD",
                        "BRL",
                        "BGN",
                        "CAD",
                        "CNY",
                        "HRK",
                        "CYP",
                        "CZK",
                        "DKK",
                        "EEK",
                        "EUR",
                        "HKD",
                        "HUF",
                        "ISK",
                        "IDR",
                        "JPY",
                        "KRW",
                        "LVL",
                        "LTL",
                        "MYR",
                        "MTL",
                        "NZD",
                        "NOK",
                        "PHP",
                        "PLN",
                        "RON",
                        "RUB",
                        "SGD",
                        "SKK",
                        "SIT",
                        "ZAR",
                        "SEK",
                        "CHF",
                        "THB",
                        "TRY",
                        "GBP",
                        "USD",
                    ],
                )
                self.assertIsInstance(remote["price"][key], float)
            self.assertIsInstance(remote["ram"], str)
            assert re.fullmatch(self._re_mem, remote["ram"])
            self.assertIsInstance(remote["cores"], int)
            self.assertGreater(remote["cores"], 0)

    def test_remote_scw_get_post(self):
        return self.check_remote_cp_get_post("scw")

    def test_remote_aws_get_post(self):
        import os

        if "AWS_ACCESS_KEY_ID" not in os.environ:
            return

        for field in [
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "AWS_S3_BUCKET",
            "AWS_REGION",
        ]:
            self.assertIn(field, os.environ)

        creds = {
            "aws": {
                "access_key_id": os.environ["AWS_ACCESS_KEY_ID"],
                "secret_access_key": os.environ["AWS_SECRET_ACCESS_KEY"],
                "s3_bucket": os.environ["AWS_S3_BUCKET"],
            }
        }

        return self.check_remote_cp_get_post("aws", creds)

    def test_datacenters_get_post(self):
        resp = self._client.query().app.datacenters("scw").get()

        self.assertIsInstance(resp, dict)
        self.assertIn("datacenters", resp)
        self.assertIsInstance(resp["datacenters"], list)

        for el in resp["datacenters"]:
            self.assertIsInstance(el, str)

        for dc in [
            "fr-par-1",
            "fr-par-2",
            "fr-par-3",
            "nl-ams-1",
            "nl-ams-2",
            "pl-waw-1",
            "pl-waw-2",
        ]:
            self.assertIn(dc, resp["datacenters"])

    def test_info_get(self):
        resp = self._client.query().app.test.helloworld.get()

        self.assertIsInstance(resp, str)

    def process(self, body):
        resp = self._client.query().app.test.helloworld.run.post(body)

        self.assertIsInstance(resp, dict)
        self.assertEqual(len(resp), 1)
        self.assertIn("id", resp)
        self.assertIsInstance(resp["id"], str)
        assert re.fullmatch(self._re_uuid4, resp["id"])

        puid = resp["id"]

        # Should be a process in the process list. We can test it
        self.test_processes_get()

        def check_status():
            resp = self._client.query().app.process(puid).get()

            self.assertIsInstance(resp, dict)
            for key in resp:
                self.assertIn(
                    key,
                    [
                        "app",
                        "domain",
                        "endpoint",
                        "id",
                        "launched",
                        "terminated",
                        "expires",
                        "body",
                        "state",
                        "outputs",
                        "metrics",
                        "quote",
                        "agent",
                        "errors",
                        "tags",
                    ],
                )

            self.assertEqual(resp["app"], "helloworld")
            self.assertEqual(resp["domain"], "test")
            self.assertEqual(resp["endpoint"], "run")
            self.assertIsInstance(resp["id"], str)
            assert re.fullmatch(self._re_uuid4, resp["id"])
            self.assertIsInstance(resp["launched"], str)
            datetime.datetime.fromisoformat(resp["launched"])
            self.assertIsInstance(resp["terminated"], str)
            datetime.datetime.fromisoformat(resp["terminated"])
            self.assertIsInstance(resp["expires"], str)
            datetime.datetime.fromisoformat(resp["expires"])
            self.assertIsInstance(resp["state"], str)
            self.assertIsInstance(resp["agent"], str)

            self.assertIn(
                resp["state"],
                ["say_hello", "upload", "pending", "waiting", "dead", "terminated"],
            )

            if "metrics" in resp:
                for key in resp["metrics"]:
                    self.assertIsInstance(resp["metrics"][key], dict)
                    for subkey in resp["metrics"][key]:
                        self.assertIn(subkey, ["rate", "datetime", "metrics"])
                        if subkey == "rate":
                            self.assertIsInstance(resp["metrics"][key]["rate"], int)
                        if subkey == "datetime":
                            datetime.datetime.fromisoformat(
                                resp["metrics"][key]["datetime"]
                            )
                        if subkey == "metrics":
                            self.assertIsInstance(resp["metrics"][key]["metrics"], list)
                            for item in resp["metrics"][key]["metrics"]:
                                self.assertIsInstance(item, list)
                                self.assertEqual(len(item), 2)
                                self.assertIsInstance(item[0], int) and isinstance(
                                    item[1], int
                                )

            if "quote" in resp:
                self.assertIsInstance(resp["quote"], float)

            if "errors" in resp:
                self.assertIsInstance(resp["errors"], str)

            return resp["state"]

        def check_outputs():
            resp = self._client.query().app.process.outputs(puid).get()
            time.sleep(1)
            resp = self._client.query().app.process.outputs(puid).get()

            self.assertIsInstance(resp, dict)
            for key in resp:
                self.assertIn(key, ["paging", "outputs"])

            if "outputs" in resp:
                self.assertIsInstance(resp["outputs"], list)
                for oo in resp["outputs"]:
                    self.assertIn("key", oo)
                    self.assertIn("url", oo)
                    self.assertIsInstance(oo["key"], str)
                    self.assertIsInstance(oo["url"], str)
                    assert oo["url"].startswith("https://")
                    assert "s3" in oo["url"]

        import time

        status = "None"
        num_tries, num_tries_max = 0, 60
        sleep_duration = 10

        while status != "dead":
            if num_tries == num_tries_max:
                break

            num_tries += 1

            time.sleep(sleep_duration)

            status = check_status()

        resp = self._client.query().app.process(puid).get()

        self.assertEqual(resp["state"], "dead")

        check_outputs()

        resp = self._client.query().app.process.cost(puid).get()

        self.assertIsInstance(resp, dict)
        self.assertEqual(len(resp), 1)
        self.assertIn("cost", resp)
        self.assertIsInstance(resp["cost"], float)
        self.assertLess(resp["cost"], 1.0)

    def test_scaleway_process(self):
        pool = ["scw:fr-par-1:PLAY2-PICO"]
        body = {"inputs": {}, "output-prefix": "test", "pool": pool}

        self.process(body)


##    def test_aws_process (self):
##
##        import os
##
##        for field in ["AWS_ACCESS_KEY_ID",
##                      "AWS_SECRET_ACCESS_KEY",
##                      "AWS_S3_BUCKET",
##                      "AWS_REGION"]:
##            self.assertIn(field, os.environ)
##
##        creds = {
##            "aws": {
##                "access_key_id": os.environ["AWS_ACCESS_KEY_ID"],
##                "secret_access_key": os.environ["AWS_SECRET_ACCESS_KEY"],
##                "s3_bucket": os.environ["AWS_S3_BUCKET"],
##                "region": os.environ["AWS_REGION"]
##                }
##            }
##
##        pool = [
##                "aws:{}:t2.micro".format(os.environ["AWS_REGION"])
##            ]
##
##        body = {
##                "inputs": {},
##                "output-prefix": "s3://test",
##                "pool": pool,
##                "creds": creds
##            }
##
##        self.process (body)

if __name__ == "__main__":
    unittest.main()
