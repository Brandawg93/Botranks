import datetime
from db import DB
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

DB_FILE = '../votes.db'


@app.get("/robots.txt")
async def robots():
    return FileResponse("static/robots.txt")


@app.get("/favicon.ico")
async def favicon():
    return FileResponse("static/icons/favicon.ico")


@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/about")
async def read_about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})


@app.get("/stats")
async def read_stats(request: Request):
    return templates.TemplateResponse("stats.html", {"request": request})


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
        'message': str(rank['rank']),
        'color': 'orange'
    }


async def get_ranks(after='1y'):
    epoch = get_epoch(after)
    ranks = []
    db = DB(DB_FILE)
    await db.connect()
    data = await db.get_ranks(epoch)
    rank = 0

    async for row in data:
        bot, link_karma, comment_karma, good_bots, bad_bots, score = row
        rank += 1
        ranks.append(
            {
                'rank': rank,
                'bot': bot,
                'score': score,
                'good_bots': good_bots,
                'bad_bots': bad_bots,
                'comment_karma': comment_karma,
                'link_karma': link_karma
            }
        )
    await db.close()
    return ranks


async def get_latest_vote():
    db = DB(DB_FILE)
    await db.connect()
    last_update = await db.get_latest_vote()
    await db.close()
    return last_update


async def get_total_votes(after='1y'):
    epoch = get_epoch(after)
    db = DB(DB_FILE)
    await db.connect()
    total_votes = await db.get_total_votes(epoch)
    await db.close()
    return total_votes


def _create_top_chart_dataset(data):
    arr = []
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
        arr.append({
            'labels': row[0],
            'data': row[1]
        })

    for elm in arr:
        top['labels'].append(elm['labels'])
        top['datasets'][0]['data'].append(elm['data'])
    return top


async def get_top_subs(after='1y'):
    epoch = get_epoch(after)
    db = DB(DB_FILE)
    await db.connect()
    data = await db.get_top_subs(epoch)
    await db.close()
    return _create_top_chart_dataset(data)


async def get_top_bots(after='1y'):
    epoch = get_epoch(after)
    db = DB(DB_FILE)
    await db.connect()
    data = await db.get_top_bots(epoch)
    await db.close()
    return _create_top_chart_dataset(data)


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


@app.get('/api/getranks')
async def get_rank_data(request: Request):
    if 'after' in request.query_params:
        after = request.query_params['after']
    else:
        after = '1y'
    return {
        'data': await get_ranks(after),
        'latest_vote': await get_latest_vote(),
        'vote_count': await get_total_votes(after)
    }


@app.get('/api/getcharts')
async def get_chart_data(request: Request):
    if 'after' in request.query_params:
        after = request.query_params['after']
    else:
        after = '1y'

    votes = await get_votes(after)
    pie = await get_pie(after)
    top_subs = await get_top_subs(after)
    top_bots = await get_top_bots(after)

    return {
        'votes': votes,
        'pie': pie,
        'top_bots': top_bots,
        'top_subs': top_subs
    }
