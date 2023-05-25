import { buildSchema } from 'graphql';

// Construct a schema, using GraphQL schema language
const schema = buildSchema(`
  type Query {
    bot(name: String!): Bot
    "List of all ranks"
    bots(after: String = "1y", sort: String = "top"): [Bot]
    "List of all subreddits with votes"
    subs(after: String = "1y", limit: Int): [Sub]
    graph(after: String = "1y"): Graph
    stats(after: String = "1y", voteType: VoteType): Stats
  }
  type Bot {
    rank: Int
    name: String
    score: Float
    votes: Votes
    karma: Karma
  }
  type Votes {
    good: Int
    bad: Int
  }
  type Karma {
    link: Int
    comment: Int
  }
  type Sub {
    name: String
    votes: Votes
  }
  type Graph {
    labels: [String]
    votes: [Votes]
  }
  enum VoteType {
    GOOD
    BAD
  }
  type Stats {
    votes: VotesStats
    bots: BotsStats
  }
  type VotesStats {
    "Epoch of the latest vote"
    latest: Int
    "Total number of votes"
    count: Int
  }
  type BotsStats {
    "Total number of ranked bots"
    count: Int
  }
`);

export default schema;
