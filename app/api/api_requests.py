import requests
import json as j
import os
from datetime import *

def create_todays_matches_json():
    date = datetime.now()
    day, month, year = date.day, date.month, date.year

    url = f"https://footapi7.p.rapidapi.com/api/matches/{day}/{month}/{year}"

    headers = {
        "X-RapidAPI-Key": "261229b62cmsh9ff85b6a1f70efep192152jsn0dd435f8eb55",
        "X-RapidAPI-Host": "footapi7.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers)

    path = f"app/api/json/todays_matches/{day}_{month}_{year}.json"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as outfile:
        j.dump(response.json(), outfile)


def create_match_statistics_json(match_id):
    url = f"https://footapi7.p.rapidapi.com/api/match/{match_id}/statistics"

    headers = {
        "X-RapidAPI-Key": "261229b62cmsh9ff85b6a1f70efep192152jsn0dd435f8eb55",
        "X-RapidAPI-Host": "footapi7.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers)

    path = f"app/api/json/match_statistics/{match_id}.json"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as outfile:
        j.dump(response.json(), outfile)


def create_match_detail_info_json(match_id):
    url = f"https://footapi7.p.rapidapi.com/api/match/{match_id}"

    headers = {
        "X-RapidAPI-Key": "261229b62cmsh9ff85b6a1f70efep192152jsn0dd435f8eb55",
        "X-RapidAPI-Host": "footapi7.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers)

    path = f"app/api/json/match_detail_info/{match_id}.json"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as outfile:
        j.dump(response.json(), outfile)

