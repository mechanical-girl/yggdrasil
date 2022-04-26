import karelia

import muninn

this_muninn = muninn.Muninn("muninn.db", "xkcd")
try:
    this_muninn.check_db()
except FileNotFoundError:
    this_muninn.create_db()

this_bot = karelia.bot("muninn", "xkcd")
this_bot.connect()
this_bot.send(this_muninn.next_log_request)

while not this_muninn.complete:
    message = this_bot.parse()
    if message.type == "log-reply":
        this_muninn.insert(message.packet)
        this_bot.send(this_muninn.next_log_request)
