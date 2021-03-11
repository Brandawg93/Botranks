import aiosqlite


class DB:
    def __init__(self, file, debug=False):
        self.file = file
        self.debug = debug
        self.conn = None

    async def connect(self):
        self.conn = await aiosqlite.connect(self.file)
        await self.conn.create_function("power", 2, lambda x, y: x ** y)

    async def _check_if_exists(self, table):
        # get the count of tables with the name
        c = await self.conn.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
                                    [table])

        # if the count is 1, then table exists
        return (await c.fetchone())[0] == 1

    async def get_lastest_vote(self):
        """Get the last updated time."""
        c = await self.conn.execute("SELECT timestamp from votes order by id DESC LIMIT 1")
        query = await c.fetchone()
        if query and len(query) > 0:
            return query[0]
        else:
            return None

    async def get_ranks(self, epoch, minvotes=3):
        """Get ranks from db."""
        c = await self.conn.execute('''select bot,
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
                        order by score desc, good_votes desc, bad_votes''', [epoch, minvotes])
        return c

    async def get_top_subs(self, epoch, limit=5):
        """Get top subreddits from db."""
        c = await self.conn.execute('''select subreddit, count(*) from votes
                        where subreddit IS NOT NULL AND subreddit != '' AND timestamp >= ?
                        group by subreddit
                        order by count(*) desc
                        limit ?''', [epoch, limit])
        return await c.fetchall()

    async def get_top_bots(self, epoch, limit=5):
        """Get top bots from db."""
        c = await self.conn.execute('''select bot, round((good_votes + 1) / (bad_votes + 1), 2)
                from (select bot,
                        sum(CASE WHEN vote = 'G' THEN 1 ELSE 0 END) as good_votes,
                        sum(CASE WHEN vote = 'B' THEN 1 ELSE 0 END) as bad_votes
                    from (select * from votes where timestamp >= ?) v
                    group by bot) v2
                group by bot
                order by round((good_votes + 1) / (bad_votes + 1), 2) DESC
                limit ?''', [epoch, limit])
        return await c.fetchall()

    async def get_vote_count(self, epoch, vote_type):
        """Get count of specific vote type."""
        c = await self.conn.execute('''select sum(CASE WHEN vote = ? THEN 1 ELSE 0 END)
                                 from votes where timestamp >= ? LIMIT 1''',
                                    [vote_type, epoch])
        return (await c.fetchone())[0]

    async def get_timeline_data(self, epoch, date_format):
        """Get data for timeline."""
        c = await self.conn.execute('''select strftime(?, timestamp, 'unixepoch') as unit,
                           sum(CASE WHEN vote = 'G' THEN 1 ELSE 0 END) as good_votes,
                           sum(CASE WHEN vote = 'B' THEN 1 ELSE 0 END) as bad_votes
                    from votes
                    where timestamp >= ?
                    group by unit''', [date_format, epoch])
        return c

    async def close(self):
        # commit the changes to db
        await self.conn.commit()

        # close the connection
        await self.conn.close()
