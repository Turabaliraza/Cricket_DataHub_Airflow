from flask import Flask, jsonify
from flask_cors import CORS 

from backend.db import get_db_connection 
from backend.routes.matches import matches_bp
from backend.routes.teams import teams_bp
from backend.routes.players import players_bp

app= Flask(__name__)
CORS(app)

app.register_blueprint(matches_bp, url_prefix="/api/matches")
app.register_blueprint(teams_bp, url_prefix="/api/teams")
app.register_blueprint(players_bp, url_prefix="/api/players")

@app.route("/",methods=["GET"])
def home():
    return jsonify({
        "message":"Welcome to Cricket DataHub API",
        "status":"running"
    })

@app.route("/api/health", methods=["GET"])
def health_check():

    try:
        conn = get_db_connection()
        conn.close()

        return jsonify({
            "status":"healthy",
            "database":"connected"
        }),200

    except Exception as error:
        app.logger.error("Database health check failed: %s",error)

        return jsonify({
            "status":"unhealthy",
            "database":"disconnected"
        }),500

if __name__=="__main__":
    app.run(debug=True, port=5000)