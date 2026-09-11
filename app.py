import os
import sqlite3
import requests
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from dotenv import load_dotenv

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(
    page_title="Cricbuzz LiveStats",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_dotenv()

# ============================================================
# THEME — palette, fonts, chart template
# ============================================================
THEME = {
    "bg_start":   "#020617",   # slate-950, near-black navy — top of gradient
    "bg_end":     "#0F172A",   # slate-900 — bottom of gradient
    "panel":      "#111827",   # card / container surface
    "panel_edge": "#1F2937",   # hairline borders
    "gold":       "#38BDF8",   # sky blue — the one confident accent
    "gold_soft":  "#0EA5E9",
    "ball_red":   "#F87171",   # coral red — secondary accent
    "ink":        "#F1F5F9",   # primary text, cool near-white
    "muted":      "#94A3B8",   # secondary text
}

CHART_COLORS = [
    "#38BDF8",  # sky blue (primary)
    "#FBBF24",  # amber
    "#34D399",  # emerald
    "#F87171",  # coral red
    "#A78BFA",  # violet
    "#FB923C",  # orange
    "#F472B6",  # pink
    "#2DD4BF",  # teal
]

pio.templates["cricket_dark"] = go.layout.Template(
    layout=go.Layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=CHART_COLORS,
        font=dict(family="Inter, -apple-system, sans-serif", color=THEME["ink"], size=13),
        title=dict(font=dict(family="Oswald, sans-serif", color=THEME["ink"], size=18)),
        legend=dict(font=dict(color=THEME["ink"])),
        xaxis=dict(
            gridcolor="rgba(148,163,184,0.12)",
            zerolinecolor="rgba(148,163,184,0.22)",
            linecolor="rgba(148,163,184,0.22)",
            tickfont=dict(color=THEME["muted"]),
            title=dict(font=dict(color=THEME["muted"])),
        ),
        yaxis=dict(
            gridcolor="rgba(148,163,184,0.12)",
            zerolinecolor="rgba(148,163,184,0.22)",
            linecolor="rgba(148,163,184,0.22)",
            tickfont=dict(color=THEME["muted"]),
            title=dict(font=dict(color=THEME["muted"])),
        ),
        margin=dict(l=10, r=10, t=55, b=10),
    )
)
pio.templates.default = "cricket_dark"
px.defaults.template = "cricket_dark"
px.defaults.color_discrete_sequence = CHART_COLORS

# ============================================================
# GLOBAL CSS — professional dark pitch theme
# ============================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');

.stApp {{
    background: linear-gradient(160deg, {THEME['bg_start']} 0%, {THEME['bg_end']} 100%);
    color: {THEME['ink']};
    font-family: 'Inter', -apple-system, sans-serif;
}}

section[data-testid="stSidebar"] {{
    background: {THEME['panel']};
    border-right: 1px solid {THEME['panel_edge']};
}}

section[data-testid="stSidebar"] * {{
    color: {THEME['ink']} !important;
}}

h1, h2, h3 {{
    font-family: 'Oswald', sans-serif !important;
    letter-spacing: 0.01em;
    color: {THEME['ink']} !important;
}}

h1 {{ color: {THEME['gold']} !important; }}

hr, div[data-testid="stDivider"] {{
    border-color: {THEME['panel_edge']} !important;
}}

div[data-testid="stMetric"] {{
    background: {THEME['panel']};
    border: 1px solid {THEME['panel_edge']};
    border-radius: 10px;
    padding: 14px 12px 10px 14px;
    border-left: 3px solid {THEME['gold']};
    overflow: visible;
    min-width: 0;
}}

div[data-testid="stMetricLabel"] {{
    color: {THEME['muted']} !important;
}}

div[data-testid="stMetricValue"] {{
    color: {THEME['ink']} !important;
    font-family: 'Oswald', sans-serif;
    font-size: clamp(1.1rem, 1.6vw, 1.7rem) !important;
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: unset !important;
    line-height: 1.15 !important;
}}

div[data-testid="stMetricValue"] > div {{
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: unset !important;
}}

div[data-testid="stMetricDelta"] {{
    color: {THEME['gold']} !important;
}}

.stTabs [data-baseweb="tab-list"] {{
    gap: 4px;
    border-bottom: 1px solid {THEME['panel_edge']};
}}

.stTabs [data-baseweb="tab"] {{
    background: transparent;
    color: {THEME['muted']};
}}

.stTabs [aria-selected="true"] {{
    color: {THEME['gold']} !important;
    border-bottom: 2px solid {THEME['gold']} !important;
}}

button[kind="primary"] {{
    background-color: {THEME['gold']} !important;
    color: {THEME['bg_end']} !important;
    border: none !important;
}}

button[kind="secondary"] {{
    background-color: transparent !important;
    color: {THEME['ink']} !important;
    border: 1px solid {THEME['panel_edge']} !important;
}}

div[data-testid="stDataFrame"] {{
    border: 1px solid {THEME['panel_edge']};
    border-radius: 8px;
    overflow: hidden;
}}

.stAlert {{
    border-radius: 8px;
}}

