def check_pagination(
    test_case, endpoint, init_body, endpoint_next=None, endpoint_previous=None
):
    if not endpoint_next:
        endpoint_next = endpoint.next
    if not endpoint_previous:
        endpoint_previous = endpoint.previous

    resp = endpoint.post(init_body)

    test_case.assertIn("paging", resp)
    test_case.assertIsInstance(resp["paging"], dict)
    for key in resp["paging"]:
        test_case.assertIn(key, ["count", "items_per_page", "next", "previous"])

    if resp["paging"]["count"] == 0:
        return

    tablenames = list([kk for kk in resp.keys() if kk != "paging"])
    atts = [
        []
        if not resp[tt] or not isinstance(resp[tt][0], dict)
        else list(resp[tt][0].keys())
        for tt in tablenames
    ]

    nb_items = sum([len(resp[tt]) for tt in tablenames if tt in resp])
    test_case.assertEqual(nb_items, resp["paging"]["count"])

    if nb_items > 1:
        resp = endpoint.post(init_body | {"items_per_page": nb_items - 1})
        nb_items = sum([len(resp[tt]) for tt in tablenames if tt in resp])
        test_case.assertEqual(nb_items, resp["paging"]["count"])

        test_case.assertIn("next", resp["paging"])
        token = resp["paging"]["next"].split("/")[-1]
        resp = endpoint_next(token).get()
        next_nb_items = sum([len(resp[tt]) for tt in tablenames if tt in resp])
        test_case.assertGreaterEqual(nb_items, 1)

        test_case.assertIn("previous", resp["paging"])
        token = resp["paging"]["previous"].split("/")[-1]
        resp = endpoint_previous(token).get()
        previous_nb_items = sum([len(resp[tt]) for tt in tablenames if tt in resp])
        test_case.assertGreaterEqual(nb_items, previous_nb_items)

    for ii, tt in enumerate(tablenames):
        if atts[ii]:
            resp = endpoint.post(init_body | {"ignores": atts[ii][1:]})

            if resp:
                test_case.assertEqual(len(resp[tt][0].keys()), 1)
