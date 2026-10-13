from flask import Blueprint, jsonify

from backend.db import get_db_connection

teams_bp = Blueprint("teams", __name__)


@teams_bp.route("/", methods=["GET"])
def get_teams():
    conn = None

    try:
        conn = get_db_connection()

        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    team_id,
                    name,
                    country,
                    external_team_id
                FROM teams
                ORDER BY name ASC;
            """)

            columns = [description[0] for description in cursor.description]
            teams = [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]

        return jsonify({
            "count": len(teams),
            "teams": teams
        }), 200

    except Exception:
        teams_bp.logger.exception("Failed to retrieve teams")

        return jsonify({
            "error": "Failed to retrieve teams"
        }), 500

    finally:
        if conn is not None:
            conn.close()