[data-testid="stExpander"] {{
    background: {THEME['panel']};
    border: 1px solid {THEME['panel_edge']};
    border-radius: 8px;
}}
</style>
""", unsafe_allow_html=True)

DB_PATH = "data/database/cricket_stats.db"
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "cricbuzz-cricket.p.rapidapi.com")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")

# ============================================================
# DATABASE
# ============================================================
@st.cache_resource
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

conn = get_connection()

@st.cache_data
def load_table(table_name):
    return pd.read_sql_query(f'SELECT * FROM "{table_name}"', conn)

def table_exists(table_name):
    q = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
    return conn.execute(q, (table_name,)).fetchone() is not None

TABLES = [
    "batting_stats", "bowling_stats", "innings_stats", "matches",
    "match_results", "player_intelligence", "player_stats",
    "team_performance", "q19_batting_consistency",
    "q24_partnership_analysis", "q12_home_away",
    "q13_partnerships_100_plus", "q17_toss_analysis",
    "historical_metadata"
]

data = {}
for table in TABLES:
    if table_exists(table):
        data[table] = load_table(table)

batting = data.get("batting_stats", pd.DataFrame())
bowling = data.get("bowling_stats", pd.DataFrame())
innings = data.get("innings_stats", pd.DataFrame())
matches = data.get("matches", pd.DataFrame())
results = data.get("match_results", pd.DataFrame())
players = data.get("player_intelligence", pd.DataFrame())
teams = data.get("team_performance", pd.DataFrame())
q19 = data.get("q19_batting_consistency", pd.DataFrame())
q24 = data.get("q24_partnership_analysis", pd.DataFrame())
q12 = data.get("q12_home_away", pd.DataFrame())
q13 = data.get("q13_partnerships_100_plus", pd.DataFrame())
q17 = data.get("q17_toss_analysis", pd.DataFrame())
historical_metadata = data.get("historical_metadata", pd.DataFrame())

for df in [batting, bowling, innings, matches, results]:
    for col in ["date", "start_date", "end_date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

# ============================================================
# HELPERS
# ============================================================
def fmt(value):
    try:
        return f"{int(value):,}"
    except Exception:
        return str(value)

def run_sql(sql):
    return pd.read_sql_query(sql, conn)

def chart_bar(df, x, y, title, horizontal=False, text=None):
    if df.empty:
        st.info("No data available.")
        return
    d = df.copy()
    if horizontal:
        d = d.sort_values(x)
        fig = px.bar(d, x=x, y=y, orientation="h", text=text, title=title)
    else:
        fig = px.bar(d, x=x, y=y, text=text, title=title)
    fig.update_traces(marker_color=THEME["gold"])
    st.plotly_chart(fig, use_container_width=True)

def get_winner_column(df):
    for col in ["winner", "winning_team", "team_winner"]:
        if col in df.columns:
            return col
    return None

def normalize_format(value):
    s = str(value).upper()
    if "T20" in s:
        return "T20"
    if "ODI" in s:
        return "ODI"
    if "TEST" in s:
        return "TEST"
    return str(value)

def find_first_existing_table(names):
    for name in names:
        if table_exists(name):
            return name
    return None

def find_logo_path():
    candidates = [
        "assets/cricket_logo.png",
        "static/cricket_logo.png",
        "images/cricket_logo.png",
        "cricket_logo.png",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None

LOGO_PATH = find_logo_path()

# ============================================================
# LIVE API
# ============================================================
@st.cache_data(ttl=60, show_spinner=False)
def get_live_matches():
    if not RAPIDAPI_KEY:
        return None, "RAPIDAPI_KEY is missing from .env"

    url = f"https://{RAPIDAPI_HOST}/matches/v1/live"
    headers = {
        "Content-Type": "application/json",
        "x-rapidapi-host": RAPIDAPI_HOST,
        "x-rapidapi-key": RAPIDAPI_KEY,
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return None, f"API returned HTTP {response.status_code}"
        return response.json(), None
    except Exception as e:
        return None, str(e)

def flatten_live_matches(payload):
    rows = []
    if not isinstance(payload, dict):
        return pd.DataFrame()

    # Cricbuzz responses normally contain type -> seriesMatches.
    for block in payload.get("typeMatches", []):
        for series in block.get("seriesMatches", []):
            series_ad = series.get("seriesAdWrapper", {})
            series_name = series_ad.get("seriesName", "")
            for match in series_ad.get("matches", []):
                info = match.get("matchInfo", {})
                score = match.get("matchScore", {})
                team1 = info.get("team1", {}) or {}
                team2 = info.get("team2", {}) or {}
                rows.append({
                    "series": series_name,
                    "match_id": info.get("matchId"),
                    "description": info.get("matchDesc"),
                    "format": info.get("matchFormat"),
                    "status": info.get("status"),
                    "team1": team1.get("teamName"),
                    "team2": team2.get("teamName"),
                    "venue": (info.get("venue") or {}).get("ground"),
                    "city": (info.get("venue") or {}).get("city"),
                    "team1_score": (score.get("team1Score") or {}),
                    "team2_score": (score.get("team2Score") or {}),
                })
    return pd.DataFrame(rows)

# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.title("🏏 Cricbuzz LiveStats")
st.sidebar.caption("Professional Cricket Analytics")

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Overview",
        "🔴 Live & Recent Matches",
        "🏏 Player Intelligence",
        "⚔️ Player vs Player",
        "🎯 Bowling Intelligence",
        "👥 Team Performance",
        "🏆 Team vs Team H2H",
        "📊 Advanced Insights",
        "🔍 SQL Analytics",
        "🛠️ CRUD Operations",
    ],
)

st.sidebar.divider()
st.sidebar.caption("SQLite + Cricbuzz RapidAPI")

# ============================================================
# HEADER
# ============================================================
st.title("🏏 Cricbuzz LiveStats")
st.caption("Historical cricket analytics, player intelligence and live match monitoring")
st.divider()

# ============================================================
# PAGE 1 — OVERVIEW
# ============================================================
if page == "🏠 Overview":

    if LOGO_PATH:
        logo_col, title_col = st.columns([1, 6])
        with logo_col:
            st.image(LOGO_PATH, use_container_width=True)
        with title_col:
            st.header("📊 Cricket Analytics Overview")
            st.caption("A season-by-season statistical record of matches, players and teams")
    else:
        st.header("📊 Cricket Analytics Overview")

    total_matches = innings["match_id"].nunique() if not innings.empty else 0
    total_players = players["player"].nunique() if not players.empty and "player" in players else 0
    total_runs = batting["runs"].sum() if not batting.empty else 0
    total_wickets = bowling["wickets"].sum() if not bowling.empty else 0
    total_teams = len(teams) if not teams.empty else 0
    total_venues = innings["venue"].nunique() if not innings.empty else 0

    c = st.columns(6)
    c[0].metric("🏏 Matches", fmt(total_matches))
    c[1].metric("👤 Players", fmt(total_players))
    c[2].metric("📈 Runs", fmt(total_runs))
    c[3].metric("🎯 Wickets", fmt(total_wickets))
    c[4].metric("🌍 Teams", fmt(total_teams))
    c[5].metric("🏟️ Venues", fmt(total_venues))

    st.divider()

    # Top players
    if not batting.empty and "batter" in batting:
        top_batter = (
            batting.groupby("batter", as_index=False)["runs"].sum()
            .sort_values("runs", ascending=False).head(1)
        )
    else:
        top_batter = pd.DataFrame()

    if not bowling.empty and "bowler" in bowling:
        top_bowler = (
            bowling.groupby("bowler", as_index=False)["wickets"].sum()
            .sort_values("wickets", ascending=False).head(1)
        )
    else:
        top_bowler = pd.DataFrame()

    c = st.columns(3)
    if not top_batter.empty:
        c[0].metric("👑 Top Run Scorer", top_batter.iloc[0]["batter"],
                    f"{fmt(top_batter.iloc[0]['runs'])} runs")
    if not top_bowler.empty:
        c[1].metric("🎯 Top Wicket Taker", top_bowler.iloc[0]["bowler"],
                    f"{fmt(top_bowler.iloc[0]['wickets'])} wickets")
    if not teams.empty:
        top_team = teams.sort_values("wins", ascending=False).iloc[0]
        c[2].metric("🏆 Most Wins", top_team["team"],
                    f"{fmt(top_team['wins'])} wins")

    st.divider()

    # 1. Matches by format
    col1, col2 = st.columns(2)
    with col1:
        if not innings.empty:
            fd = innings.groupby("format", as_index=False).agg(matches=("match_id", "nunique"))
            chart_bar(fd, "format", "matches", "Matches by Format", text="matches")

    # 2. Team wins
    with col2:
        if not teams.empty:
            tw = teams[["team", "wins"]].sort_values("wins", ascending=True)
            chart_bar(tw, "wins", "team", "Team Wins", horizontal=True, text="wins")

    # 3. Team wins by format
    st.subheader("🏆 Team Wins Across Test / ODI / T20")
    if not results.empty and {"format", "winner"}.issubset(results.columns):
        wf = results[
            results["winner"].notna() &
            ~results["winner"].astype(str).str.contains("No Result|Draw|Tie|Incomplete", case=False, na=False)
        ].groupby(["winner", "format"], as_index=False).size().rename(columns={"size": "wins"})
        if not wf.empty:
            fig = px.bar(wf, x="winner", y="wins", color="format",
                         barmode="group", title="Wins by Team and Format")
            st.plotly_chart(fig, use_container_width=True)

    # 4. Home vs Away
    st.subheader("🏠 Home vs Away Wins by Team")
    if not q12.empty and {"team", "location", "wins"}.issubset(q12.columns):
        ha = q12[q12["location"].isin(["Home", "Away", "Neutral"])].copy()
        fig = px.bar(
            ha, x="team", y="wins", color="location",
            barmode="group", title="Home vs Away Wins by Team"
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(
            ha[[c for c in [
                "team", "location", "matches", "wins", "losses",
                "no_results", "win_percentage"
            ] if c in ha.columns]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning(
            "Q12 Home/Away data is not available in SQLite yet."
        )

    # 5. Toss
    st.subheader("🪙 Toss Analysis")
    if not q17.empty and {"toss_winner", "winner"}.issubset(q17.columns):
        toss = q17[
            q17["toss_winner"].notna() &
            q17["winner"].notna()
        ].copy()

        toss["outcome"] = toss.apply(
            lambda r: "Toss Winner Won"
            if r["toss_winner"] == r["winner"]
            else "Toss Winner Lost",
            axis=1
        )

        toss_summary = (
            toss.groupby("outcome", as_index=False)
            .size()
            .rename(columns={"size": "matches"})
        )

        fig = px.pie(
            toss_summary, names="outcome", values="matches",
            hole=0.45, title="Toss Winner vs Match Winner"
        )
        st.plotly_chart(fig, use_container_width=True)

        if "decision" in toss.columns and "toss_winner_won" in toss.columns:
            decision = (
                toss.groupby("decision", dropna=False)
                .agg(
                    matches=("match_id", "count"),
                    toss_winner_wins=("toss_winner_won", "sum")
                )
                .reset_index()
            )
            decision["win_percentage"] = (
                decision["toss_winner_wins"] /
                decision["matches"] * 100
            ).round(2)
            st.dataframe(
                decision,
                use_container_width=True,
                hide_index=True
            )
    else:
        st.warning(
            "Q17 Toss data is not available in SQLite yet."
        )

    # 6. Run rate + yearly trend
    col1, col2 = st.columns(2)
    with col1:
        if not innings.empty:
            rr = innings.groupby("format", as_index=False)["run_rate"].mean()
            rr["run_rate"] = rr["run_rate"].round(2)
            chart_bar(rr, "format", "run_rate", "Average Run Rate", text="run_rate")

    with col2:
        if not innings.empty:
            yearly = innings.dropna(subset=["date"]).assign(
                year=innings["date"].dt.year
            ).groupby("year", as_index=False)["runs"].sum()
            fig = px.line(yearly, x="year", y="runs", markers=True,
                          title="Total Runs by Year")
            st.plotly_chart(fig, use_container_width=True)

    # 7. Top 10 batters
    if not batting.empty:
        st.subheader("👑 Top 10 Run Scorers")
        top10 = batting.groupby("batter", as_index=False)["runs"].sum().nlargest(10, "runs")
        chart_bar(top10.sort_values("runs"), "runs", "batter",
                  "Top 10 Run Scorers", horizontal=True, text="runs")

# ============================================================
# PAGE 2 — LIVE & RECENT
# ============================================================
elif page == "🔴 Live & Recent Matches":
    st.header("🔴 Live & Recent Matches")

    if st.button("🔄 Refresh Live Matches"):
        get_live_matches.clear()

    payload, error = get_live_matches()

    if error:
        st.error(error)
    else:
        live_df = flatten_live_matches(payload)

        if live_df.empty:
            st.info("No live matches are currently returned by the API.")
        else:
            st.success(f"{len(live_df)} live/ongoing match records returned.")

            for _, row in live_df.iterrows():
                with st.container(border=True):
                    st.subheader(
                        f"🔴 {row.get('team1', '')} vs {row.get('team2', '')}"
                    )
                    c = st.columns(4)
                    c[0].write(f"**Format:** {row.get('format', '')}")
                    c[1].write(f"**Match:** {row.get('description', '')}")
                    c[2].write(f"**Venue:** {row.get('venue', '')}, {row.get('city', '')}")
                    c[3].write(f"**Status:** {row.get('status', '')}")

                    s1 = row.get("team1_score") or {}
                    s2 = row.get("team2_score") or {}
                    if s1 or s2:
                        st.write(
                            f"**{row.get('team1', '')}:** {s1}   |   "
                            f"**{row.get('team2', '')}:** {s2}"
                        )

    st.divider()
    st.subheader("📅 Recent Completed Matches")

    if not matches.empty:
        recent = matches.copy()
        recent = recent.sort_values("start_date", ascending=False).head(20)
        cols = [
            "match_id", "match_format", "start_date", "series_name",
            "match_desc", "team1_name", "team2_name",
            "venue_name", "venue_city", "status"
        ]
        cols = [x for x in cols if x in recent.columns]
        st.dataframe(recent[cols], use_container_width=True, hide_index=True)

# ============================================================
# PAGE 3 — PLAYER INTELLIGENCE
# ============================================================
elif page == "🏏 Player Intelligence":
    st.header("🏏 Player Intelligence")

    if players.empty:
        st.warning("player_intelligence table is empty.")
    else:
        player_list = sorted(players["player"].dropna().unique())
        selected_player = st.selectbox("Select Player", player_list)
        pf = players[players["player"] == selected_player].copy()

        if not pf.empty:
            st.subheader(f"📌 {selected_player}")
            c = st.columns(4)
            c[0].metric("Batting Runs", fmt(pf["runs"].sum()))
            c[1].metric("Fours", fmt(pf["fours"].sum()))
            c[2].metric("Sixes", fmt(pf["sixes"].sum()))
            c[3].metric("Wickets", fmt(pf["wickets"].sum()))

        st.subheader("💥 Most Sixes by Player")
        sixers = (
            players.groupby("player", as_index=False)["sixes"]
            .sum()
            .sort_values("sixes", ascending=False)
            .head(15)
        )
        if not sixers.empty:
            chart_bar(
                sixers.sort_values("sixes"),
                "sixes", "player",
                "Top 15 Players by Sixes",
                horizontal=True, text="sixes"
            )

            st.dataframe(pf, use_container_width=True, hide_index=True)

        st.divider()
        selected_format = st.selectbox(
            "Format",
            ["All"] + sorted(players["format"].dropna().unique().tolist())
        )

        compare = players.copy()
        if selected_format != "All":
            compare = compare[compare["format"] == selected_format]

        summary = compare.groupby("player", as_index=False).agg(
            runs=("runs", "sum"),
            wickets=("wickets", "sum"),
            fours=("fours", "sum"),
            sixes=("sixes", "sum"),
            batting_matches=("batting_matches", "sum"),
            bowling_matches=("bowling_matches", "sum"),
        )
        summary["impact"] = summary["runs"] + summary["wickets"] * 20

        c1, c2 = st.columns(2)
        with c1:
            chart_bar(
                summary.nlargest(10, "runs").sort_values("runs"),
                "runs", "player", "Top Players by Runs",
                horizontal=True, text="runs"
            )
        with c2:
            chart_bar(
                summary.nlargest(10, "wickets").sort_values("wickets"),
                "wickets", "player", "Top Players by Wickets",
                horizontal=True, text="wickets"
            )

# ============================================================
# PAGE 4 — PLAYER VS PLAYER
# ============================================================
elif page == "⚔️ Player vs Player":
    st.header("⚔️ Player vs Player Analysis")
    st.caption("Compare two players using the historical batting and bowling data in your database.")

    if players.empty:
        st.warning("player_intelligence table is empty.")
    else:
        player_list = sorted(players["player"].dropna().unique())
        c1, c2 = st.columns(2)
        with c1:
            p1 = st.selectbox("Player 1", player_list, index=0)
        with c2:
            default2 = 1 if len(player_list) > 1 else 0
            p2 = st.selectbox("Player 2", player_list, index=default2)

        if p1 == p2:
            st.warning("Select two different players.")
        else:
            def player_summary(name):
                p = players[players["player"] == name].copy()
                return {
                    "Runs": p["runs"].sum(),
                    "Wickets": p["wickets"].sum(),
                    "Fours": p["fours"].sum(),
                    "Sixes": p["sixes"].sum(),
                    "Batting Matches": p["batting_matches"].sum(),
                    "Batting Innings": p["batting_innings"].sum(),
                    "Batting Balls": p["batting_balls"].sum(),
                    "Bowling Matches": p["bowling_matches"].sum(),
                    "Bowling Innings": p["bowling_innings"].sum(),
                    "Runs Conceded": p["runs_conceded"].sum(),
                    "Bowling Balls": p["bowling_balls"].sum(),
                }

            s1, s2 = player_summary(p1), player_summary(p2)

            def sr(s):
                return (s["Runs"] * 100 / s["Batting Balls"]) if s["Batting Balls"] else 0

            def econ(s):
                return (s["Runs Conceded"] * 6 / s["Bowling Balls"]) if s["Bowling Balls"] else 0

            st.subheader("📌 Career Comparison")
            rows = [
                ("Runs", s1["Runs"], s2["Runs"]),
                ("Wickets", s1["Wickets"], s2["Wickets"]),
                ("Fours", s1["Fours"], s2["Fours"]),
                ("Sixes", s1["Sixes"], s2["Sixes"]),
                ("Batting Matches", s1["Batting Matches"], s2["Batting Matches"]),
                ("Batting Innings", s1["Batting Innings"], s2["Batting Innings"]),
                ("Strike Rate", round(sr(s1), 2), round(sr(s2), 2)),
                ("Bowling Matches", s1["Bowling Matches"], s2["Bowling Matches"]),
                ("Bowling Innings", s1["Bowling Innings"], s2["Bowling Innings"]),
                ("Economy Rate", round(econ(s1), 2), round(econ(s2), 2)),
            ]
            comp = pd.DataFrame(rows, columns=["Metric", p1, p2])
            st.dataframe(comp, use_container_width=True, hide_index=True)

            chart_df = pd.DataFrame({
                "Metric": ["Runs", "Wickets", "Fours", "Sixes"],
                p1: [s1["Runs"], s1["Wickets"], s1["Fours"], s1["Sixes"]],
                p2: [s2["Runs"], s2["Wickets"], s2["Fours"], s2["Sixes"]],
            }).melt("Metric", var_name="Player", value_name="Value")

            fig = px.bar(chart_df, x="Metric", y="Value", color="Player",
                         barmode="group", title=f"{p1} vs {p2} — Batting & Bowling Output")
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("📊 Format-by-Format Comparison")
            fmt = players[players["player"].isin([p1, p2])].groupby(
                ["format", "player"], as_index=False
            ).agg(
                runs=("runs", "sum"),
                wickets=("wickets", "sum"),
                fours=("fours", "sum"),
                sixes=("sixes", "sum"),
            )
            if not fmt.empty:
                fig = px.bar(
                    fmt, x="format", y="runs", color="player",
                    barmode="group", title="Runs by Format"
                )
                st.plotly_chart(fig, use_container_width=True)

# ============================================================
# PAGE 5 — BOWLING
# ============================================================
elif page == "🎯 Bowling Intelligence":
    st.header("🎯 Bowling Intelligence")

    if bowling.empty:
        st.warning("bowling_stats table is empty.")
    else:
        formats = ["All"] + sorted(bowling["format"].dropna().unique().tolist())
        selected = st.selectbox("Format", formats)
        b = bowling.copy()
        if selected != "All":
            b = b[b["format"] == selected]

        summary = b.groupby("bowler", as_index=False).agg(
            wickets=("wickets", "sum"),
            runs_conceded=("runs_conceded", "sum"),
            balls=("balls", "sum"),
            matches=("match_id", "nunique")
        )
        summary["economy_rate"] = (
            summary["runs_conceded"] / summary["balls"] * 6
        ).replace([float("inf"), -float("inf")], 0).round(2)

        c = st.columns(4)
        c[0].metric("Wickets", fmt(b["wickets"].sum()))
        c[1].metric("Runs Conceded", fmt(b["runs_conceded"].sum()))
        c[2].metric("Bowlers", fmt(summary["bowler"].nunique()))
        c[3].metric("Matches", fmt(b["match_id"].nunique()))

        c1, c2 = st.columns(2)
        with c1:
            chart_bar(summary.nlargest(15, "wickets").sort_values("wickets"),
                      "wickets", "bowler", "Top 15 Wicket Takers",
                      horizontal=True, text="wickets")
        with c2:
            econ = summary[summary["balls"] >= 600].nsmallest(10, "economy_rate")
            chart_bar(econ.sort_values("economy_rate", ascending=False),
                      "economy_rate", "bowler", "Best Economy Rates",
                      horizontal=True, text="economy_rate")

        st.dataframe(summary.sort_values("wickets", ascending=False).head(50),
                     use_container_width=True, hide_index=True)

# ============================================================
# PAGE 5 — TEAM PERFORMANCE
# ============================================================
elif page == "👥 Team Performance":
    st.header("👥 Team Performance")

    if teams.empty:
        st.warning("team_performance table is empty.")
    else:
        st.dataframe(teams, use_container_width=True, hide_index=True)

        c1, c2 = st.columns(2)
        with c1:
            chart_bar(teams.sort_values("wins"), "wins", "team",
                      "Total Wins", horizontal=True, text="wins")
        with c2:
            if "win_percentage" in teams.columns:
                chart_bar(
                    teams.sort_values("win_percentage"),
                    "win_percentage", "team", "Win Percentage",
                    horizontal=True, text="win_percentage"
                )

        st.subheader("💥 Most Sixes by Team")
        if not batting.empty and "batting_team" in batting.columns and "sixes" in batting.columns:
            team_sixes = (
                batting.groupby("batting_team", as_index=False)["sixes"]
                .sum()
                .rename(columns={"batting_team": "team"})
                .sort_values("sixes", ascending=False)
            )
            chart_bar(
                team_sixes.sort_values("sixes"),
                "sixes", "team",
                "Most Sixes by Team",
                horizontal=True, text="sixes"
            )

        if not results.empty and {"winner", "format"}.issubset(results.columns):
            st.subheader("Wins by Team and Format")
            wf = results[results["winner"].notna()].groupby(
                ["winner", "format"], as_index=False
            ).size().rename(columns={"size": "wins"})
            fig = px.bar(wf, x="winner", y="wins", color="format",
                         barmode="group", title="Team Wins by Format")
            st.plotly_chart(fig, use_container_width=True)

# ============================================================
# PAGE 7 — TEAM VS TEAM H2H
# ============================================================
elif page == "🏆 Team vs Team H2H":
    st.header("🏆 Team vs Team — Head-to-Head")
    st.caption("Compare two teams across the historical match dataset.")

    if results.empty or not {"team1", "team2", "winner"}.issubset(results.columns):
        st.warning("The match_results table does not contain the required team and winner fields.")
    else:
        team_values = sorted(set(results["team1"].dropna().unique()) |
                             set(results["team2"].dropna().unique()))
        c1, c2 = st.columns(2)
        with c1:
            team1 = st.selectbox("Team 1", team_values, index=0)
        with c2:
            team2 = st.selectbox("Team 2", team_values,
                                 index=1 if len(team_values) > 1 else 0)

        if team1 == team2:
            st.warning("Select two different teams.")
        else:
            h = results[
                ((results["team1"] == team1) & (results["team2"] == team2)) |
                ((results["team1"] == team2) & (results["team2"] == team1))
            ].copy()

            h["winner_clean"] = h["winner"].astype(str)

            team1_wins = (h["winner_clean"] == team1).sum()
            team2_wins = (h["winner_clean"] == team2).sum()
            draws_ties = h["winner_clean"].str.contains("Tie|Draw", case=False, na=False).sum()
            decided = team1_wins + team2_wins

            c = st.columns(5)
            c[0].metric("🏏 Matches", fmt(len(h)))
            c[1].metric(f"🏆 {team1} Wins", fmt(team1_wins))
            c[2].metric(f"🏆 {team2} Wins", fmt(team2_wins))
            c[3].metric("🤝 Ties / Draws", fmt(draws_ties))
            c[4].metric("📊 Decided", fmt(decided))

            if not h.empty:
                win_chart = pd.DataFrame({
                    "Team": [team1, team2],
                    "Wins": [team1_wins, team2_wins]
                })
                chart_bar(win_chart, "Team", "Wins",
                          f"{team1} vs {team2} — Head-to-Head Wins", text="Wins")

            if "format" in h.columns:
                st.subheader("📋 Head-to-Head by Format")
                hf = []
                for f in sorted(h["format"].dropna().unique()):
                    x = h[h["format"] == f]
                    hf.append({
                        "Format": f,
                        "Matches": len(x),
                        f"{team1} Wins": (x["winner_clean"] == team1).sum(),
                        f"{team2} Wins": (x["winner_clean"] == team2).sum(),
                    })
                if hf:
                    st.dataframe(pd.DataFrame(hf), use_container_width=True, hide_index=True)

            if "date" in h.columns:
                st.subheader("📅 Recent Meetings")
                recent_h = h.sort_values("date", ascending=False).head(20)
                display_cols = [c for c in [
                    "date", "format", "team1", "team2", "winner",
                    "result_type", "margin", "match_id"
                ] if c in recent_h.columns]
                st.dataframe(
                    recent_h[display_cols],
                    use_container_width=True,
                    hide_index=True
                )

# ============================================================
# PAGE 8 — ADVANCED INSIGHTS
# ============================================================
elif page == "📊 Advanced Insights":
    st.header("📊 Advanced Cricket Insights")

    # Q9
    st.subheader("Q9 — All-rounders: 1,000+ Runs and 50+ Wickets")
    if not players.empty:
        ar = players.groupby(["player", "format"], as_index=False).agg(
            runs=("runs", "sum"), wickets=("wickets", "sum")
        )
        ar = ar[(ar["runs"] > 1000) & (ar["wickets"] > 50)].sort_values(
            ["runs", "wickets"], ascending=False
        )
        st.dataframe(ar, use_container_width=True, hide_index=True)

    # Q19
    st.divider()
    st.subheader("Q19 — Batting Consistency")
    if not q19.empty:
        st.dataframe(q19.head(50), use_container_width=True, hide_index=True)
        if "longest_30_plus_streak" in q19.columns:
            d = q19.nlargest(15, "longest_30_plus_streak").sort_values(
                "longest_30_plus_streak"
            )
            chart_bar(d, "longest_30_plus_streak", "batter",
                      "Longest 30+ Run Streaks", horizontal=True,
                      text="longest_30_plus_streak")

    # Q24
    st.divider()
    st.subheader("Q24 — Partnership Intelligence")
    if not q24.empty:
        st.dataframe(q24.head(50), use_container_width=True, hide_index=True)
        if "partnerships_over_50" in q24.columns:
            d = q24.nlargest(15, "partnerships_over_50").sort_values(
                "partnerships_over_50"
            )
            chart_bar(d, "partnerships_over_50", "partnership_pair",
                      "Most 50+ Partnerships", horizontal=True,
                      text="partnerships_over_50")

    # Format run rate
    st.divider()
    st.subheader("📈 Average Run Rate by Format")
    if not innings.empty:
        rr = innings.groupby("format", as_index=False)["run_rate"].mean()
        rr["run_rate"] = rr["run_rate"].round(2)
        chart_bar(rr, "format", "run_rate", "Average Run Rate",
                  text="run_rate")

    # Sixes by year
    st.subheader("💥 Sixes by Year")
    if not batting.empty and "date" in batting.columns:
        yearly_sixes = (
            batting.dropna(subset=["date"])
            .assign(year=batting["date"].dt.year)
            .groupby("year", as_index=False)["sixes"]
            .sum()
            .sort_values("year")
        )
        fig = px.line(
            yearly_sixes, x="year", y="sixes",
            markers=True, title="Total Sixes by Year"
        )
        fig.update_layout(margin=dict(l=10, r=10, t=55, b=10))
        st.plotly_chart(fig, use_container_width=True)

    # Yearly batting
    st.subheader("📅 Batting Runs by Year")
    if not batting.empty:
        yearly = batting.dropna(subset=["date"]).assign(
            year=batting["date"].dt.year
        ).groupby("year", as_index=False)["runs"].sum()
        fig = px.line(yearly, x="year", y="runs", markers=True,
                      title="Total Batting Runs by Year")
        st.plotly_chart(fig, use_container_width=True)

# ============================================================
# PAGE 7 — ALL 25 SQL QUESTIONS
# ============================================================
elif page == "🔍 SQL Analytics":
    st.header("🔍 SQL Analytics")
    st.caption("All 25 project questions are listed below. Select any question to view and run its SQL.")

    queries = {
        "Q1 — India players": """
