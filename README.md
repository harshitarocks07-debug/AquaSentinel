# AquaSentinel
### AI-Powered Flood and Drought Intelligence Platform for Gujarat

AquaSentinel is an AI-powered environmental monitoring and decision-support platform designed to assess flood and drought conditions across Gujarat, India. It combines historical rainfall data, the Standardized Precipitation Index (SPI-3), machine learning, and rule-based risk assessment to provide district-level environmental intelligence.

The platform helps users monitor changing weather conditions, identify high-risk districts, and understand potential environmental threats through an interactive dashboard.

---

## 1. Problem Statement

Floods and droughts pose significant risks to agriculture, infrastructure, water resources, and communities. Delayed identification of environmental risks can increase damage and reduce the effectiveness of preparedness measures.

AquaSentinel addresses this challenge by consolidating rainfall and drought indicators into a centralized platform that provides district-level risk assessment and machine-learning-based extreme rainfall warnings.

## 2. Proposed Solution

AquaSentinel provides an integrated environmental intelligence system that:

- Monitors flood and drought conditions across 33 districts of Gujarat.
- Evaluates flood risk using rainfall measurements and accumulated rainfall indicators.
- Uses machine learning to identify potential next-day extreme rainfall events.
- Assesses drought severity using the Standardized Precipitation Index (SPI-3).
- Combines flood and drought indicators to generate overall district-level alerts.
- Presents results through an interactive dashboard and district-level monitoring interface.

## 3. Key Features

### 3.1 Environmental Overview
- Displays the number of monitored districts.
- Summarizes critical alerts and high flood-risk districts.
- Shows the number of drought-affected districts.
- Displays the latest available flood and drought observation dates.

### 3.2 Interactive Gujarat Risk Map
- Displays district-level geographical boundaries.
- Visualizes flood risk classifications.
- Provides a separate machine-learning warning view.
- Allows users to select districts and inspect their environmental indicators.

### 3.3 Flood Analysis
- Evaluates rainfall across multiple time windows.
- Calculates rule-based flood risk scores.
- Classifies districts into flood-risk levels.
- Uses an XGBoost model to identify potential next-day extreme rainfall events.

### 3.4 Drought Analysis
- Uses SPI-3 values to assess drought conditions.
- Classifies drought severity into Normal, Moderate, Severe, and Extreme categories.
- Displays district-level drought severity distribution.
- Identifies districts experiencing significant rainfall deficits.

### 3.5 District Monitoring
- Provides a consolidated district-level view.
- Displays SPI-3 values, drought status, flood scores, and overall alerts.
- Supports district searching and risk filtering.

### 3.6 District-Level Intelligence
- Displays selected district information.
- Presents available flood and drought indicators.
- Shows machine-learning warning information when returned by the API.

## 4. System Architecture

AquaSentinel follows a frontend-backend architecture with independent data processing and machine learning components.

**Workflow:**

1. Historical rainfall and drought datasets are processed.
2. Feature engineering generates rainfall indicators for flood assessment.
3. The flood engine calculates rule-based risk scores and obtains machine-learning predictions.
4. The drought engine evaluates SPI-3 values and classifies drought severity.
5. The unified risk engine combines flood and drought classifications into overall alerts.
6. FastAPI exposes the processed results through REST API endpoints.
7. The React frontend retrieves the API data and displays it through dashboard components, charts, tables, and the geographical map.

## 5. Technology Stack

| Component | Technologies |
|---|---|
| Frontend | React.js, Vite, JavaScript |
| Styling | CSS |
| Data Visualization | Recharts |
| Interactive Mapping | React Leaflet, Leaflet |
| Backend | Python, FastAPI |
| Machine Learning | XGBoost, Random Forest, Scikit-learn |
| Data Processing | Pandas, NumPy |
| Model Serialization | Joblib, Pickle |
| Data Format | CSV, GeoJSON |
| API Communication | Axios |

## 6. Machine Learning Approach

### 6.1 Flood Prediction

- **Algorithm:** XGBoost Classifier
- **Target:** Next-day extreme rainfall event based on district-specific historical rainfall thresholds.
- **Features:** Daily rainfall, 3-day rainfall, 7-day rainfall, 30-day rainfall, month, and district.
- **Evaluation:** Precision, Recall, F1-score, and PR-AUC.
- **Model Output:** Extreme rainfall warning score and warning classification.

