import pandas as pd


# ============================================================
# BATTING EXTRACTION
# ============================================================

def extract_batting_data(scorecard_data, match_id):
    """
    Extract batting information from a Cricbuzz scorecard.

    Returns:
        pandas.DataFrame
    """

    batting_records = []

    for innings in scorecard_data.get("scorecard", []):

        innings_id = innings.get("inningsid")
        batting_team = innings.get("batteamname")

        batsmen = innings.get("batsman", [])

        for batsman in batsmen:

            record = {
                "match_id": match_id,
                "innings_id": innings_id,
                "batting_team": batting_team,
                "player_id": batsman.get("id"),
                "player_name": batsman.get("name"),
                "runs": batsman.get("runs"),
                "balls": batsman.get("balls"),
                "fours": batsman.get("fours"),
                "sixes": batsman.get("sixes"),
                "strike_rate": batsman.get("strkrate"),
                "dismissal": batsman.get("outdec")
            }

            batting_records.append(record)

    return pd.DataFrame(batting_records)


# ============================================================
# BOWLING EXTRACTION
# ============================================================

def extract_bowling_data(
    scorecard_data,
    match_id,
    team1_name=None,
    team2_name=None
):
    """
    Extract bowling information from a Cricbuzz scorecard.

    The bowling team is determined from the batting team
    of each innings.

    Returns:
        pandas.DataFrame
    """

    bowling_records = []

    for innings in scorecard_data.get("scorecard", []):

        innings_id = innings.get("inningsid")
        batting_team = innings.get("batteamname")

        # ----------------------------------------------------
        # Determine bowling team
        # ----------------------------------------------------

        if batting_team == team1_name:
            bowling_team = team2_name

        elif batting_team == team2_name:
            bowling_team = team1_name

        else:
            bowling_team = None

        bowlers = innings.get("bowler", [])

        for bowler in bowlers:

            record = {
                "match_id": match_id,
                "innings_id": innings_id,
                "bowling_team": bowling_team,
                "opposition_batting_team": batting_team,
                "player_id": bowler.get("id"),
                "player_name": bowler.get("name"),
                "overs": bowler.get("overs"),
                "maidens": bowler.get("maidens"),
                "runs_conceded": bowler.get("runs"),
                "wickets": bowler.get("wickets"),
                "economy": bowler.get("economy")
            }

            bowling_records.append(record)

    return pd.DataFrame(bowling_records)