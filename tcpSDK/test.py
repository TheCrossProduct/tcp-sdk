def get_API(host="https://api.thecrossproduct.xyz/v1", token=None):
    from .API import API

    api = API (host, token) 

    return api

def test_lics ():

    api = get_API ()

    resp = api.query().lics.get()
    assert isinstance (resp, list)
    for el in resp:
        assert isinstance (el, dict)
        for field in ['token', 
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
                      'failed_attempts']:
            assert field in el

def test_app ():

    api = get_API ()

    resp = api.query().app.get()
    assert isinstance (resp, dict)
    for key in resp:
        assert isinstance (resp[key], list)
        for el in resp[key]:
            assert isinstance (el, str) 

    resp = api.query().app.Process.get()
    assert isinstance (resp, list)
    for el in resp:
        assert isinstance (el, dict)
        for field in ['id',
                      'user_id',
                      'app',
                      'domain',
                      'launched',
                      'terminated',
                      'expires',
                      'state',
                      'exact_match']:
            assert field in el

    resp = api.query().app.Remote.get()
    assert isinstance (resp, list)
    for el in resp:
        assert isinstance (el, dict)
        for field in ['id',
                      'name',
                      'user_id',
                      'ip',
                      'key',
                      'num_cores',
                      'mem',
                      'ram',
                      'input_path',
                      'working_path',
                      'output_path',
                      'usr',
                      'instanciated']:
            assert field in el

    resp = api.query().app.Instance.get()
    assert isinstance (resp, list)
    for el in resp:
        assert isinstance (el, dict)
        for field in ['id',
                      'ext_id',
                      'user_id',
                      'process_id',
                      'launched',
                      'expires',
                      'state',
                      'ip',
                      'ssh_usr'
                      'input_path',
                      'working_path',
                      'output_path',
                      'num_cores',
                      'mem_required',
                      'ram_required']:
            assert field in el

    resp = api.query().app.PostMortem.get()
    assert isinstance (resp, list)
    for el in resp:
        assert isinstance (el, dict)
        for field in ['id',
                      'user_id',
                      'process_id',
                      'launched',
                      'num_cores',
                      'mem',
                      'ram',
                      'terminated',
                      'state']:
            assert field in el

    resp = api.query().app.info.get(Domain='railway', App='classification')
    assert '\nThe Cross Product, Inc -- Railway' in resp.decode()

def test_data ():

    api = get_API ()

    resp = api.query().data.generate_presigned_get_logo.get()
