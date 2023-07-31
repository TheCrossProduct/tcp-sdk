import unittest
import tcp
import re

class AppTestCase (unittest.TestCase):

    def setUp (self):

        import os

        self._test_account = os.environ["TCP_TEST_ACCOUNT"]
        self._test_passwd = os.environ["TCP_TEST_PASSWD"]

        self._client = tcp.client (usermail=self._test_account, passwd= self._test_passwd)

        self._re_uuid4 = "^[0-9a-f]{8}\-[0-9a-f]{4}\-4[0-9a-f]{3}\-[89ab][0-9a-f]{3}\-[0-9a-f]{12}$"
        self._re_datetime = "^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[ ]+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[ ]+([1-9]|[1-2][0-9]|3[0-1])[ ]+([0-1][0-9]|2[0-4]):([0-5][0-9]|60):([0-5][0-9]|60)[ ]+[0-9]{4}$"
        self._re_ip = "^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.){3}(25[0-5]|(2[0-4]|1\d|[1-9]|)\d)$"
        self._re_usr = "^[a-z_]([a-z0-9_-]{0,31}|[a-z0-9_-]{0,30}\$)$"
        self._re_path = "^([^ !$`&*()+]|(\\[ !$`&*()+]))+$"
        self._re_mem = "^[1-9][0-9]{0,32}(|b|Kb|Mb|Gb|Tb|Pb)$"
        self._re_remote_cp = "^(scw|aws):[a-zA-Z0-9_-]+:[\.a-zA-Z0-9_-]+$"

    def test_get (self):
        resp = self._client.query().app.get()

        assert isinstance (resp, dict)

        for key in resp:
            assert isinstance (resp[key], list)
            for el in resp[key]:
                assert isinstance (el, str)

    def test_list_Process_get (self):

        resp = self._client.query().app.list.Process.get() 

        assert isinstance (resp, list)

        for el in resp:

            for key in el:
                assert key in ['id', 
                               'user_id', 
                               'app',
                               'domain',
                               'endpoint',
                               'launched',
                               'terminated',
                               'expires',
                               'state']

            assert isinstance (el, dict) 
            assert isinstance (el['id'], str)
            assert re.fullmatch (self._re_uuid4, el['id'])
            assert isinstance (el['user_id'], str)
            assert re.fullmatch (self._re_uuid4, el['user_id'])
            assert isinstance (el['app'], str)
            assert isinstance (el['domain'], str)
            assert isinstance (el['endpoint'], str)
            assert el['endpoint'] in ['run', 'quotation']
            assert isinstance (el['launched'], str)
            assert re.fullmatch (self._re_datetime, el['launched'])
            assert isinstance (el['terminated'], str)
            assert re.fullmatch (self._re_datetime, el['terminated'])
            assert isinstance (el['expires'], str)
            assert re.fullmatch (self._re_datetime, el['expires'])
            assert isinstance (el['state'], str)

    def test_list_Instance_get (self):

        resp = self._client.query().app.list.Instance.get() 

        assert isinstance (resp, list)

        for el in resp:

            for key in el:
                assert key in ['id', 
                               'ext_id', 
                               'user_id', 
                               'process_id',
                               'launched',
                               'expires',
                               'state',
                               'ip',
                               'ssh_usr',
                               'input_path',
                               'working_path',
                               'output_path',
                               'num_cores',
                               'mem_required',
                               'ram_required']

            assert isinstance (el, dict) 
            assert isinstance (el['id'], str)
            assert re.fullmatch (self._re_uuid4, el['id'])
            assert isinstance (el['ext_id'], str)
            assert re.fullmatch (self._re_uuid4, el['ext_id'])
            assert isinstance (el['user_id'], str)
            assert re.fullmatch (self._re_uuid4, el['user_id'])
            assert isinstance (el['process_id'], str)
            assert re.fullmatch (self._re_uuid4, el['process_id'])
            assert isinstance (el['launched'], str)
            assert re.fullmatch (self._re_datetime, el['launched'])
            assert isinstance (el['expires'], str)
            assert re.fullmatch (self._re_datetime, el['expires'])
            assert isinstance (el['state'], str)
            assert isinstance (el['ip'], str) 
            assert re.fullmatch (self._re_ip, el['ip'])
            assert isinstance (el['ssh_usr'], str)
            assert re.fullmatch (self._re_usr, el['ssh_usr'])
            assert isinstance (el['input_path'], str)
            assert re.fullmatch (self._re_path, el['input_path'])
            assert isinstance (el['working_path'], str)
            assert re.fullmatch (self._re_path, el['working_path'])
            assert isinstance (el['output_path'], str)
            assert re.fullmatch (self._re_path, el['output_path'])
            assert isinstance (el['num_cores'], int)
            assert el['num_cores'] > 0
            assert isinstance (el['mem_required'], int)
            assert el['mem_required'] >= 0
            assert isinstance (el['ram_required'], int)
            assert el['ram_required'] >= 0

    def test_list_Remote_get (self):

        resp = self._client.query().app.list.Remote.get() 

        assert isinstance (resp, list)

        for el in resp:

            for key in el:
                assert key in ['id', 
                               'name', 
                               'user_id', 
                               'ip',
                               'usr',
                               'num_cores',
                               'mem',
                               'ram',
                               'input_path',
                               'working_path',
                               'output_path',
                               'instanciated']

            assert isinstance (el, dict) 
            assert isinstance (el['id'], str)
            assert re.fullmatch (self._re_uuid4, el['id'])
            assert isinstance (el['user_id'], str)
            assert re.fullmatch (self._re_uuid4, el['user_id'])
            assert isinstance (el['ip'], str) 
            assert re.fullmatch (self._re_ip, el['ip'])
            assert isinstance (el['usr'], str)
            assert re.fullmatch (self._re_usr, el['usr'])
            assert isinstance (el['num_cores'], int)
            assert el['num_cores'] > 0
            assert isinstance (el['mem'], int)
            assert el['mem'] >= 0
            assert isinstance (el['ram'], int)
            assert el['ram'] >= 0
            assert isinstance (el['input_path'], str)
            assert re.fullmatch (self._re_path, el['input_path'])
            assert isinstance (el['working_path'], str)
            assert re.fullmatch (self._re_path, el['working_path'])
            assert isinstance (el['output_path'], str)
            assert re.fullmatch (self._re_path, el['output_path'])
            assert isinstance (el['instanciated'], bool)

    def test_list_PostMortem_get (self):

        resp = self._client.query().app.list.PostMortem.get() 

        assert isinstance (resp, list)

        for el in resp:

            for key in el:
                assert key in ['id', 
                               'ext_id', 
                               'user_id', 
                               'process_id',
                               'launched',
                               'terminated',
                               'state',
                               'num_cores',
                               'mem',
                               'ram']

            assert isinstance (el, dict) 
            assert isinstance (el['id'], str)
            assert re.fullmatch (self._re_uuid4, el['id'])
            assert isinstance (el['ext_id'], str)
            assert re.fullmatch (self._re_uuid4, el['ext_id'])
            assert isinstance (el['user_id'], str)
            assert re.fullmatch (self._re_uuid4, el['user_id'])
            assert isinstance (el['process_id'], str)
            assert re.fullmatch (self._re_uuid4, el['process_id'])
            assert isinstance (el['launched'], str)
            assert re.fullmatch (self._re_datetime, el['launched'])
            assert isinstance (el['terminated'], str)
            assert re.fullmatch (self._re_datetime, el['terminated'])
            assert isinstance (el['state'], str)
            assert isinstance (el['num_cores'], int)
            assert el['num_cores'] > 0
            assert isinstance (el['mem'], int)
            assert el['mem'] >= 0
            assert isinstance (el['ram'], int)
            assert el['ram'] >= 0

    def test_remote_create_get_delete (self):
      
        import uuid

        first = 'test_remote_'+str(uuid.uuid4()).replace ('-','_')
        second = 'test_remote_'+str(uuid.uuid4()).replace ('-','_')


        body = {
                "name": first,
                "ip": "127.0.0.1",
                "usr": "test_user",
                "mem": "10Gb",
                "ram": "10Gb",
                "num_cores" : 1,
                "input_path": "/home/test_user/data/input",
                "working_path": "/home/test_user/data/working",
                "output_path": "/home/test_user/data/output"
            }

        resp = self._client.query().app.new_remote.post (body)

        assert isinstance (resp, dict)
        for key in resp:
            assert key in ['id', 'pub']

        assert isinstance (resp['id'], str)
        assert re.fullmatch ("^remote:"+self.re_uuid4[1:], resp['id'])
        assert isinstance (resp['pub'], str)
        assert re.fullmatch ("^ssh-ed25519 [a-Az-Z1-9]+$")

        body['name'] = second 
        body['num_cores'] = 2

        resp = self._client.query().app.new_remote.post (body)

        assert isinstance (resp, dict)
        for key in resp:
            assert key in ['id', 'pub']

        assert isinstance (resp['id'], str)
        assert re.fullmatch ("^remote:"+self.re_uuid4[1:], resp['id'])
        assert isinstance (resp['pub'], str)
        assert re.fullmatch ("^ssh-ed25519 [a-Az-Z1-9]+$")

        resp = self._client.query().app.remote.get ()

        assert isinstance (resp, dict)

        for remote_name in [first, second]:
            assert remote_name in resp
            assert isinstance(resp[remote_name], dict)

            remote = resp[remote_name]
    
            for key in remote:
                assert key in ['id', 'num_cores', 'mem', 'ram', 'instanciated']
    
            assert isinstance (remote['id'], str)
            assert re.fullmatch(self._re_uuid4, remote['id'])
            assert isinstance (remote['num_cores'], int)
            assert remote['num_cores'] > 0
            assert isinstance (remote['mem'], str)
            assert re.fullmatch(self._re_mem, remote['mem'])
            assert isinstance (remote['ram'], str)
            assert re.fullmatch(self._re_mem, remote['ram'])
            assert isinstance (remote['instanciated'], bool)
            assert not remote['instanciated']

        resp = self._client.query().app.remote.post({"cores":2})

        assert first not in resp
        assert second in resp

        assert self._client.query().app.remote(first).delete ()
        assert self._client.query().app.remote(second).delete ()

    def test_remote_cp_get_post (self):

        resp = self._client.query().app.remote("scw").get ()

        assert isinstance(resp, dict)

        # Asserting only the first tenth elements
        max_element = min (len(resp), 10)
        keys = list(resp.keys())[:max_element]
        remotes = {}
        for ii in range(max_element):
            remotes[keys[ii]] = resp[keys[ii]]

        for key in remotes:
            remote = remotes[key]
            assert re.fullmatch (self._re_remote_cp, key)
            assert isinstance (remote, dict)
            for kk in remote:
                assert kk in ['cp', 'price', 'ram', 'cores']
            assert remote['cp'] in ['scw', 'aws']
            assert isinstance(remote['price'], dict)
            for key in remote['price']:
                assert key in ["AUD",
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
                               "USD"]
                assert isinstance (remote['price'][key], float)
            assert isinstance(remote['ram'], str)
            assert re.fullmatch (self._re_mem, remote['ram'])
            assert isinstance(remote['cores'], int)            
            assert remote['cores'] > 0

    def test_datacenters_get_post (self):

        resp = self._client.query().app.datacenters("scw").get ()

        assert isinstance (resp, list)
        for el in resp:
            assert isinstance (el, str)

        for dc in ["fr-par-1",
                   "fr-par-2",
                   "fr-par-3",
                   "nl-ams-1",
                   "nl-ams-2",
                   "pl-waw-1",
                   "pl-waw-2"]:

            assert dc in resp

    def test_info_get (self):

        try:
            resp = self._client.query().app.info.get(Domain="test", App="helloworld")
        except tcp.exceptions.HttpClientError as err:
            print (err.response.text)

        assert isinstance (resp, bytes)

    def test_process (self):

        body = {
                "inputs": {},
                "output-prefix": "test",
                "pool": ["scw:fr-par-1:PLAY2-PICO"]
            }

        resp = self._client.query().app.run.post(body, Domain="test", App="helloworld")

        assert isinstance (resp, dict)
        assert len(resp) == 1
        assert 'id' in resp
        assert isinstance (resp['id'], str)
        assert re.fullmatch (self._re_uuid4, resp['id'])

        puid = resp['id']

        # Should be a process in the process list
        self.test_list_Process_get ()

        def check_status ():

            resp = self._client.query().app.status (Process=puid).get ()

            assert isinstance (resp, dict)
            for key in resp:
                assert key in ['user_id',
                               'app',
                               'domain',
                               'endpoint',
                               'id',
                               'launched',
                               'terminated',
                               'expires',
                               'state',
                               'outputs']
    
            assert isinstance (resp['user_id'], str)
            assert re.fullmatch (self._re_uuid4, resp['user_id'])
            assert resp['app'] == 'helloworld'
            assert resp['domain'] == 'test'
            assert resp['endpoint'] == 'run'
            assert isinstance (resp['id'], str)
            assert re.fullmatch (self._re_uuid4, resp['id'])
            assert isinstance (resp['launched'], str)
            assert re.fullmatch (self._re_datetime, resp['launched'])
            assert isinstance (resp['terminated'], str)
            assert re.fullmatch (self._re_datetime, resp['terminated'])
            assert isinstance (resp['expires'], str)
            assert re.fullmatch (self._re_datetime, resp['expires'])
            assert isinstance (resp['state'], str)
            assert resp['state'] in ['say_hello', 'upload', 'pending', 'waiting', 'dead', 'terminated']
            assert isinstance (resp['outputs'], dict)

            if resp['outputs']:
                for key in resp['outputs']:
                    assert isinstance (resp[key], str)

       
            return resp

        import sleep

        status = "None"
        num_tries, num_tries_max = 0, 10
        sleep_duration = 10

        while status != "dead":

            if num_tries == num_tries_max:
                break

            num_tries += 1

            time.sleep (sleep_duration)

            status = check_status ()

        resp = self._client.query().app.status (Process=puid).get ()

        assert resp['state'] == 'dead'

        assert 'test/msg-test.txt' in resp['outputs']

        resp = self._client.query().app.cost (Process=puid).get ()

        assert isinstance (resp, dict)
        assert len(resp) == 1
        assert 'cost' in resp
        assert isinstance (resp['cost'], float)
        assert resp['cost'] < 1.0

if __name__ == '__main__':
    unittest.main()
