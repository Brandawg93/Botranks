import datetime
from db import DB
from models import Bot, Stats, Votes, Karma, VotesStats, BotsStats, Sub, Graph
from aiocache import cached
from aiocache.serializers import PickleSerializer

DB_FILE = '../votes.db'
TTL = 60


def get_epoch(after):
    """Get epoch from string."""
    length = abs(int(after[:-1]))
    l_type = after[-1]
    if l_type not in 'hdwMy':
        l_type = 'h'
    tdelta = None
    if l_type == 'h':
        tdelta = datetime.timedelta(hours=length)
    if l_type == 'd':
        tdelta = datetime.timedelta(days=length)
    if l_type == 'w':
        tdelta = datetime.timedelta(days=length * 7)
    if l_type == 'M':
        tdelta = datetime.timedelta(days=length * 30)
    if l_type == 'y':
        tdelta = datetime.timedelta(days=length * 365)
    return int((datetime.datetime.now() - tdelta).strftime('%s'))


@cached(ttl=TTL, serializer=PickleSerializer())
async def get_ranks(after='1y', sort='top', limit=None):
    if sort == 'hot':
        after = '1y'
    epoch = get_epoch(after)
    ranks = []
    db = DB(DB_FILE)
    await db.connect()
    data = await db.get_ranks(epoch, sort, limit)
    num = 1

    async for row in data:
        bot, link_karma, comment_karma, good_bots, bad_bots, top_score, hot_score, controversial_score = row
        rank = Bot()
        rank.name = bot
        rank.score = top_score
        votes = Votes()
        votes.good = good_bots
        votes.bad = bad_bots
        rank.votes = votes
        karma = Karma()
        karma.link = link_karma
        karma.comment = comment_karma
        rank.karma = karma
        ranks.append(rank)
    await db.close()
    for bot in sorted(ranks, key=lambda x: x.score, reverse=True):
        bot.rank = num
        num += 1
    return ranks


@cached(ttl=TTL, serializer=PickleSerializer())
async def get_stats(after='1y', vote=None):
    vote_type = None
    if vote:
        vote_type = vote.value
    stats = Stats()
    epoch = get_epoch(after)
    db = DB(DB_FILE)
    await db.connect()
    votes_stats = VotesStats()
    votes_stats.latest = await db.get_latest_vote(vote_type)
    votes_stats.count = await db.get_vote_count(epoch, vote_type)
    stats.votes = votes_stats
    bots_stats = BotsStats()
    bots_stats.count = await db.get_bot_count(epoch)
    stats.bots = bots_stats
    await db.close()
    return stats


@cached(ttl=TTL, serializer=PickleSerializer())
async def get_subs(after='1y', limit=None):
    epoch = get_epoch(after)
    db = DB(DB_FILE)
    subs = []
    await db.connect()
    data = await db.get_subs(epoch, limit)
    async for row in data:
        sub = Sub()
        sub.name = row[0]
        votes = Votes()
        votes.good = row[1]
        votes.bad = row[2]
        sub.votes = votes
        subs.append(sub)
    await db.close()
    return subs


@cached(ttl=TTL, serializer=PickleSerializer())
async def get_graph(after='1y'):
    epoch = get_epoch(after)
    db = DB(DB_FILE)
    await db.connect()

    results = {}
    if 'd' in after:
        for i in range(24):
            results[str(i)] = {'good_votes': 0, 'bad_votes': 0}
        data = await db.get_timeline_data(epoch, '%H')
        async for row in data:
            key, good_votes, bad_votes = row
            results[str(int(key))] = {'good_votes': good_votes, 'bad_votes': bad_votes}

    elif 'w' in after:
        days_of_week = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        for day in days_of_week:
            results[day] = {'good_votes': 0, 'bad_votes': 0}
        data = await db.get_timeline_data(epoch, '%w')
        async for row in data:
            key, good_votes, bad_votes = row
            results[days_of_week[int(key)]] = {'good_votes': good_votes, 'bad_votes': bad_votes}

    elif 'M' in after:
        for i in range(31):
            results[str(i)] = {'good_votes': 0, 'bad_votes': 0}
        data = await db.get_timeline_data(epoch, '%d')
        async for row in data:
            key, good_votes, bad_votes = row
            results[str(int(key))] = {'good_votes': good_votes, 'bad_votes': bad_votes}

    else:
        months_of_year = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
                          'October', 'November', 'December']
        for month in months_of_year:
            results[month] = {'good_votes': 0, 'bad_votes': 0}
        data = await db.get_timeline_data(epoch, '%m')
        async for row in data:
            key, good_votes, bad_votes = row
            results[months_of_year[int(key) - 1]] = {'good_votes': good_votes, 'bad_votes': bad_votes}

    graph = Graph()
    graph.labels = []
    graph.votes = []
    for key in results:
        good_votes = results[key]['good_votes']
        bad_votes = results[key]['bad_votes']
        graph.labels.append(key)
        votes = Votes()
        votes.good = good_votes
        votes.bad = bad_votes
        graph.votes.append(votes)

    await db.close()
    return graph
