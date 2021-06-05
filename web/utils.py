import datetime
from db import DB
from models import Bot, Stats, Votes, Karma, VotesStats, BotsStats
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
async def get_stats(after='1y', vote_type=None):
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


def _create_top_chart_dataset(data):
    top = {
        'labels': [],
        'datasets':
            [
                {
                    'data': [],
                    'backgroundColor': [
                        'rgba(0, 255, 0, 1)',
                        'rgba(255, 0, 0, 1)',
                        'rgba(0, 0, 255, 1)',
                        'rgba(255, 255, 0, 1)',
                        'rgba(255, 0, 255, 1)'
                    ]
                }
            ]
    }
    for row in data:
        top['labels'].append(row[0])
        top['datasets'][0]['data'].append(row[1])
    return top


@cached(ttl=TTL, serializer=PickleSerializer())
async def get_top_subs(after='1y'):
    epoch = get_epoch(after)
    db = DB(DB_FILE)
    await db.connect()
    data = await db.get_top_subs(epoch)
    await db.close()
    return _create_top_chart_dataset(data)


@cached(ttl=TTL, serializer=PickleSerializer())
async def get_top_bots(after='1y'):
    epoch = get_epoch(after)
    db = DB(DB_FILE)
    await db.connect()
    data = await db.get_top_bots(epoch)
    await db.close()
    return _create_top_chart_dataset(data)


@cached(ttl=TTL, serializer=PickleSerializer())
async def get_pie(after='1y'):
    epoch = get_epoch(after)
    db = DB(DB_FILE)
    await db.connect()
    total_gb = await db.get_vote_count(epoch, 'G')
    total_bb = await db.get_vote_count(epoch, 'B')
    await db.close()
    return {
        'labels': ['Good Bot Votes', 'Bad Bot Votes'],
        'datasets':
            [
                {
                    'data': [total_gb, total_bb],
                    'backgroundColor': ['rgba(0, 255, 0, 1)', 'rgba(255, 0, 0, 1)']
                }
            ]
    }


@cached(ttl=TTL, serializer=PickleSerializer())
async def get_votes(after='1y'):
    epoch = get_epoch(after)
    db = DB(DB_FILE)
    await db.connect()

    votes = {
        'labels': [],
        'datasets':
            [
                {
                    'label': 'Bad Bot Votes',
                    'data': [],
                    'fill': True,
                    'tension': 0.4,
                    'backgroundColor': 'rgba(255, 0, 0, 1)'
                },
                {
                    'label': 'Good Bot Votes',
                    'data': [],
                    'fill': True,
                    'tension': 0.4,
                    'backgroundColor': 'rgba(0, 0, 255, 1)'
                },
                {
                    'label': 'Total Votes',
                    'data': [],
                    'fill': True,
                    'tension': 0.4,
                    'backgroundColor': 'rgba(128, 0, 128, 1)'
                }

            ]
    }
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

    for key in results:
        good_votes = results[key]['good_votes']
        bad_votes = results[key]['bad_votes']
        votes['labels'].append(key)
        votes['datasets'][2]['data'].append(good_votes + bad_votes)
        votes['datasets'][1]['data'].append(good_votes)
        votes['datasets'][0]['data'].append(bad_votes)

    await db.close()
    return votes
