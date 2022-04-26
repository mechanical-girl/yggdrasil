import sqlite3
from datetime import datetime
from os.path import exists


class Muninn:
    def __init__(self, db_location, room):
        self.DB_PATH = db_location
        self.room = room
        self.complete = False
        self.next_log_request = {"type": "log", "data": {"n": 1000}}


    def check_db(self):
        if not exists(self.DB_PATH):
            raise FileNotFoundError("Database file not found")

        self.conn = sqlite3.connect(self.DB_PATH)
        self.c = self.conn.cursor()

    def create_db(self):
        self.conn = sqlite3.connect(self.DB_PATH)
        self.c = self.conn.cursor()
        # Create the message table
        self.c.execute("""  CREATE TABLE IF NOT EXISTS message (
                                room TEXT,
                                id TEXT PRIMARY KEY NOT NULL,
                                parent TEXT,
                                previous_edit_id TEXT,
                                time INTEGER NOT NULL,
                                nick TEXT NOT NULL,
                                user_id TEXT REFERENCES sender(id),
                                session_id TEXT REFERENCES sender(session_id),
                                content TEXT NOT NULL,
                                encryption_key_id TEXT,
                                edited TEXT,
                                deleted TEXT,
                                truncated INTEGER
                            )""")

        # Create the sender table
        self.c.execute("""  CREATE TABLE IF NOT EXISTS sender (
                                id TEXT NOT NULL,
                                server_id TEXT NOT NULL,
                                server_era TEXT NOT NULL,
                                session_id TEXT,
                                is_staff INTEGER,
                                is_manager INTEGER,
                                client_address TEXT,
                                real_client_address TEXT,
                                PRIMARY KEY (id, session_id)
                            )""")

        # Tree index generation
        self.c.execute("""  CREATE INDEX IF NOT EXISTS message_parent ON message (
                                parent,
                                id
                            )""")

        # Index for partial message querying
        self.c.execute("""  CREATE INDEX IF NOT EXISTS partial_message ON message (
                                id,
                                room,
                                parent,
                                time,
                                nick,
                                user_id,
                                content,
                                deleted
                            )""")

    def insert(self, packet, on_conflict="REPLACE", requested_n=1000):
        # Run through the packet and insert all messages into the database
        if packet.type != "log-reply":
            raise ValueError("Packet type is not a log-reply")
        

        message_values = []
        sender_values = []
        print(datetime.utcfromtimestamp(packet.data.log[0]["time"]).strftime('%Y-%m-%d %H:%M'))

        for message in packet.data.log:
            message_values.append((
                self.room,
                message["id"],
                message["parent"] if "parent" in message.keys() else "",
                message["edited"],
                message["time"],
                message["sender"]["name"],
                message["sender"]["id"],
                message["sender"]["session_id"],
                message["content"],
                "", # encryption_key_id doesn't seem to appear anywhere
                False if message["edited"] == "null" else True,
                False if message["deleted"] == "null" else True,
                False if not "truncated" in message.keys() else True
            ))

            sender_values.append((
                message["sender"]["id"],
                message["sender"]["server_id"],
                message["sender"]["server_era"],
                message["sender"]["session_id"],
                True if "is_staff" in message["sender"].keys() and message["sender"]["is_staff"] else False,
                True if "is_manager" in message["sender"].keys()and message["sender"]["is_manager"] else False,
                "",
                ""
            ))

        self.c.executemany(f"""  INSERT or {on_conflict} INTO message VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", message_values)
        self.c.executemany(f"""  INSERT or {on_conflict} INTO sender VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", sender_values)
        self.conn.commit()

        self.next_log_request = {"type": "log", "data": {"n": requested_n, "before": message_values[0][1]}}

        if len(message_values) < requested_n:
            self.complete = True
        else:
            self.complete = False
