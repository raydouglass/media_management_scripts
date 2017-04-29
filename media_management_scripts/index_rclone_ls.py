import sqlite3
import os
import sys


def index(rclone_ls_output, db_file):
    if os.path.exists(db_file):
        os.remove(db_file)
    with sqlite3.connect(db_file) as conn:
        # conn.execute(
        #     'CREATE TABLE IF NOT EXISTS file (file TEXT, size INT)')
        conn.execute('CREATE VIRTUAL TABLE IF NOT EXISTS file USING fts4(name TEXT, size INT);')
        data = []
        for line in rclone_ls_output:
            line = line.strip()
            i = line.index(' ')
            size = int(line[:i])
            file = line[i + 1::]
            data.append((file, size))
        conn.executemany('INSERT INTO file (name, size) VALUES(?, ?)', data)
        conn.commit()


def from_stdin(db_file):
    lines = sys.stdin.readlines()
    index(lines, db_file)
