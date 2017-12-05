import sqlite3
import sys

from invoke import task

from defs import DB_URI


@task
def dbshell(ctx, db_name='map'):
    """ Creates a minimal SQLite shell session for experiments.
    """
    if db_name not in DB_URI:
        print("Error, unknown DB name: '{}', available: {}".format(db_name, ', '.join(DB_URI.keys())))
        sys.exit(1)

    con = sqlite3.connect(DB_URI[db_name].replace('sqlite:///', 'file:'), uri=True)
    con.isolation_level = None
    cur = con.cursor()
    buffer = ''
    shell_prompt = '{}=> '.format(db_name)
    shell_prompt_non_completed = '{}-> '.format(db_name)

    print("Enter your SQL commands to execute in sqlite3.\n"
          "Enter a blank line to exit.")

    curr_shell_prompt = shell_prompt
    while True:
        line = input(curr_shell_prompt)
        if line == '':
            break
        buffer += line
        if sqlite3.complete_statement(buffer):
            try:
                buffer = buffer.strip()
                cur.execute(buffer)
                if buffer.lstrip().upper().startswith('SELECT'):
                    for line in cur.fetchall():
                        print(line)
            except sqlite3.Error as e:
                print("An error occurred: {}".format(e.args[0]))
            buffer = ''
            curr_shell_prompt = shell_prompt
        else:
            curr_shell_prompt = shell_prompt_non_completed

    con.close()
    sys.exit(0)