The model identifies extreme rainfall conditions. Its output should not be interpreted as a confirmed flood occurrence probability.

### 6.2 Drought Assessment

- **Indicator:** Standardized Precipitation Index (SPI-3).
- **Approach:** SPI-based drought severity classification.
- **Categories:** Normal, Moderate Drought, Severe Drought, and Extreme Drought.

## 7. API Endpoints

The backend provides REST APIs for retrieving environmental intelligence.

| Endpoint | Purpose |
|---|---|
| `/api/flood/latest` | Latest district-level flood assessment |
| `/api/drought/latest` | Latest district-level drought assessment |
| `/api/risk/latest` | Combined flood and drought risk assessment |

Interactive API documentation is available through FastAPI Swagger UI at:

`http://127.0.0.1:8000/docs`

## 8. Database and Data Sources

The current implementation uses processed CSV datasets and GeoJSON geographical boundaries.

| Dataset | Purpose |
|---|---|
| Gujarat district flood features | Rainfall indicators and flood model features |
| Gujarat district SPI dataset | Drought assessment |
| Gujarat district GeoJSON | District geographical boundaries |

The platform currently monitors 33 districts of Gujarat.

## 9. Project Structure

```text
AquaSentinel/
│
├── Data/
│   ├── Raw/
│   └── Processed/
│       ├── daily_rainfall/
│       ├── gujarat_district_spi.csv
│       └── gujarat_districts.geojson
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routes/
│   │   │   ├── flood.py
│   │   │   ├── drought.py
│   │   │   └── risk.py
│   │   └── services/
│   │       ├── flood_engine.py
│   │       ├── drought_engine.py
│   │       └── unified_risk_engine.py
│   │
│   └── requirements.txt
│
├── frontend/
│   ├── public/
│   │   └── data/
│   └── src/
│       ├── App.jsx
│       ├── App.css
│       ├── index.css
│       └── main.jsx
│
├── ml/
│   ├── models/
│   │   ├── flood_xgb_model.joblib
│   │   ├── flood_model_metrics.json
│   │   ├── drought_rf_model.pkl
│   │   └── drought_model_metrics.json
│   └── train_flood_model.py
│
└── README.md
```

## 10. Installation and Execution

### Prerequisites

- Python 3.10 or later
- Node.js and npm
- Git

### Step 1: Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd AquaSentinel
```

### Step 2: Start the Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend:

`http://127.0.0.1:8000`

Swagger documentation:

`http://127.0.0.1:8000/docs`

### Step 3: Start the Frontend

Open a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL provided by Vite, usually:

`http://localhost:5173`

## 11. Value and Potential Impact

AquaSentinel aims to support environmental monitoring and risk awareness through centralized district-level intelligence.

Potential applications include:

- Disaster preparedness and risk monitoring.
- Agricultural planning and drought awareness.
- District-level environmental assessment.
- Water-resource management.
- Decision support for local authorities and stakeholders.

## 12. Limitations

- Model performance depends on the quality and coverage of historical datasets.
- Extreme rainfall warnings do not guarantee flood occurrence.
- The platform currently focuses on Gujarat.
- The system relies on the availability and freshness of processed datasets.
- It is a decision-support prototype and does not replace official meteorological or disaster-management alerts.

## 13. Future Scope

- Integration with real-time rainfall and weather APIs.
- Expansion to additional Indian states.
- Improved model calibration and validation.
- Integration of satellite imagery and remote-sensing data.
- More granular geographical risk assessment.
- Automated notifications for high-risk districts.
- Deployment on a scalable cloud infrastructure.

## 14. Conclusion

AquaSentinel demonstrates how machine learning, environmental indicators, geographical visualization, and API-driven architecture can be integrated into a unified flood and drought intelligence platform.

By providing district-level monitoring and risk assessment, the platform aims to improve environmental awareness and support more informed disaster-preparedness decisions.

---

**Project:** AquaSentinel  
**Domain:** Artificial Intelligence, Machine Learning, Environmental Sustainability  
**Geographical Focus:** Gujarat, India  
**Application Type:** Web-Based Environmental Intelligence Platform
