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


if __name__ == '__main__':
    unittest.main()
