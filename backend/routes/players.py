from flask import Blueprint, jsonify

from backend.db import get_db_connection

players_bp = Blueprint("players", __name__)


@players_bp.route("/", methods=["GET"])
def get_players():
    conn = None

    try:
        conn = get_db_connection()

        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    player_id,
                    name,
                    external_player_id
                FROM players
                ORDER BY name ASC;
            """)

            columns = [
                description[0]
                for description in cursor.description
            ]

            rows = cursor.fetchall()

            players = [
                dict(zip(columns, row))
                for row in rows
            ]

        return jsonify({
            "count": len(players),
            "players": players
        }), 200

    except Exception:
        players_bp.logger.exception(
            "Failed to retrieve players"
        )

        return jsonify({
            "error": "Failed to retrieve players"
        }), 500

    finally:
        if conn is not None:
            conn.close()
