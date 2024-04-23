
TCP python SDK 
==============

tcp-sdk is a Python module that provides a convenient object-oriented interface to TCP API. It acts as a wrapper around [slumber](https://github.com/samgiles/slumber).

QuickStart
----------

* Install *tcp-sdk*


      $ virtualenv my_virtualenv
      $ source my_virtualenv/bin/activate
      $ pip install tcp-sdk

* Connect to your TCP account

      import tcp
      client = tcp.client (usermail="user@domain.org", passwd="passwd")
      print(client.token)

  
Save this token to the environment variable `$TCP_API_TOKEN`.
Latter calls to ``tcp.client()`` will automatically connect to TCP API using this environment variable.

* Start using tcp-sdk

      import tcp
      client = tcp.client ()
      print (client.query().auth.get())

Requirements
------------

*tcp-sdk* requires the following modules.

 * *requests*
 * *slumber*
 * *requests-oauthlib*


