import flask
import boto3
import datetime
from boto3.dynamodb.conditions import Attr
from itertools import groupby
from math import sqrt

app = flask.Flask(__name__)
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')


@app.route('/')
def index():
    """Displays the index page accessible at '/'"""
    return flask.render_template('index.html')


def calculate_score(good_bots, bad_bots):
    """Calculate the bot score."""
    score = round(((good_bots + 1.9208) / (good_bots + bad_bots) - 1.96 * sqrt((good_bots * bad_bots) / (good_bots + bad_bots) + 0.9604) / (good_bots + bad_bots)) / (1 + 3.8416 / (good_bots + bad_bots)),4)
    return score


def get_epoch(after):
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
        tdelta = datetime.timedelta(days=length*7)
    if l_type == 'M':
        tdelta = datetime.timedelta(days=length*30)
    if l_type == 'y':
        tdelta = datetime.timedelta(days=length*365)
    return int((datetime.datetime.now() - tdelta).strftime('%s'))


@app.route('/api/getranks')
def lambda_handler():
    after = flask.request.args.get('after')
    if not after:
        after = '1d'
    db_table = 'VotesTest'
    epoch = get_epoch(after)
    table = dynamodb.Table(db_table)
    response = table.scan(
        FilterExpression=Attr('timestamp').gt(epoch)
    )
    items = response['Items']
    ranks = []
    for key, group in groupby(items, key=lambda x: x['bot']):
        good_bots = 0
        bad_bots = 0
        for vote in group:
            if vote['vote'] == 'G':
                good_bots += 1
            if vote['vote'] == 'B':
                bad_bots += 1

        ranks.append(
            {
                'bot': key,
                'score': calculate_score(good_bots, bad_bots),
                'good_bots': good_bots,
                'bad_bots': bad_bots
            }
        )
    ranks.sort(key=lambda x: x['score'], reverse=True)
    for i in range(len(ranks)):
        ranks[i]['rank'] = i + 1
    total_times = [datetime.datetime.fromtimestamp(x['timestamp']) for x in items]
    good_times = [datetime.datetime.fromtimestamp(x['timestamp']) for x in items if x['vote'] == 'G']
    bad_times = [datetime.datetime.fromtimestamp(x['timestamp']) for x in items if x['vote'] == 'B']

    total_times.sort()
    good_times.sort()
    bad_times.sort()
    votes = {
        'labels': [],
        'datasets':
        [
            {
                'label': 'Total Votes',
                'data': []
            },
            {
                'label': 'Good Bot Votes',
                'data': []
            },
            {
                'label': 'Bad Bot Votes',
                'data': []
            }
        ]
    }
    for key, group in groupby(total_times, key=lambda x: x.hour):
        votes['labels'].append(key)
        votes['datasets'][0]['data'].append(len(list(group)))
    for key, group in groupby(good_times, key=lambda x: x.hour):
        votes['datasets'][1]['data'].append(len(list(group)))
    for key, group in groupby(bad_times, key=lambda x: x.hour):
        votes['datasets'][2]['data'].append(len(list(group)))

    response = {
        'ranks': ranks,
        'votes': votes
    }
    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "headers": {},
        "multiValueHeaders": {},
        "body": response
    }


if __name__ == '__main__':
    app.run()
