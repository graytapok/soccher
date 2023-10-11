from flask import Flask, render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, login_required, current_user

from app import app, db, login
from app.models import User, FollowedMatch
from app.api.api_requests import create_match_statistics_json, create_todays_matches_json, create_match_detail_info_json

from datetime import *
import os
import requests
import json

with app.app_context():
    db.create_all()
    db.session.close_all()

@app.route("/", methods=["GET", "POST"])
@app.route("/home", methods=["GET", "POST"])
@app.route("/index", methods=["GET", "POST"])
def index():
    date = datetime.now()
    day, month, year = date.day, date.month, date.year

    matches_file = f"app/api/json/todays_matches/{day}_{month}_{year}.json"
    print("sasf")
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
                matches.update({event['id']: [event['homeTeam']['name'], event['awayTeam']['name'], f'{hour}:00']})
        priority -= 50

    fav_ids = []
    if current_user.is_authenticated:
        for i in matches:
            fav = FollowedMatch.query.filter_by(match_id=i, user_id=current_user.id).first()
            if fav is not None:
                fav_ids.append(i)
    return render_template("index.html", title="Homepage", matches=matches, user=current_user, fav_ids=fav_ids)


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
    team.update({"home": [details_json["event"]["homeTeam"]["name"], details_json["event"]["homeTeam"]["teamColors"]["primary"]],
                 "away": [details_json["event"]["awayTeam"]["name"], details_json["event"]["awayTeam"]["teamColors"]["primary"]]})

    score = {}
    score.update({"home": details_json["event"]["homeScore"]["normaltime"], 
                  "away": details_json["event"]["awayScore"]["normaltime"]})

    i = 0
    game_posession = {}
    for posession in statistics_json["statistics"]:
        game_posession.update({i: [posession['groups'][1]['statisticsItems'][0]['home'],
                                   posession['groups'][1]['statisticsItems'][0]['away']]})
        i += 1
    return render_template("match_details.html", title="Match Details", match_id=match_id, team=team, posession=game_posession, score=score)


@app.route("/countrys_ranking")
def countrys_ranking():
    file = "app/api/json/ranking.json"
    with open(file, 'rb') as f:
        data = f.read()
        json_data = json.loads(data)

    countrys = {}
    colors = {}
    for country in json_data["rankings"]:
        countrys.update({country['team']['ranking']: country['team']['name']})
        colors.update({country['team']['ranking']: [country['team']['teamColors']['primary'],
                                                    country['team']['teamColors']['text']]})
    return render_template("countrys_ranking.html", title="County Ranking", countrys=countrys, colors=colors)


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
