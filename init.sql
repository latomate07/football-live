-- ── Football Pipeline · Schema ──────────────────────────────

CREATE TABLE IF NOT EXISTS matches (
    id            INTEGER PRIMARY KEY,
    utc_date      TIMESTAMP,
    status        VARCHAR(20),
    home_team     VARCHAR(100),
    away_team     VARCHAR(100),
    home_score    INTEGER,
    away_score    INTEGER,
    matchday      INTEGER,
    season        VARCHAR(10),
    inserted_at   TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS standings (
    id            SERIAL PRIMARY KEY,
    team          VARCHAR(100),
    position      INTEGER,
    played        INTEGER,
    won           INTEGER,
    draw          INTEGER,
    lost          INTEGER,
    goals_for     INTEGER,
    goals_against INTEGER,
    points        INTEGER,
    fetched_at    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS scorers (
    id            SERIAL PRIMARY KEY,
    player_name   VARCHAR(100),
    team          VARCHAR(100),
    goals         INTEGER,
    assists       INTEGER,
    fetched_at    TIMESTAMP DEFAULT NOW()
);

-- ── Vues analytiques (ELT) ───────────────────────────────────

-- Classement actuel (dernière snapshot)
CREATE OR REPLACE VIEW v_standings_latest AS
SELECT DISTINCT ON (team)
    position, team, played, won, draw, lost,
    goals_for, goals_against,
    goals_for - goals_against AS goal_diff,
    points
FROM standings
ORDER BY team, fetched_at DESC;

-- Top buteurs actuels
CREATE OR REPLACE VIEW v_top_scorers AS
SELECT DISTINCT ON (player_name)
    player_name, team, goals, assists
FROM scorers
ORDER BY player_name, fetched_at DESC;

-- Forme de Chelsea (5 derniers matchs)
CREATE OR REPLACE VIEW v_chelsea_form AS
SELECT
    utc_date,
    home_team,
    away_team,
    home_score,
    away_score,
    CASE
        WHEN home_team = 'Chelsea FC' AND home_score > away_score THEN 'W'
        WHEN away_team = 'Chelsea FC' AND away_score > home_score THEN 'W'
        WHEN home_score = away_score THEN 'D'
        ELSE 'L'
    END AS result
FROM matches
WHERE (home_team = 'Chelsea FC' OR away_team = 'Chelsea FC')
  AND status = 'FINISHED'
ORDER BY utc_date DESC
LIMIT 5;

-- Buts par journée
CREATE OR REPLACE VIEW v_goals_per_matchday AS
SELECT
    matchday,
    COUNT(*) AS matches_played,
    SUM(home_score + away_score) AS total_goals,
    ROUND(AVG(home_score + away_score), 2) AS avg_goals
FROM matches
WHERE status = 'FINISHED'
GROUP BY matchday
ORDER BY matchday;

-- Prochains matchs Chelsea
CREATE OR REPLACE VIEW v_chelsea_next AS
SELECT
    utc_date,
    home_team,
    away_team,
    matchday
FROM matches
WHERE (home_team = 'Chelsea FC' OR away_team = 'Chelsea FC')
  AND status IN ('SCHEDULED', 'TIMED')
ORDER BY utc_date
LIMIT 3;
