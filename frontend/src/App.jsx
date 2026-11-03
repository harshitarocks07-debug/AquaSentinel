
import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import {
  Activity,
  AlertTriangle,
  Bell,
  CloudRain,
  Droplets,
  Gauge,
  LayoutDashboard,
  Map,
  RefreshCw,
  Search,
  ShieldCheck,
  Waves,
  Wind,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import "./App.css";

const API_URL = "http://127.0.0.1:8000/api/risk/latest";

function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("All");

  const fetchData = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await axios.get(API_URL);
      setData(response.data);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to connect to AquaSentinel API. Check whether the backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const districts = data?.districts || [];

  const summary = useMemo(() => {
    const alerts = districts.reduce((acc, item) => {
      const level = item.overall_alert || "Insufficient Data";
      acc[level] = (acc[level] || 0) + 1;
      return acc;
    }, {});

    const floodHigh = districts.filter((item) =>
      ["High", "Very High"].includes(item.flood?.status)
    ).length;

    const droughtAffected = districts.filter((item) =>
      ["Moderate Drought", "Severe Drought", "Extreme Drought"].includes(
        item.drought?.status
      )
    ).length;

    return {
      critical: alerts.Critical || 0,
      high: alerts.High || 0,
      floodHigh,
      droughtAffected,
    };
  }, [districts]);

  const filteredDistricts = useMemo(() => {
    return districts.filter((item) => {
      const matchesSearch = item.district
        ?.toLowerCase()
        .includes(search.toLowerCase());

      const matchesFilter =
        filter === "All" || item.overall_alert === filter;

      return matchesSearch && matchesFilter;
    });
  }, [districts, search, filter]);

  const chartData = districts
    .filter((item) => item.flood?.risk_score != null)
    .sort((a, b) => b.flood.risk_score - a.flood.risk_score)
    .slice(0, 8)
    .map((item) => ({
      district: item.district,
      flood: item.flood.risk_score,
    }));

  const alertData = [
    { name: "Critical", value: summary.critical, color: "#ef4444" },
    { name: "High", value: summary.high, color: "#f97316" },
    {
      name: "Moderate",
      value: districts.filter((d) => d.overall_alert === "Moderate").length,
      color: "#eab308",
    },
    {
      name: "Low",
      value: districts.filter((d) => d.overall_alert === "Low").length,
      color: "#3b82f6",
    },
    {
      name: "Normal",
      value: districts.filter((d) => d.overall_alert === "Normal").length,
      color: "#22c55e",
    },
  ].filter((item) => item.value > 0);

  const getAlertClass = (level) => {
    const classes = {
      Critical: "critical",
      High: "high",
      Moderate: "moderate",
      Low: "low",
      Normal: "normal",
      "Insufficient Data": "unknown",
    };
    return classes[level] || "unknown";
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">
            <Droplets size={23} />
          </div>
          <div>
            <h2>AquaSentinel</h2>
            <span>ENVIRONMENTAL INTELLIGENCE</span>
          </div>
        </div>

        <div className="nav-label">WORKSPACE</div>
        <nav className="navigation">
          <a className="nav-item active" href="#overview">
            <LayoutDashboard size={18} />
            Overview
          </a>
          <a className="nav-item" href="#districts">
            <Map size={18} />
            District Monitoring
          </a>
          <a className="nav-item" href="#flood">
            <Waves size={18} />
            Flood Analysis
          </a>
          <a className="nav-item" href="#drought">
            <Wind size={18} />
            Drought Analysis
          </a>
          <a className="nav-item" href="#alerts">
            <Bell size={18} />
            Risk Alerts
          </a>
        </nav>

        <div className="sidebar-bottom">
          <div className="system-status">
            <span className="status-dot" />
            <div>
              <strong>System Online</strong>
              <span>Monitoring Gujarat</span>
            </div>
          </div>
          <div className="sidebar-footer">AquaSentinel · 2026</div>
        </div>
      </aside>

      <main className="main-content" id="overview">
        <header className="topbar">
          <div>
            <div className="breadcrumb">Workspace / Overview</div>
            <h1>Environmental Overview</h1>
            <p>Flood and drought intelligence for Gujarat, India</p>
          </div>

          <button className="refresh-button" onClick={fetchData}>
            <RefreshCw size={16} />
            Refresh Data
          </button>
        </header>

        {error && (
          <div className="error-banner">
            <AlertTriangle size={18} />
            <span>{error}</span>
            <button onClick={fetchData}>Retry</button>
          </div>
        )}

        {loading ? (
          <div className="loading-panel">
            <RefreshCw className="spin" size={25} />
            <p>Loading district intelligence...</p>
          </div>
        ) : (
          <>
            <section className="date-strip">
              <div>
                <Activity size={17} />
                <span>Latest available observations</span>
              </div>
              <div className="date-values">
                <span>Drought: <strong>{data?.drought_data_date || "N/A"}</strong></span>
                <span>Flood: <strong>{data?.flood_data_date || "N/A"}</strong></span>
              </div>
            </section>

            <section className="stats-grid">
              <StatCard
                icon={<Map size={20} />}
                label="Districts Monitored"
                value={data?.total_districts ?? 0}
                detail="Across Gujarat"
                color="blue"
              />
              <StatCard
                icon={<AlertTriangle size={20} />}
                label="Critical Alerts"
                value={summary.critical}
                detail="Highest alert priority"
                color="red"
              />
              <StatCard
                icon={<CloudRain size={20} />}
                label="High Flood Risk"
                value={summary.floodHigh}
                detail="High and very high"
                color="orange"
              />
              <StatCard
                icon={<Gauge size={20} />}
                label="Drought Affected"
                value={summary.droughtAffected}
                detail="Moderate to extreme"
                color="purple"
              />
            </section>

            <section className="section-heading">
              <div>
                <h2>Risk Intelligence</h2>
                <p>District-level environmental risk indicators</p>
              </div>
              <span className="live-label">
                <span className="status-dot" /> API CONNECTED
              </span>
            </section>

            <section className="charts-grid">
              <div className="panel chart-panel" id="flood">
                <div className="panel-heading">
                  <div>
                    <h3>Flood Risk by District</h3>
                    <p>Top 8 districts by current flood score</p>
                  </div>
                  <span className="panel-icon blue-icon">
                    <Waves size={19} />
                  </span>
                </div>

                {chartData.length ? (
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={chartData} margin={{ top: 15, right: 8, left: -15, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#293343" />
                      <XAxis dataKey="district" tick={{ fill: "#94a3b8", fontSize: 11 }} axisLine={false} tickLine={false} />
                      <YAxis domain={[0, 100]} tick={{ fill: "#94a3b8", fontSize: 11 }} axisLine={false} tickLine={false} />
                      <Tooltip
                        contentStyle={{ background: "#151e2c", border: "1px solid #334155", borderRadius: 8 }}
                        labelStyle={{ color: "#fff" }}
                      />
                      <Bar dataKey="flood" name="Flood score" fill="#38bdf8" radius={[5, 5, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <EmptyChart />
                )}
              </div>

              <div className="panel chart-panel">
                <div className="panel-heading">
                  <div>
                    <h3>Overall Alert Distribution</h3>
                    <p>Districts grouped by alert priority</p>
                  </div>
                  <span className="panel-icon purple-icon">
                    <ShieldCheck size={19} />
                  </span>
                </div>

                {alertData.length ? (
                  <>
                    <ResponsiveContainer width="100%" height={220}>
                      <PieChart>
                        <Pie
                          data={alertData}
                          dataKey="value"
                          nameKey="name"
                          innerRadius={58}
                          outerRadius={85}
                          paddingAngle={3}
                        >
                          {alertData.map((entry) => (
                            <Cell key={entry.name} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{ background: "#151e2c", border: "1px solid #334155", borderRadius: 8 }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="chart-legend">
                      {alertData.map((item) => (
                        <span key={item.name}>
                          <i style={{ background: item.color }} />
                          {item.name}: {item.value}
                        </span>
                      ))}
                    </div>
                  </>
                ) : (
                  <EmptyChart />
                )}
              </div>
            </section>

            <section className="section-heading table-title" id="districts">
              <div>
                <h2>District Risk Monitoring</h2>
                <p>Current drought, flood and combined alert status</p>
              </div>
              <span className="record-count">{filteredDistricts.length} districts</span>
            </section>

            <section className="panel table-panel" id="alerts">
              <div className="table-controls">
                <div className="search-box">
                  <Search size={17} />
                  <input
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search district..."
                  />
                </div>
                <select value={filter} onChange={(e) => setFilter(e.target.value)}>
                  <option>All</option>
                  <option>Critical</option>
                  <option>High</option>
                  <option>Moderate</option>
                  <option>Low</option>
                  <option>Normal</option>
                </select>
              </div>

              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>District</th>
                      <th>SPI-3</th>
                      <th>Drought Status</th>
                      <th>Flood Score</th>
                      <th>Flood Status</th>
                      <th>Overall Alert</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredDistricts.map((item) => (
                      <tr key={item.district}>
                        <td className="district-name">{item.district}</td>
                        <td>{Number.isFinite(Number(item.drought?.spi_3))
                          ? Number(item.drought.spi_3).toFixed(2)
                          : "—"}</td>
                        <td>
                          <span className={`status-pill ${getAlertClass(item.drought?.status)}`}>
                            {item.drought?.status || "Insufficient Data"}
                          </span>
                        </td>
                        <td>{item.flood?.risk_score ?? "—"}</td>
                        <td>
                          <span className={`status-pill ${getAlertClass(item.flood?.status)}`}>
                            {item.flood?.status || "Insufficient Data"}
                          </span>
                        </td>
                        <td>
                          <span className={`status-pill ${getAlertClass(item.overall_alert)}`}>
                            {item.overall_alert || "Insufficient Data"}
                          </span>
                        </td>
                      </tr>
                    ))}
                    {!filteredDistricts.length && (
                      <tr>
                        <td colSpan="6" className="no-results">No matching districts found.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>

            <footer className="page-footer">
              <span>AquaSentinel · Flood & Drought Early Warning System</span>
              <span>Data-driven environmental monitoring · Gujarat, India</span>
            </footer>
          </>
        )}
      </main>
    </div>
  );
}

function StatCard({ icon, label, value, detail, color }) {
  return (
    <div className="stat-card">
      <div className={`stat-icon ${color}`}>{icon}</div>
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      <div className="stat-detail">{detail}</div>
    </div>
  );
}

function EmptyChart() {
  return <div className="empty-chart">No chart data available.</div>;
}

export default App;
