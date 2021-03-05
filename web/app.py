import datetime
import sqlite3
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse

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
    conn = sqlite3.connect(DB)
    conn.create_function("power", 2, lambda x, y: x ** y)
    c = conn.cursor()
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
                        group by v.bot)
                    where good_votes + bad_votes >= ?
                    order by score desc''', [epoch, MINVOTES])

    rank = 0
    for row in c:
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
    conn.close()
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
                    where subreddit IS NOT NULL AND subreddit != '' AND timestamp >= ?
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
                from (select bot,
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
    conn = sqlite3.connect(DB)
    c = conn.cursor()

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
        c.execute('''select strftime('%H', timestamp, 'unixepoch') as unit,
                           sum(CASE WHEN vote = 'G' THEN 1 ELSE 0 END) as good_votes,
                           sum(CASE WHEN vote = 'B' THEN 1 ELSE 0 END) as bad_votes
                    from votes
                    where timestamp >= ?
                    group by unit''', [epoch])
        for row in c:
            key, good_votes, bad_votes = row
            results[str(int(key))] = {'good_votes': good_votes, 'bad_votes': bad_votes}

    elif 'w' in after:
        days_of_week = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        for day in days_of_week:
            results[day] = {'good_votes': 0, 'bad_votes': 0}
        c.execute('''select strftime('%w', timestamp, 'unixepoch') as unit,
                           sum(CASE WHEN vote = 'G' THEN 1 ELSE 0 END) as good_votes,
                           sum(CASE WHEN vote = 'B' THEN 1 ELSE 0 END) as bad_votes
                    from votes
                    where timestamp >= ?
                    group by unit''', [epoch])
        for row in c:
            key, good_votes, bad_votes = row
            results[days_of_week[int(key)]] = {'good_votes': good_votes, 'bad_votes': bad_votes}

    elif 'M' in after:
        for i in range(31):
            results[str(i)] = {'good_votes': 0, 'bad_votes': 0}
        c.execute('''select strftime('%d', timestamp, 'unixepoch') as unit,
                           sum(CASE WHEN vote = 'G' THEN 1 ELSE 0 END) as good_votes,
                           sum(CASE WHEN vote = 'B' THEN 1 ELSE 0 END) as bad_votes
                    from votes
                    where timestamp >= ?
                    group by unit''', [epoch])
        for row in c:
            key, good_votes, bad_votes = row
            results[str(int(key))] = {'good_votes': good_votes, 'bad_votes': bad_votes}

    else:
        months_of_year = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
        for month in months_of_year:
            results[month] = {'good_votes': 0, 'bad_votes': 0}
        c.execute('''select strftime('%m', timestamp, 'unixepoch') as unit,
                           sum(CASE WHEN vote = 'G' THEN 1 ELSE 0 END) as good_votes,
                           sum(CASE WHEN vote = 'B' THEN 1 ELSE 0 END) as bad_votes
                    from votes
                    where timestamp >= ?
                    group by unit''', [epoch])
        for row in c:
            key, good_votes, bad_votes = row
            results[months_of_year[int(key) - 1]] = {'good_votes': good_votes, 'bad_votes': bad_votes}

    for key in results:
        good_votes = results[key]['good_votes']
        bad_votes = results[key]['bad_votes']
        votes['labels'].append(key)
        votes['datasets'][2]['data'].append(good_votes + bad_votes)
        votes['datasets'][1]['data'].append(good_votes)
        votes['datasets'][0]['data'].append(bad_votes)

    conn.close()
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
