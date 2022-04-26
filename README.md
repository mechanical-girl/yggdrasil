# yggdrasil
Yggdrasil is a series of Python modules for writing bots to interface with euphoria.io. It is designed to be bot-library-independent.


## ravens
The Ravens are used for the purposes of archiving a room. Muninn ("memory") archives historic messages, while Huginn ("thought") records those received in real time.

### muninn
Muninn is used for retrieving historical room messages. An example is presented below, using the [Karelia](https://github.com/struandw/karelia) bot library:

```
import karelia

import ravens

muninn = ravens.Muninn("logs.db", "xkcd")
try:
    muninn.check_db()
except FileNotFoundError:
    muninn.create_db()

this_bot = karelia.bot("ravens", "xkcd")
this_bot.connect()
this_bot.send(muninn.next_log_request)

while not muninn.complete:
    message = this_bot.parse()
    if message.type == "log-reply":
        muninn.insert(message.packet, replace_old=False)
        this_bot.send(muninn.next_log_request)

print("Room has been archived!")
```

The Muninn workflow is simple:
1. Create a Muninn object (`this_muninn = muninn.Muninn(path_to_db, room)`) 
2. Verify the database `this_muninn.check_db()`. This will raise a FileNotFound error if the database file doesn't exist; in this case, `this_muninn.create_db()` will create both the file and the database structure within it.
3. Establish a connection to the room you want the logs of, using the botlib of your choice. After the initial handshake, send the dict found at `this_muninn.next_log_request` or create your own. The pre-made dict will request the most recent 1000 messages.
4. When you receive a `log-reply` from Heim, send it in dict form to `this_muninn.insert()`. You can optionally specify whether to `REPLACE` or `ABORT` on conflict with the `replace_old` argument (the default is `True`, which means `REPLACE` will be used on conflict) and the number of messages requested in the next packet with the `requested_n` argument (the default is 1000). You may wish to use the `replace_old=True` if you intend to update your whole database (including "new" edits of "old" messages) or `replace_old=False` to only add messages sent since the database was last updated.
5. Muninn will automatically assemble the next log request packet for you, based on your specified `requested_n` value and the earliest message contained in the last packet. You can find it at `this_muninn.next_log_request` or send your own.
6. Repeat 4 and 5 as long as required;you can use `this_muninn.complete` as a conditional. This value will be true under the following circumstances:
    - if `replace_old=True`, this value will be True as long as the last log-reply contained the requested number of messages. If this is not the case, it is assumed that the log-reply data were truncated due to the earliest message being contained in it.
    - if `replace_old=False`, this value will be True as long as there were no conflicts on insertion. A conflict on insertion is taken as evidence that the database is now up-to-date, i.e. that the message being processed already exists in the database. 

It is worthwhile to note that using *only* Muninn will fail to capture messages sent during the archival process. For this, we must turn to Huginn.

### Huginn
Huginn is used for archiving messages being sent in real-time. A bare-bones example is presented below, using the [Karelia](https://github.com/struandw/karelia) bot library:

```
import karelia

import ravens

huginn = ravens.Huginn("logs.db", "xkcd")
this_bot = karelia.bot("ravens", "xkcd")
this_bot.connect()

while True:
    message = this_bot.parse()
    if message.type == "send-event":
        huginn.insert(message.packet)
```

The Huginn workflow is - in fact - even simpler than that of Muninn. However, this comes at a cost - Huginn is not designed to work "stand-alone", but rather to take up where Muninn leaves off. This means that it assumes that the database file given exists and is correct.