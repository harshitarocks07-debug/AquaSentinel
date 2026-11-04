
import { useEffect, useMemo, useState } from "react";

import {
  LayoutDashboard,
  Map,
  Waves,
  Wind,
  Bell,
  Droplets,
  RefreshCw,
  AlertTriangle,
  Activity,
  ShieldCheck,
  Gauge,
  Search,
  Menu,
  X,
  BrainCircuit,
  CloudRain,
} from "lucide-react";

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";

import "./App.css";

const API_URL = "http://127.0.0.1:8000/api/risk/latest";

// --------------------------------------------------
// NAVIGATION
// --------------------------------------------------

const NAV_ITEMS = [
  { label: "Overview", icon: LayoutDashboard, id: "overview" },
  { label: "District Monitoring", icon: Map, id: "districts" },
  { label: "Flood Analysis", icon: Waves, id: "flood" },
  { label: "AI Early Warnings", icon: BrainCircuit, id: "ml-warning" },
  { label: "Drought Analysis", icon: Wind, id: "drought" },
  { label: "Risk Alerts", icon: Bell, id: "alerts" },
];

// --------------------------------------------------
// ALERT COLORS
// --------------------------------------------------

const ALERT_COLORS = {
  Critical: "#ef4444",
  High: "#f97316",
  Moderate: "#eab308",
  Low: "#3b82f6",
  Normal: "#22c55e",
  "Insufficient Data": "#64748b",
};

// --------------------------------------------------
// STATUS COMPONENTS
// --------------------------------------------------

function getStatusClass(status) {
  const value = (status || "Insufficient Data").toLowerCase();

  const classes = {
    "extreme drought": "extreme-drought",
    "severe drought": "severe-drought",
    "moderate drought": "moderate-drought",
    "very high": "very-high",
    high: "high",
    moderate: "moderate",
    low: "low",
    normal: "normal",
    critical: "critical",
    "insufficient data": "insufficient-data",
  };

  return classes[value] || "insufficient-data";
}

function StatusPill({ status }) {
  const value = status || "Insufficient Data";

  return (
    <span className={`status-pill ${getStatusClass(value)}`}>
      {value}
    </span>
  );
}

// --------------------------------------------------
// STAT CARD
// --------------------------------------------------

function StatCard({ icon: Icon, label, value, subtitle, color }) {
  return (
    <div className="stat-card">
      <div className={`stat-icon ${color}`}>
        <Icon size={21} />
      </div>

      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      <div className="stat-subtitle">{subtitle}</div>
    </div>
  );
}

// --------------------------------------------------
// MAIN APP
// --------------------------------------------------

