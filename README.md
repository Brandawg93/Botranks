# BotRanks
[![PayPal](https://img.shields.io/badge/paypal-donate-blue?logo=paypal)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=CEYYGVB7ZZ764&item_name=Botranks&currency_code=USD&source=url)

BotRanks is a website that shows the ranks of bots on Reddit.

# Scoring

The score is based on the [lower bound of a Wilson score](https://www.evanmiller.org/how-not-to-sort-by-average-rating.html) confidence interval between the number of good votes and number of bad votes. The fomula is shown below:

```
                                ___________________
                               / G  *  B           
                            | /  -------  +  0.9604
 G  +  1.9208               |/   G  +  B           
 ------------  -  1.96  *  ------------------------
    G  +  B                         G  +  B        
---------------------------------------------------
                   1  +  3.8416                    
                   ------------                    
                      G  +  B                      

G = Good Votes
B = Bad Votes
```

# Badges for Developers
Badges can be created using [shields.io](https://shields.io/). Here are a few examples:

[![GifReversingBot](https://img.shields.io/endpoint?url=https://botranks.com/api/getbadge/GifReversingBot)](https://github.com/pmdevita/GifReversingBot)
[![gifendore](https://img.shields.io/endpoint?url=https://botranks.com/api/getbadge/gifendore&label=gifendore%20rank)](https://github.com/Brandawg93/Gifendore)

# GraphQL API for Developers
BotRanks uses [GraphQL](https://graphql.org/) for its API. Feel free to look around on the [Graph*i*QL page](https://botranks.com/graphql).

# REST API Endpoints

## JSON

- ``/api/getrank/{username}`` : gets a users ranking, karma, score, and vote counts

- ``/api/getbadge/{username}`` : gets a users rank to be used in a badge.

- ``/api/ping`` : returns pong

# FAQ
**Q:** How do I vote?

**A:** Simply reply to a bot with "Good bot" or "Bad bot" to have your vote counted in the rankings. It may take up to 10 minutes to see your vote reflected on the page.

**Q:** How does this site handle vote manipulation?

**A:** BotRanks uses time to mitigate vote manipulation. The site can be filtered between day/week/month/year allowing viewers to see which bots have had a recent rise in the rankings and which have been consistently ranked in the top. All votes stop being counted exactly one year from when they were cast to allow new bots a chance to climb the ranks.

# Support BotRanks
This website was made to keep Redditors informed on bots both good and bad. If you wish to show support for its continued development, consider [sponsoring me on Github](https://github.com/sponsors/Brandawg93).

**Note:** The site is currently in development and more will come soon! Feel free to look around and submit issues or feedback on the [Github](https://github.com/Brandawg93/Botranks).