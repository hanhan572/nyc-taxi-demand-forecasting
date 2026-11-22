
# NYC Taxi Demand Forecasting & AI Driver Assistant

## 1. Project Overview

This project is developed as the final project for IDS706 at Duke University.

Our goal is to build an end-to-end data engineering and machine learning platform that analyzes historical NYC taxi trips, forecasts hourly taxi demand across different areas, and provides AI-powered insights for taxi drivers.

The platform integrates data ingestion, data storage, transformation, SQL querying, machine learning, workflow orchestration, and interactive visualization.

## 2. Project Objectives

- Ingest real-world NYC taxi trip data from multiple sources.
- Clean and transform large datasets using Polars.
- Store structured data and forecasting results in PostgreSQL.
- Analyze taxi demand patterns using SQL.
- Develop baseline and XGBoost models for hourly taxi demand forecasting.
- Automate data workflows using Apache Airflow.
- Build an interactive dashboard using Streamlit.
- Develop an LLM-powered driver assistant using function calling.
- Ensure reproducibility using Docker, GitHub Actions, and pytest.

## 3. Data Sources

### NYC TLC Trip Record Data

https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page

Historical Yellow Taxi trip records containing pickup/drop-off times, taxi zone IDs, trip distances, and fare information.

We plan to use approximately three months of data from 2025.

### NYC Taxi Zone Lookup

https://data.cityofnewyork.us/Transportation/NYC-Taxi-Zones/8meu-9t5y/about_data

Geographic reference data containing taxi zone IDs, boroughs, and zone names.

## 4. Technology Stack

| Component | Technology |
|---|---|
| Programming | Python |
| Data Ingestion | Python, Parquet |
| Data Transformation | Polars |
| Data Storage | PostgreSQL |
| Data Querying | SQL |
| Machine Learning | scikit-learn, XGBoost |
| Orchestration | Apache Airflow |
| LLM Assistant | OpenAI API, Function Calling |
| Dashboard | Streamlit |
| Containerization | Docker |
| CI/CD | GitHub Actions |
| Testing | pytest |
| Collaboration | Git, GitHub |

## 5. Team Members and Responsibilities

| Team Member | Primary Responsibility |
|---|---|
| Evelyn Wang | Data Ingestion, Transformation, Airflow |
| Haoran Wang | PostgreSQL Database, Schema, ERD, SQL |
| Steven Xu | Machine Learning, Baseline, XGBoost |
| Royce Zhang | LLM Assistant, Function Calling |
| Haoyan Zhong | Streamlit Dashboard, Docker, CI/CD |

All members contribute to testing, documentation, and integration.

## 6. Planned Architecture

1. Data Sources: NYC Taxi Trips and Taxi Zone Lookup
2. Data Ingestion: Python
3. Data Transformation: Polars
4. Data Storage: PostgreSQL
5. Analysis and Querying: SQL
6. Machine Learning: Baseline and XGBoost
7. AI Assistant: LLM with Function Calling
8. Visualization: Streamlit

Apache Airflow will orchestrate pipeline tasks.

Docker, GitHub Actions, and pytest will support reproducibility, continuous integration, and reliability.

A detailed architecture diagram will be added in the docs directory.

## 7. Repository Structure

```text
nyc-taxi-demand-forecasting/
├── data/
├── src/
│   ├── ingestion/
│   ├── transformation/
│   ├── database/
│   ├── forecasting/
│   ├── assistant/
│   └── dashboard/
├── sql/
├── dags/
├── tests/
├── docs/
├── .github/workflows/
├── requirements.txt
├── .gitignore
└── README.md
```

## 8. Project Timeline

| Week | Dates | Goals |
|---|---|---|
| Week 1 | Nov 16–22 | Project setup, architecture, data preparation, initial implementation |
| Week 2 | Nov 23–29 | Core pipeline implementation and integration |
| Week 3 | Nov 30–Dec 4 | Testing, documentation, video, final submission |

## 9. Setup Instructions

The project is under active development.

Initial environment setup:

```bash
git clone <repository-url>
cd nyc-taxi-demand-forecasting

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

Detailed component-specific run instructions will be added as the implementation progresses.

## 10. Data Engineering Principles

The project aims to demonstrate:

- Scalability through efficient columnar processing and modular pipeline stages.
- Modularity through separation of ingestion, transformation, storage, forecasting, and application layers.
- Reusability through reusable Python modules and SQL scripts.
- Reliability through automated testing and orchestration.
- Observability through workflow logs and data validation.
- Security through environment variables and excluded credentials.
- Data governance through documented schemas and data sources.
- Efficiency through aggregated analytical storage and optimized transformations.

Implementation-specific evidence will be added as development progresses.

## 11. Project Status

Initial project setup and development in progress.
