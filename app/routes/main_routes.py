from flask import Flask, render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, login_required, current_user

from app import app, db, login
from app.models import User, FollowedMatch
from app.api.api_requests import (create_match_statistics_json, create_todays_matches_json,
                                  create_match_detail_info_json, create_categories, country_list)

from PIL import ImageColor
from icecream import ic
from datetime import *
import requests
import json
import os

with app.app_context():
    db.create_all()
    db.session.close_all()
    with open("app/api/json/api_info/categories.json", "rb") as f:
        data = f.read()
        categories_json = json.loads(data)
    with open("app/api/json/country_codes.json", "rb") as f:
        data = f.read()
        country_codes_json = json.loads(data)


@app.route("/", methods=["GET", "POST"])
@app.route("/home", methods=["GET", "POST"])
@app.route("/index", methods=["GET", "POST"])
def index():
    today = datetime.now()
    day, month, year = today.day, today.month, today.year

    matches_file = f"app/api/json/todays_matches/{18}_{month}_{year}.json"
    
    if not os.path.exists(matches_file):
        create_todays_matches_json()
        while not os.path.exists(matches_file):
            continue

    os.makedirs(os.path.dirname(matches_file), exist_ok=True)
    with open(matches_file, "rb") as f:
        data = f.read()
        matches_json = json.loads(data)

    matches = {}
    priority = 450
    while len(matches) < 5:
        for event in matches_json["events"]:
            if "women" in event["tournament"]["name"].lower():
                continue
            elif event["tournament"]["priority"] >= priority:
                timestamp = event['startTimestamp']
                hour = datetime.fromtimestamp(timestamp).hour
                minutes = datetime.fromtimestamp(timestamp).minute
                if minutes < 10:
                    minutes = "0" + str(datetime.fromtimestamp(timestamp).minute)
                if hour < 10:
                    hour = "0" + str(datetime.fromtimestamp(timestamp).hour)
                is_country = False
                if event['homeTeam']['name'] in country_list or event['awayTeam']['name'] in country_list:
                    is_country = True
                try:
                    matches.update({event['id']: {"home": event['homeTeam']['name'],
                                                  "away": event['awayTeam']['name'],
                                                  "time": f'{hour}:{minutes}',
                                                  "country": is_country,
                                                  "home_code": "images/country_flags/" +
                                                               country_list[event['homeTeam']['name']] + ".png",
                                                  "away_code": "images/country_flags/" +
                                                               country_list[event['awayTeam']['name']] + ".png"}})
                except:
                    matches.update({event['id']: {"home": event['homeTeam']['name'],
                                                  "away": event['awayTeam']['name'],
                                                  "time": f'{hour}:{minutes}',
                                                  "country": is_country}})
        priority -= 50

    fav_ids = []
    if current_user.is_authenticated:
        for i in matches:
            fav = FollowedMatch.query.filter_by(match_id=i, user_id=current_user.id).first()
            if fav is not None:
                fav_ids.append(i)
    return render_template("index.html", title="Homepage", matches=matches, user=current_user,
                           fav_ids=fav_ids)


@app.route("/leagues", methods=["GET", "POST"])
def leagues():
    file = "app/api/json/matches.json"
    with open(file, 'rb') as f:
        data = f.read()
        json_data = json.loads(data)

    bundesliga, premier_league, laliga, seria_a, ligue_1, ukraine = {}, {}, {}, {}, {}, {}

    for event in json_data["events"]:
        if "woman" in event["tournament"]["name"].lower():
            continue
        elif event["tournament"]["id"] == 1:  # Premier League
            premier_league.update({event['id']: [event['homeTeam']['name'], event['awayTeam']['name']]})

        elif event["tournament"]["id"] == 33:  # Seria A
            seria_a.update({event['id']: [event['homeTeam']['name'], event['awayTeam']['name']]})

        elif event["tournament"]["id"] == 36:  # La Liga
            laliga.update({event['id']: [event['homeTeam']['name'], event['awayTeam']['name']]})

        elif event["tournament"]["id"] == 42:  # Bundesliga
            bundesliga.update({event['id']: [event['homeTeam']['name'], event['awayTeam']['name']]})

        elif event["tournament"]["id"] == 4:  # Ligue_1
            ligue_1.update({event['id']: [event['homeTeam']['name'], event['awayTeam']['name']]})

        elif event["tournament"]["id"] == 384:  # Ukraine Premiere League
            ukraine.update({event['id']: [event['homeTeam']['name'], event['awayTeam']['name'], event['winnerCode']]})
    return render_template("leagues.html",
                           title="Leagues", ligue_1=ligue_1, premier_league=premier_league, bundesliga=bundesliga,
                           laliga=laliga, seria_a=seria_a, ukraine=ukraine, json_file="app/api/json/matches.json")


