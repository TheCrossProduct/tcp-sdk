def _upload_part (args):

    url = args[0]
    part_no = args[1]
    src_local, part_size = args[2][0], args[2][1]

    import requests
    
    file_data = None

    with open(src_local, 'rb') as f:

        f.seek ((part_no-1)*part_size)
        file_data = f.read (part_size)

    resp = requests.put (url, data=file_data)

    if resp.status_code != 200:
        return False, {'url': url, 'PartNumber': part_no} 

    return True, {'ETag': resp.headers['ETag'].replace('"', ''), 'PartNumber': part_no} 
