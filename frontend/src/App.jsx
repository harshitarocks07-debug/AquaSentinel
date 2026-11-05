
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
import "leaflet/dist/leaflet.css";
import { GeoJSON, MapContainer, TileLayer } from "react-leaflet";
import "./App.css";

const API_BASE_URL = import.meta.env.DEV
  ? "http://127.0.0.1:8000"
  : "";

const API_URL = `${API_BASE_URL}/api/risk/latest`;
const FLOOD_API_URL = `${API_BASE_URL}/api/flood/latest`;
const GEOJSON_URL = "/data/gujarat_districts.geojson";

function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("All");
  const [floodData, setFloodData] = useState(null);
  const [geoJson, setGeoJson] = useState(null);
  const [geoError, setGeoError] = useState("");
  const [mapMode, setMapMode] = useState("flood");
  const [selectedMapDistrict, setSelectedMapDistrict] = useState(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError("");

      const [riskResponse, floodResponse] = await Promise.all([
        axios.get(API_URL),
        axios.get(FLOOD_API_URL).catch(() => null),
      ]);
      setData(riskResponse.data);
      setFloodData(floodResponse?.data || null);
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
    axios.get(GEOJSON_URL)
      .then((response) => setGeoJson(response.data))
      .catch(() => setGeoError("District boundary file not found. Copy gujarat_districts.geojson into frontend/public/data/"));
  }, []);

  const districts = data?.districts || [];
  const floodDistricts = Array.isArray(floodData?.districts)
    ? floodData.districts
    : Array.isArray(floodData) ? floodData : [];

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

  // Drought analysis chart data derived from the unified risk API response.
  const droughtChartData = districts
    .filter((item) => item.drought?.spi_3 != null && Number.isFinite(Number(item.drought.spi_3)))
    .map((item) => {
      const spi = Number(item.drought.spi_3);
      return {
        district: item.district,
        spi,
        severity: Math.abs(spi),
      };
    })
    .sort((a, b) => b.severity - a.severity)
    .slice(0, 10);

  const droughtSeverityData = [
    { name: "Extreme Drought", value: districts.filter((d) => d.drought?.status === "Extreme Drought").length, color: "#991b1b" },
    { name: "Severe Drought", value: districts.filter((d) => d.drought?.status === "Severe Drought").length, color: "#ef4444" },
    { name: "Moderate Drought", value: districts.filter((d) => d.drought?.status === "Moderate Drought").length, color: "#f97316" },
    { name: "Normal", value: districts.filter((d) => d.drought?.status === "Normal").length, color: "#22c55e" },
  ].filter((item) => item.value > 0);

  const droughtAffectedCount = districts.filter((d) =>
    ["Extreme Drought", "Severe Drought", "Moderate Drought"].includes(d.drought?.status)
  ).length;

  // Plot absolute SPI-3 magnitude so more severe drought bars rise upward.
  // Axis and tooltip labels retain the actual negative SPI-3 sign.

  // Inline badge colours avoid conflicting or missing CSS class rules.
  const getStatusStyle = (status) => {
    const value = String(status || "").trim().toLowerCase();
    const palette = {
      "very high": ["#3b1720", "#fca5a5", "#7f1d1d"],
      "high": ["#3b2416", "#fdba74", "#9a3412"],
      "moderate": ["#3b3215", "#fde047", "#854d0e"],
      "low": ["#123448", "#7dd3fc", "#155e75"],
      "critical": ["#3b1720", "#fca5a5", "#7f1d1d"],
      "extreme drought": ["#3b1720", "#fca5a5", "#7f1d1d"],
      "severe drought": ["#3b2416", "#fdba74", "#9a3412"],
      "moderate drought": ["#3b3215", "#fde047", "#854d0e"],
      "normal": ["#123322", "#86efac", "#166534"],
      "insufficient data": ["#273449", "#cbd5e1", "#475569"],
    };
    const [background, color, borderColor] = palette[value] || palette["insufficient data"];
    return {
      backgroundColor: background,
      color,
      border: `1px solid ${borderColor}`,
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center",
      minWidth: "88px",
      padding: "5px 10px",
      borderRadius: "6px",
      fontWeight: 600,
      fontSize: "11px",
      lineHeight: 1.3,
      whiteSpace: "nowrap",
    };
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
          <a className="nav-item" href="#district-map">
            <Map size={18} />
            Gujarat Risk Map
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

            <section className="dashboard-section" id="district-map">
              <div className="section-heading map-section-heading">
                <div>
                  <h2>Gujarat District Risk Map</h2>
                  <p>Interactive district-level flood risk and machine-learning warnings</p>
                </div>
                <div className="map-mode-switch" role="group" aria-label="Map display mode">
                  <button className={mapMode === "flood" ? "selected" : ""} onClick={() => setMapMode("flood")}>Flood Risk</button>
                  <button className={mapMode === "ml" ? "selected" : ""} onClick={() => setMapMode("ml")}>ML Warning</button>
                </div>
              </div>
              <div className="map-layout">
                <div className="panel gujarat-map-panel">
                  {geoJson ? (
                    <GujaratRiskMap
                      geoJson={geoJson}
                      districts={districts}
                      floodDistricts={floodDistricts}
                      mode={mapMode}
                      selectedDistrict={selectedMapDistrict}
                      onSelect={setSelectedMapDistrict}
                    />
                  ) : (
                    <div className="map-placeholder">
                      <Map size={26} />
                      <strong>{geoError || "Loading Gujarat district boundaries..."}</strong>
                      <span>Expected file: frontend/public/data/gujarat_districts.geojson</span>
                    </div>
                  )}
                  <div className="map-legend">
                    {mapMode === "flood" ? <>
                      <LegendItem color="#ef4444" label="Very High" />
                      <LegendItem color="#f97316" label="High" />
                      <LegendItem color="#eab308" label="Moderate" />
                      <LegendItem color="#22c55e" label="Low" />
                      <LegendItem color="#64748b" label="No data" />
                    </> : <>
                      <LegendItem color="#ef4444" label="Warning issued" />
                      <LegendItem color="#22c55e" label="No warning" />
                      <LegendItem color="#64748b" label="No ML data" />
                    </>}
                  </div>
                </div>
                <div className="panel map-detail-panel">
                  <div className="panel-heading">
                    <div><h3>{selectedMapDistrict?.district || "District details"}</h3><p>{selectedMapDistrict ? "Selected district intelligence" : "Select a district on the map"}</p></div>
                  </div>
                  {selectedMapDistrict ? (
                    <DistrictMapDetails district={selectedMapDistrict} floodDistricts={floodDistricts} />
                  ) : (
                    <div className="map-empty-detail"><Map size={25} /><span>Click any district to inspect its latest flood and drought indicators.</span></div>
                  )}
                </div>
              </div>
              <p className="map-method-note">Flood colours use the backend rule-based risk classification. ML Warning mode shows the model's extreme-rainfall warning where that field is returned by the flood API; it is not a confirmed flood prediction.</p>
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

            <section className="dashboard-section" id="drought">
              <div className="section-heading">
                <div>
                  <h2>Drought Analysis</h2>
                  <p>Latest district-level drought conditions using the Standardized Precipitation Index (SPI-3)</p>
                </div>
                <span className="record-count">{droughtAffectedCount} affected districts</span>
              </div>

              <div className="charts-grid">
                <div className="panel chart-panel">
                  <div className="panel-heading">
                    <div>
                      <h3>Lowest SPI-3 by District</h3>
                      <p>Districts with the greatest drought severity (most negative SPI-3)</p>
                    </div>
                    <span className="panel-icon purple-icon">
                      <Wind size={19} />
                    </span>
                  </div>

                  {droughtChartData.length ? (
                    <ResponsiveContainer width="100%" height={280}>
                      <BarChart
                        data={droughtChartData}
                        margin={{ top: 15, right: 12, left: 8, bottom: 42 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#293343" />
                        <XAxis
                          dataKey="district"
                          angle={-25}
                          textAnchor="end"
                          interval={0}
                          height={55}
                          tick={{ fill: "#94a3b8", fontSize: 10 }}
                          axisLine={false}
                          tickLine={false}
                        />
                        <YAxis
                          type="number"
                          domain={[0, "auto"]}
                          tickCount={6}
                          allowDecimals={true}
                          tickFormatter={(value) => value === 0 ? "0.00" : `-${Number(value).toFixed(2)}`}
                          width={58}
                          tick={{ fill: "#94a3b8", fontSize: 11 }}
                          axisLine={false}
                          tickLine={false}
                        />
                        <Tooltip
                          formatter={(value) => [`-${Number(value).toFixed(2)}`, "SPI-3"]}
                          contentStyle={{ background: "#151e2c", border: "1px solid #334155", borderRadius: 8 }}
                          labelStyle={{ color: "#fff" }}
                        />
                        <Bar dataKey="severity" name="SPI-3 magnitude" fill="#a78bfa" radius={[5, 5, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <EmptyChart />
                  )}
                </div>

                <div className="panel chart-panel">
                  <div className="panel-heading">
                    <div>
                      <h3>Drought Severity Distribution</h3>
                      <p>Latest status across monitored districts</p>
                    </div>
                    <span className="panel-icon purple-icon">
                      <Gauge size={19} />
                    </span>
                  </div>

                  {droughtSeverityData.length ? (
                    <>
                      <ResponsiveContainer width="100%" height={220}>
                        <PieChart>
                          <Pie
                            data={droughtSeverityData}
                            dataKey="value"
                            nameKey="name"
                            innerRadius={58}
                            outerRadius={85}
                            paddingAngle={3}
                          >
                            {droughtSeverityData.map((entry) => (
                              <Cell key={entry.name} fill={entry.color} />
                            ))}
                          </Pie>
                          <Tooltip
                            contentStyle={{ background: "#151e2c", border: "1px solid #334155", borderRadius: 8 }}
                          />
                        </PieChart>
                      </ResponsiveContainer>
                      <div className="chart-legend">
                        {droughtSeverityData.map((item) => (
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
              </div>

              <div className="panel table-panel drought-table-panel">
                <div className="panel-heading">
                  <div>
                    <h3>District Drought Status</h3>
                    <p>Latest available SPI-3 reading and drought classification</p>
                  </div>
                </div>
                <div className="table-scroll">
                  <table>
                    <thead>
                      <tr>
                        <th>District</th>
                        <th>SPI-3</th>
                        <th>Drought Status</th>
                        <th>Overall Alert</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[...districts]
                        .sort((a, b) => {
                          const aValue = Number(a.drought?.spi_3);
                          const bValue = Number(b.drought?.spi_3);
                          return (Number.isFinite(aValue) ? aValue : Infinity) -
                            (Number.isFinite(bValue) ? bValue : Infinity);
                        })
                        .map((item) => (
                          <tr key={item.district}>
                            <td className="district-name">{item.district}</td>
                            <td>{Number.isFinite(Number(item.drought?.spi_3))
                              ? Number(item.drought.spi_3).toFixed(2)
                              : "—"}</td>
                            <td>
                              <span className="status-pill" style={getStatusStyle(item.drought?.status)}>
                                {item.drought?.status || "Insufficient Data"}
                              </span>
                            </td>
                            <td>
                              <span className="status-pill" style={getStatusStyle(item.overall_alert)}>
                                {item.overall_alert || "Insufficient Data"}
                              </span>
                            </td>
                          </tr>
                        ))}
                      {!districts.length && (
                        <tr>
                          <td colSpan="4" className="no-results">No drought data available.</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
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
                          <span className="status-pill" style={getStatusStyle(item.drought?.status)}>
                            {item.drought?.status || "Insufficient Data"}
                          </span>
                        </td>
                        <td>{item.flood?.risk_score ?? "—"}</td>
                        <td>
                          <span className="status-pill" style={getStatusStyle(item.flood?.status)}>
                            {item.flood?.status || "Insufficient Data"}
                          </span>
                        </td>
                        <td>
                          <span className="status-pill" style={getStatusStyle(item.overall_alert)}>
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

function normalizeDistrictName(value = "") {
  const key = value.toLowerCase().replace(/[^a-z]/g, "");
  const aliases = {
    ahmedabad: "ahmadabad", banaskantha: "banaskantha", kachchh: "kachchh",
    kutch: "kachchh", dahod: "dohad", mehsana: "mahesana", panchmahal: "panchmahals",
    sabarkantha: "sabarkantha", aravalli: "arvalli", chhotaudepur: "chhotaudepur",
  };
  return aliases[key] || key;
}

function featureDistrictName(feature) {
  const p = feature?.properties || {};
  const candidates = ["district", "DISTRICT", "District", "DIST_NAME", "dtname", "DTNAME", "NAME_2", "name_2", "name", "NAME"];
  for (const key of candidates) if (p[key]) return String(p[key]);
  return "Unknown district";
}

function findFloodRecord(name, floodDistricts) {
  const normalized = normalizeDistrictName(name);
  return floodDistricts.find((item) => normalizeDistrictName(item.district || item.name) === normalized);
}

function districtColor(item, floodRecord, mode) {
  if (mode === "ml") {
    const warning = floodRecord?.extreme_rainfall_warning ?? floodRecord?.ml_warning ?? floodRecord?.warning;
    if (warning === true) return "#ef4444";
    if (warning === false) return "#22c55e";
    return "#64748b";
  }
  const level = item?.flood?.status || floodRecord?.risk_level || floodRecord?.risk_status || "Insufficient Data";
  return ({ "Very High": "#ef4444", High: "#f97316", Moderate: "#eab308", Low: "#22c55e", "Insufficient Data": "#64748b" })[level] || "#64748b";
}

function GujaratRiskMap({ geoJson, districts, floodDistricts, mode, selectedDistrict, onSelect }) {
  const lookup = (name) => districts.find((d) => normalizeDistrictName(d.district) === normalizeDistrictName(name));
  const style = (feature) => {
    const name = featureDistrictName(feature);
    const item = lookup(name);
    const floodRecord = findFloodRecord(name, floodDistricts);
    const selected = selectedDistrict && normalizeDistrictName(selectedDistrict.district) === normalizeDistrictName(name);
    return { fillColor: districtColor(item, floodRecord, mode), fillOpacity: selected ? 0.9 : 0.68, color: selected ? "#ffffff" : "#cbd5e1", weight: selected ? 2.5 : 1, opacity: 0.9 };
  };
  const onEachFeature = (feature, layer) => {
    const name = featureDistrictName(feature);
    const item = lookup(name);
    const floodRecord = findFloodRecord(name, floodDistricts);
    layer.bindTooltip(name, { sticky: true, className: "district-map-tooltip" });
    layer.on({ click: () => onSelect({ district: item?.district || name, drought: item?.drought, flood: item?.flood, overall_alert: item?.overall_alert, ml: floodRecord }) });
  };
  return (
    <MapContainer center={[22.5, 71.5]} zoom={6} minZoom={5} maxZoom={9} scrollWheelZoom={true} className="gujarat-leaflet-map" style={{ height: 460, width: "100%" }}>
      <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      <GeoJSON key={`${mode}-${selectedDistrict?.district || "none"}`} data={geoJson} style={style} onEachFeature={onEachFeature} />
    </MapContainer>
  );
}

function LegendItem({ color, label }) {
  return <span className="map-legend-item"><i style={{ background: color }} />{label}</span>;
}

function DistrictMapDetails({ district, floodDistricts }) {
  const ml = district.ml || findFloodRecord(district.district, floodDistricts);
  const warning = ml?.extreme_rainfall_warning ?? ml?.ml_warning ?? ml?.warning;
  const mlScore = ml?.ml_score ?? ml?.model_score ?? ml?.extreme_rainfall_score;
  const rows = [
    ["Flood risk score", district.flood?.risk_score ?? ml?.risk_score ?? "—"],
    ["Flood status", district.flood?.status ?? ml?.risk_level ?? "Insufficient Data"],
    ["Drought status", district.drought?.status ?? "—"],
    ["SPI-3", Number.isFinite(Number(district.drought?.spi_3)) ? Number(district.drought.spi_3).toFixed(2) : "—"],
    ["ML model score", mlScore != null ? `${Number(mlScore).toFixed(1)}%` : "Not returned by API"],
    ["ML warning", warning === true ? "Warning issued" : warning === false ? "No warning" : "Not available"],
    ["Latest flood data", district.flood?.date ?? ml?.date ?? "—"],
  ];
  return (
    <div className="district-detail-list">
      {rows.map(([label, value]) => (
        <div className="district-detail-row" key={label}>
          <span>{label}:</span>
          <strong>{value}</strong>
        </div>
      ))}
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
