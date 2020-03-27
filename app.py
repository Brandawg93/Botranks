import aioboto3
import datetime
import calendar
from aiocache import cached
from aiocache.serializers import PickleSerializer
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from boto3.dynamodb.conditions import Attr
from itertools import groupby
from math import sqrt

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
cached_items = {}

MINVOTES = 2


@app.get("/robots.txt")
async def robots():
    return FileResponse("static/robots.txt")


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


@cached(ttl=60, serializer=PickleSerializer())
async def get_items_from_db(after):
    global cached_items
    db_table = 'Votes'
    epoch = get_epoch(after)
    items = cached_items.get('items')
    last_update = cached_items.get('last_update')

    async with aioboto3.resource('dynamodb', region_name='us-east-1', verify=False) as dynamodb:
        table = dynamodb.Table(db_table)
        if items:
            response = await table.scan(
                FilterExpression=Attr('timestamp').gt(last_update)
            )
            items += response['Items']
        else:
            response = await table.scan()
            items = response['Items']
            while response.get('LastEvaluatedKey'):
                response = await table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                items.extend(response['Items'])

    last_update = int((datetime.datetime.now()).strftime('%s'))
    cached_items['last_update'] = last_update
    cached_items['items'] = items
    return list(filter(lambda x: x['timestamp'] > epoch, items))


@app.get('/api/getrank')
async def get_bot_rank(request: Request):
    bot = request.query_params['bot']
    if bot:
        items = await get_items_from_db('1y')
        ranks = await get_ranks(items)
        rank = [x for x in ranks if x['bot'] == bot]
        return {
            "statusCode": 200,
            "body": rank[0] if len(rank) > 0 else None
        }
    return {
        "statusCode": 400,
        "body": "Please specify a bot"
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
