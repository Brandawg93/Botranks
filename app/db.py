import sqlite3
import re
import praw
from praw.exceptions import ClientException
import constants
from enum import Enum


class VoteType(Enum):
    NONE = 0
    GOOD = 1
    BAD = 2


def get_vote_type(body):
    """Return type of vote."""
    regex = re.compile(r'^(good|bad) bot.*', re.I)
    text = re.search(regex, body)
    if text:
        vote = text.group(0).lower()
        if 'good bot' in vote:
            return VoteType.GOOD
        elif 'bad bot' in vote:
            return VoteType.BAD
    return VoteType.NONE


class DB:
    def __init__(self, file):
        self.conn = sqlite3.connect(file)
        if not self._check_if_exists('votes'):
            self._create_votes_table()
        if not self._check_if_exists('bots'):
            self._create_bots_table()

    def _check_if_exists(self, table):
        c = self.conn.cursor()

        # get the count of tables with the name
        c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name=?", [table])

        # if the count is 1, then table exists
        return c.fetchone()[0] == 1

    def _create_votes_table(self):
        c = self.conn.cursor()

        # Create table
        c.execute('''CREATE TABLE votes
                     (bot text, 
                     id text, 
                     subreddit text, 
                     timestamp INTEGER, 
                     vote text, 
                     author text)''')

        c.execute("CREATE UNIQUE INDEX idx_votes_id ON votes (id)")

    def _create_bots_table(self):
        c = self.conn.cursor()

        # Create table
        c.execute("CREATE TABLE bots (bot text, comment_karma INTEGER, link_karma INTEGER)")

        c.execute("CREATE UNIQUE INDEX idx_bots_bot ON bots (bot)")

    def get_last_updated_timestamp(self):
        c = self.conn.cursor()
        c.execute("SELECT timestamp from votes order by id DESC LIMIT 1")
        query = c.fetchone()
        if query and len(query) > 0:
            return query[0]
        else:
            return None

    def add_votes(self, votes):
        """Update bots in db."""
        c = self.conn.cursor()
        updates = 0
        bots = {}

        r = praw.Reddit(
            client_id=constants.REDDIT_CLIENT_ID,
            client_secret=constants.REDDIT_CLIENT_SECRET,
            password=constants.REDDIT_PASSWORD,
            user_agent='mobile:botranker:0.1 (by /u/brandawg93)',
            username=constants.REDDIT_USERNAME)

        for vote in votes:
            parent = None
            vote_type = get_vote_type(vote.body)
            if vote_type == VoteType.NONE:
                continue
            try:
                p_type = vote.parent_id[:2]
                if p_type == 't1':
                    parent = r.comment(vote.parent_id[3:])
                elif p_type == 't3':
                    parent = r.submission(vote.parent_id[3:])
                if parent and parent.author:
                    try:
                        comment_karma = parent.author.comment_karma
                        link_karma = parent.author.link_karma
                    except:
                        comment_karma = 0
                        link_karma = 0

                    if parent.author.name in bots:
                        bot = bots[parent.author.name]
                        if comment_karma > bot['comment_karma']:
                            bot['comment_karma'] = comment_karma
                        if link_karma > bot['link_karma']:
                            bot['link_karma'] = link_karma
                    else:
                        bots[parent.author.name] = {'comment_karma': comment_karma, 'link_karma': link_karma}
                    try:
                        # Insert a row of data
                        c.execute("INSERT INTO votes VALUES (?, ?, ?, ?, ?, ?)",
                                  [parent.author.name,
                                   vote.id,
                                   vote.subreddit,
                                   vote.created_utc,
                                   vote_type.name[0],
                                   vote.author
                                   ])
                        updates += 1
                    except sqlite3.IntegrityError:
                        pass
            except ClientException as e:
                print(e)
        for bot in bots:
            try:
                # Insert a row of data
                c.execute("INSERT INTO bots VALUES (?, ?, ?)",
                          [bot,
                           bots[bot]['comment_karma'],
                           bots[bot]['link_karma']
                           ])
            except sqlite3.IntegrityError:
                c.execute("UPDATE bots SET comment_karma = ?, link_karma = ? WHERE bot = ?",
                          [bots[bot]['comment_karma'],
                           bots[bot]['link_karma'],
                           bot
                           ])

        return updates

    def close(self):
        # commit the changes to db
        self.conn.commit()

        # close the connection
        self.conn.close()
