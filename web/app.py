import datetime
import calendar
import sqlite3
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from itertools import groupby
from math import sqrt

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

DB = '../app/votes.db'
MINVOTES = 3
TOP = 5


@app.get("/robots.txt")
async def robots():
    return FileResponse("static/robots.txt")


@app.get("/favicon.ico")
async def favicon():
    return FileResponse("static/icons/favicon.ico")


@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


def calculate_score(good_bots, bad_bots, karma):
    """Calculate the bot score."""
    # good_bots += int(karma / 10000)
    score = round(((good_bots + 1.9208) / (good_bots + bad_bots) - 1.96 * sqrt(
        (good_bots * bad_bots) / (good_bots + bad_bots) + 0.9604) / (good_bots + bad_bots)) / (
                              1 + 3.8416 / (good_bots + bad_bots)), 4)
    return score


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


@app.get('/api/ping')
async def ping():
    return 'pong'


@app.get('/api/getrank/{bot}')
async def get_bot_rank(bot: str):
    ranks = await get_ranks('1y')
    rank = next((x for x in ranks if x['bot'] == bot), None)
    if not rank:
        raise HTTPException(status_code=404, detail="Bot not found")
    return rank


@app.get('/api/getbadge/{bot}')
async def get_bot_rank(bot: str):
    ranks = await get_ranks('1y')
    rank = next((x for x in ranks if x['bot'] == bot), None)
    if not rank:
        raise HTTPException(status_code=404, detail="Bot not found")
    return {
        'schemaVersion': 1,
        'label': rank['bot'],
        'message': rank['rank'],
        'color': 'orange'
    }


async def get_ranks(after='1y'):
    epoch = get_epoch(after)
    ranks = []
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''select bot,
    			link_karma,
    			comment_karma,
    			good_votes,
    			bad_votes
                    from (select	v.bot,
    			            max(b.link_karma) as link_karma,
                            max(b.comment_karma) as comment_karma,
                            sum(CASE WHEN v.vote = 'G' THEN 1 ELSE 0 END) as good_votes,
                            sum(CASE WHEN v.vote = 'B' THEN 1 ELSE 0 END) as bad_votes
                        from (select * from votes where timestamp >= ?) v
                        inner join bots b on v.bot = b.bot
                        group by v.bot)
                    where good_votes + bad_votes >= ?''', [epoch, MINVOTES])

    for row in c:
        bot, link_karma, comment_karma, good_bots, bad_bots = row
        ranks.append(
            {
                'bot': bot,
                'score': calculate_score(good_bots, bad_bots, int(comment_karma + link_karma)),
                'good_bots': good_bots,
                'bad_bots': bad_bots,
                'comment_karma': int(comment_karma),
                'link_karma': int(link_karma)
            }
        )
    conn.close()
    ranks.sort(key=lambda x: x['score'], reverse=True)
    for count, _ in enumerate(ranks):
        ranks[count]['rank'] = count + 1
    return ranks


async def get_top_subs(count=TOP, after='1y'):
    epoch = get_epoch(after)
    subs = []
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    top_subs = {
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
    c.execute('''select subreddit, count(*) from votes
                    where subreddit IS NOT NULL AND subreddit != "" AND timestamp >= ?
                    group by subreddit
                    order by count(*) desc
                    limit ?''', [epoch, count])
    for row in c:
        subs.append({
            'labels': row[0],
            'data': row[1]
        })
    conn.close()

    for sub in subs:
        top_subs['labels'].append(sub['labels'])
        top_subs['datasets'][0]['data'].append(sub['data'])
    return top_subs


async def get_top_bots(count=TOP, after='1y'):
    epoch = get_epoch(after)
    bots = []
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    top_bots = {
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
    c.execute('''select bot,
			round((good_votes + 1) / (bad_votes + 1), 2)
                from (select	bot,
                        sum(CASE WHEN vote = 'G' THEN 1 ELSE 0 END) as good_votes,
                        sum(CASE WHEN vote = 'B' THEN 1 ELSE 0 END) as bad_votes
                    from (select * from votes where timestamp >= ?)
                    group by bot)
                group by bot
                order by round((good_votes + 1) / (bad_votes + 1), 2) DESC
                limit ?''', [epoch, count])
    for row in c:
        bots.append({
            'labels': row[0],
            'data': row[1]
        })
    conn.close()

    for bot in bots:
        top_bots['labels'].append(bot['labels'])
        top_bots['datasets'][0]['data'].append(bot['data'])
    return top_bots


async def get_pie(after='1y'):
    epoch = get_epoch(after)
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''select sum(CASE WHEN vote = 'G' THEN 1 ELSE 0 END) from votes where timestamp >= ?''', [epoch])
    total_gb = c.fetchone()[0]
    c.execute('''select sum(CASE WHEN vote = 'B' THEN 1 ELSE 0 END) from votes where timestamp >= ?''', [epoch])
    total_bb = c.fetchone()[0]
    conn.close()
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


