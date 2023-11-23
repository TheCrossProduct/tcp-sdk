import datetime
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
        self._re_ip = "^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.){3}(25[0-5]|(2[0-4]|1\d|[1-9]|)\d)$"
        self._re_usr = "^[a-z_]([a-z0-9_-]{0,31}|[a-z0-9_-]{0,30}\$)$"
        self._re_path = "^([^ !$`&*()+]|(\\[ !$`&*()+]))+$"
        self._re_mem = "^[1-9][0-9]{0,32}(|.[0-9]+)(|b|Kb|Mb|Gb|Tb|Pb)$"
        self._re_remote_cp = "^(scw|aws):[a-zA-Z0-9_-]+:[\.a-zA-Z0-9_-]+$"
        self._re_remote_id = "^(scw|aws):[a-zA-Z0-9_-]+:[\.a-zA-Z0-9_-]+:[\.a-zA-Z0-9_-]+$"

    def test_get (self):
        resp = self._client.query().app.get()

        assert isinstance (resp, dict)

        for key in resp:
            assert isinstance (resp[key], list)
            for el in resp[key]:
                assert isinstance (el, str)

    def test_list_Process_get (self):

        resp = self._client.query().app.process.get() 

        assert isinstance (resp, dict)

        if not resp:
            return

        assert 'processes' in resp
        assert isinstance (resp['processes'], list)

        for el in resp['processes']:

            for key in el:
                assert key in ['id', 
                               'app',
                               'domain',
                               'endpoint',
                               'launched',
                               'terminated',
                               'expires',
                               'body',
                               'state',
                               'agent']

            assert isinstance (el, dict) 
            assert isinstance (el['id'], str)
            assert re.fullmatch (self._re_uuid4, el['id'])
            assert isinstance (el['user_id'], str)
            assert re.fullmatch (self._re_uuid4, el['user_id'])
            assert isinstance (el['app'], str)
            assert isinstance (el['domain'], str)
            assert isinstance (el['endpoint'], str)
            assert el['endpoint'] in ['run', 'test', 'quotation']
            assert isinstance (el['launched'], str)
            datetime.datetime.fromisoformat (el['launched'])
            assert isinstance (el['terminated'], str)
            datetime.datetime.fromisoformat (el['terminated'])
            assert isinstance (el['expires'], str)
            datetime.datetime.fromisoformat (el['expires'])
            assert isinstance (el['body'], dict)
            assert isinstance (el['state'], str)
            assert isinstance (el['agent'], str)

    def test_list_Instance_get (self):

        resp = self._client.query().app.instance.get() 

        assert isinstance (resp, dict)

        if not resp:
            return

        assert 'instances' in resp
        assert isinstance (resp['instances'], list)

        for el in resp['instances']:

            for key in el:
                assert key in ['id', 
                               'ext_id', 
                               'process_id',
                               'pool',
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
            assert (re.fullmatch ('^remote:'+self._re_uuid4[1:], el['ext_id']) or re.fullmatch(self._re_remote_id, el['ext_id']) or not el['ext_id'])
            assert isinstance (el['user_id'], str)
            assert re.fullmatch (self._re_uuid4, el['user_id'])
            assert isinstance (el['process_id'], str)
            assert re.fullmatch (self._re_uuid4, el['process_id'])
            assert isinstance (el['launched'], str)
            datetime.datetime.fromisoformat (el['launched'])
            assert isinstance (el['expires'], str)
            datetime.datetime.fromisoformat (el['expires'])
            assert isinstance (el['state'], str)
            assert isinstance (el['ip'], str) 
            assert re.fullmatch (self._re_ip, el['ip']) or not el['ip']
            assert isinstance (el['ssh_usr'], str)
            assert re.fullmatch (self._re_usr, el['ssh_usr']) or not el['ssh_usr']
            assert isinstance (el['input_path'], str)
            assert re.fullmatch (self._re_path, el['input_path']) or not el['input_path']
            assert isinstance (el['working_path'], str)
            assert re.fullmatch (self._re_path, el['working_path']) or not el['working_path']
            assert isinstance (el['output_path'], str)
            assert re.fullmatch (self._re_path, el['output_path']) or not el['output_path']
            assert isinstance (el['num_cores'], int)
            assert el['num_cores'] > 0
            assert isinstance (el['mem_required'], int)
            assert el['mem_required'] >= 0
            assert isinstance (el['ram_required'], int)
            assert el['ram_required'] >= 0

    def test_list_Remote_get (self):

        resp = self._client.query().app.remote.get() 

        assert isinstance (resp, dict)

        if not resp:
            return

        assert 'remotes' in resp
        assert isinstance (resp['remotes'], list)

        for el in resp['remotes']:

            for key in el:
                assert key in ['id', 
                               'name', 
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
            assert (re.fullmatch ('^remote:'+self._re_uuid4[1:], el['id']) or re.fullmatch(self._re_remote_id, el['id']))
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

        resp = self._client.query().app.postmortem.get() 

        assert isinstance (resp, dict)

        if not resp:
            return

        assert 'postmortems' in resp
        assert isinstance (resp['postmortems'], list)

        for el in resp['postmortems']:

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
            assert (re.fullmatch ('^remote:'+self._re_uuid4[1:], el['ext_id']) or re.fullmatch(self._re_remote_id, el['ext_id'])) or el['ext_id'] == ''
            assert isinstance (el['user_id'], str)
            assert re.fullmatch (self._re_uuid4, el['user_id'])
            assert isinstance (el['process_id'], str)
            assert re.fullmatch (self._re_uuid4, el['process_id'])
            assert isinstance (el['launched'], str)
            datetime.datetime.fromisoformat (el['launched'])
            assert isinstance (el['terminated'], str)
            datetime.datetime.fromisoformat (el['terminated'])
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

        ids = []

        for ii, name in enumerate([first, second]):

            body = {
                    "name": name,
                    "ip": "127.0.0.1",
                    "usr": "test_user",
                    "mem": "10Gb",
                    "ram": "10Gb",
                    "num_cores" : ii+1,
                    "input_path": "/home/test_user/data/input",
                    "working_path": "/home/test_user/data/working",
                    "output_path": "/home/test_user/data/output"
                }
    
            resp = self._client.query().app.new_remote.post (body)
    
            assert isinstance (resp, dict)
            for key in resp:
                assert key in ['id', 'pub']
    
            assert isinstance (resp['id'], str)
            assert re.fullmatch ("^remote:"+self._re_uuid4[1:], resp['id'])
            assert isinstance (resp['pub'], str)
            assert re.fullmatch ("^ssh-ed25519 [a-zA-Z0-9\/+]+$", resp['pub'])

            ids.append (resp['id'])

        resp = self._client.query().app.remote.get ()

        assert isinstance (resp, dict)

        for remote_name in [first, second]:
            assert remote_name in resp
            assert isinstance(resp[remote_name], dict)

            remote = resp[remote_name]
    
            for key in remote:
                assert key in ['id', 'num_cores', 'mem', 'ram', 'instanciated']
    
            assert isinstance (remote['id'], str)
            assert re.fullmatch("^remote:"+self._re_uuid4[1:], remote['id'])
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

        # delete by name
        assert self._client.query().app.remote(first).delete ()
        # delete by id
        assert self._client.query().app.remote(ids[1]).delete ()

        resp = self._client.query().app.remote.get ()

        assert first not in resp
        assert second not in resp

    def check_remote_cp_get_post (self, cloud_providor, creds=None):

        if not creds:
            resp = self._client.query().app.remote(cloud_providor).get ()
        else:
            resp = self._client.query().app.remote(cloud_providor).post (creds)

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

    def test_remote_scw_get_post (self):
        return self.check_remote_cp_get_post ('scw')

    def test_remote_aws_get_post (self):
        import os 

        for field in ["AWS_ACCESS_KEY_ID",
                      "AWS_SECRET_ACCESS_KEY",
                      "AWS_S3_BUCKET",
                      "AWS_REGION"]:
            assert field in os.environ 

        creds = {
            "aws": {
                "access_key_id": os.environ["AWS_ACCESS_KEY_ID"],
                "secret_access_key": os.environ["AWS_SECRET_ACCESS_KEY"],
                "s3_bucket": os.environ["AWS_S3_BUCKET"],
                }
            } 

        return self.check_remote_cp_get_post ('aws', creds)

    def test_datacenters_get_post (self):

        resp = self._client.query().app.datacenters("scw").get ()

        assert isinstance (resp, dict)
        assert 'datacenters' in resp
        assert isinstance (resp['datacenters'], list)

        for el in resp['datacenters']:
            assert isinstance (el, str)

        for dc in ["fr-par-1",
                   "fr-par-2",
                   "fr-par-3",
                   "nl-ams-1",
                   "nl-ams-2",
                   "pl-waw-1",
                   "pl-waw-2"]:

            assert dc in resp['datacenters']

    def test_info_get (self):

        resp = self._client.query().app.info.get(Domain="test", App="helloworld")

        assert isinstance (resp, str)

    def process (self, body):

        resp = self._client.query().app.run.post(body, Domain="test", App="helloworld")

        assert isinstance (resp, dict)
        assert len(resp) == 1
        assert 'id' in resp
        assert isinstance (resp['id'], str)
        assert re.fullmatch (self._re_uuid4, resp['id'])

        puid = resp['id']

        # Should be a process in the process list. We can test it
        self.test_list_Process_get ()

        def check_status ():

            resp = self._client.query().app.status.get (Process=puid)

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
                               'outputs',
                               'metrics',
                               'quote',
                               'errors']
    
            assert isinstance (resp['user_id'], str)
            assert re.fullmatch (self._re_uuid4, resp['user_id'])
            assert resp['app'] == 'helloworld'
            assert resp['domain'] == 'test'
            assert resp['endpoint'] == 'run'
            assert isinstance (resp['id'], str)
            assert re.fullmatch (self._re_uuid4, resp['id'])
            assert isinstance (resp['launched'], str)
            datetime.datetime.fromisoformat (resp['launched'])
            assert isinstance (resp['terminated'], str)
            datetime.datetime.fromisoformat (resp['terminated'])
            assert isinstance (resp['expires'], str)
            datetime.datetime.fromisoformat (resp['expires'])
            assert isinstance (resp['state'], str)

            assert resp['state'] in ['say_hello', 'upload', 'pending', 'waiting', 'dead', 'terminated']
            if 'outputs' in resp:
                assert isinstance (resp['outputs'], dict)
                for key in resp['outputs']:
                    assert isinstance (resp['outputs'][key], str)
                    assert resp['outputs'][key].startswith('https://')
                    assert 's3' in resp['outputs'][key]

            if 'metrics' in resp:
                for key in resp['metrics']:
                    assert isinstance (resp['metrics'][key], dict)
                    for subkey in resp['metrics'][key]:
                        assert subkey in ['rate', 'datetime', 'metrics']
                        if subkey == 'rate':
                            assert isinstance(resp['metrics'][key]['rate'], int)
                        if subkey == 'datetime':
                            datetime.datetime.fromisoformat (resp['metrics'][key]['datetime'])
                        if subkey == 'metrics':
                            assert isinstance (resp['metrics'][key]['metrics'], list)
                            for item in resp['metrics'][key]['metrics']:
                                assert isinstance (item, list)
                                assert len(item) == 2
                                assert isinstance (item[0], int) and isinstance (item[1], int)
            if 'quote' in resp:
                assert isinstance (resp['quote'], float)

            if 'errors' in resp:
                assert isinstance (resp['errors'], list)
                for item in resp['errors']:
                    assert isinstance (item, str)
       
            return resp['state']

        import time

        status = "None"
        num_tries, num_tries_max = 0, 60
        sleep_duration = 10

        while status != "dead":

            if num_tries == num_tries_max:
                break

            num_tries += 1

            time.sleep (sleep_duration)

            status = check_status ()

        resp = self._client.query().app.status.get (Process=puid)

        assert resp['state'] == 'dead'

        dest = body['output-prefix']
        assert f'{dest}/msg-test.txt' in resp['outputs']

        resp = self._client.query().app.cost.get (Process=puid)

        assert isinstance (resp, dict)
        assert len(resp) == 1
        assert 'cost' in resp
        assert isinstance (resp['cost'], float)
        assert resp['cost'] < 1.0

    def test_scaleway_process (self):

        pool = ["scw:fr-par-1:PLAY2-PICO"]        
        body = {
                "inputs": {},
                "output-prefix": "test",
                "pool": pool 
            }

        self.process (body) 

#    def test_aws_process (self):
#
#        import os 
#
#        for field in ["AWS_ACCESS_KEY_ID",
#                      "AWS_SECRET_ACCESS_KEY",
#                      "AWS_S3_BUCKET",
#                      "AWS_REGION"]:
#            assert field in os.environ 
#
#        creds = {
#            "aws": {
#                "access_key_id": os.environ["AWS_ACCESS_KEY_ID"],
#                "secret_access_key": os.environ["AWS_SECRET_ACCESS_KEY"],
#                "s3_bucket": os.environ["AWS_S3_BUCKET"],
#                "region": os.environ["AWS_REGION"]
#                }
#            } 
#
#        pool = [
#                "aws:{}:t2.micro".format(os.environ["AWS_REGION"])
#            ] 
#
#        body = {
#                "inputs": {},
#                "output-prefix": "s3://test",
#                "pool": pool,
#                "creds": creds
#            }
#
#        self.process (body) 

if __name__ == '__main__':
    unittest.main()