SELECT player, SUM(runs) AS runs, SUM(wickets) AS wickets
FROM player_intelligence
WHERE player IN (
    SELECT batter FROM batting_stats WHERE batting_team = 'India'
)
GROUP BY player
ORDER BY runs DESC;
""",
        "Q2 — Matches in last 30 days": """
SELECT match_id, match_desc, team1_name, team2_name,
       venue_city, start_date, status
FROM matches
WHERE date(start_date) >= date(
    (SELECT MAX(start_date) FROM matches), '-30 day'
)
ORDER BY date(start_date) DESC;
""",
        "Q3 — Top 10 ODI run scorers": """
SELECT batter AS player, SUM(runs) AS total_runs,
       SUM(balls) AS balls,
       ROUND(SUM(runs) * 100.0 / NULLIF(SUM(balls),0),2) AS strike_rate
FROM batting_stats
WHERE format = 'ODI'
GROUP BY batter
ORDER BY total_runs DESC
LIMIT 10;
""",
        "Q4 — Venues with most matches": """
SELECT
    venue,
    city,
    country,
    capacity
FROM venue_metadata
WHERE capacity > 50000
ORDER BY capacity DESC;
""",
        "Q5 — Team wins": """
SELECT team, wins, win_percentage
FROM team_performance
ORDER BY wins DESC;
""",
        "Q6 — Players by role": """
