#!/usr/bin/env python3
"""
producer.py — Fetch football-data.org → publie dans Kafka
"""
import json
import time
import requests
from kafka import KafkaProducer
from config import API_KEY, API_BASE, COMPETITION, KAFKA_BROKER, KAFKA_TOPIC

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

HEADERS = {"X-Auth-Token": API_KEY}


def fetch_matches():
    url = f"{API_BASE}/competitions/{COMPETITION}/matches"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    return r.json().get("matches", [])


def fetch_standings():
    url = f"{API_BASE}/competitions/{COMPETITION}/standings"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    data = r.json()
    # On prend la table "TOTAL"
    for table in data.get("standings", []):
        if table.get("type") == "TOTAL":
            return table.get("table", [])
    return []


def fetch_scorers():
    url = f"{API_BASE}/competitions/{COMPETITION}/scorers?limit=20"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    return r.json().get("scorers", [])


def publish(event_type, payload):
    message = {"type": event_type, "data": payload, "ts": time.time()}
    producer.send(KAFKA_TOPIC, value=message)
    print(f"[producer] sent {event_type}")


def run():
    print("[producer] Démarrage...")

    # Matchs
    matches = fetch_matches()
    for m in matches:
        publish("match", {
            "id":         m["id"],
            "utc_date":   m["utcDate"],
            "status":     m["status"],
            "home_team":  m["homeTeam"]["name"],
            "away_team":  m["awayTeam"]["name"],
            "home_score": m["score"]["fullTime"].get("home"),
            "away_score": m["score"]["fullTime"].get("away"),
            "matchday":   m.get("matchday"),
            "season":     m["season"]["startDate"][:4],
        })

    # Classement
    standings = fetch_standings()
    for row in standings:
        publish("standing", {
            "team":          row["team"]["name"],
            "position":      row["position"],
            "played":        row["playedGames"],
            "won":           row["won"],
            "draw":          row["draw"],
            "lost":          row["lost"],
            "goals_for":     row["goalsFor"],
            "goals_against": row["goalsAgainst"],
            "points":        row["points"],
        })

    # Buteurs
    scorers = fetch_scorers()
    for s in scorers:
        publish("scorer", {
            "player_name": s["player"]["name"],
            "team":        s["team"]["name"],
            "goals":       s.get("goals", 0),
            "assists":     s.get("assists", 0),
        })

    producer.flush()
    print("[producer] Terminé.")


if __name__ == "__main__":
    run()
