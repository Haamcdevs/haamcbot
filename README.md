# Simple Discord Bot for HAAMC


Prerequities 
Core Requires:
1. python >3.6 ( https://www.python.org/downloads/ )
2. discord.py   ( https://pypi.org/project/discord.py/ )

Plugin Requires:
1. jikanpy - Myanimelist unofficial api client ( https://pypi.org/project/jikanpy/)
2. CacheControl - cache the requests
3. Lockfile
4. mysql-connector-python

A pip requirements freeze has been provided, to install the exact versions perform this command:
`pip install -r requirements.txt`

Stepts to get it to work:
1) Copy config.py.example and rename it to config.py
2) In config set the Authkey to your bot token ( Discord Dev Porta > Select your bot > Bot > Token)
3) If you run the bot on the test server, its best to change cmd prefix from the default, so that no one else triggers your bot.
