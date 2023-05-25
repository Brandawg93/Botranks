import React from 'react';
import { Container } from 'react-bootstrap';
import { useQuery, gql } from '@apollo/client';
import { Grid } from 'gridjs-react';

let query = gql`
  query ($after: String, $sort: String) {
    bots(after: $after, sort: $sort) {
      rank
      name
      score
      votes {
        good
        bad
      }
      karma {
        link
        comment
      }
    }
    stats(after: $after) {
      votes {
        latest
        count
      }
    }
  }
`;

export default function BotGrid() {
  const { data } = useQuery(query, {
    variables: { after: '1y', sort: 'top' },
  });

  return (
    <Container>
      <Grid
        data={data?.bots || (() => new Promise(() => {}))}
        autoWidth
        columns={[
          { name: 'Rank' },
          { name: 'Name' },
          { name: 'Score' },
          { name: 'Good Bot Votes', data: (row: any) => row.votes.good },
          { name: 'Bad Bot Votes', data: (row: any) => row.votes.bad },
          { name: 'Comment Karma', data: (row: any) => row.karma.comment },
          { name: 'Link Karma', data: (row: any) => row.karma.link },
        ]}
        search
        sort
        pagination={{
          limit: 100,
        }}
        language={{
          search: {
            placeholder: '🔍 Search for a bot...',
          },
        }}
      />
    </Container>
  );
}
