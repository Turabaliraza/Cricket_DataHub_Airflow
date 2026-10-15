
import { useEffect, useState } from "react";
import "./App.css";

const API_BASE = "http://127.0.0.1:5000/api";

const navigation = [
  { name: "Overview", icon: "⌂" },
  { name: "Matches", icon: "🏏" },
  { name: "Teams", icon: "♧" },
  { name: "Players", icon: "♙" },
];

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

        const responses = await Promise.all([
          fetch(`${API_BASE}/matches/`),
          fetch(`${API_BASE}/teams/`),
          fetch(`${API_BASE}/players/`),
          fetch(`${API_BASE.replace("/api", "")}/api/health`),
        ]);

        if (responses.some((response) => !response.ok)) {
          throw new Error("A dashboard API request failed.");
        }

        const [matchesData, teamsData, playersData] = await Promise.all(
          responses.slice(0, 3).map((response) => response.json())
        );

        setMatches(Array.isArray(matchesData) ? matchesData : []);
        setTeams(teamsData.teams ?? []);
        setPlayers(playersData.players ?? []);
      } catch (err) {
        console.error(err);
        setError(
          "Unable to load data. Please confirm the Flask API is running on port 5000."
        );
      } finally {
        setLoading(false);
      }
    }

    fetchDashboardData();
  }, []);

  const recentMatches = [...matches]
    .sort((a, b) =>
      (b.match_date || "").localeCompare(a.match_date || "")
    )
    .slice(0, 5);

  return (
    <div className="dashboard-shell">
      <aside className="sidebar">
        <a className="brand" href="#" onClick={(event) => {
          event.preventDefault();
          setActivePage("Overview");
        }}>
          <div className="brand-logo">C<span>.</span></div>
          <div className="brand-copy">
            <strong>Cricket<span>DataHub</span></strong>
            <small>INTELLIGENCE PLATFORM</small>
          </div>
        </a>

        <div className="sidebar-section-label">WORKSPACE</div>

        <nav className="sidebar-nav">
          {navigation.map((item) => (
            <button
              key={item.name}
              className={`sidebar-link ${
                activePage === item.name ? "active" : ""
              }`}
              onClick={() => setActivePage(item.name)}
            >
              <span className="sidebar-link-icon">{item.icon}</span>
              <span>{item.name}</span>
              {item.name === "Matches" && (
                <span className="nav-badge">{matches.length}</span>
              )}
            </button>
          ))}
        </nav>

        <div className="sidebar-section-label pipeline-label">
          DATA ENGINEERING
        </div>

        <div className="pipeline-card">
          <div className="pipeline-card-icon">↗</div>
          <div className="pipeline-card-copy">
            <strong>ETL Pipeline</strong>
            <span>Apache Airflow</span>
          </div>
          <span className="pipeline-status-dot" />
          <p>Orchestrated data ingestion and loading</p>
        </div>

        <div className="sidebar-bottom">
          <div className="profile-avatar">CD</div>
          <div className="profile-copy">
            <strong>Cricket DataHub</strong>
            <span>Analytics workspace</span>
          </div>
          <span className="profile-menu">•••</span>
        </div>
      </aside>

      <main className="dashboard-main">
        <header className="dashboard-header">
          <div className="header-title">
            <div className="breadcrumb">
              Workspace <span>/</span> <strong>{activePage}</strong>
            </div>
            <h1>{activePage}</h1>
            <p>Your cricket data, organized in one place.</p>
          </div>

          <div className="header-actions">
            <div className="connection-pill">
              <span className="connection-dot" />
              API connected
            </div>
            <div className="header-date">
              <span className="date-icon">▦</span>
              Live data
            </div>
          </div>
        </header>

        <div className="dashboard-content">
          {loading ? (
            <div className="feedback-panel">Loading your cricket data...</div>
          ) : error ? (
            <div className="feedback-panel error-panel">{error}</div>
          ) : (
            <>
              {activePage === "Overview" && (
                <>
                  <section className="hero-panel">
                    <div className="hero-copy">
                      <span className="hero-tag">
                        <span className="hero-tag-dot" />
                        YOUR CRICKET WORKSPACE
                      </span>
                      <h2>Numbers tell the story.<br />Cricket tells the rest.</h2>
                      <p>
                        Explore match records, discover teams, and bring
                        cricket data together through one analytics platform.
                      </p>
                      <button
                        className="primary-button"
                        onClick={() => setActivePage("Matches")}
                      >
                        Explore matches <span>↗</span>
                      </button>
                    </div>
                    <div className="hero-visual" aria-hidden="true">
                      <div className="hero-circle circle-one" />
                      <div className="hero-circle circle-two" />
                      <div className="hero-ball">🏏</div>
                      <div className="hero-float-card">
                        <span>DATA COLLECTION</span>
                        <strong>Match by match.</strong>
                        <small>Structured. Organized. Ready.</small>
                      </div>
                    </div>
                  </section>

                  <section className="section-block">
                    <div className="section-title-row">
                      <div>
                        <span className="section-kicker">AT A GLANCE</span>
                        <h2>Your cricket overview</h2>
                      </div>
                      <span className="section-caption">Database snapshot</span>
                    </div>

                    <div className="metrics-grid">
                      <MetricCard
                        icon="🏏"
                        label="Total matches"
                        value={matches.length}
                        note="Match records"
                        accent="green"
                      />
                      <MetricCard
                        icon="🛡"
                        label="Teams"
                        value={teams.length}
                        note="Teams in database"
                        accent="yellow"
                      />
                      <MetricCard
                        icon="♙"
                        label="Players"
                        value={players.length}
                        note="Player records"
                        accent="blue"
                      />
                      <MetricCard
                        icon="↗"
                        label="Data platform"
                        value="Online"
                        note="API responding"
                        accent="purple"
                      />
                    </div>
                  </section>

                  <section className="section-block recent-section">
                    <div className="section-title-row">
                      <div>
                        <span className="section-kicker">MATCH CENTRE</span>
                        <h2>Recent matches</h2>
                        <p className="section-description">
                          The latest match records available in your database.
                        </p>
                      </div>
                      <button
                        className="text-button"
                        onClick={() => setActivePage("Matches")}
                      >
                        View all matches <span>→</span>
                      </button>
                    </div>
                    <MatchTable matches={recentMatches} />
                  </section>
                </>
              )}

              {activePage === "Matches" && (
                <section className="content-panel">
                  <div className="section-title-row">
                    <div>
                      <span className="section-kicker">MATCH CENTRE</span>
                      <h2>All matches</h2>
                      <p className="section-description">
                        Browse the match records stored in PostgreSQL.
                      </p>
                    </div>
                    <span className="count-chip">{matches.length} records</span>
                  </div>
                  <MatchTable matches={matches} />
                </section>
              )}

              {activePage === "Teams" && (
                <section className="content-panel">
                  <div className="section-title-row">
                    <div>
                      <span className="section-kicker">TEAM DIRECTORY</span>
                      <h2>Explore teams</h2>
                      <p className="section-description">
                        Teams represented in your cricket database.
                      </p>
                    </div>
                    <span className="count-chip">{teams.length} teams</span>
                  </div>
                  <div className="team-grid">
                    {teams.map((team) => (
                      <article className="team-card" key={team.team_id}>
                        <div className="team-emblem">♧</div>
                        <div className="team-card-body">
                          <h3>{team.name}</h3>
                          <p>{team.country || "Country not available"}</p>
                        </div>
                        <span className="team-id">#{team.team_id}</span>
                      </article>
                    ))}
                  </div>
                </section>
              )}

              {activePage === "Players" && (
                <section className="content-panel">
                  <div className="section-title-row">
                    <div>
                      <span className="section-kicker">PLAYER DIRECTORY</span>
                      <h2>Explore players</h2>
                      <p className="section-description">
                        Player records available in your database.
                      </p>
                    </div>
                    <span className="count-chip">{players.length} players</span>
                  </div>
                  <div className="player-grid">
                    {players.map((player) => (
                      <article className="player-card" key={player.player_id}>
                        <div className="player-avatar">
                          {player.name
                            .split(" ")
                            .map((part) => part[0])
                            .join("")
                            .slice(0, 2)
                            .toUpperCase()}
                        </div>
                        <div className="player-card-body">
                          <h3>{player.name}</h3>
                          <p>Player ID: {player.player_id}</p>
                        </div>
                        <span
                          className={`record-tag ${
                            player.external_player_id ? "linked" : ""
                          }`}
                        >
                          {player.external_player_id ? "Linked" : "Local"}
                        </span>
                      </article>
                    ))}
                  </div>
                </section>
              )}
            </>
          )}
        </div>

        <footer className="dashboard-footer">
          <span>© Cricket DataHub</span>
          <div className="footer-tech">
            <span>React</span>
            <span>Flask API</span>
            <span>PostgreSQL</span>
            <span>Apache Airflow</span>
          </div>
        </footer>
      </main>
    </div>
  );
}