SELECT role, COUNT(*) AS player_count
FROM player_stats
GROUP BY role
ORDER BY player_count DESC;
""",
        "Q7 — Highest individual score by format": """
SELECT format, batter AS player, MAX(runs) AS highest_score
FROM batting_stats
GROUP BY format
ORDER BY format, highest_score DESC;
""",
        "Q8 — Series represented in available match data": """
SELECT series_name,
       match_format,
       COUNT(DISTINCT match_id) AS matches,
       MIN(date(start_date)) AS first_match
FROM matches
WHERE series_name IS NOT NULL
  AND TRIM(series_name) <> ''
GROUP BY series_name, match_format
ORDER BY first_match DESC, matches DESC;
""",
        "Q9 — All-rounders over thresholds": """
SELECT player, format, SUM(runs) AS runs, SUM(wickets) AS wickets
FROM player_intelligence
GROUP BY player, format
HAVING SUM(runs) > 1000 AND SUM(wickets) > 50
ORDER BY runs DESC;
""",
        "Q10 — Last 20 completed matches": """
SELECT match_id, match_desc, team1_name, team2_name,
       winner, victory_margin, victory_type, venue_name, start_date
FROM matches
WHERE LOWER(state) = 'complete'
ORDER BY date(start_date) DESC
LIMIT 20;
""",
        "Q11 — Cross-format performance": """
