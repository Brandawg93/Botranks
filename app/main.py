import requests
from db import DB
from datetime import datetime
from timeloop import Timeloop
from datetime import timedelta

timer = Timeloop()

SIZE = 500
AFTER = '1h'
UPDATE_INTERVAL = 1


def search_pushshift(q):
    """Search pushshift for specific criteria."""
    fields = 'author,body,created_utc,id,link_id,parent_id,subreddit'
    r = requests.get('https://api.pushshift.io/reddit/search/comment/?q={}&fields={}&after={}&size={}&sort=asc&sort_type=created_utc'.format(q, fields, AFTER, SIZE))
    r.raise_for_status()
    return r.json()['data']


def get_votes():
    """Get last hour worth of votes."""
    query = '"good%20bot"|"bad%20bot"'
    return search_pushshift(query)


@timer.job(interval=timedelta(hours=UPDATE_INTERVAL))
def update_db():
    db = DB('votes.db')

    print('Updating db...')
    votes = get_votes()
    num_of_updates = db.add_votes(votes)
    now = datetime.now()
    print('db updated at {} with {} updates.'.format(now.strftime('%Y-%m-%d %H:%M:%S'), num_of_updates))

    db.close()


if __name__ == "__main__":
    update_db()
    timer.start(block=True)
