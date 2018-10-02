import sqlite3
from datetime import datetime
import os
import json

target = None


def load_config(_file):
    global target
    if target is None:
        target_filename = _file
        config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), target_filename) \
            if os.path.basename(target_filename) == target_filename else target_filename
        with open(config_file) as f:
            target = json.load(f)
    return target


def add_robot_user():
    config = load_config('config.json')
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), config['db_path']))
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    robot_user = (
        111,
        'pbkdf2_sha256$100000$ewf3ALdvAJNE$AQ6MWIPavbxgp/+lDJezDDKRaIQ0s82ISaWtV6Z5YG4=',
        'robot',
        False,
        True,
        False,
        datetime.now(),
        datetime.now(),
        datetime.now(),
        '',
        '',
        '',
        '',
        1,
        0,
        False,
        False,
        111
    )
    c.execute('SELECT * FROM apps_user WHERE id = 111')
    if len(c.fetchall()) == 0:
        c.execute('INSERT INTO apps_user (id, password, username, is_superuser, is_active, is_staff, date_joined, '
                  'time_created, time_modified, first_name, last_name, email, twitter, status, supporters_num, '
                  'comments_enabled, profile_public, submitter_id) VALUES '
                  '(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', robot_user)
        conn.commit()
    conn.close()

if __name__ == '__main__':
    add_robot_user()