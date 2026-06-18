# ⚽ Football Live Pipeline

> Pipeline ETL/ELT end-to-end de données de Premier League — ESILV MSc A4 · ETL & Pipeline Orchestration

## Cas d'usage

En tant que supporter de Chelsea FC, je voulais centraliser toutes les stats de Premier League en temps réel sans jongler entre plusieurs sites. Ce pipeline collecte automatiquement les données (matchs, classement, buteurs), les transforme et les affiche dans un dashboard live.

---

## Architecture

```
football-data.org API
        │
        ▼
  Python Producer        ← ETL Batch : fetch + publish
        │
        ▼
   Apache Kafka          ← Streaming (topic: match-events)
        │
        ▼
  Python Consumer        ← Lit Kafka, insère en base
        │
        ▼
   PostgreSQL            ← Staging (raw data)
        │
        ▼
   SQL Views / ELT       ← Transformations analytiques
        │
        ▼
  Apache Airflow         ← Orchestration (DAG toutes les 30 min)
        │
        ▼
Streamlit Dashboard      ← 6 visualisations live
```

---

## Stack technique

| Couche         | Outil                        |
|----------------|------------------------------|
| Source         | football-data.org (API REST) |
| Ingestion      | Python + requests            |
| Streaming      | Apache Kafka 4.0 (KRaft)     |
| Stockage       | PostgreSQL 18                |
| Transformation | SQL Views (ELT)              |
| Orchestration  | Apache Airflow               |
| Dashboard      | Streamlit + Plotly           |
| Infra          | AWS EC2 Ubuntu 26.04         |

---

## Structure du projet

```
football-pipeline/
├── producer.py           # Fetch API → publie dans Kafka
├── consumer.py           # Kafka → insère dans PostgreSQL
├── config.py.example     # Template de configuration
├── requirements.txt      # Dépendances Python
├── db/
│   └── init.sql          # Schéma : tables + vues analytiques
├── dags/
│   └── football_dag.py   # DAG Airflow (toutes les 30 min)
└── dashboard/
    └── app.py            # Dashboard Streamlit (6 vues)
```

---

## Setup — Lancer le projet en local

### Prérequis

- Python 3.10+
- Java 21+
- PostgreSQL
- Apache Kafka 4.x

### 1. Cloner le repo

```bash
git clone https://github.com/latomate07/football-live.git
cd football-live
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Configurer

```bash
cp config.py.example config.py
nano config.py  # Renseigner ta clé API et les infos PostgreSQL
```

Clé API gratuite sur : https://www.football-data.org/client/register

### 4. Initialiser la base de données

```bash
psql -U football_user -d football -h localhost -f db/init.sql
```

### 5. Démarrer Kafka

```bash
KAFKA_CLUSTER_ID="$(~/kafka/bin/kafka-storage.sh random-uuid)"
~/kafka/bin/kafka-storage.sh format --standalone -t $KAFKA_CLUSTER_ID -c ~/kafka/config/server.properties
~/kafka/bin/kafka-server-start.sh -daemon ~/kafka/config/server.properties
sleep 8
~/kafka/bin/kafka-topics.sh --create --topic match-events \
  --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
```

### 6. Lancer le pipeline

```bash
# Étape 1 — Fetch API et publish dans Kafka
python3 producer.py

# Étape 2 — Consommer Kafka et insérer en base
python3 consumer.py
```

### 7. Lancer le dashboard

```bash
python3 -m streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

Dashboard accessible sur : `http://localhost:8501`

---

## Vues analytiques (ELT)

| Vue                    | Description                              |
|------------------------|------------------------------------------|
| `v_standings_latest`   | Classement actuel de la Premier League   |
| `v_top_scorers`        | Top buteurs (dernière snapshot)          |
| `v_chelsea_form`       | Forme de Chelsea sur les 5 derniers matchs |
| `v_goals_per_matchday` | Buts par journée                         |
| `v_chelsea_next`       | Prochains matchs de Chelsea              |

---

## DAG Airflow

Le DAG `football_live_pipeline` orchestre le pipeline toutes les 30 minutes :

```
produce → consume → transform
```

Avec 2 retries automatiques en cas d'échec.

---

## Dashboard — Visualisations

1. Classement Premier League (bar chart)
2. Top 10 Buteurs (horizontal bar)
3. Forme récente de Chelsea (W/D/L sur 5 matchs)
4. Buts par journée (line chart)
5. Attaque vs Défense — Top 10 (grouped bar)
6. Prochains matchs Chelsea

---

## Données

- **Source** : [football-data.org](https://www.football-data.org/) — API gratuite
- **Compétition** : Premier League (code `PL`)
- **Fréquence** : toutes les 30 minutes via Airflow

---

*Projet réalisé dans le cadre du cours ETL & Pipeline Orchestration — ESILV MSc A4 · Juin 2026*
