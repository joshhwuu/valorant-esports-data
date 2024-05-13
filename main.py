import pandas as pd
import requests
import json


def format_to_csv(df, cols, path):
    df = pd.DataFrame(df)
    df.columns = cols
    df.index = pd.RangeIndex(len(df.index))
    df.to_csv(path)


# URL for VCT americas 2024: stage 1
url = "https://be-prod.rib.gg/v1/series?completed=true&take=50&eventIds%5B%5D=4388"  # replace with any event id on rib
JSONContent = requests.get(url).json()
matchIDs = []
for data in JSONContent["data"]:
    for match in data["matches"]:
        matchIDs.append(match["id"])

# match events, each event is one of: start, kill, plant, defuse
# all IDs are rib.gg internal
matchEvents = []

# event locations, each event is given a specific x and y coordinate
eventLocations = []

# At the start of each round, economy info on each player
playerEconomies = []

for matchID in matchIDs:
    content = requests.get("https://be-prod.rib.gg/v1/matches/" + str(matchID) + "/details").json()
    for event in content["events"]:
        matchEvents.append([content["id"],
                            event["roundId"],
                            event["roundNumber"],
                            event["roundTimeMillis"],
                            event["eventType"],
                            event["killId"],
                            event["tradedByKillId"],
                            event["tradedForKillId"],
                            event["bombId"],
                            event["resId"],
                            event["playerId"],
                            event["assists"],
                            event["referencePlayerId"],
                            event["damageType"],
                            event["weaponId"],
                            event["ability"]])

    for location in content["locations"]:
        eventLocations.append([location["roundNumber"],
                               location["playerId"],
                               location["roundTimeMillis"],
                               location["locationX"],
                               location["locationY"],
                               location["viewRadians"]])

    for economy in content["economies"]:
        playerEconomies.append([economy["roundId"],
                                economy["roundNumber"],
                                economy["playerId"],
                                economy["agentId"],
                                economy["score"],
                                economy["weaponId"],
                                economy["armorId"],
                                economy["remainingCreds"],
                                economy["spentCreds"],
                                economy["loadoutValue"],
                                economy["survived"],
                                economy["kast"]])

matchEvents_dataset_columns = ['Match_Id',
                               'Round_ID',
                               'Round_Number',
                               'Round_Time',
                               'Event_Type',
                               'Kill_ID',
                               'Traded_by_ID',
                               'Traded_for_ID',
                               'Bomb_Status',
                               'Resurrection_ID',
                               'Player_ID',
                               'Assists',
                               'Reference_Player_ID',
                               'Damage_Type',
                               'Weapon_ID',
                               'Ability']
matchEvents_dataset_path = 'datasets/valorant-match-events.csv'
format_to_csv(matchEvents, matchEvents_dataset_columns, matchEvents_dataset_path)

eventLocations_dataset_columns = ['Round_Number',
                                  'Player_ID',
                                  'Round_Time',
                                  'X', 'Y',
                                  'View_Radians', ]
eventLocations_dataset_path = 'datasets/valorant-event-locations.csv'
format_to_csv(eventLocations, eventLocations_dataset_columns, eventLocations_dataset_path)
playerEconomies_dataset_columns = ['Round_ID',
                                   'Round_Number',
                                   'Player_ID',
                                   'Agent_ID',
                                   'Round_Score',
                                   'Weapon_ID',
                                   'Armor_ID',
                                   'Remaining_Credits',
                                   'Spent_Credits',
                                   'Loadout_Value',
                                   'Survived',
                                   'kast']
playerEconomies_dataset_path = 'datasets/valorant-player-economies.csv'
format_to_csv(playerEconomies, playerEconomies_dataset_columns, playerEconomies_dataset_path)
