# AquaSentinel
### AI-Powered Flood and Drought Early Warning System for Gujarat

**Live Demo:** https://aquasentinel-fwbv.onrender.com

## Overview

AquaSentinel is an AI-powered climate-risk monitoring and early warning platform designed to assess flood and drought conditions across Gujarat.

The platform combines machine learning, rainfall analysis, drought indicators, geospatial visualization, and district-level risk assessment to transform environmental data into actionable insights.

It provides a centralized dashboard for monitoring flood risk, identifying extreme rainfall conditions, assessing drought severity, and understanding district-wise climate vulnerability.

## Problem Statement

Gujarat experiences recurring climate-related challenges, including extreme rainfall, flooding, and prolonged dry periods.

Traditional monitoring approaches can make it difficult to interpret large volumes of environmental data and communicate district-level risks effectively.

AquaSentinel addresses this challenge through an integrated platform that combines predictive analytics and drought assessment to support better climate-risk monitoring and early decision-making.

## Key Features

### 1. District-Level Flood Risk Monitoring
- Interactive Gujarat district map.
- District-wise flood risk visualization.
- Categorization of flood risk into different severity levels.
- Geographic representation of potential high-risk areas.

### 2. Machine Learning-Based Flood Prediction
- Uses an XGBoost Classifier for extreme rainfall prediction.
- Analyzes historical rainfall and engineered flood-related features.
- Identifies potential extreme rainfall conditions.
- Generates ML-based warning signals.

### 3. Drought Intelligence
- Uses the Standardized Precipitation Index (SPI-3).
- Evaluates rainfall deficits over a three-month period.
- Classifies drought conditions using SPI thresholds.
- Provides district-wise drought status.

**Drought classification thresholds:**

| SPI-3 Value | Classification |
|---|---|
| SPI ≤ -2.0 | Extreme Drought |
| -2.0 < SPI ≤ -1.5 | Severe Drought |
| -1.5 < SPI ≤ -1.0 | Moderate Drought |
| SPI > -1.0 | Normal |

### 4. Unified Risk Intelligence
- Combines flood and drought assessment outputs.
- Provides a consolidated view of climate-related risks.
- Supports district-level risk monitoring.

### 5. Interactive Dashboard
- Gujarat district-level map visualization.
- Flood Risk and ML Warning map modes.
- Risk monitoring charts and visualizations.
- District-wise drought status.
- Latest available risk information.

## Machine Learning Model

### XGBoost Classifier

AquaSentinel's flood prediction component uses an **XGBoost Classifier** to identify potential extreme rainfall events.

The prediction target is whether next-day rainfall exceeds the district-specific 95th percentile threshold calculated from the training period.

**Model configuration and evaluation:**

| Parameter | Value |
|---|---|
| Algorithm | XGBoost Classifier |
| Model Artifact | `flood_xgb_model.joblib` |
| Test Records | 82,401 |
| Classification Threshold | 0.80 |

### Model Performance

| Evaluation Metric | Score |
|---|---:|
| Accuracy | 92% |
| Macro Precision | 0.71 |
| Macro Recall | 0.85 |
| Macro F1-Score | 0.76 |
| PR-AUC | 0.5415 |

Accuracy represents overall classification correctness. Precision, recall, F1-score, and PR-AUC provide additional insight into performance, particularly for identifying extreme rainfall events.

*Note: These are the previously reported model evaluation results. They should not be interpreted as a guarantee of real-world flood prediction accuracy.*

## Drought Assessment Methodology

AquaSentinel uses SPI-3 to assess meteorological drought conditions.

The SPI approach measures precipitation anomalies over a three-month accumulation period and helps identify rainfall deficits.

The drought engine processes district-level SPI data and classifies conditions using predefined severity thresholds.

Unlike the flood prediction component, this is an indicator-based drought assessment rather than an XGBoost prediction model.

## System Architecture

```text
              React + Vite Frontend
                       |
                       v
                FastAPI Backend
                       |
          +------------+------------+
          |            |            |
          v            v            v
      Flood Engine  Drought Engine  Unified Risk
          |            |            |
          v            v            v
      XGBoost       SPI-3 Data    Risk Assessment
      Classifier    Processing
          |            |            |
          +------------+------------+
                       |
                       v
             Processed Risk Outputs
                       |
                       v
              Interactive Dashboard
```

## Technology Stack

| Category | Technologies |
|---|---|
| Frontend | React.js, Vite, JavaScript |
| Backend | Python, FastAPI |
| Machine Learning | XGBoost |
| Data Processing | Pandas, NumPy |
| Model Serialization | Joblib |
| Drought Assessment | Standardized Precipitation Index (SPI-3) |
| Visualization | Interactive maps, charts |
| API Communication | REST APIs |
| Deployment | Render |
| Version Control | Git, GitHub |

## API Endpoints

| Endpoint | Description |
|---|---|
| `/health` | Checks backend health |
| `/api/risk/latest` | Retrieves latest unified risk information |
| `/api/flood/latest` | Retrieves latest flood assessment |
| `/api/drought/latest` | Retrieves latest drought assessment |

## Dashboard Screenshots

### 1. AquaSentinel Overview
![AquaSentinel Overview](./Aqua_overview.png)

### 2. Gujarat District Map
![Gujarat Map](./Aqua_gujaratMap.png)

### 3. Risk and Drought Intelligence
![Risk and Drought Intelligence](./Aqua_risk_and_drought_intelligence.png)

### 4. District-Wise Drought Status
![District Drought Status](./district_drought_status.png)

### 5. Risk Monitoring
![Risk Monitoring](./risk_monitoring.png)

## Local Installation and Setup

### Prerequisites
- Python 3.10+
- Node.js and npm
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/harshitarocks07-debug/AquaSentinel.git
cd AquaSentinel
```

### 2. Set Up the Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Backend API:

`http://127.0.0.1:8000`

API Documentation:

`http://127.0.0.1:8000/docs`

### 3. Set Up the Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend development server will be available at the URL displayed in the terminal.

## Deployment

AquaSentinel is deployed on Render as a web service.

**Live Application:** https://aquasentinel-fwbv.onrender.com

The deployment serves the React frontend and FastAPI backend through a single application URL.

## Limitations

- Predictions depend on the quality and availability of historical rainfall data.
- Model performance on test data does not guarantee real-world forecasting accuracy.
- SPI-based drought assessment is dependent on precipitation data and does not independently measure soil moisture or groundwater availability.
- The platform currently focuses on Gujarat rather than nationwide coverage.
- Early warnings should be interpreted as decision-support information, not official disaster alerts.
- Live performance may be affected by free-tier hosting limitations.

## Future Roadmap

- Integrate real-time meteorological data sources.
- Improve flood forecasting with additional environmental variables.
- Add district-level drought trend analysis.
- Introduce automated alerts and notifications.
- Incorporate satellite imagery and remote-sensing data.
- Expand coverage to additional Indian states.
- Improve model evaluation using additional validation datasets.
- Develop a mobile-friendly monitoring experience.

## Project Significance

AquaSentinel aims to make climate-risk information more accessible and interpretable through machine learning, geospatial analysis, and environmental indicators.

By bringing flood prediction and drought assessment together, the platform can support researchers, administrators, and communities in understanding regional climate risks and making more informed decisions.

---

**AquaSentinel — Turning Environmental Data into Climate-Risk Intelligence.**