async def get_votes(after='1y'):
    epoch = get_epoch(after)
    items = []
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''select timestamp, vote from votes where timestamp >= ?''', [epoch])
    for row in c:
        timestamp, vote = row
        items.append({
            'vote': vote,
            'datetime': datetime.datetime.fromtimestamp(timestamp)
        })
    conn.close()

    votes = {
        'labels': [],
        'datasets':
            [
                {
                    'label': 'Bad Bot Votes',
                    'data': [],
                    'backgroundColor': 'rgba(255, 0, 0, 1)'
                },
                {
                    'label': 'Good Bot Votes',
                    'data': [],
                    'backgroundColor': 'rgba(0, 0, 255, 1)'
                },
                {
                    'label': 'Total Votes',
                    'data': [],
                    'backgroundColor': 'rgba(128, 0, 128, 1)'
                }

            ]
    }
    if 'd' in after:
        items.sort(key=lambda x: x['datetime'].hour)
        group_by = groupby(items, key=lambda x: x['datetime'].hour)
    elif 'w' in after:
        items.sort(key=lambda x: x['datetime'].weekday())
        group_by = groupby(items, key=lambda x: calendar.day_name[x['datetime'].weekday()])
    elif 'M' in after:
        items.sort(key=lambda x: x['datetime'].day)
        group_by = groupby(items, key=lambda x: x['datetime'].day)
    else:
        items.sort(key=lambda x: x['datetime'].month)
        group_by = groupby(items, key=lambda x: calendar.month_name[x['datetime'].month])
    for key, group in group_by:
        votes['labels'].append(key)
        group_lst = list(group)
        good_bots = len(list(filter(lambda x: x['vote'] == 'G', group_lst)))
        bad_bots = len(list(filter(lambda x: x['vote'] == 'B', group_lst)))
        votes['datasets'][2]['data'].append(len(group_lst))
        votes['datasets'][1]['data'].append(good_bots)
        votes['datasets'][0]['data'].append(bad_bots)

    # This fills empty values in the votes line graph
    if 'd' in after:
        for _ in range(24 - len(votes['labels'])):
            for count, label in enumerate(votes['labels']):
                if (count == 0 and votes['labels'][-1] != label - 1 and label > 0) or (votes['labels'][count - 1] != label - 1 and label > 0):
                    votes['labels'].insert(count, label - 1)
                    votes['datasets'][2]['data'].insert(count, 0)
                    votes['datasets'][1]['data'].insert(count, 0)
                    votes['datasets'][0]['data'].insert(count, 0)
                    break
                if count + 1 == len(votes['labels']) and label != 23:
                    votes['labels'].append(label + 1)
                    votes['datasets'][2]['data'].append(0)
                    votes['datasets'][1]['data'].append(0)
                    votes['datasets'][0]['data'].append(0)
                    break
    return votes


@app.get('/api/getranks')
async def get_rank_data(request: Request):
    if 'after' in request.query_params:
        after = request.query_params['after']
    else:
        after = '1y'
    return await get_ranks(after)


@app.get('/api/getcharts')
async def get_chart_data(request: Request):
    if 'after' in request.query_params:
        after = request.query_params['after']
    else:
        after = '1y'

    votes = await get_votes(after)
    pie = await get_pie(after)
    top_subs = await get_top_subs(TOP, after)
    top_bots = await get_top_bots(TOP, after)

    return {
        'votes': votes,
        'pie': pie,
        'top_bots': top_bots,
        'top_subs': top_subs
    }