SELECT player,
       SUM(CASE WHEN format='TEST' THEN runs ELSE 0 END) AS test_runs,
       SUM(CASE WHEN format='ODI' THEN runs ELSE 0 END) AS odi_runs,
       SUM(CASE WHEN format='T20' THEN runs ELSE 0 END) AS t20_runs,
       SUM(runs) AS total_runs
FROM player_intelligence
GROUP BY player
ORDER BY total_runs DESC
LIMIT 20;
""",
        "Q12 — Home vs away": """
SELECT team, location, matches, wins, losses,
       no_results, win_percentage
FROM q12_home_away
WHERE location IN ('Home','Away')
ORDER BY team,
         CASE location WHEN 'Home' THEN 1 ELSE 2 END;
""",
        "Q13 — Partnerships >= 100": """
SELECT rank, match_id, format, date, innings,
       batting_team, partnership_pair, partnership_runs
FROM q13_partnerships_100_plus
WHERE partnership_runs >= 100
ORDER BY partnership_runs DESC, date DESC;
""",
        "Q14 — Venue bowling performance": """
WITH venue_bowler_match AS (
    SELECT
        i.venue,
        b.match_id,
        b.bowler,
        SUM(b.balls) AS balls,
        SUM(b.runs_conceded) AS runs_conceded,
        SUM(b.wickets) AS wickets
    FROM bowling_stats b
    JOIN (
        SELECT DISTINCT match_id, venue
        FROM innings_stats
        WHERE venue IS NOT NULL
    ) i
      ON i.match_id = b.match_id
    GROUP BY i.venue, b.match_id, b.bowler
),
qualifying_bowlers AS (
    SELECT venue, bowler
    FROM venue_bowler_match
    GROUP BY venue, bowler
    HAVING COUNT(*) >= 3
       AND MIN(balls) >= 24
)
SELECT
    vbm.venue,
    vbm.bowler,
    COUNT(*) AS matches,
    ROUND(
        AVG(vbm.runs_conceded * 6.0 / NULLIF(vbm.balls, 0)),
        2
    ) AS average_economy_rate,
    SUM(vbm.wickets) AS total_wickets
