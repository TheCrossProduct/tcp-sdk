import time
import tcp

nbr_of_tries = 20
delay = 1


def retry(test_case, func, *args, **kwargs):
    for ii in range(nbr_of_tries - 1):
        try:
            return func(*args, **kwargs)
        except tcp.exceptions.HttpClientError as err:
            time.sleep(delay)

    return func(*args, **kwargs)


def retry_until_resp(test_case, func, ref, *args, **kwargs):
    resp = None

    for ii in range(nbr_of_tries):
        try:
            resp = func(*args, **kwargs)
            if resp == ref:
                continue
        except tcp.exceptions.HttpClientError as err:
            time.sleep(delay)

    test_case.assertNotEqual(resp, None)
    test_case.assertDictEqual(resp, ref)
