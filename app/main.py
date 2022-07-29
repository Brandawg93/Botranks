from pmaw import PushshiftAPI
from db import DB
from datetime import datetime
from time import sleep
import sys

api = PushshiftAPI()

UPDATE_INTERVAL = 10
YEAR_IN_SECONDS = 31556926
DB_FILE = '../votes.db'


def search_pushshift(q, timestamp=None):
    """Search pushshift for specific criteria."""
    if not timestamp:
        timestamp = '1h'
    fields = ['author', 'body', 'created_utc', 'id', 'link_id', 'parent_id', 'subreddit']
    return api.search_comments(q=q, after=timestamp, filter=fields)


def get_votes(timestamp):
    """Get last hour worth of votes."""
    query = '"good bot"|"bad bot"'
    return search_pushshift(query, timestamp)


def update_db():
    try:
        backfill = '--backfill' in sys.argv
        vacuum = '--vacuum' in sys.argv
        db = DB(DB_FILE, vacuum=vacuum, debug=backfill)
        db.create_tables()

        if backfill:
            print('Backfilling db...')
            last_update = int(time.time()) - YEAR_IN_SECONDS
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