FROM venue_bowler_match vbm
JOIN qualifying_bowlers qb
  ON qb.venue = vbm.venue
 AND qb.bowler = vbm.bowler
GROUP BY vbm.venue, vbm.bowler
ORDER BY average_economy_rate ASC, total_wickets DESC;
""",
        "Q15 — Close matches (available match-margin data)": """
WITH close_matches AS (
    SELECT
        match_id,
        winner
    FROM historical_metadata
    WHERE
        (win_runs IS NOT NULL AND win_runs > 0 AND win_runs < 50)
        OR
        (win_wickets IS NOT NULL AND win_wickets > 0 AND win_wickets < 5)
),
player_close_match AS (
    SELECT
        b.batter,
        b.match_id,
        b.batting_team,
        SUM(b.runs) AS match_runs,
        CASE
            WHEN b.batting_team = cm.winner THEN 1
            ELSE 0
        END AS team_won
    FROM batting_stats b
    INNER JOIN close_matches cm
        ON b.match_id = cm.match_id
    GROUP BY
        b.batter,
        b.match_id,
        b.batting_team,
        cm.winner
)
SELECT
    batter AS player,
    ROUND(AVG(match_runs), 2) AS average_runs,
    COUNT(DISTINCT match_id) AS close_matches_played,
    SUM(team_won) AS close_matches_won_when_batted
FROM player_close_match
GROUP BY batter
ORDER BY
    close_matches_won_when_batted DESC,
    average_runs DESC;
""",
        "Q16 — Yearly batting since 2020": """
