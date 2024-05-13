## Valorant Esports Data

This simple tool scrapes data from [rib.gg](https://www.rib.gg/) and returns three csv files: `valorant-event-locations.csv`, `valorant-match-events.csv` and `valorant-player-economies.csv`.

Currently, URL is hardcoded but can be easily changed to accomodate whichever Valorant event you want to scrape. Simply change event id "4388" to the rib.gg id of any event.

___
### Notes
All "ID" columns contain rib.gg's internal keys for each match, round, etc. 

#### Player ID:
Event involving this player. Eg: Player with ID killed/planted ...

#### Reference Player ID:
Event involving this player with another player. Eg: Player with ID killed player with reference ID

#### Damage Type:
One of: Weapon, ability, null

#### Ability:
Ability involved with event

#### Round/Kill/TradedBy/TradedFor/Res/Bomb ID
rib.gg's internal key for each type of data

#### Location X, Y:
Pixel coordinates of each player in the match at a certain time in a round based on a 1024x1024 PNG of the map
