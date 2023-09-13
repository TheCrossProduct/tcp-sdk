import tcp
import unittest
import re
import json
import slumber
class RunTestCase (unittest.TestCase):

    def setUp (self):

        import os

        self._test_account = os.environ["TCP_TEST_ACCOUNT"]
        self._test_passwd = os.environ["TCP_TEST_PASSWD"]
        self._client = tcp.client (usermail=self._test_account, passwd= self._test_passwd)

    
    def test_run(self):
        
        apps = self._client.query().app.get()
        assert isinstance (apps, dict)
        print(apps)
        proc_id=[]

        for domain in ["railway"]:#apps.keys():
            assert isinstance(apps[domain],type([]))

            for app in ['rail-modeling']:#apps[domain]:

                uri = "testing@"+domain.lower()+'/'+app.replace('-','_').lower()+'/input/body.json'
                print(uri)
                resp=self._client.download(uri,"/home/elise/tmp_body.json")
                body=json.load(open("/home/elise/tmp_body.json"))
                print(body)
                body['pool']=["scw:fr-par-1:ENT1-M"]
                resp = self._client.query().app.run.post(body, Domain=domain, App=app)
                print(resp)
                assert isinstance(resp,dict)
                assert isinstance (resp['id'], str)
                proc_id.append(resp['id'])
 

