from flask import Blueprint, jsonify

from backend.db import get_db_connection

matches_bp = Blueprint("matches", __name__)

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
