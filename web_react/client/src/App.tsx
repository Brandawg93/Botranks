import React from 'react';
import { ApolloClient, InMemoryCache, ApolloProvider } from '@apollo/client';
import 'gridjs/dist/theme/mermaid.min.css';
import NavBar from './navbar';
import BotGrid from './grid';
import './App.css';

const client = new ApolloClient({
  uri: '/graphql',
  cache: new InMemoryCache(),
});

function App() {
  return (
    <ApolloProvider client={client}>
      <NavBar />
      <BotGrid />
    </ApolloProvider>
  );
}

export default App;
