# BotRanks
[![BuyMeACoffee](https://img.shields.io/badge/coffee-donate-orange?logo=buy-me-a-coffee&logoColor=yellow)](https://www.buymeacoffee.com/L1FgZTD)

BotRanks is a website that shows the ranks of bots on Reddit.

# Scoring

The score is based on a confidence interval between the number of good votes and number of bad votes. The fomula is shown below:

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

# Badges
Badges can be created using [shields.io](https://shields.io/). Here are a few examples:

[![GifReversingBot](https://img.shields.io/endpoint?url=https://botranks.com/api/getbadge/GifReversingBot)](https://github.com/pmdevita/GifReversingBot)
[![gifendore](https://img.shields.io/endpoint?url=https://botranks.com/api/getbadge/gifendore&label=gifendore%20rank)](https://github.com/Brandawg93/Gifendore)

#### Note:
The site is currently in development and more will come soon! Feel free to look around and submit issues or feedback on the [Github](https://github.com/Brandawg93/Botranks).

# Support BotRanks
This website was made to keep Redditors informed on bots both good and bad. If you wish to show support for its continued development, consider [buying me a coffee](https://www.buymeacoffee.com/L1FgZTD).