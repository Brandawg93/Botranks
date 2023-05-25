import Database, { Database as DBType } from 'better-sqlite3';
import { VoteType, SortType } from './types';

const MINVOTES = 3;

export class DB {
  file: string;
  debug: boolean;
  conn: DBType | null;

  constructor(file: string, debug = false) {
    this.file = file;
    this.debug = debug;
    this.conn = null;
  }

  connect() {
    this.conn = new Database(this.file);
    this.conn.pragma('journal_mode = WAL');
    this.conn.function('power', (x, y) => x ** y);
    this.conn.function('hot_weight', (x, y) => x / (x - y) ** 2);
  }

  getLatestVote(voteType?: VoteType) {
    // Get the last updated time.
    if (voteType) {
      const stmt = this.conn?.prepare('SELECT timestamp from votes where vote = ? order by id DESC LIMIT 1');
      return stmt?.get(voteType);
    }
    const stmt = this.conn?.prepare('SELECT timestamp from votes order by id DESC LIMIT 1');
    return stmt?.pluck().get();
  }

  getRanks(epoch: number, sort: SortType, limit?: number, bot?: string, minvotes?: number) {
    if (typeof minvotes === 'undefined') {
      minvotes = MINVOTES;
    }
    let whereStr = '';
    if (bot) {
      whereStr = `where bot = \'${bot}\'`;
    }
    let limitStr = '';
    if (limit) {
      limitStr = `LIMIT ${limit}`;
    }
    const now = Math.floor(Date.now() / 1000);
    const stmt = this.conn?.prepare(`select *
    from (
        select
        row_number () over (
            order by ${sort} desc, good_votes desc, bad_votes
        ) rank, *
        from (
            select v.bot,
            b.link_karma,
            b.comment_karma,
            v.good_votes,
            v.bad_votes,
            ROUND(((v.good_votes + 1.9208) / (v.good_votes + v.bad_votes) - 1.96 * power(
            (v.good_votes * v.bad_votes) / (v.good_votes + v.bad_votes) + 0.9604, 0.5) /
            (v.good_votes + v.bad_votes)) / (
            1 + 3.8416 / (v.good_votes + v.bad_votes)), 4) as top,
            ((v.good_time + 1.9208) / (v.good_time + v.bad_time) - 1.96 * power(
            (v.good_time * v.bad_time) / (v.good_time + v.bad_time) + 0.9604, 0.5) /
            (v.good_time + v.bad_time)) / (
            1 + 3.8416 / (v.good_time + v.bad_time)) as hot,
            (v.good_votes + v.bad_votes) / (abs(v.good_votes - v.bad_votes) + 1) as controversial
                from (select bot,
                        count(CASE WHEN vote = 'G' THEN 1 END) as good_votes,
                        count(CASE WHEN vote = 'B' THEN 1 END) as bad_votes,
                        sum(CASE WHEN vote = 'G' THEN hot_weight(${now}, timestamp) ELSE 0 END) as good_time,
                        sum(CASE WHEN vote = 'B' THEN hot_weight(${now}, timestamp) ELSE 0 END) as bad_time
                    from votes
                    where timestamp >= ?
                    group by bot) v
                inner join bots b on v.bot = b.bot
                where v.good_votes + v.bad_votes >= ?
        )
    ) ${whereStr} ${limitStr}`);
    return stmt?.all(epoch, minvotes);
  }

  getSubs(epoch: number, limit?: number) {
    // Get top subreddits from db.
    let limitStr = '';
    if (limit) {
      limitStr = `LIMIT ${limit}`;
    }
    const stmt = this.conn?.prepare(`select subreddit as name,
        sum(CASE WHEN vote = 'G' THEN 1 ELSE 0 END) as good_votes,
        sum(CASE WHEN vote = 'B' THEN 1 ELSE 0 END) as bad_votes
    from votes
    where subreddit IS NOT NULL AND subreddit != '' AND timestamp >= ?
    group by subreddit
    order by count(*) desc
    ${limitStr}`);
    return stmt?.all(epoch);
  }

  getVoteCount(epoch: number, voteType?: VoteType) {
    // Get count of specific vote type.
    if (voteType) {
      const stmt = this.conn?.prepare(
        'select sum(CASE WHEN vote = ? THEN 1 ELSE 0 END) from votes where timestamp >= ? LIMIT 1',
      );
      return stmt?.pluck().get(voteType, epoch);
    }
    const stmt = this.conn?.prepare('SELECT count(id) from votes where timestamp >= ?');
    return stmt?.pluck().get(epoch);
  }

  getBotCount(epoch: number, minvotes?: number) {
    // Get count of bots.
    if (typeof minvotes === 'undefined') {
      minvotes = MINVOTES;
    }
    const stmt = this.conn?.prepare(`select count(bot)
      from (select vo.bot,
              count(vote) as votes
          from votes vo
          inner join bots b on vo.bot = b.bot
          where timestamp >= ?
          group by vo.bot) v
      where v.votes >= ?`);
    return stmt?.pluck().get(epoch, minvotes);
  }

  getTimelineData(epoch: number, dateFormat: string) {
    // Get data for timeline.
    const stmt = this.conn?.prepare(`select strftime(?, timestamp, 'unixepoch') as key,
          sum(CASE WHEN vote = 'G' THEN 1 ELSE 0 END) as good_votes,
          sum(CASE WHEN vote = 'B' THEN 1 ELSE 0 END) as bad_votes
      from votes
      where timestamp >= ?
      group by key`);
    return stmt?.all(dateFormat, epoch);
  }

  close() {
    this.conn?.close();
  }
}
