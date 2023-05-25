import { DB } from './db';
import { SortType, VoteType, GraphType } from './types';

const DB_FILE = '../votes.db';

const getEpoch = (after: string) => {
  // Get epoch from string.
  const length = Math.abs(parseInt(after.slice(0, -1)));
  const lType = after.slice(-1);
  const hour = 60 * 60 * 1000;
  const day = hour * 24;
  const week = day * 7;
  const month = day * 30;
  const year = day * 365;
  let timeDelta;
  switch (lType) {
    case 'h':
      timeDelta = hour;
      break;
    case 'd':
      timeDelta = day;
      break;
    case 'w':
      timeDelta = week;
      break;
    case 'M':
      timeDelta = month;
      break;
    case 'y':
      timeDelta = year;
      break;
    default:
      timeDelta = hour;
      break;
  }
  return Math.floor((Date.now() - timeDelta * length) / 1000);
};

export const getRanks = (after = '1y', sort: SortType = 'top', bot?: string, limit?: number) => {
  if (sort === 'hot') {
    after = '1y';
  }
  const ranks: Array<any> = [];
  const epoch = getEpoch(after);
  const db = new DB(DB_FILE);
  db.connect();
  const data = db.getRanks(epoch, sort, limit, bot);
  db.close();
  data?.forEach((value) => {
    const { rank: rank_num, bot, link_karma, comment_karma, good_votes, bad_votes, top: top_score } = value;
    ranks.push({
      rank: rank_num,
      name: bot,
      score: top_score,
      votes: {
        good: good_votes,
        bad: bad_votes,
      },
      karma: {
        link: link_karma,
        comment: comment_karma,
      },
    });
  });
  return ranks;
};

export const getSubs = (after = '1y', limit?: number) => {
  const epoch = getEpoch(after);
  const subs: Array<any> = [];
  const db = new DB(DB_FILE);
  db.connect();
  const data = db.getSubs(epoch, limit);
  db.close();
  data?.forEach((sub) => {
    const { name, good_votes, bad_votes } = sub;
    subs.push({
      name: name,
      votes: {
        good: good_votes,
        bad: bad_votes,
      },
    });
  });
  return subs;
};

export const getGraph = (after = '1y') => {
  const epoch = getEpoch(after);
  const db = new DB(DB_FILE);
  db.connect();
  const lType = after.slice(-1);
  const results: any = {};
  let data;
  switch (lType) {
    case 'd':
      for (let i = 0; i < 24; i++) {
        results[i.toString()] = { good_votes: 0, bad_votes: 0 };
      }
      data = db.getTimelineData(epoch, '%H');
      data?.forEach((value) => {
        const { key, good_votes, bad_votes } = value;
        results[key] = { good_votes: good_votes, bad_votes: bad_votes };
      });
      break;
    case 'w':
      const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
      days.forEach((day) => {
        results[day] = { good_votes: 0, bad_votes: 0 };
      });
      data = db.getTimelineData(epoch, '%w');
      data?.forEach((value) => {
        const { key, good_votes, bad_votes } = value;
        results[days[parseInt(key)]] = { good_votes: good_votes, bad_votes: bad_votes };
      });
      break;
    case 'M':
      for (let i = 0; i < 31; i++) {
        results[i.toString()] = { good_votes: 0, bad_votes: 0 };
      }
      data = db.getTimelineData(epoch, '%d');
      data?.forEach((value) => {
        const { key, good_votes, bad_votes } = value;
        results[key] = { good_votes: good_votes, bad_votes: bad_votes };
      });
      break;
    case 'y':
    default:
      const months = [
        'January',
        'February',
        'March',
        'April',
        'May',
        'June',
        'July',
        'August',
        'September',
        'October',
        'November',
        'December',
      ];
      months.forEach((month) => {
        results[month] = { good_votes: 0, bad_votes: 0 };
      });
      data = db.getTimelineData(epoch, '%m');
      data?.forEach((value) => {
        const { key, good_votes, bad_votes } = value;
        results[months[parseInt(key) - 1]] = { good_votes: good_votes, bad_votes: bad_votes };
      });
      break;
  }
  db.close();
  const graph: GraphType = {
    labels: [],
    votes: [],
  };

  Object.keys(results).forEach((value: string) => {
    graph.labels.push(value);
    graph.votes.push({
      good: results[value].good_votes,
      bad: results[value].bad_votes,
    });
  });
  return graph;
};

export const getStats = (after = '1y', voteType?: VoteType) => {
  const epoch = getEpoch(after);
  const db = new DB(DB_FILE);
  db.connect();
  const count = db.getVoteCount(epoch, voteType);
  const botCount = db.getBotCount(epoch);
  const latestVote = db.getLatestVote(voteType);
  db.close();
  return {
    votes: {
      count: count,
      latest: latestVote,
    },
    bots: {
      count: botCount,
    },
  };
};
