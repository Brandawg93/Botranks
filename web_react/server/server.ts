import express, { Express, Request, Response } from 'express';
import { graphqlHTTP } from 'express-graphql';
import { GraphQLError } from 'graphql';
import path from 'path';
import cors from 'cors';
import schema from './schema';
import { getRanks, getSubs, getStats, getGraph } from './utils';

// The root provides a resolver function for each API endpoint
const root = {
  bot: (params: any) => {
    const ranks = getRanks('1y', undefined, params.name);
    if (!ranks) {
      throw new GraphQLError('Bot not found.');
    }
    return ranks[0];
  },
  bots: (params: any) => {
    return getRanks(params.after, params.sort);
  },
  subs: (params: any) => {
    return getSubs(params.after, params.limit);
  },
  graph: (params: any) => {
    return getGraph(params.after);
  },
  stats: (params: any) => {
    return getStats(params.after, params.vote_type);
  },
};

const app: Express = express();
const port = 8080;

app.use(cors());
app.use(express.json());

app.use(express.static(path.join(__dirname, '../client/build')));

app.get('/api/ping', (req: Request, res: Response) => {
  res.send('pong');
});

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, '../client/build/index.html'));
});

app.get('/api/getrank/:bot', (req, res) => {
  const ranks = getRanks('1y', undefined, req.params.bot);
  if (ranks && ranks.length > 0) {
    return res.send(ranks[0]);
  }
  return res.status(404).send('Bot not found');
});

app.get('/api/getbadge/:bot', (req, res) => {
  const ranks = getRanks('1y', undefined, req.params.bot);
  if (ranks && ranks.length > 0) {
    return res.send({
      schemaVersion: 1,
      label: ranks[0].name,
      message: ranks[0].rank.toString(),
      color: 'orange',
    });
  }
  return res.status(404).send('Bot not found');
});

app.all(
  '/graphql',
  graphqlHTTP({
    schema: schema,
    rootValue: root,
    graphiql: true,
  }),
);

app.listen(port, () => {
  console.log(`⚡️[server]: Server is running at http://localhost:${port}`);
});
