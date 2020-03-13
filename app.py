import flask
import boto3
import datetime
import calendar
from boto3.dynamodb.conditions import Attr
from itertools import groupby
from math import sqrt

app = flask.Flask(__name__, static_folder='static', static_url_path='')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

MINVOTES = 2


@app.route('/')
def index():
    """Displays the index page accessible at '/'."""
    return flask.render_template('index.html')


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


@app.route('/api/getranks')
def get_ranks():
    after = flask.request.args.get('after')
    if not after:
        after = '1y'
    db_table = 'Votes'
    epoch = get_epoch(after)
    table = dynamodb.Table(db_table)
    response = table.scan(
        FilterExpression=Attr('timestamp').gt(epoch)
    )
    items = response['Items']
    ranks = []
    total_gb = 0
    total_bb = 0
    for key, group in groupby(items, key=lambda x: x['bot']):
        good_bots = 0
        bad_bots = 0
        comment_karma = 0
        link_karma = 0
        for vote in group:
            if vote['vote'] == 'G':
                good_bots += 1
                total_gb += 1
            if vote['vote'] == 'B':
                bad_bots += 1
                total_bb += 1
            if vote['comment_karma'] > comment_karma:
                comment_karma = vote['comment_karma']
            if vote['link_karma'] > link_karma:
                link_karma = vote['link_karma']
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
    for item in items:
        item['datetime'] = datetime.datetime.fromtimestamp(item['timestamp'])
        if 'subreddit' not in item:
            item['subreddit'] = 'NA'

    items.sort(key=lambda x: x['subreddit'])
    top_subs = {
        'labels': [],
        'datasets':
            [
                {
                    'data': [],
                    'backgroundColor': ['rgba(0, 255, 0, 1)', 'rgba(255, 0, 0, 1)', 'rgba(0, 0, 255, 1)', 'rgba(255, 255, 0, 1)', 'rgba(255, 0, 255, 1)']
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
    top_bots = {
        'labels': [],
        'datasets':
            [
                {
                    'data': [],
                    'backgroundColor': ['rgba(0, 255, 0, 1)', 'rgba(255, 0, 0, 1)', 'rgba(0, 0, 255, 1)', 'rgba(255, 255, 0, 1)', 'rgba(255, 0, 255, 1)']
                }
            ]
    }
    for bot in ranks[:5]:
        top_bots['labels'].append(bot['bot'])
        top_bots['datasets'][0]['data'].append(round((bot['good_bots'] + 1) / (bot['bad_bots'] + 1), 2))
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
        lst = list(group)
        good_count = 0
        bad_count = 0
        for item in lst:
            if item['vote'] == 'G':
                good_count += 1
            if item['vote'] == 'B':
                bad_count += 1
        votes['datasets'][2]['data'].append(len(lst))
        votes['datasets'][1]['data'].append(good_count)
        votes['datasets'][0]['data'].append(bad_count)

    response = {
        'ranks': ranks,
        'votes': votes,
        'pie': pie,
        'top_bots': top_bots,
        'top_subs': top_subs
    }
    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "headers": {},
        "multiValueHeaders": {},
        "body": response
    }


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=443)
