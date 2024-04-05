def test_pagination(test_case,
                    endpoint,
                    init_body):

    resp = endpoint.post (init_body)

    if not resp:
        test_case.assertEqual(resp, [])
        return

    test_case.assertIn("paging", resp)
    test_case.assertIsInstance(resp['paging'], dict)
    for key in resp['paging']:
        test_case.assertIn(key, ['count',
                                 'items_per_page',
                                 'next',
                                 'previous'])

    tablenames = list([kk for kk in resp.keys() if kk != 'paging'])
    atts = [list(resp[tt][0].keys()) if isinstance(resp[tt][0], dict) else [] for tt in tablenames]
    print(atts)

    nb_items = sum([len(resp[tt]) for tt in tablenames if tt in resp])
    test_case.assertEqual(nb_items, resp['paging']['count'])

    if nb_items > 1:
        resp = endpoint.post (init_body | {'items_per_page':nb_items-1})
        print(resp)
        nb_items = sum([len(resp[tt]) for tt in tablenames if tt in resp])
        test_case.assertEqual(nb_items, resp['paging']['count'])

        test_case.assertIn("next", resp['paging'])
        token = resp['paging']['next'].split('/')[-1]
        resp = endpoint.next (token).get()
        print(resp)
        next_nb_items = sum([len(resp[tt]) for tt in tablenames if tt in resp])
        test_case.assertGreaterEqual (nb_items, 1)

        test_case.assertIn("previous", resp['paging'])
        token = resp['paging']['previous'].split('/')[-1]
        resp = endpoint.previous (token).get()
        print(resp)
        previous_nb_items = sum([len(resp[tt]) for tt in tablenames if tt in resp])
        test_case.assertGreaterEqual (nb_items, previous_nb_items)

    for ii,tt in enumerate(tablenames):

        if atts[ii]:
            resp = endpoint.post (init_body | {'ignores':atts[ii][1:]})
            print(resp)

            if resp:
                test_case.assertEqual(len(resp[tt][0].keys()), 1)

