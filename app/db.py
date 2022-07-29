import re
import praw
import sqlite3
from praw.exceptions import ClientException
from prawcore.exceptions import NotFound, ResponseException
from enum import Enum
from os import environ

REDDIT_CLIENT_ID = environ['REDDIT_CLIENT_ID']
REDDIT_CLIENT_SECRET = environ['REDDIT_CLIENT_SECRET']
REDDIT_USERNAME = environ['REDDIT_USERNAME']
REDDIT_PASSWORD = environ['REDDIT_PASSWORD']


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
    def __init__(self, file, vacuum=False, debug=False):
        self.file = file
        self.conn = None
        self.debug = debug
        if vacuum:
            self._open()
            self._vacuum()
            self._close()


    def _vacuum(self):
        c = self.conn.cursor()
        c.execute("VACUUM")

    def _check_if_exists(self, table):
        c = self.conn.cursor()

        # get the count of tables with the name
        c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name=? LIMIT 1", [table])

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

    def _filter_valid(self, vote):
        """Filter existing votes."""
        vote_type = get_vote_type(vote.body)
        if vote_type == VoteType.NONE:
            return False
        c = self.conn.cursor()
        c.execute("SELECT count(id) from votes where id = ? LIMIT 1", [vote.id])
        return c.fetchone()[0] == 0

    def create_tables(self):
        """Create necessary tables if they do not exist."""
        self._open()
        if not self._check_if_exists('votes'):
            self._create_votes_table()
        if not self._check_if_exists('bots'):
            self._create_bots_table()
        self._close()

    def get_last_updated_timestamp(self):
        self._open()
        c = self.conn.cursor()
        c.execute("SELECT timestamp from votes order by id DESC LIMIT 1")
        query = c.fetchone()
        self._close()
        if query and len(query) > 0:
            return query[0]
        else:
            return None

    def add_bot(self, bot):
        """Add bots to db."""
        self._open()
        c = self.conn.cursor()
        try:
            # Insert a row of data
            data = [str(bot.name), bot.comment_karma, bot.link_karma]
            c.execute("INSERT INTO bots VALUES (?, ?, ?)", data)
            if self.debug:
                print('Adding bot {} with comment karma={}, link karma={}.'.format(bot.name, bot.comment_karma,
                                                                                    bot.link_karma))
        except sqlite3.IntegrityError:
            data = [bot.comment_karma, bot.link_karma, str(bot.name)]
            c.execute("UPDATE bots SET comment_karma = ?, link_karma = ? WHERE bot = ?", data)
            if self.debug:
                print('Updating bot {} with comment karma={}, link karma={}.'.format(bot.name, bot.comment_karma,
                                                                                        bot.link_karma))

        except Exception as e:
            print(e)
        
        self._close()

    def add_votes(self, votes):
        """Add votes to db."""
        updates = 0
        r = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            password=REDDIT_PASSWORD,
            user_agent='mobile:botranker:0.1 (by /u/brandawg93)',
            username=REDDIT_USERNAME)

        self._open()
        votes_lst = list(filter(self._filter_valid, votes))
        self._close()
        parents = list(r.info([vote.parent_id for vote in votes_lst]))
        bots = list([parent.author for parent in parents if parent.author])
        self._open()
        c = self.conn.cursor()
        for vote in votes_lst:
            try:
                parent = next(iter([p for p in parents if p.name == vote.parent_id]), None)
                if parent.author:
                    try:
                        vote_type = get_vote_type(vote.body)
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
                        if self.debug:
                            print('Adding vote with id={}, bot={}, vote={}.'.format(vote.id,
                                                                                    parent.author.name,
                                                                                    vote_type.name[0]))

                    except sqlite3.IntegrityError:
                        pass
            except ResponseException as e:
                print('Received {} for {}. Skipping...'.format(e.response.status_code, vote.parent_id))
            except Exception as e:
                print(e)
        self._close()

        seen_bots = set()
        unique_bots = []
        for bot in bots:
            if bot.name not in seen_bots:
                unique_bots.append(bot)
                seen_bots.add(bot.name)

        for bot in unique_bots:
            self.add_bot(bot)
        return updates

    def _open(self):
        # open the connection
        self.conn = sqlite3.connect(self.file)

    def _close(self):
        # commit the changes to db
        self.conn.commit()

        # close the connection
        self.conn.close()
