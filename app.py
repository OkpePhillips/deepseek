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
    """Get average points scored for a team's last 10 games."""
    try:
        gamelog = teamgamelog.TeamGameLog(team_id=team_id, timeout=10)
        df = gamelog.get_data_frames()[0].head(10)
        if df.empty:
            return None  # No games found
        avg_scored = df["PTS"].mean()
        return avg_scored
    except Exception as e:
        print(f"Error fetching stats for team {team_id}: {e}")
        return None


@app.route("/")
def index():
    games = get_upcoming_games()
    return render_template("index.html", games=games)


@app.route("/predict", methods=["POST"])
def predict():
    selected_indices = request.form.getlist("game_index")
    games = get_upcoming_games()
    predictions = []

    for index in selected_indices:
        try:
            index = int(index)
            game = games[index]
            home_id = game["home_team_id"]
            away_id = game["away_team_id"]

            # Get stats for BOTH teams
            home_avg = get_team_stats(home_id)
            away_avg = get_team_stats(away_id)

            if home_avg is None or away_avg is None:
                predictions.append(
                    {
                        "matchup": f"{game['home_team']} vs {game['away_team']}",
                        "total": "Data unavailable",
                    }
                )
                continue

            # Correct formula: Total = Home Avg + Away Avg
            predicted_total = round(home_avg + away_avg)

            predictions.append(
                {
                    "matchup": f"{game['home_team']} vs {game['away_team']}",
                    "total": predicted_total,
                }
            )
        except Exception as e:
            print(f"Error processing game {index}: {e}")
            continue

    return render_template("results.html", predictions=predictions)


if __name__ == "__main__":
    app.run(debug=True)