@app.route("/match_details/<match_id>", methods=["GET", "POST"])
def match_details(match_id):
    details_file = f"app/api/json/match_detail_info/{match_id}.json"
    if not os.path.exists(details_file):
        create_match_detail_info_json(match_id)
        os.makedirs(os.path.dirname(details_file), exist_ok=True)
        while not os.path.exists(details_file):
            continue
    with open(details_file, "rb") as f:
        data = f.read()
        details_json = json.loads(data)

    statistics_file = f"app/api/json/match_statistics/{match_id}.json"
    if not os.path.exists(statistics_file):
        create_match_statistics_json(match_id)
        os.makedirs(os.path.dirname(statistics_file), exist_ok=True)
        while not os.path.exists(statistics_file):
            continue
    with open(statistics_file, "rb") as f:
        data = f.read()
        statistics_json = json.loads(data)

    team = {}
    home_color = ImageColor.getcolor(details_json["event"]["homeTeam"]["teamColors"]["primary"], "RGB")
    away_color = ImageColor.getcolor(details_json["event"]["awayTeam"]["teamColors"]["primary"], "RGB")

    team.update({"home": [details_json["event"]["homeTeam"]["name"], home_color],
                 "away": [details_json["event"]["awayTeam"]["name"], away_color]})

    match = {}
    t = details_json["event"]["startTimestamp"]
    match_time = datetime.fromtimestamp(t)
    hour = datetime.fromtimestamp(t).hour
    minutes = datetime.fromtimestamp(t).minute
    if minutes < 10:
        minutes = "0" + str(datetime.fromtimestamp(t).minute)
    if hour < 10:
        hour = "0" + str(datetime.fromtimestamp(t).minute)
    match.update({"starttime": f"{hour}:{minutes}, {match_time.day}.{match_time.month}"})

    score = {}
    try:
        score.update({"home": details_json["event"]["homeScore"]["normaletime"],
                      "away": details_json["event"]["awayScore"]["normaletime"]})
    except KeyError:
        score.update({"home": 0, "away": 0})

    i = 0
    game_posession = {}
    for posession in statistics_json["statistics"]:
        game_posession.update({i: [posession['groups'][1]['statisticsItems'][0]['home'],
                                   posession['groups'][1]['statisticsItems'][0]['away']]})
        i += 1
    return render_template("match_details.html", title="Match Details", match_id=match_id, team=team,
                           score=score, match=match)


@app.route("/countrys_ranking")
def countrys_ranking():
    file = "app/api/json/ranking.json"
    with open(file, 'rb') as f:
        data = f.read()
        json_data = json.loads(data)

    countrys = {}
    colors = {}
    for country in json_data["rankings"]:
        if country["points"]-country["previousPoints"] == 0:
            diff_points = 0 
        elif country["points"]-country["previousPoints"] > 0:
            diff_points = f"+{round(country['points']-country['previousPoints'], 2)}"
        else:
            diff_points = round(country["points"]-country["previousPoints"], 2)
        ic(country["points"]-country["previousPoints"])
        if (country["previousRanking"] - country['team']['ranking']) > 0:
            diff_ranking = f"+{country['previousRanking'] - country['team']['ranking']}" 
        else: 
            diff_ranking = country["previousRanking"] - country['team']['ranking']
        countrys.update({country['team']['ranking']: {"name": country['team']['name'],
                                                      "code": "images/country_flags/" + country_list[country['team']['name']] + ".png",
                                                      "points": country["points"],
                                                      "prev_points": country["previousPoints"],
                                                      "prev_ranking": country["previousRanking"],
                                                      "diff_points": diff_points,
                                                      "diff_ranking": diff_ranking}})
        colors.update({country['team']['ranking']: [ImageColor.getcolor(country['team']['teamColors']['primary'], "RGB"),
                                                    ImageColor.getcolor(country['team']['teamColors']['text'], "RGB")]})
    return render_template("countrys_ranking.html", title="County Ranking", countrys=countrys,
                           colors=colors, dict_len=len(countrys))


@app.route("/countrys_ranking/<country_name>")
def country(country_name):
    file = "app/api/json/ranking.json"
    with open(file, 'rb') as f:
        data = f.read()
        json_data = json.loads(data)
    return render_template("country.html", title="County Ranking", country_name=country_name)


@app.route("/add_favorite_game/<match_id>")
def add_favorite_game(match_id):
    if not current_user.is_authenticated:
        flash(f"please login: {match_id}")
        return redirect(url_for("index"))
    fav = FollowedMatch.query.filter_by(match_id=match_id).filter_by(user_id=current_user.id).first()
    if fav is None:
        db.session.add(FollowedMatch(user_id=current_user.id, match_id=match_id))
    else:
        db.session.delete(fav)
    db.session.commit()
    return redirect(url_for("index"))
