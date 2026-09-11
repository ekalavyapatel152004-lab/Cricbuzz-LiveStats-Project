import pandas as pd


def extract_recent_matches(data):
    """
    Extract match-level information from the Cricbuzz
    recent matches API response.
    """

    matches = []

    for match_type in data.get("typeMatches", []):

        match_type_name = match_type.get("matchType")

        for series_item in match_type.get("seriesMatches", []):

            series_wrapper = series_item.get("seriesAdWrapper")

            if not series_wrapper:
                continue

            series_id = series_wrapper.get("seriesId")
            series_name = series_wrapper.get("seriesName")

            for match in series_wrapper.get("matches", []):

                match_info = match.get("matchInfo", {})
                team1 = match_info.get("team1", {})
                team2 = match_info.get("team2", {})
                venue = match_info.get("venueInfo", {})

                matches.append({
                    "match_type": match_type_name,
                    "series_id": series_id,
                    "series_name": series_name,

                    "match_id": match_info.get("matchId"),
                    "match_desc": match_info.get("matchDesc"),
                    "match_format": match_info.get("matchFormat"),

                    "start_date": match_info.get("startDate"),
                    "end_date": match_info.get("endDate"),

                    "state": match_info.get("state"),
                    "status": match_info.get("status"),
                    "state_title": match_info.get("stateTitle"),

                    "team1_id": team1.get("teamId"),
                    "team1_name": team1.get("teamName"),
                    "team1_short_name": team1.get("teamSName"),

                    "team2_id": team2.get("teamId"),
                    "team2_name": team2.get("teamName"),
                    "team2_short_name": team2.get("teamSName"),

                    "venue_id": venue.get("id"),
                    "venue_name": venue.get("ground"),
                    "venue_city": venue.get("city"),
                    "venue_timezone": venue.get("timezone"),

                    "latitude": venue.get("latitude"),
                    "longitude": venue.get("longitude"),

                    "current_batting_team_id": match_info.get(
                        "currBatTeamId"
                    )
                })

    df = pd.DataFrame(matches)

    return clean_matches(df)


def clean_matches(df):
    """
    Clean and standardize the matches DataFrame.
    """

    df = df.copy()

    # -------------------------------------------------
    # 1. Convert Unix timestamps from milliseconds
    # -------------------------------------------------

    df["start_date"] = pd.to_datetime(
        pd.to_numeric(df["start_date"], errors="coerce"),
        unit="ms"
    )

    df["end_date"] = pd.to_datetime(
        pd.to_numeric(df["end_date"], errors="coerce"),
        unit="ms"
    )

    # -------------------------------------------------
    # 2. Convert geographic coordinates to numeric
    # -------------------------------------------------

    df["latitude"] = pd.to_numeric(
        df["latitude"],
        errors="coerce"
    )

    df["longitude"] = pd.to_numeric(
        df["longitude"],
        errors="coerce"
    )

    # -------------------------------------------------
    # 3. Standardize text columns
    # -------------------------------------------------

    text_columns = [
        "match_type",
        "series_name",
        "match_desc",
        "match_format",
        "state",
        "status",
        "state_title",
        "team1_name",
        "team1_short_name",
        "team2_name",
        "team2_short_name",
        "venue_name",
        "venue_city",
        "venue_timezone"
    ]

    for column in text_columns:
        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
        )

    # -------------------------------------------------
    # 4. Standardize match format
    # -------------------------------------------------

    df["match_format"] = df["match_format"].str.upper()

    # -------------------------------------------------
    # 5. Remove duplicate match IDs
    # -------------------------------------------------

    df = df.drop_duplicates(
        subset=["match_id"]
    ).reset_index(drop=True)

    return df