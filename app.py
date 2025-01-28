from flask import Flask, render_template, request
from nba_api.live.nba.endpoints import scoreboard
from nba_api.stats.endpoints import teamgamelog
from nba_api.stats.static import teams

app = Flask(__name__)


def get_upcoming_games():
    """Fetch upcoming games for the next 7 days with team IDs."""
    try:
        sb = scoreboard.ScoreBoard()
        games = sb.games.get_dict()
        upcoming = []
        for game in games:
            upcoming.append(
                {
                    "game_id": game["gameId"],
                    "home_team_id": game["homeTeam"]["teamId"],
                    "home_team": game["homeTeam"]["teamName"],
                    "away_team_id": game["awayTeam"]["teamId"],
                    "away_team": game["awayTeam"]["teamName"],
                    "date": game["gameTimeUTC"],
                }
            )
        return upcoming
    except:
        # Fallback mock data if API fails
        return [
            {
                "game_id": "0022301234",
                "home_team_id": 1610612737,
                "home_team": "Atlanta Hawks",
                "away_team_id": 1610612738,
                "away_team": "Boston Celtics",
                "date": "2024-03-30T23:30:00Z",
            }
        ]


def get_team_stats(team_id):
    """Get average points scored/allowed for a team's last 10 games."""
    try:
        gamelog = teamgamelog.TeamGameLog(team_id=team_id, timeout=10)
        df = gamelog.get_data_frames()[0].head(10)
        avg_scored = df["PTS"].mean()
        avg_allowed = df["OPP_PTS"].mean()
        return avg_scored, avg_allowed
    except:
        # Fallback if no data (e.g., preseason)
        return 110.0, 110.0  # Mock averages


@app.route("/")
def index():
    """Show upcoming games."""
    games = get_upcoming_games()
    return render_template("index.html", games=games)


@app.route("/predict", methods=["POST"])
def predict():
    """Handle prediction request."""
    selected_indices = request.form.getlist("game_index")
    games = get_upcoming_games()
    predictions = []

    for index in selected_indices:
        try:
            index = int(index)
            game = games[index]
            home_id = game["home_team_id"]
            away_id = game["away_team_id"]

            # Get stats for both teams
            home_scored, _ = get_team_stats(home_id)
            _, away_allowed = get_team_stats(away_id)

            # Simple prediction model
            predicted_total = round((home_scored + away_allowed) * 0.5)

            predictions.append(
                {
                    "matchup": f"{game['home_team']} vs {game['away_team']}",
                    "total": predicted_total,
                }
            )
        except:
            continue

    return render_template("results.html", predictions=predictions)


if __name__ == "__main__":
    app.run(debug=True)
