# Sales Analytics Dashboard (ETL and BI Project)

Live Demo:  
https://sales-dashboard-dolly.streamlit.app/

---

## Project Overview

This project demonstrates an end-to-end analytics pipeline, including data ingestion, transformation, storage, and visualization.

The workflow simulates a production-style analytics engineering process using Python, SQL, and PostgreSQL.

---

## Architecture

```
Source Data (CSV / API)
        ↓
Python ETL
        ↓
PostgreSQL (raw_sales)
        ↓
SQL Transformation
        ↓
PostgreSQL (clean_sales)
        ↓
Export to CSV
        ↓
Streamlit Dashboard
```

---

## Technology Stack

- Python (Pandas, SQLAlchemy)
- PostgreSQL
- SQL
- Streamlit
- Git
- Streamlit Community Cloud

---

## ETL Pipeline

### Extract
- Ingest raw sales data from CSV or API sources.

### Load (Raw Layer)
- Load unprocessed data into the `raw_sales` table.

### Transform (Clean Layer)
- Apply data validation and cleaning rules using SQL.
- Handle missing values and inconsistent formats.
- Generate derived metrics such as revenue.

### Load (Analytics Layer)
- Store transformed data in the `clean_sales` table.

### Publish
- Export clean data to CSV.
- Serve analytics dashboard using Streamlit.

---

## Dashboard Features

- Order count
- Total revenue
- Average order value
- Revenue by product category
- Tabular data preview

---

## Local Setup

### Clone the Repository

```bash
git clone https://github.com/dollyca/sales-dashboard.git
cd sales-dashboard
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run the Application

```bash
streamlit run app.py
```

---

## Project Structure

```
sales-dashboard/
│
├── app.py
├── clean_sales.csv
├── requirements.txt
└── README.md
```

---

## Learning Outcomes

- Designed reproducible ETL pipelines
- Implemented layered data architecture
- Performed SQL-based transformations
- Built and deployed cloud-based dashboards
- Integrated data engineering and BI workflows

---

## Future Enhancements

- Connect dashboard to cloud-hosted PostgreSQL
- Implement automated scheduling with Airflow
- Support incremental data loading
- Improve data quality monitoring
- Add advanced analytical visualizations

---

## Author

Dolly Wu  
GitHub: https://github.com/dollyca
