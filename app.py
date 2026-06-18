"""
app.py — Dashboard Streamlit · Football Live Pipeline
"""
import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
sys.path.append("..")
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS

st.set_page_config(
    page_title="⚽ Football Live Pipeline",
    page_icon="⚽",
    layout="wide"
)

# ── Connexion DB ─────────────────────────────────────────────
@st.cache_resource
def get_conn():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASS
    )

@st.cache_data(ttl=60)
def query(sql):
    conn = get_conn()
    return pd.read_sql(sql, conn)


# ── Header ───────────────────────────────────────────────────
st.title("⚽ Football Live Pipeline")
st.caption(f"Premier League · Dernière mise à jour : {datetime.now().strftime('%H:%M:%S')}")
st.divider()

# ── KPIs ─────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

matches_df   = query("SELECT * FROM matches WHERE status = 'FINISHED'")
standings_df = query("SELECT * FROM v_standings_latest ORDER BY position")
scorers_df   = query("SELECT * FROM v_top_scorers ORDER BY goals DESC LIMIT 20")
chelsea_form = query("SELECT * FROM v_chelsea_form")

# Position Chelsea
chelsea_row = standings_df[standings_df["team"] == "Chelsea FC"]
chelsea_pos = int(chelsea_row["position"].values[0]) if not chelsea_row.empty else "?"
chelsea_pts = int(chelsea_row["points"].values[0]) if not chelsea_row.empty else "?"

col1.metric("🔵 Chelsea — Position", f"{chelsea_pos}e")
col2.metric("🏆 Points Chelsea", chelsea_pts)
col3.metric("⚽ Matchs joués", len(matches_df))
col4.metric("🥇 Leader", standings_df.iloc[0]["team"] if not standings_df.empty else "?")

st.divider()

# ── Viz 1 : Classement Premier League ────────────────────────
st.subheader("📊 Classement Premier League")

fig_standing = px.bar(
    standings_df.head(20),
    x="team", y="points",
    color="points",
    color_continuous_scale="Blues",
    labels={"team": "Équipe", "points": "Points"},
)
fig_standing.update_layout(
    xaxis_tickangle=-45,
    showlegend=False,
    height=420,
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
)
# Highlight Chelsea
fig_standing.update_traces(
    marker_color=[
        "#034694" if t == "Chelsea FC" else "#90AFC5"
        for t in standings_df.head(20)["team"]
    ]
)
st.plotly_chart(fig_standing, use_container_width=True)

# ── Viz 2 : Top Buteurs ──────────────────────────────────────
st.subheader("🥇 Top 10 Buteurs")

fig_scorers = px.bar(
    scorers_df.head(10),
    x="goals", y="player_name",
    orientation="h",
    color="goals",
    color_continuous_scale="Oranges",
    text="goals",
    labels={"goals": "Buts", "player_name": "Joueur"},
    hover_data=["team", "assists"]
)
fig_scorers.update_layout(
    yaxis={"categoryorder": "total ascending"},
    height=380,
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    showlegend=False,
)
st.plotly_chart(fig_scorers, use_container_width=True)

# ── Viz 3 : Forme Chelsea ────────────────────────────────────
st.subheader("🔵 Forme récente de Chelsea (5 derniers matchs)")

if not chelsea_form.empty:
    result_colors = {"W": "#00C851", "D": "#FFBB33", "L": "#FF4444"}
    cols = st.columns(len(chelsea_form))
    for i, (_, row) in enumerate(chelsea_form.iterrows()):
        with cols[i]:
            color = result_colors.get(row["result"], "#888")
            opponent = row["away_team"] if row["home_team"] == "Chelsea FC" else row["home_team"]
            venue    = "DOM" if row["home_team"] == "Chelsea FC" else "EXT"
            score    = f"{row['home_score']} - {row['away_score']}"
            st.markdown(f"""
                <div style='text-align:center;padding:12px;border-radius:10px;
                            background:{color}22;border:2px solid {color}'>
                    <div style='font-size:24px;font-weight:bold;color:{color}'>{row['result']}</div>
                    <div style='font-size:12px'>{opponent[:15]}</div>
                    <div style='font-size:11px;color:gray'>{score} · {venue}</div>
                </div>
            """, unsafe_allow_html=True)
else:
    st.info("Pas encore de données sur la forme de Chelsea.")

# ── Viz 4 : Buts par journée ─────────────────────────────────
st.subheader("📈 Buts par journée")

goals_md = query("SELECT * FROM v_goals_per_matchday")
if not goals_md.empty:
    fig_goals = px.line(
        goals_md,
        x="matchday", y="total_goals",
        markers=True,
        labels={"matchday": "Journée", "total_goals": "Total buts"},
        color_discrete_sequence=["#034694"]
    )
    fig_goals.add_scatter(
        x=goals_md["matchday"], y=goals_md["avg_goals"],
        mode="lines", name="Moyenne",
        line=dict(dash="dash", color="#E55B2B")
    )
    fig_goals.update_layout(
        height=350,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_goals, use_container_width=True)

# ── Viz 5 : Attaque vs Défense ───────────────────────────────
st.subheader("⚔️ Attaque vs Défense — Top 10")

top10 = standings_df.head(10).copy()
fig_atk = go.Figure()
fig_atk.add_trace(go.Bar(
    name="Buts marqués", x=top10["team"], y=top10["goals_for"],
    marker_color="#00C851"
))
fig_atk.add_trace(go.Bar(
    name="Buts encaissés", x=top10["team"], y=top10["goals_against"],
    marker_color="#FF4444"
))
fig_atk.update_layout(
    barmode="group",
    xaxis_tickangle=-30,
    height=380,
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(fig_atk, use_container_width=True)

# ── Viz 6 : Prochains matchs Chelsea ─────────────────────────
st.subheader("🗓️ Prochains matchs Chelsea")

next_matches = query("SELECT * FROM v_chelsea_next")
if not next_matches.empty:
    for _, row in next_matches.iterrows():
        opponent = row["away_team"] if row["home_team"] == "Chelsea FC" else row["home_team"]
        venue    = "Domicile" if row["home_team"] == "Chelsea FC" else "Extérieur"
        date_str = pd.to_datetime(row["utc_date"]).strftime("%d %b %Y %H:%M")
        st.markdown(f"**J{row['matchday']}** · {date_str} · Chelsea vs {opponent} · *{venue}*")
else:
    st.info("Pas de prochain match planifié.")

# ── Auto-refresh ─────────────────────────────────────────────
st.divider()
if st.button("🔄 Rafraîchir les données"):
    st.cache_data.clear()
    st.rerun()