SELECT strftime('%Y', date) AS year,
       batter,
       SUM(runs) AS runs,
       SUM(balls) AS balls,
       ROUND(SUM(runs)*100.0/NULLIF(SUM(balls),0),2) AS strike_rate
FROM batting_stats
WHERE date >= '2020-01-01'
GROUP BY year, batter
ORDER BY year, runs DESC;
""",
        "Q17 — Toss advantage": """
SELECT
    CASE WHEN toss_winner = winner
         THEN 'Toss Winner Won'
         ELSE 'Toss Winner Lost'
    END AS outcome,
    COUNT(*) AS matches,
    ROUND(
        COUNT(*) * 100.0 /
        SUM(COUNT(*)) OVER (), 2
    ) AS percentage
FROM q17_toss_analysis
WHERE toss_winner IS NOT NULL
  AND winner IS NOT NULL
GROUP BY outcome;
""",
        "Q18 — Most economical ODI/T20 bowlers": """
SELECT bowler, format,
       COUNT(DISTINCT match_id) AS matches,
       SUM(balls) AS balls,
       ROUND(SUM(runs_conceded)*6.0/NULLIF(SUM(balls),0),2) AS economy_rate,
       SUM(wickets) AS wickets
FROM bowling_stats
WHERE format IN ('ODI','T20')
GROUP BY bowler, format
HAVING COUNT(DISTINCT match_id) >= 10
ORDER BY economy_rate ASC
LIMIT 20;
""",
        "Q19 — Batting consistency": """
SELECT *
FROM q19_batting_consistency
ORDER BY longest_30_plus_streak DESC, qualifying_streaks DESC;
""",
        "Q20 — Format participation and batting": """
SELECT player, format,
       batting_matches, batting_innings, runs,
       batting_balls,
       ROUND(runs*100.0/NULLIF(batting_balls,0),2) AS strike_rate
FROM player_intelligence
ORDER BY player, format;
""",
        "Q21 — Comprehensive ranking": """
SELECT player,
       SUM(runs) AS runs,
       SUM(wickets) AS wickets,
       SUM(runs) + SUM(wickets)*20 AS ranking_score
FROM player_intelligence
GROUP BY player
ORDER BY ranking_score DESC
LIMIT 50;
""",
        "Q22 — Head-to-head last 3 years": """
SELECT team1, team2, COUNT(*) AS matches,
       SUM(CASE WHEN winner=team1 THEN 1 ELSE 0 END) AS team1_wins,
       SUM(CASE WHEN winner=team2 THEN 1 ELSE 0 END) AS team2_wins
FROM match_results
WHERE date >= date('now','-3 year')
GROUP BY team1, team2
HAVING COUNT(*) >= 5
ORDER BY matches DESC;
""",
        "Q23 — Recent player form": """
SELECT batter,
       COUNT(*) AS innings,
       SUM(runs) AS runs,
       ROUND(AVG(runs),2) AS avg_runs
FROM batting_stats
WHERE date >= date('now','-12 months')
GROUP BY batter
HAVING COUNT(*) >= 5
ORDER BY avg_runs DESC
LIMIT 30;
""",
        "Q24 — Partnership analysis": """
SELECT *
FROM q24_partnership_analysis
ORDER BY partnerships_over_50 DESC, avg_partnership DESC;
""",
        "Q25 — Quarterly batting trajectory": """
SELECT strftime('%Y', date) AS year,
       ((CAST(strftime('%m', date) AS INTEGER)-1)/3)+1 AS quarter,
       batter,
       COUNT(*) AS innings,
       SUM(runs) AS runs,
       ROUND(AVG(runs),2) AS avg_runs