function MetricCard({ icon, label, value, note, accent }) {
  return (
    <article className="metric-card">
      <div className="metric-card-top">
        <span className={`metric-icon ${accent}`}>{icon}</span>
        <span className="metric-more">↗</span>
      </div>
      <p className="metric-label">{label}</p>
      <strong className="metric-value">{value}</strong>
      <div className="metric-bottom">
        <span className="metric-indicator" />
        <span>{note}</span>
      </div>
    </article>
  );
}

function MatchTable({ matches }) {
  if (matches.length === 0) {
    return <div className="empty-state">No matches found.</div>;
  }

  return (
    <div className="table-container">
      <table className="match-table">
        <thead>
          <tr>
            <th>Match ID</th>
            <th>Tournament</th>
            <th>Match date</th>
            <th>Venue</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {matches.map((match) => (
            <tr key={match.match_id}>
              <td>
                <span className="match-id-cell">
                  <span className="match-mini-icon">🏏</span>
                  <span>
                    <strong>Match #{match.match_id}</strong>
                    <small>
                      {match.external_match_id
                        ? `ESPN · ${match.external_match_id}`
                        : "Local record"}
                    </small>
                  </span>
                </span>
              </td>
              <td>
                <span className="tournament-name">
                  {match.tournament_name || "Unknown tournament"}
                </span>
              </td>
              <td>{formatDate(match.match_date)}</td>
              <td>{match.venue || "Not available"}</td>
              <td>
                <span className="match-status">
                  <span />
                  {match.status || "Unknown"}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatDate(date) {
  if (!date) return "—";

  const parsed = new Date(`${date}`.slice(0, 10) + "T00:00:00");

  if (Number.isNaN(parsed.getTime())) return date;

  return parsed.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export default App;
