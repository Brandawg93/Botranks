from psaw import PushshiftAPI
from db import DB
from datetime import datetime
from timeloop import Timeloop
from datetime import timedelta

timer = Timeloop()
api = PushshiftAPI()

UPDATE_INTERVAL = 10


def search_pushshift(q, timestamp=None):
    """Search pushshift for specific criteria."""
    if not timestamp:
        timestamp = '1h'
    return api.search_comments(q=q, after=timestamp)


def get_votes(timestamp):
    """Get last hour worth of votes."""
    query = '"good bot"|"bad bot"'
    return search_pushshift(query, timestamp)


@timer.job(interval=timedelta(minutes=UPDATE_INTERVAL))
def update_db():
    db = DB('votes.db')

    print('Updating db...')
    last_update = db.get_last_updated_timestamp()
    votes = get_votes(last_update)
    num_of_updates = db.add_votes(votes)
    now = datetime.now()
    print('db updated at {} with {} updates.'.format(now.strftime('%Y-%m-%d %H:%M:%S'), num_of_updates))

    db.close()


if __name__ == "__main__":
    update_db()
    timer.start(block=True)
