"""
football_dag.py — Orchestre le pipeline complet
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_DIR = "/home/ubuntu/football-pipeline"

default_args = {
    "owner":            "tahirou",
    "retries":          2,
    "retry_delay":      timedelta(minutes=2),
    "email_on_failure": False,
}

with DAG(
    dag_id="football_live_pipeline",
    description="Fetch PL data → Kafka → PostgreSQL → vues SQL",
    default_args=default_args,
    start_date=datetime(2026, 6, 1),
    schedule_interval="*/30 * * * *",   # toutes les 30 minutes
    catchup=False,
    tags=["football", "esilv", "etl"],
) as dag:

    # Étape 1 — Fetch API et publication dans Kafka
    produce = BashOperator(
        task_id="produce",
        bash_command=f"cd {PROJECT_DIR} && python3 producer.py",
    )

    # Étape 2 — Consommer Kafka et insérer dans PostgreSQL
    consume = BashOperator(
        task_id="consume",
        bash_command=f"cd {PROJECT_DIR} && python3 consumer.py",
    )

    # Étape 3 — Rafraîchir les vues analytiques (ELT)
    transform = BashOperator(
        task_id="transform",
        bash_command=f"""
            psql postgresql://football_user:football_pass@localhost/football -c "
                REFRESH MATERIALIZED VIEW IF EXISTS v_standings_latest;
            " || true
        """,
    )

    # Dépendances : produce → consume → transform
    produce >> consume >> transform
