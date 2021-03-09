import sqlite3


class DB:
    def __init__(self, file, debug=False):
        self.conn = sqlite3.connect(file)
        self.conn.create_function("power", 2, lambda x, y: x ** y)
        self.debug = debug

    def _check_if_exists(self, table):
        c = self.conn.cursor()

        # get the count of tables with the name
        c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name=? LIMIT 1", [table])

        # if the count is 1, then table exists
        return c.fetchone()[0] == 1

    def get_ranks(self, epoch, minvotes=3):
        """Get ranks from db."""
        c = self.conn.cursor()
        c.execute('''select bot,
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
                            group by v.bot) v2
                        where good_votes + bad_votes >= ?
                        order by score desc''', [epoch, minvotes])
        return c

    def get_top_subs(self, epoch, limit=5):
        """Get top subreddits from db."""
        c = self.conn.cursor()
        c.execute('''select subreddit, count(*) from votes
                        where subreddit IS NOT NULL AND subreddit != '' AND timestamp >= ?
                        group by subreddit
                        order by count(*) desc
                        limit ?''', [epoch, limit])
        return c.fetchall()

    def get_top_bots(self, epoch, limit=5):
        """Get top bots from db."""
        c = self.conn.cursor()
        c.execute('''select bot, round((good_votes + 1) / (bad_votes + 1), 2)
                from (select bot,
                        sum(CASE WHEN vote = 'G' THEN 1 ELSE 0 END) as good_votes,
                        sum(CASE WHEN vote = 'B' THEN 1 ELSE 0 END) as bad_votes
                    from (select * from votes where timestamp >= ?) v
                    group by bot) v2
                group by bot
                order by round((good_votes + 1) / (bad_votes + 1), 2) DESC
                limit ?''', [epoch, limit])
        return c.fetchall()

    def get_vote_count(self, epoch, vote_type):
        """Get count of specific vote type."""
        c = self.conn.cursor()
        c.execute('''select sum(CASE WHEN vote = ? THEN 1 ELSE 0 END) from votes where timestamp >= ? LIMIT 1''',
                  [vote_type, epoch])
        return c.fetchone()[0]

    def get_timeline_data(self, epoch, date_format):
        """Get data for timeline."""
        c = self.conn.cursor()
        c.execute('''select strftime(?, timestamp, 'unixepoch') as unit,
                           sum(CASE WHEN vote = 'G' THEN 1 ELSE 0 END) as good_votes,
                           sum(CASE WHEN vote = 'B' THEN 1 ELSE 0 END) as bad_votes
                    from votes
                    where timestamp >= ?
                    group by unit''', [date_format, epoch])
        return c

    def close(self):
        # commit the changes to db
        self.conn.commit()

        # close the connection
        self.conn.close()