function App() {
  const [data, setData] = useState([]);

  const [droughtDate, setDroughtDate] = useState("N/A");
  const [floodDate, setFloodDate] = useState("N/A");

  const [modelStatus, setModelStatus] = useState({
    available: false,
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("All");

  const [activePage, setActivePage] = useState("overview");
  const [mobileMenu, setMobileMenu] = useState(false);

  // --------------------------------------------------
  // FETCH UNIFIED BACKEND DATA
  // --------------------------------------------------

  const fetchData = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(API_URL);

      if (!response.ok) {
        throw new Error(`API returned HTTP ${response.status}`);
      }

      const result = await response.json();

      if (!Array.isArray(result.districts)) {
        throw new Error("Unexpected API response format");
      }

      setData(result.districts);

      setDroughtDate(result.drought_data_date || "N/A");
      setFloodDate(result.flood_data_date || "N/A");

      setModelStatus(
        result.flood_model_status || {
          available: false,
        }
      );
    } catch (err) {
      console.error("API error:", err);

      setError(
        "Unable to connect to AquaSentinel API. Check whether the backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // --------------------------------------------------
  // DASHBOARD STATISTICS
  // --------------------------------------------------

  const stats = useMemo(() => {
    const critical = data.filter(
      (item) => item.overall_alert === "Critical"
    ).length;

    const highFlood = data.filter((item) =>
      ["High", "Very High"].includes(item.flood?.status)
    ).length;

    const droughtAffected = data.filter((item) =>
      [
        "Moderate Drought",
        "Severe Drought",
        "Extreme Drought",
      ].includes(item.drought?.status)
    ).length;

    const mlWarnings = data.filter(
      (item) => item.flood?.extreme_rainfall_warning === true
    ).length;

    return {
      districts: data.length,
      critical,
      highFlood,
      droughtAffected,
      mlWarnings,
    };
  }, [data]);

  // --------------------------------------------------
  // ALERT DISTRIBUTION
  // --------------------------------------------------

  const alertDistribution = useMemo(() => {
    const levels = [
      "Critical",
      "High",
      "Moderate",
      "Low",
      "Normal",
      "Insufficient Data",
    ];

    return levels
      .map((level) => ({
        name: level,
        value: data.filter(
          (item) => item.overall_alert === level
        ).length,
      }))
      .filter((item) => item.value > 0);
  }, [data]);

  // --------------------------------------------------
  // FLOOD CHART DATA
  // --------------------------------------------------

  const floodChartData = useMemo(() => {
    return [...data]
      .sort(
        (a, b) =>
          (b.flood?.risk_score ?? 0) -
          (a.flood?.risk_score ?? 0)
      )
      .slice(0, 8)
      .map((item) => ({
        district: item.district,
        score: item.flood?.risk_score ?? 0,
      }));
  }, [data]);

  // --------------------------------------------------
  // ACTIVE ML WARNINGS
  // --------------------------------------------------

  const mlWarningDistricts = useMemo(() => {
    return data
      .filter(
        (item) =>
          item.flood?.extreme_rainfall_warning === true
      )
      .sort(
        (a, b) =>
          (b.flood?.extreme_rainfall_model_score ?? 0) -
          (a.flood?.extreme_rainfall_model_score ?? 0)
      );
  }, [data]);

  // --------------------------------------------------
  // DISTRICT SEARCH AND FILTER
  // --------------------------------------------------

  const filteredDistricts = useMemo(() => {
    return data.filter((item) => {
      const matchesSearch = (item.district || "")
        .toLowerCase()
        .includes(search.toLowerCase());

      const matchesFilter =
        filter === "All" ||
        item.overall_alert === filter;

      return matchesSearch && matchesFilter;
    });
  }, [data, search, filter]);

  // --------------------------------------------------
  // NAVIGATION
  // --------------------------------------------------

  const scrollToSection = (id) => {
    setActivePage(id);
    setMobileMenu(false);

    document.getElementById(id)?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  };

  // --------------------------------------------------
  // LOADING STATE
  // --------------------------------------------------

  if (loading && data.length === 0) {
    return (
      <div className="loading-state">
        <RefreshCw className="spin" size={28} />
        <p>Loading AquaSentinel environmental intelligence...</p>
      </div>
    );
  }

  // --------------------------------------------------
  // MAIN DASHBOARD
  // --------------------------------------------------

  return (
    <div className="app-shell">

      {/* MOBILE OVERLAY */}

      {mobileMenu && (
        <button
          className="mobile-overlay"
          aria-label="Close navigation"
          onClick={() => setMobileMenu(false)}
        />
      )}

      {/* SIDEBAR */}

      <aside
        className={`sidebar ${mobileMenu ? "sidebar-open" : ""}`}
      >
        <div className="brand">
          <div className="brand-icon">
            <Droplets size={25} />
          </div>

          <div className="brand-text">
            <h2>AquaSentinel</h2>
            <span>ENVIRONMENTAL INTELLIGENCE</span>
          </div>

          <button
            className="close-menu"
            onClick={() => setMobileMenu(false)}
            aria-label="Close menu"
          >
            <X size={20} />
          </button>
        </div>

        <div className="nav-heading">WORKSPACE</div>

        <nav className="navigation">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;

            return (
              <button
                key={item.id}
                className={`nav-item ${
                  activePage === item.id ? "active" : ""
                }`}
                onClick={() => scrollToSection(item.id)}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="sidebar-bottom">
          <div className="sidebar-status">
            <span className="online-dot"></span>

            <div>
              <strong>System Online</strong>
              <span>Monitoring Gujarat</span>
            </div>
          </div>

          <div className="sidebar-footer">
            AquaSentinel · 2026
          </div>
        </div>
      </aside>

      {/* MAIN CONTENT */}

      <main className="main-content">

        {/* TOPBAR */}

        <header className="topbar">
          <button
            className="mobile-menu-button"
            onClick={() => setMobileMenu(true)}
            aria-label="Open menu"
          >
            <Menu size={21} />
          </button>

          <div className="breadcrumb">
            Workspace / {activePage.replaceAll("-", " ")}
          </div>

          <button
            className="refresh-button"
            onClick={fetchData}
            disabled={loading}
          >
            <RefreshCw
              size={16}
              className={loading ? "spin" : ""}
            />
            Refresh Data
          </button>
        </header>

        {/* ==========================================
            1. OVERVIEW
        ========================================== */}

        <section id="overview" className="dashboard-section">

          <div className="page-heading">
            <div>
              <h1>Environmental Overview</h1>
              <p>
                Flood and drought intelligence for Gujarat, India
              </p>
            </div>
          </div>

          {/* DATA DATES */}

          <div className="date-strip">
            <div className="date-label">
              <Activity size={17} />
              <span>Latest available observations</span>
            </div>

            <div className="date-values">
              <span>
                Drought: <strong>{droughtDate}</strong>
              </span>

              <span>
                Flood: <strong>{floodDate}</strong>
              </span>
            </div>
          </div>

          {/* ERROR */}

          {error && (
            <div className="error-banner">
              <AlertTriangle size={18} />
              <span>{error}</span>
              <button onClick={fetchData}>Retry</button>
            </div>
          )}

          {/* OVERVIEW CARDS */}

          <section className="stats-grid">

            <StatCard
              icon={Map}
              label="Districts Monitored"
              value={stats.districts}
              subtitle="Across Gujarat"
              color="blue"
            />

            <StatCard
              icon={AlertTriangle}
              label="Critical Alerts"
              value={stats.critical}
              subtitle="Highest alert priority"
              color="red"
            />

            <StatCard
              icon={Waves}
              label="High Flood Risk"
              value={stats.highFlood}
              subtitle="High and very high"
              color="orange"
            />

            <StatCard
              icon={Gauge}
              label="Drought Affected"
              value={stats.droughtAffected}
              subtitle="Moderate to extreme"
              color="purple"
            />

            <StatCard
              icon={BrainCircuit}
              label="ML Rainfall Warnings"
              value={stats.mlWarnings}
              subtitle="Next-day extreme-rainfall alerts"
              color="orange"
            />

          </section>

          {/* ==========================================
              2. RISK INTELLIGENCE
          ========================================== */}

          <section className="dashboard-section" id="flood">

            <div className="section-heading">
              <div>
                <h2>Risk Intelligence</h2>
                <p>
                  District-level environmental risk indicators
                </p>
              </div>

              <span className="api-status">
                <span className="online-dot"></span>
                API CONNECTED
              </span>
            </div>

            <div className="charts-grid">

              {/* FLOOD CHART */}

              <div className="panel chart-panel">

                <div className="panel-heading">
                  <div>
                    <h3>Flood Risk by District</h3>
                    <p>
                      Top 8 districts by current flood score
                    </p>
                  </div>

                  <div className="panel-icon blue">
                    <Waves size={19} />
                  </div>
                </div>

                <div className="chart-container">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={floodChartData}
                      margin={{
                        top: 10,
                        right: 10,
                        left: 0,
                        bottom: 5,
                      }}
                    >
                      <CartesianGrid
                        strokeDasharray="3 3"
                        stroke="#26364a"
                      />

                      <XAxis
                        dataKey="district"
                        tick={{
                          fill: "#91a7c1",
                          fontSize: 10,
                        }}
                        angle={-15}
                        textAnchor="end"
                        height={55}
                      />

                      <YAxis
                        domain={[0, 100]}
                        tick={{
                          fill: "#91a7c1",
                          fontSize: 11,
                        }}
                      />

                      <Tooltip
                        contentStyle={{
                          background: "#111d2c",
                          border: "1px solid #293c52",
                          borderRadius: "8px",
                          color: "#fff",
                        }}
                      />

                      <Bar
                        dataKey="score"
                        name="Flood Risk Score"
                        fill="#38bdf8"
                        radius={[5, 5, 0, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* ALERT DISTRIBUTION */}

              <div className="panel chart-panel">

                <div className="panel-heading">
                  <div>
                    <h3>Overall Alert Distribution</h3>
                    <p>
                      Districts grouped by alert priority
                    </p>
                  </div>

                  <div className="panel-icon purple">
                    <ShieldCheck size={19} />
                  </div>
                </div>

                <div className="chart-container">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={alertDistribution}
                        dataKey="value"
                        nameKey="name"
                        cx="50%"
                        cy="45%"
                        innerRadius={48}
                        outerRadius={78}
                        paddingAngle={2}
                      >
                        {alertDistribution.map((entry) => (
                          <Cell
                            key={entry.name}
                            fill={ALERT_COLORS[entry.name]}
                          />
                        ))}
                      </Pie>

                      <Tooltip
                        contentStyle={{
                          background: "#111d2c",
                          border: "1px solid #293c52",
                          borderRadius: "8px",
                          color: "#fff",
                        }}
                      />

                      <Legend
                        verticalAlign="bottom"
                        formatter={(value) => (
                          <span className="legend-text">
                            {value}
                          </span>
                        )}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>

            </div>
          </section>

          {/* ==========================================
              3. AI EARLY WARNING CENTRE
          ========================================== */}

          <section
            className="dashboard-section"
            id="ml-warning"
          >

            <div className="section-heading">
              <div>
                <h2>AI Early Warning Centre</h2>
                <p>
                  XGBoost-based next-day extreme-rainfall predictions
                </p>
              </div>

              <span className="api-status">
                <span
                  className={
                    modelStatus.available
                      ? "online-dot"
                      : "offline-dot"
                  }
                ></span>

                {modelStatus.available
                  ? "MODEL ACTIVE"
                  : "MODEL UNAVAILABLE"}
              </span>
            </div>

            {/* MODEL INFORMATION */}

            <div className="panel">

              <div className="panel-heading">
                <div>
                  <h3>
                    <BrainCircuit
                      size={19}
                      style={{
                        display: "inline",
                        marginRight: "8px",
                        verticalAlign: "middle",
                      }}
                    />
                    XGBoost Prediction Model
                  </h3>

                  <p>
                    Machine learning assessment of next-day extreme rainfall
                  </p>
                </div>
              </div>

              <div className="drought-summary">

                <div>
                  <strong>
                    {stats.mlWarnings}
                  </strong>

                  <span>
                    Districts with active ML warnings
                  </span>
                </div>

                <div>
                  <strong>
                    {modelStatus.available &&
                    modelStatus.test_f1 != null
                      ? `${(
                          Number(modelStatus.test_f1) * 100
                        ).toFixed(1)}%`
                      : "N/A"}
                  </strong>

                  <span>
                    Model test F1 score
                  </span>
                </div>

                <div>
                  <strong>
                    {modelStatus.available &&
                    modelStatus.test_pr_auc != null
                      ? Number(modelStatus.test_pr_auc).toFixed(3)
                      : "N/A"}
                  </strong>

                  <span>
                    Test PR-AUC
                  </span>
                </div>

                <div>
                  <strong>
                    {modelStatus.available &&
                    modelStatus.decision_threshold != null
                      ? Number(
                          modelStatus.decision_threshold
                        ).toFixed(2)
                      : "N/A"}
                  </strong>

                  <span>
                    Decision threshold
                  </span>
                </div>

              </div>

              <p className="method-note">
                {modelStatus.prediction_target ||
                  "Prediction target information is unavailable."}
              </p>

              <p className="method-note">
                {modelStatus.warning ||
                  "The model warning is an extreme-rainfall proxy, not verified flood occurrence or calibrated flood probability."}
              </p>

            </div>

            {/* ACTIVE WARNINGS TABLE */}

            <div className="panel table-panel">

              <div className="panel-heading">
                <div>
                  <h3>Active ML Warnings</h3>
                  <p>
                    Districts flagged by the XGBoost classifier
                  </p>
                </div>

                <div className="panel-icon">
                  <CloudRain size={19} />
                </div>
              </div>

              <div className="table-wrapper">

                <table>
                  <thead>
                    <tr>
                      <th>District</th>
                      <th>ML Score</th>
                      <th>Decision Threshold</th>
                      <th>Flood Risk</th>
                      <th>Warning</th>
                    </tr>
                  </thead>

                  <tbody>

                    {mlWarningDistricts.map((item) => (
                      <tr key={item.district}>

                        <td>
                          <strong>{item.district}</strong>
                        </td>

                        <td>
                          {item.flood?.extreme_rainfall_model_score != null
                            ? `${Number(
                                item.flood.extreme_rainfall_model_score
                              ).toFixed(2)} / 100`
                            : "N/A"}
                        </td>

                        <td>
                          {item.flood?.model_decision_threshold != null
                            ? Number(
                                item.flood.model_decision_threshold
                              ).toFixed(2)
                            : "N/A"}
                        </td>

                        <td>
                          <StatusPill
                            status={item.flood?.status}
                          />
                        </td>

                        <td>
                          <span className="status-pill high">
                            Active
                          </span>
                        </td>

                      </tr>
                    ))}

                    {mlWarningDistricts.length === 0 && (
                      <tr>
                        <td colSpan="5" className="empty-row">
                          No active extreme-rainfall warnings.
                        </td>
                      </tr>
                    )}

                  </tbody>
                </table>

              </div>

              <div className="table-footer">
                Showing {mlWarningDistricts.length} active ML warnings
                across {data.length} districts
              </div>

            </div>

          </section>

          {/* ==========================================
              4. DROUGHT ANALYSIS
          ========================================== */}

          <section
            className="dashboard-section"
            id="drought"
          >

            <div className="section-heading">
              <div>
                <h2>Drought Analysis</h2>
                <p>
                  Standardized Precipitation Index (SPI-3) by district
                </p>
              </div>
            </div>

            <div className="panel drought-panel">

              <div className="drought-summary">

                <div>
                  <strong>{stats.droughtAffected}</strong>
                  <span>
                    Districts showing drought conditions
                  </span>
                </div>

                <div>
                  <strong>{droughtDate}</strong>
                  <span>
                    Latest available SPI observation
                  </span>
                </div>

              </div>

              <p className="method-note">
                Drought classifications are based on the calculated
                SPI-3 indicator. They represent rainfall anomaly
                conditions, not a guaranteed forecast of future drought.
              </p>

            </div>

          </section>

          {/* ==========================================
              5. DISTRICT MONITORING
          ========================================== */}

          <section
            className="dashboard-section"
            id="districts"
          >

            <div className="section-heading">
              <div>
                <h2>District Monitoring</h2>
                <p>
                  Unified flood and drought status across Gujarat
                </p>
              </div>
            </div>

            <div className="panel table-panel">

              {/* SEARCH AND FILTER */}

              <div className="table-controls">

                <div className="search-box">
                  <Search size={16} />

                  <input
                    type="text"
                    placeholder="Search district..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                  />
                </div>

                <select
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                >
                  <option value="All">All alerts</option>
                  <option value="Critical">Critical</option>
                  <option value="High">High</option>
                  <option value="Moderate">Moderate</option>
                  <option value="Low">Low</option>
                  <option value="Normal">Normal</option>
                  <option value="Insufficient Data">
                    Insufficient Data
                  </option>
                </select>

              </div>

              {/* DISTRICT TABLE */}

              <div className="table-wrapper">

                <table>
                  <thead>
                    <tr>
                      <th>District</th>
                      <th>SPI-3</th>
                      <th>Drought Status</th>
                      <th>Flood Score</th>
                      <th>Flood Status</th>
                      <th>ML Warning</th>
                      <th>Overall Alert</th>
                    </tr>
                  </thead>

                  <tbody>

                    {filteredDistricts.map((item) => (
                      <tr key={item.district}>

                        <td>
                          <strong>{item.district}</strong>
                        </td>

                        <td>
                          {Number.isFinite(
                            Number(item.drought?.spi_3)
                          )
                            ? Number(
                                item.drought.spi_3
                              ).toFixed(2)
                            : "N/A"}
                        </td>

                        <td>
                          <StatusPill
                            status={item.drought?.status}
                          />
                        </td>

                        <td>
                          {item.flood?.risk_score ?? "N/A"}
                        </td>

                        <td>
                          <StatusPill
                            status={item.flood?.status}
                          />
                        </td>

                        <td>
                          {item.flood?.extreme_rainfall_warning === true ? (
                            <span className="status-pill high">
                              Active
                            </span>
                          ) : item.flood?.extreme_rainfall_warning === false ? (
                            <span className="status-pill normal">
                              No Warning
                            </span>
                          ) : (
                            "N/A"
                          )}
                        </td>

                        <td>
                          <StatusPill
                            status={item.overall_alert}
                          />
                        </td>

                      </tr>
                    ))}

                    {filteredDistricts.length === 0 && (
                      <tr>
                        <td colSpan="7" className="empty-row">
                          No matching districts found.
                        </td>
                      </tr>
                    )}

                  </tbody>
                </table>

              </div>

              <div className="table-footer">
                Showing {filteredDistricts.length} of{" "}
                {data.length} districts
              </div>

            </div>

          </section>

          {/* ==========================================
              6. RISK ALERTS
          ========================================== */}

          <section
            className="dashboard-section"
            id="alerts"
          >

            <div className="section-heading">
              <div>
                <h2>Risk Alerts</h2>
                <p>
                  Districts requiring attention based on combined indicators
                </p>
              </div>
            </div>

            <div className="panel alerts-panel">

              {data
                .filter((item) =>
                  ["Critical", "High"].includes(
                    item.overall_alert
                  )
                )
                .map((item) => (

                  <div
                    className="alert-row"
                    key={item.district}
                  >

                    <div className="alert-indicator">
                      <AlertTriangle size={18} />
                    </div>

                    <div className="alert-details">
                      <strong>{item.district}</strong>

                      <span>
                        Drought: {item.drought?.status || "N/A"}
                        {" · "}
                        Flood: {item.flood?.status || "N/A"}
                        {item.flood?.extreme_rainfall_warning === true
                          ? " · ML Warning Active"
                          : ""}
                      </span>
                    </div>

                    <StatusPill
                      status={item.overall_alert}
                    />

                  </div>

                ))}

              {data.filter((item) =>
                ["Critical", "High"].includes(
                  item.overall_alert
                )
              ).length === 0 && (
                <p className="empty-row">
                  No high-priority alerts.
                </p>
              )}

            </div>

          </section>

          {/* FOOTER */}

          <footer className="page-footer">

            <span>
              AquaSentinel · Environmental Intelligence Workspace
            </span>

            <span>
              Gujarat, India · 2026
            </span>

          </footer>

        </section>

      </main>

    </div>
  );
}

export default App;
