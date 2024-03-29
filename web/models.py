from graphene import ObjectType, String, Float, Int, Enum, Field, List


class VoteType(Enum):
    GOOD = 'G'
    BAD = 'B'


class VotesStats(ObjectType):
    latest = Int(description="Epoch of the latest vote")
    count = Int(description="Total number of votes")


class BotsStats(ObjectType):
    count = Int(description="Total number of ranked bots")


class Stats(ObjectType):
    votes = Field(VotesStats)
    bots = Field(BotsStats)


class Votes(ObjectType):
    good = Int()
    bad = Int()


class Graph(ObjectType):
    labels = List(String)
    votes = List(Votes)


class Karma(ObjectType):
    link = Int()
    comment = Int()


class Bot(ObjectType):
    rank = Int()
    name = String()
    score = Float()
    votes = Field(Votes)
    karma = Field(Karma)


class Sub(ObjectType):
    name = String()
    votes = Field(Votes)
