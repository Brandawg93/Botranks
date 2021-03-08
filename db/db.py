import sqlite3
import re
import praw
from praw.exceptions import ClientException
from db import constants
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
        self.conn.create_function("power", 2, lambda x, y: x ** y)

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

    def _filter_valid(self, vote):
        """Filter existing votes."""
        c = self.conn.cursor()
        c.execute("SELECT count(id) from votes where id = ?", [vote.id])
        vote_type = get_vote_type(vote.body)
        return vote_type != VoteType.NONE and c.fetchone()[0] == 0

    def create_tables(self):
        """Create necessary tables if they do not exist."""
        if not self._check_if_exists('votes'):
            self._create_votes_table()
        if not self._check_if_exists('bots'):
            self._create_bots_table()

    def get_last_updated_timestamp(self):
        c = self.conn.cursor()
        c.execute("SELECT timestamp from votes order by id DESC LIMIT 1")
        query = c.fetchone()
        if query and len(query) > 0:
            return query[0]
        else:
            return None

    def get_ranks(self, epoch, minvotes=3):
        """Get ranks from db."""
        c = self.conn.cursor()
        return c.execute('''select bot,
                    link_karma,
                    comment_karma,
                    good_votes,
                    bad_votes,
                    ROUND(((good_votes + 1.9208) / (good_votes + bad_votes) - 1.96 * power(
                    (good_votes * bad_votes) / (good_votes + bad_votes) + 0.9604, 0.5) / (good_votes + bad_votes)) / (
                    1 + 3.8416 / (good_votes + bad_votes)), 4) as score
                        from (select v.bot,
                                max(b.link_karma) as link_karma,
                                max(b.comment_karma) as comment_karma,
                                sum(CASE WHEN v.vote = 'G' THEN 1 ELSE 0 END) as good_votes,
                                sum(CASE WHEN v.vote = 'B' THEN 1 ELSE 0 END) as bad_votes
                            from (select * from votes where timestamp >= ?) v
                            inner join bots b on v.bot = b.bot
                            group by v.bot)
                        where good_votes + bad_votes >= ?
                        order by score desc''', [epoch, minvotes])

    def get_top_subs(self, epoch, limit=5):
        """Get top subreddits from db."""
        c = self.conn.cursor()
        return c.execute('''select subreddit, count(*) from votes
                        where subreddit IS NOT NULL AND subreddit != '' AND timestamp >= ?
                        group by subreddit
                        order by count(*) desc
                        limit ?''', [epoch, limit]).fetchall()

    def get_top_bots(self, epoch, limit=5):
        """Get top bots from db."""
        c = self.conn.cursor()
        return c.execute('''select bot, round((good_votes + 1) / (bad_votes + 1), 2)
                from (select bot,
                        sum(CASE WHEN vote = 'G' THEN 1 ELSE 0 END) as good_votes,
                        sum(CASE WHEN vote = 'B' THEN 1 ELSE 0 END) as bad_votes
                    from (select * from votes where timestamp >= ?)
                    group by bot)
                group by bot
                order by round((good_votes + 1) / (bad_votes + 1), 2) DESC
                limit ?''', [epoch, limit]).fetchall()

    def get_vote_count(self, epoch, vote_type):
        """Get count of specific vote type."""
        c = self.conn.cursor()
        return c.execute('''select sum(CASE WHEN vote = ? THEN 1 ELSE 0 END) from votes where timestamp >= ?''',
                         [vote_type, epoch]).fetchone()[0]

    def get_timeline_data(self, epoch, date_format):
        """Get data for timeline."""
        c = self.conn.cursor()
        return c.execute('''select strftime(?, timestamp, 'unixepoch') as unit,
                           sum(CASE WHEN vote = 'G' THEN 1 ELSE 0 END) as good_votes,
                           sum(CASE WHEN vote = 'B' THEN 1 ELSE 0 END) as bad_votes
                    from votes
                    where timestamp >= ?
                    group by unit''', [date_format, epoch])

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

        for vote in filter(self._filter_valid, votes):
            vote_type = get_vote_type(vote.body)
            try:
                parent = next(r.info(fullnames=[vote.parent_id]), None)
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
                        self.conn.commit()
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
