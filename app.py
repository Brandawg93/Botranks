import aioboto3
import datetime
import calendar
import asyncio
from aiocache import cached
from aiocache.serializers import PickleSerializer
from timeloop import Timeloop
from datetime import timedelta
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from itertools import groupby
from math import sqrt

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
timer = Timeloop()
cached_items = []

UPDATE_INTERVAL = 600
MINVOTES = 3


@app.get("/robots.txt")
async def robots():
    return FileResponse("static/robots.txt")


@app.get("/favicon.ico")
async def favicon():
    return FileResponse("static/favicon.ico")


@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


def calculate_score(good_bots, bad_bots):
    """Calculate the bot score."""
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


@timer.job(interval=timedelta(seconds=UPDATE_INTERVAL))
def update_items():
    """Run the process asynchronously on a timer."""
    asyncio.run(update_items_from_db())


@app.on_event('startup')
async def start_timer():
    await update_items_from_db()
    timer.start(False)


@app.on_event('shutdown')
async def stop_timer():
    timer.stop()


async def update_items_from_db():
    global cached_items
    db_table = 'Votes'
    async with aioboto3.resource('dynamodb', region_name='us-east-1', verify=False) as dynamodb:
        table = dynamodb.Table(db_table)
        response = await table.scan()
        items = response['Items']
        while response.get('LastEvaluatedKey'):
            response = await table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response['Items'])

        cached_items = items


@cached(ttl=60, serializer=PickleSerializer())
async def get_items_from_db(after='1y'):
    epoch = get_epoch(after)
    return list(filter(lambda x: x['timestamp'] > epoch, cached_items))


@app.get('/api/getrank/{bot}')
async def get_bot_rank(bot: str):
    items = await get_items_from_db('1y')
    ranks = await get_ranks(items)
    rank = [x for x in ranks if x['bot'] == bot]
    if not rank:
        raise HTTPException(status_code=404, detail="Bot not found")
    return {
        "statusCode": 200,
        "body": rank[0] if len(rank) > 0 else None
    }


async def get_ranks(items):
    ranks = []
    for key, group in groupby(items, key=lambda x: x['bot']):
        group_lst = list(group)
        good_bots = len(list(filter(lambda x: x['vote'] == 'G', group_lst)))
        bad_bots = len(list(filter(lambda x: x['vote'] == 'B', group_lst)))
        comment_karma = max(x['comment_karma'] for x in group_lst)
        link_karma = max(x['link_karma'] for x in group_lst)
        if good_bots + bad_bots >= MINVOTES:
            ranks.append(
                {
                    'bot': key,
                    'score': calculate_score(good_bots, bad_bots),
                    'good_bots': good_bots,
                    'bad_bots': bad_bots,
                    'comment_karma': int(comment_karma),
                    'link_karma': int(link_karma)
                }
            )
    ranks.sort(key=lambda x: x['score'], reverse=True)
    for count, _ in enumerate(ranks):
        ranks[count]['rank'] = count + 1
    return ranks


async def get_top_subs(items):
    items.sort(key=lambda x: x['subreddit'])
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
    subs = []
    for key, group in groupby(items, key=lambda x: x['subreddit']):
        if key and key != 'NA':
            subs.append({
                'labels': key,
                'data': len(list(group))
            })
    subs.sort(key=lambda x: x['data'], reverse=True)
    for sub in subs[:5]:
        top_subs['labels'].append(sub['labels'])
        top_subs['datasets'][0]['data'].append(sub['data'])
    return top_subs


async def get_top_bots(items):
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
    for bot in items:
        top_bots['labels'].append(bot['bot'])
        top_bots['datasets'][0]['data'].append(round((bot['good_bots'] + 1) / (bot['bad_bots'] + 1), 2))
    return top_bots


@app.get('/api/getdata')
async def get_data(request: Request):
    after = request.query_params['after']
    if not after:
        after = '1y'
    items = await get_items_from_db(after)
    ranks = await get_ranks(items)
    for item in items:
        item['datetime'] = datetime.datetime.fromtimestamp(item['timestamp'])
        if 'subreddit' not in item:
            item['subreddit'] = 'NA'

    top_subs = await get_top_subs(items)
    items.sort(key=lambda x: x['timestamp'])
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
    total_gb = len(list(filter(lambda x: x['vote'] == 'G', items)))
    total_bb = len(list(filter(lambda x: x['vote'] == 'B', items)))
    pie = {
        'labels': ['Good Bot Votes', 'Bad Bot Votes'],
        'datasets':
            [
                {
                    'data': [total_gb, total_bb],
                    'backgroundColor': ['rgba(0, 255, 0, 1)', 'rgba(255, 0, 0, 1)']
                }
            ]
    }
    top_bots = await get_top_bots(ranks[:5])
    if 'd' in after:
        group_by = groupby(items, key=lambda x: x['datetime'].hour)
    elif 'w' in after:
        group_by = groupby(items, key=lambda x: calendar.day_name[x['datetime'].weekday()])
    elif 'M' in after:
        group_by = groupby(items, key=lambda x: x['datetime'].day)
    else:
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
        while len(votes['labels']) < 24:
            inserts = []
            for count, label in enumerate(votes['labels']):
                if count == 0 and votes['labels'][-1] != label - 1 and label > 0:
                    inserts.append({'count': count, 'label': label - 1})
                elif votes['labels'][count - 1] != label - 1 and label > 0:
                    inserts.append({'count': count + 1, 'label': label - 1})
            for insert in inserts:
                votes['labels'].insert(insert['count'], insert['label'])
                votes['datasets'][2]['data'].insert(insert['count'], 0)
                votes['datasets'][1]['data'].insert(insert['count'], 0)
                votes['datasets'][0]['data'].insert(insert['count'], 0)

    response = {
        'ranks': ranks,
        'votes': votes,
        'pie': pie,
        'top_bots': top_bots,
        'top_subs': top_subs
    }
    return {
        "statusCode": 200,
        "body": response
    }