FROM batting_stats
GROUP BY year, quarter, batter
ORDER BY year, quarter, runs DESC;
"""
    }

    selected = st.selectbox("Select Question", list(queries.keys()))
    sql = queries[selected]

    st.code(sql, language="sql")

    if st.button("▶ Run Selected Query", type="primary"):
        try:
            result = run_sql(sql)
            st.success(f"Query executed successfully — {len(result):,} rows.")
            st.dataframe(result, use_container_width=True, hide_index=True)

            # Automatic chart for common query outputs
            numeric = result.select_dtypes(include="number").columns.tolist()
            text_cols = result.select_dtypes(include=["object"]).columns.tolist()

            if len(result) > 1 and numeric and text_cols:
                y = numeric[0]
                x = text_cols[0]
                if result[x].nunique() <= 30:
                    fig = px.bar(result.head(30), x=x, y=y, title=f"{selected} — Visualization")
                    st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"SQL Error: {e}")
            st.info(
                "This question depends on a source table that is not currently in the SQLite database "
                "(for example venue/series/home-away/toss/partnership metadata). "
                "The question is still included here so all 25 project questions remain visible."
            )

# ============================================================
# PAGE — CRUD OPERATIONS
# ============================================================
elif page == "🛠️ CRUD Operations":

    st.header("🛠️ CRUD Operations — Players")
    st.caption(
        "Full create / read / update / delete on the players table, "
        "backed by the validated CRUD module."
    )

    # --------------------------------------------------------
    # CREATE PLAYERS TABLE IF IT DOES NOT EXIST
    # --------------------------------------------------------
    conn.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL UNIQUE,
            country TEXT NOT NULL,
            batting_style TEXT,
            bowling_style TEXT,
            playing_role TEXT NOT NULL
        )
    """)
    conn.commit()

    # --------------------------------------------------------
    # TABS
    # --------------------------------------------------------
    create_tab, read_tab, update_tab, delete_tab = st.tabs([
        "➕ Create",
        "🔎 Read / Search",
        "✏️ Update",
        "🗑️ Delete"
    ])

    # ========================================================
    # CREATE
    # ========================================================
    with create_tab:

        st.markdown("### Create New Player")

        col1, col2 = st.columns(2)

        with col1:
            full_name = st.text_input(
                "Full name*",
                key="crud_create_name"
            )

            country = st.text_input(
                "Country*",
                key="crud_create_country"
            )

            playing_role = st.selectbox(
                "Playing role*",
                [
                    "Batsman",
                    "Bowler",
                    "All-rounder",
                    "Wicket-keeper"
                ],
                key="crud_create_role"
            )

        with col2:
            batting_style = st.selectbox(
                "Batting style",
                [
                    "Choose an option",
                    "Right-hand bat",
                    "Left-hand bat"
                ],
                key="crud_create_batting"
            )

            bowling_style = st.selectbox(
                "Bowling style",
                [
                    "Choose an option",
                    "Right-arm fast",
                    "Right-arm medium",
                    "Right-arm offbreak",
                    "Right-arm legbreak",
                    "Left-arm fast",
                    "Left-arm medium",
                    "Left-arm orthodox",
                    "Left-arm chinaman"
                ],
                key="crud_create_bowling"
            )

        if st.button(
            "Create player",
            use_container_width=True,
            type="primary",
            key="crud_create_button"
        ):
            if not full_name.strip():
                st.error("Full name is required.")

            elif not country.strip():
                st.error("Country is required.")

            else:
                batting_value = (
                    None
                    if batting_style == "Choose an option"
                    else batting_style
                )

                bowling_value = (
                    None
                    if bowling_style == "Choose an option"
                    else bowling_style
                )

                try:
                    conn.execute("""
                        INSERT INTO players
                        (
                            full_name,
                            country,
                            batting_style,
                            bowling_style,
                            playing_role
                        )
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        full_name.strip(),
                        country.strip(),
                        batting_value,
                        bowling_value,
                        playing_role
                    ))

                    conn.commit()

                    load_table.clear()

                    st.success(
                        f"Player '{full_name.strip()}' created successfully."
                    )

                except sqlite3.IntegrityError:
                    st.error("A player with this name already exists.")

                except Exception as e:
                    st.error(f"Create error: {e}")

    # ========================================================
    # READ / SEARCH
    # ========================================================
    with read_tab:

        st.markdown("### Read / Search Players")

        search_text = st.text_input(
            "Search by player name or country",
            key="crud_search"
        )

        if search_text.strip():

            result = pd.read_sql_query("""
                SELECT
                    id,
                    full_name,
                    country,
                    batting_style,
                    bowling_style,
                    playing_role
                FROM players
                WHERE
                    full_name LIKE ?
                    OR country LIKE ?
                ORDER BY full_name
            """, conn, params=(
                f"%{search_text.strip()}%",
                f"%{search_text.strip()}%"
            ))

        else:

            result = pd.read_sql_query("""
                SELECT
                    id,
                    full_name,
                    country,
                    batting_style,
                    bowling_style,
                    playing_role
                FROM players
                ORDER BY full_name
            """, conn)

        st.dataframe(
            result,
            use_container_width=True,
            hide_index=True
        )

        st.caption(f"{len(result):,} player record(s) found.")

    # ========================================================
    # UPDATE
    # ========================================================
    with update_tab:

        st.markdown("### Update Player")

        players_df = pd.read_sql_query("""
            SELECT id, full_name
            FROM players
            ORDER BY full_name
        """, conn)

        if players_df.empty:

            st.info("No player records available to update.")

        else:

            selected_player = st.selectbox(
                "Select player",
                players_df["full_name"].tolist(),
                key="crud_update_player"
            )

            selected_id = int(
                players_df.loc[
                    players_df["full_name"] == selected_player,
                    "id"
                ].iloc[0]
            )

            current = pd.read_sql_query("""
                SELECT *
                FROM players
                WHERE id = ?
            """, conn, params=(selected_id,)).iloc[0]

            col1, col2 = st.columns(2)

            with col1:
                update_name = st.text_input(
                    "Full name*",
                    value=str(current["full_name"]),
                    key="crud_update_name"
                )

                update_country = st.text_input(
                    "Country*",
                    value=str(current["country"]),
                    key="crud_update_country"
                )

                role_options = [
                    "Batsman",
                    "Bowler",
                    "All-rounder",
                    "Wicket-keeper"
                ]

                current_role = (
                    current["playing_role"]
                    if current["playing_role"] in role_options
                    else "Batsman"
                )

                update_role = st.selectbox(
                    "Playing role*",
                    role_options,
                    index=role_options.index(current_role),
                    key="crud_update_role"
                )

            with col2:

                batting_options = [
                    "Choose an option",
                    "Right-hand bat",
                    "Left-hand bat"
                ]

                current_batting = (
                    current["batting_style"]
                    if current["batting_style"] in batting_options
                    else "Choose an option"
                )

                update_batting = st.selectbox(
                    "Batting style",
                    batting_options,
                    index=batting_options.index(current_batting),
                    key="crud_update_batting"
                )

                bowling_options = [
                    "Choose an option",
                    "Right-arm fast",
                    "Right-arm medium",
                    "Right-arm offbreak",
                    "Right-arm legbreak",
                    "Left-arm fast",
                    "Left-arm medium",
                    "Left-arm orthodox",
                    "Left-arm chinaman"
                ]

                current_bowling = (
                    current["bowling_style"]
                    if current["bowling_style"] in bowling_options
                    else "Choose an option"
                )

                update_bowling = st.selectbox(
                    "Bowling style",
                    bowling_options,
                    index=bowling_options.index(current_bowling),
                    key="crud_update_bowling"
                )

            if st.button(
                "Update player",
                use_container_width=True,
                type="primary",
                key="crud_update_button"
            ):

                if not update_name.strip():
                    st.error("Full name is required.")

                elif not update_country.strip():
                    st.error("Country is required.")

                else:

                    batting_value = (
                        None
                        if update_batting == "Choose an option"
                        else update_batting
                    )

                    bowling_value = (
                        None
                        if update_bowling == "Choose an option"
                        else update_bowling
                    )

                    try:
                        conn.execute("""
                            UPDATE players
                            SET
                                full_name = ?,
                                country = ?,
                                batting_style = ?,
                                bowling_style = ?,
                                playing_role = ?
                            WHERE id = ?
                        """, (
                            update_name.strip(),
                            update_country.strip(),
                            batting_value,
                            bowling_value,
                            update_role,
                            selected_id
                        ))

                        conn.commit()

                        load_table.clear()

                        st.success("Player updated successfully.")

                    except sqlite3.IntegrityError:
                        st.error("Another player already has this name.")

                    except Exception as e:
                        st.error(f"Update error: {e}")

    # ========================================================
    # DELETE
    # ========================================================
    with delete_tab:

        st.markdown("### Delete Player")

        players_df = pd.read_sql_query("""
            SELECT id, full_name, country, playing_role
            FROM players
            ORDER BY full_name
        """, conn)

        if players_df.empty:

            st.info("No player records available to delete.")

        else:

            selected_delete = st.selectbox(
                "Select player",
                players_df["full_name"].tolist(),
                key="crud_delete_player"
            )

            selected_delete_row = players_df[
                players_df["full_name"] == selected_delete
            ].iloc[0]

            st.info(
                f"**Player:** {selected_delete_row['full_name']}  \n"
                f"**Country:** {selected_delete_row['country']}  \n"
                f"**Role:** {selected_delete_row['playing_role']}"
            )

            confirm_delete = st.checkbox(
                "I understand that this deletion is permanent.",
                key="crud_delete_confirm"
            )

            if st.button(
                "Delete player",
                use_container_width=True,
                type="primary",
                key="crud_delete_button"
            ):

                if not confirm_delete:

                    st.error("Please confirm the deletion first.")

                else:

                    try:
                        conn.execute("""
                            DELETE FROM players
                            WHERE full_name = ?
                        """, (selected_delete,))

                        conn.commit()

                        load_table.clear()

                        st.success(
                            f"Player '{selected_delete}' deleted successfully."
                        )

                    except Exception as e:
                        st.error(f"Delete error: {e}")


st.sidebar.divider()
st.sidebar.caption("Cricbuzz LiveStats | Portfolio Project")