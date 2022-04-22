from graphql import GraphQLError
from graphene import Schema
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from starlette_graphene3 import GraphQLApp, make_graphiql_handler
from graphene import ObjectType, Int, List, String, Field
from models import Bot, Stats, Sub, VoteType, Graph
from utils import get_ranks, get_stats, get_graph, get_subs


class Query(ObjectType):
    bot = Field(Bot, name=String())
    bots = List(Bot,
                after=String(default_value="1y"),
                sort=String(default_value="top"),
                limit=Int(),
                description="List of all ranks")
    subs = List(Sub,
                after=String(default_value="1y"),
                limit=Int(),
                description="List of all subreddits with votes")
    graph = Field(Graph,
                  after=String(default_value="1y"),
                  description="Graph data")
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

    async def resolve_subs(self, info, after, limit=None):
        return await get_subs(after, limit)

    async def resolve_graph(self, info, after):
        return await get_graph(after)


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_route("/graphql", GraphQLApp(schema=Schema(query=Query), on_get=make_graphiql_handler()))
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
