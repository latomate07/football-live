#!/usr/bin/env python3
"""
consumer.py — Lit Kafka → insère dans PostgreSQL
"""
import json
import psycopg2
from kafka import KafkaConsumer
from config import KAFKA_BROKER, KAFKA_TOPIC, DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS


def get_conn():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASS
    )


def upsert_match(cur, d):
    cur.execute("""
        INSERT INTO matches (id, utc_date, status, home_team, away_team,
                             home_score, away_score, matchday, season)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            status     = EXCLUDED.status,
            home_score = EXCLUDED.home_score,
            away_score = EXCLUDED.away_score
    """, (
        d["id"], d["utc_date"], d["status"],
        d["home_team"], d["away_team"],
        d["home_score"], d["away_score"],
        d["matchday"], d["season"]
    ))


def insert_standing(cur, d):
    cur.execute("""
        INSERT INTO standings (team, position, played, won, draw, lost,
                               goals_for, goals_against, points)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        d["team"], d["position"], d["played"], d["won"],
        d["draw"], d["lost"], d["goals_for"], d["goals_against"], d["points"]
    ))


def insert_scorer(cur, d):
    cur.execute("""
        INSERT INTO scorers (player_name, team, goals, assists)
        VALUES (%s, %s, %s, %s)
    """, (d["player_name"], d["team"], d["goals"], d["assists"]))


def run():
    print("[consumer] Connexion à Kafka...")
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
        consumer_timeout_ms=10000   # s'arrête après 10s sans message
    )

    conn = get_conn()
    cur  = conn.cursor()
    count = 0

    for msg in consumer:
        event = msg.value
        etype = event.get("type")
        data  = event.get("data", {})

        try:
            if etype == "match":
                upsert_match(cur, data)
            elif etype == "standing":
                insert_standing(cur, data)
            elif etype == "scorer":
                insert_scorer(cur, data)
            conn.commit()
            count += 1
            print(f"[consumer] {etype} inséré ({count})")
        except Exception as e:
            conn.rollback()
            print(f"[consumer] Erreur sur {etype}: {e}")

    cur.close()
    conn.close()
    print(f"[consumer] Terminé — {count} événements traités.")


if __name__ == "__main__":
    run()
