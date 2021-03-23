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

    async def get_latest_vote(self):
        """Get the last updated time."""
        c = await self.conn.execute("SELECT timestamp from votes order by id DESC LIMIT 1")
        query = await c.fetchone()
        if query and len(query) > 0:
            return query[0]
        else:
            return None

    async def get_total_votes(self, epoch):
        """Get the total number of votes."""
        c = await self.conn.execute("SELECT count(id) from votes where timestamp >= ?", [epoch])
        query = await c.fetchone()
        if query and len(query) > 0:
            return query[0]
        else:
            return 0

    async def get_ranks(self, epoch, sort, minvotes=3):
        """Get ranks from db."""
        if sort not in ['top', 'hot', 'controversial']:
            sort = 'top'
        c = await self.conn.execute('''select v.bot,
                    b.link_karma,
                    b.comment_karma,
                    v.good_votes,
                    v.bad_votes,
                    ROUND(((v.good_votes + 1.9208) / (v.good_votes + v.bad_votes) - 1.96 * power(
                    (v.good_votes * v.bad_votes) / (v.good_votes + v.bad_votes) + 0.9604, 0.5) /
                    (v.good_votes + v.bad_votes)) / (
                    1 + 3.8416 / (v.good_votes + v.bad_votes)), 4) as top,
                    ROUND(((v.good_time + 1.9208) / (v.good_time + v.bad_time) - 1.96 * power(
                    (v.good_time * v.bad_time) / (v.good_time + v.bad_time) + 0.9604, 0.5) /
                    (v.good_time + v.bad_time)) / (
                    1 + 3.8416 / (v.good_time + v.bad_time)), 4) as hot,
                    (v.good_votes + v.bad_votes) / (abs(v.good_votes - v.bad_votes) + 1) as controversial
                        from (select bot,
                                count(CASE WHEN vote = 'G' THEN 1 END) as good_votes,
                                count(CASE WHEN vote = 'B' THEN 1 END) as bad_votes,
                                count(CASE WHEN vote = 'G' THEN 1 END)
                                    + (avg(CASE WHEN vote = 'G' THEN timestamp ELSE 0 END) / 1000000) as good_time,
                                count(CASE WHEN vote = 'B' THEN 1 END)
                                    + (avg(CASE WHEN vote = 'B' THEN timestamp ELSE 0 END) / 1000000) as bad_time
                            from votes
                            where timestamp >= ?
                            group by bot) v
                        inner join bots b on v.bot = b.bot
                        where v.good_votes + v.bad_votes >= ?
                        order by {} desc, v.good_votes desc, v.bad_votes'''.format(sort), [epoch, minvotes])
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
                    from votes
                    where timestamp >= ?
                    group by bot) v
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
