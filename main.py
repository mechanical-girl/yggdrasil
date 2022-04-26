import karelia

import ravens

muninn = ravens.Muninn("logs.db", "xkcd")
huginn = ravens.Huginn("logs.db", "xkcd")
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

print("Huginn taking over")
while True:
    message = this_bot.parse()
    if message.type == "send-event":
        huginn.insert(message.packet)
