
import { useEffect, useState } from "react";
import "./App.css";

const API_BASE = "http://127.0.0.1:5000/api";

function App() {
  const [activePage, setActivePage] = useState("Overview");
  const [matches, setMatches] = useState([]);
  const [teams, setTeams] = useState([]);
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchDashboardData() {
      try {
        setLoading(true);
        setError("");

        const [matchesResponse, teamsResponse, playersResponse] =
          await Promise.all([
            fetch(`${API_BASE}/matches/`),
            fetch(`${API_BASE}/teams/`),
            fetch(`${API_BASE}/players/`),
          ]);

        if (
          !matchesResponse.ok ||
          !teamsResponse.ok ||
          !playersResponse.ok
        ) {
          throw new Error("One or more API requests failed.");
        }

        const matchesData = await matchesResponse.json();
        const teamsData = await teamsResponse.json();
        const playersData = await playersResponse.json();

        setMatches(Array.isArray(matchesData) ? matchesData : []);
        setTeams(teamsData.teams ?? []);
        setPlayers(playersData.players ?? []);
      } catch (err) {
        setError(
          "Unable to load cricket data. Make sure Flask is running on port 5000."
        );
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    fetchDashboardData();
  }, []);

  const navigation = [
    { name: "Overview", icon: "◫" },
    { name: "Matches", icon: "🏏" },
    { name: "Teams", icon: "◉" },
    { name: "Players", icon: "♙" },
  ];

  const recentMatches = [...matches]
    .sort((a, b) => (b.match_date || "").localeCompare(a.match_date || ""))
    .slice(0, 5);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">C</div>
          <div>
            <h1>Cricket<span>DataHub</span></h1>
            <p>DATA & ANALYTICS</p>
          </div>
        </div>

        <p className="nav-label">WORKSPACE</p>

        <nav className="navigation">
          {navigation.map((item) => (
            <button
              key={item.name}
              className={`nav-item ${
                activePage === item.name ? "active" : ""
              }`}
              onClick={() => setActivePage(item.name)}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.name}
              {item.name === "Matches" && (
                <span className="nav-count">{matches.length}</span>
              )}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="status-dot" />
          <div>
            <strong>Pipeline status</strong>
            <span>API connected</span>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <p className="eyebrow">CRICKET DATA PLATFORM</p>
            <h2>{activePage}</h2>
          </div>
          <div className="topbar-right">
            <span className="live-indicator">
              <span /> LIVE API
            </span>
            <div className="avatar">CD</div>
          </div>
        </header>

        <section className="page-content">
          {loading ? (
            <div className="message-card">Loading cricket data...</div>
          ) : error ? (
            <div className="message-card error-message">{error}</div>
          ) : (
            <>
              {activePage === "Overview" && (
                <>
                  <div className="welcome-section">
                    <div>
                      <p className="eyebrow">YOUR CRICKET WORKSPACE</p>
                      <h3>Every match tells a story.</h3>
                      <p>
                        Explore match data, teams, and player statistics
                        in one place.
                      </p>
                    </div>
                    <div className="welcome-icon">🏏</div>
                  </div>

                  <div className="stats-grid">
                    <StatCard
                      label="Total Matches"
                      value={matches.length}
                      icon="🏏"
                      note="Stored in database"
                    />
                    <StatCard
                      label="Teams"
                      value={teams.length}
                      icon="🛡"
                      note="Across competitions"
                    />
                    <StatCard
                      label="Players"
                      value={players.length}
                      icon="♙"
                      note="Available in database"
                    />
                    <StatCard
                      label="API Status"
                      value="Online"
                      icon="↗"
                      note="PostgreSQL connected"
                    />
                  </div>

                  <MatchTable
                    matches={recentMatches}
                    title="Recent matches"
                    onSelect={() => setActivePage("Matches")}
                  />
                </>
              )}

              {activePage === "Matches" && (
                <MatchTable matches={matches} title="All matches" />
              )}

              {activePage === "Teams" && (
                <section className="data-section">
                  <SectionHeading
                    title="Teams directory"
                    subtitle={`${teams.length} teams available`}
                  />
                  <div className="entity-grid">
                    {teams.map((team) => (
                      <article className="entity-card" key={team.team_id}>
                        <div className="entity-icon">🛡</div>
                        <div>
                          <h4>{team.name}</h4>
                          <p>{team.country || "Country unavailable"}</p>
                        </div>
                        <span className="entity-id">
                          #{team.team_id}
                        </span>
                      </article>
                    ))}
                  </div>
                </section>
              )}

              {activePage === "Players" && (
                <section className="data-section">
                  <SectionHeading
                    title="Players directory"
                    subtitle={`${players.length} players available`}
                  />
                  <div className="players-list">
                    {players.map((player) => (
                      <article className="player-row" key={player.player_id}>
                        <div className="player-avatar">
                          {player.name
                            .split(" ")
                            .map((part) => part[0])
                            .join("")
                            .slice(0, 2)
                            .toUpperCase()}
                        </div>
                        <div className="player-details">
                          <strong>{player.name}</strong>
                          <span>Player ID: {player.player_id}</span>
                        </div>
                        <span className="entity-id">
                          {player.external_player_id
                            ? "External ID linked"
                            : "Local record"}
                        </span>
                      </article>
                    ))}
                  </div>
                </section>
              )}
            </>
          )}
        </section>

        <footer className="app-footer">
          <span>Cricket DataHub</span>
          <span>Powered by Flask · PostgreSQL · Airflow</span>
        </footer>
      </main>
    </div>
  );
}

function StatCard({ label, value, icon, note }) {
  return (
    <article className="stat-card">
      <div className="stat-card-top">
        <span>{label}</span>
        <span className="stat-icon">{icon}</span>
      </div>
      <strong className="stat-value">{value}</strong>
      <span className="stat-note">{note}</span>
    </article>
  );
}

function SectionHeading({ title, subtitle }) {
  return (
    <div className="section-heading">
      <div>
        <h3>{title}</h3>
        <p>{subtitle}</p>
      </div>
    </div>
  );
}

function MatchTable({ matches, title, onSelect }) {
  return (
    <section className="data-section">
      <SectionHeading
        title={title}
        subtitle={`${matches.length} ${
          matches.length === 1 ? "match" : "matches"
        }`}
      />

      {matches.length === 0 ? (
        <div className="empty-state">No matches found.</div>
      ) : (
        <div className="table-wrapper">
          <table className="match-table">
            <thead>
              <tr>
                <th>Match</th>
                <th>Tournament</th>
                <th>Date</th>
                <th>Venue</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {matches.map((match) => (
                <tr key={match.match_id} onClick={onSelect}>
                  <td>
                    <strong>Match #{match.match_id}</strong>
                    <span className="table-subtext">
                      {match.external_match_id
                        ? `ESPN ID: ${match.external_match_id}`
                        : "Local match"}
                    </span>
                  </td>
                  <td>{match.tournament_name || "Unknown tournament"}</td>
                  <td>{match.match_date || "—"}</td>
                  <td>{match.venue || "Not available"}</td>
                  <td>
                    <span className="status-badge">
                      {match.status || "Unknown"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export default App;
