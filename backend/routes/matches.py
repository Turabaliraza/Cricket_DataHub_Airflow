from flask import Blueprint, jsonify

from backend.db import get_db_connection

matches_bp = Blueprint("matches", __name__)

@matches_bp.route("/",methods=["GET"])
def get_matches():
    conn=None 

    try:
        conn=get_db_connection()

        with conn.cursor() as cursor:
            cursor.execute("""
               SELECT 
                  m.match_id,
                  m.tournament_id,
                  m.match_date,
                  m.venue,
                  m.status,
                  m.winner_id,
                  m.external_match_id,
                  t.name AS tournament_name
                FROM matches m
                LEFT JOIN tournaments t
                   ON m.tournament_id = t.tournament_id
                   ORDER BY m.match_date DESC, m.match_id DESC;

         """)
            rows = cursor.fetchall()
        matches=[]

        for row in rows:
            matches.append({
                "match_id":row[0],
                "tournament_id":row[1],
                "match_date":row[2].isoformat() if row[2] else None,
                "venue":row[3],
                "status":row[4],
                "winner_id":row[5],
                "external_match_id":row[6],
                "tournament_name":row[7]
            })

        return jsonify(matches),200

    except Exception:
        matches_bp.logger.exception("Failed to retrieve matches")
        return jsonify({
            "error:Failed to retrieve matches"
        }),500
    finally:
        if conn is not None:
            conn.close()


@matches_bp.route("/<int:match_id>", methods=["GET"])
def get_match_details(match_id):
    conn = None

    try:
        conn = get_db_connection()

        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    m.match_id,
                    m.tournament_id,
                    m.match_date,
                    m.venue,
                    m.status,
                    m.winner_id,
                    m.external_match_id,
                    t.team_id,
                    t.name AS team_name,
                    t.country AS team_country
                FROM matches m
                LEFT JOIN match_teams mt
                    ON m.match_id = mt.match_id
                LEFT JOIN teams t
                    ON mt.team_id = t.team_id
                WHERE m.match_id = %s
                ORDER BY t.name;
            """, (match_id,))

            rows = cursor.fetchall()

        if not rows:
            return jsonify({
                "error": "Match not found"
            }), 404

        match = {
            "match_id": rows[0][0],
            "tournament_id": rows[0][1],
            "match_date": (
                rows[0][2].isoformat()
                if rows[0][2] else None
            ),
            "venue": rows[0][3],
            "status": rows[0][4],
            "winner_id": rows[0][5],
            "external_match_id": rows[0][6],
            "teams": []
        }

        for row in rows:
            if row[7] is not None:
                match["teams"].append({
                    "team_id": row[7],
                    "name": row[8],
                    "country": row[9]
                })

        return jsonify(match), 200

    except Exception:
        matches_bp.logger.exception(
            "Failed to retrieve match details"
        )
        return jsonify({
            "error": "Failed to retrieve match details"
        }), 500

    finally:
        if conn is not None:
            conn.close()

@matches_bp.route("/<int:match_id>/scorecard", methods=["GET"])
def get_match_scorecard(match_id):
    conn = None

    try:
        conn = get_db_connection()

        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT match_id FROM matches WHERE match_id = %s;",
                (match_id,)
            )

            if cursor.fetchone() is None:
                return jsonify({"error": "Match not found"}), 404

            cursor.execute("""
                SELECT
                    i.innings_id,
                    i.innings_number,
                    i.runs AS innings_runs,
                    i.wickets,
                    i.overs,
                    t.team_id,
                    t.name AS team_name,
                    p.player_id,
                    p.name AS player_name,
                    pp.runs AS player_runs,
                    pp.balls_faced,
                    pp.fours,
                    pp.sixes,
                    pp.dismissal
                FROM innings i
                JOIN teams t
                    ON i.team_id = t.team_id
                LEFT JOIN player_performance pp
                    ON i.innings_id = pp.innings_id
                LEFT JOIN players p
                    ON pp.player_id = p.player_id
                WHERE i.match_id = %s
                ORDER BY i.innings_number, i.innings_id, p.name;
            """, (match_id,))

            rows = cursor.fetchall()

        innings_map = {}

        for row in rows:
            innings_id = row[0]

            if innings_id not in innings_map:
                innings_map[innings_id] = {
                    "innings_id": row[0],
                    "innings_number": row[1],
                    "runs": row[2],
                    "wickets": row[3],
                    "overs": row[4],
                    "team": {
                        "team_id": row[5],
                        "name": row[6]
                    },
                    "batting": []
                }

            if row[7] is not None:
                innings_map[innings_id]["batting"].append({
                    "player_id": row[7],
                    "player_name": row[8],
                    "runs": row[9],
                    "balls_faced": row[10],
                    "fours": row[11],
                    "sixes": row[12],
                    "dismissal": row[13]
                })

        return jsonify({
            "match_id": match_id,
            "innings_count": len(innings_map),
            "innings": list(innings_map.values())
        }), 200

    except Exception:
        matches_bp.logger.exception(
            "Failed to retrieve match scorecard"
        )
        return jsonify({
            "error": "Failed to retrieve match scorecard"
        }), 500

    finally:
        if conn is not None:
            conn.close()
