from pmaw import PushshiftAPI
from db import DB
from datetime import datetime
from time import sleep, time
import re
import sys

api = PushshiftAPI()

UPDATE_INTERVAL = 10
YEAR_IN_SECONDS = 31556926
DB_FILE = '../votes.db'

def fxn(item):
        regex = re.compile(r'^(good|bad) bot.*', re.I)
        text = re.search(regex, item['body'])
        db = DB(DB_FILE)
        db._open()
        valid = db._filter_valid(item)
        db._close()
        return text is not None and valid and item['parent_id'] is not None


def search_pushshift(q, timestamp):
    """Search pushshift for specific criteria."""
    fields = ['author', 'body', 'created_utc', 'id', 'link_id', 'parent_id', 'subreddit']
    if not timestamp:
        return api.search_comments(q=q, search_window=365, filter=fields, mem_safe=True, filter_fn=fxn)
    return api.search_comments(q=q, after=timestamp, filter=fields, mem_safe=True, filter_fn=fxn)


def get_votes(timestamp):
    """Get last timestamp worth of votes."""
    query = '"good bot"|"bad bot"'
    return search_pushshift(query, timestamp)


def update_db():
    try:
        backfill = '--backfill' in sys.argv
        vacuum = '--vacuum' in sys.argv
        last_update = None
        db = DB(DB_FILE, vacuum=vacuum, debug=backfill)
        db.create_tables()

        if backfill:
            print('Backfilling db...')
        else:
            print('Updating db...')
            last_update = db.get_last_updated_timestamp()

        votes = get_votes(last_update)
        num_of_updates = db.add_votes(votes)

        now = datetime.now()
        print('db updated at {} with {} updates.'.format(now.strftime('%Y-%m-%d %H:%M:%S'), num_of_updates))
    except KeyboardInterrupt:
        print('\nExiting...')
        sys.exit(0)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    update_db()
    if '--backfill' not in sys.argv:
        while True:
            sleep(60 * UPDATE_INTERVAL)
            update_db()
