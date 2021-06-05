from graphql.execution.executors.asyncio import AsyncioExecutor
from graphql import GraphQLError
from graphene import Schema
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from starlette.graphql import GraphQLApp
from graphene import ObjectType, Int, List, String, Field
from models import Bot, Stats, VoteType
from utils import get_ranks, get_stats, get_votes, get_pie, get_top_bots, get_top_subs


class Query(ObjectType):
    bot = Field(Bot, name=String())
    bots = List(Bot,
                after=String(default_value="1y"),
                sort=String(default_value="top"),
                limit=Int(),
                description="Lists of all ranks")
    stats = Field(Stats,
                  after=String(default_value="1y"),
                  vote_type=VoteType())

    async def resolve_bot(self, info, name):
        all_ranks = await get_ranks('1y')
        rank = next((x for x in all_ranks if x.name == name), None)
        if not rank:
            raise GraphQLError("Bot not found")
        return rank

    async def resolve_bots(self, info, after, sort, limit=None):
        return await get_ranks(after, sort, limit)

    async def resolve_stats(self, info, after, vote_type=None):
        return await get_stats(after, vote_type)


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_route("/graphql", GraphQLApp(schema=Schema(query=Query), executor_class=AsyncioExecutor))
templates = Jinja2Templates(directory="templates")


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


@app.get('/api/ping')
async def ping():
    return 'pong'


@app.get('/api/getrank/{bot}')
async def get_bot_rank(bot: str):
    ranks = await get_ranks('1y')
    rank = next((x for x in ranks if x.name == bot), None)
    if not rank:
        raise HTTPException(status_code=404, detail="Bot not found")
    return rank


@app.get('/api/getbadge/{bot}')
async def get_bot_rank(bot: str):
    ranks = await get_ranks('1y')
    rank = next((x for x in ranks if x.name == bot), None)
    if not rank:
        raise HTTPException(status_code=404, detail="Bot not found")
    return {
        'schemaVersion': 1,
        'label': rank.name,
        'message': str(rank.rank),
        'color': 'orange'
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
