
# 🏘️ Avito Real Estate ETL Pipeline

An automated end-to-end data pipeline designed to scrape, clean, and warehouse real estate data from Avito.ma. This project leverages **Selenium** for dynamic web scraping, **PostgreSQL** for data warehousing, and **Docker** for seamless orchestration.

## 🚀 Overview

The pipeline automates the following stages:

1. **Scraping** : Extracting property listings (Appartements, Maisons, etc.) using Selenium.
2. **Staging** : Loading raw text data into a PostgreSQL staging area.
3. **Cleaning** : Utilizing SQL procedures to parse relative dates (e.g., "il y a 2 heures"), clean currency strings, and handle missing values.
4. **Warehousing** : Moving validated data into a structured production schema.
5. **Reporting** : Exporting final cleaned datasets to CSV for analysis.

---

## 🏗️ Project Structure

**Plaintext**

```
avito-realestate-pipeline/
├── data/               # CSV exports (rawdata.csv, clean_data.csv)
├── db_init/            # SQL logic (init, cleaning, warehouse, purge)
├── logs/               # Pipeline execution logs
├── scraper/            # Selenium scraper logic (main.py, helpers.py)
├── utils/              # Shared utilities (logger.py)
├── docker-compose.yml  # Docker services orchestration
├── Dockerfile          # Python environment containerization
├── run_pipeline.py     # Main entry point for the ETL process
└── requirements.txt    # Python dependencies
```

---

## 🛠️ Tech Stack

* **Language:** Python 3.9+
* **Libraries:** Pandas, SQLAlchemy, Selenium, Selenium-wire
* **Database:** PostgreSQL 15
* **Infrastructure:** Docker, Docker Compose

---

## ⚙️ Setup & Installation

### 1. Environment Configuration

Create a `.env` file in the root directory with your database credentials:

**Code snippet**

```
DATABASE_URL=postgresql://user:password@db:5432/avito_db
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=avito_db
```

### 2. Install Requirements

If you are running the scraper locally (outside of Docker) for testing, set up a virtual environment and install the dependencies:

**Bash**

```
# Create a virtual environment
python -m venv .venv

# Activate the environment (Windows)
.venv\Scripts\activate

# Activate the environment (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Running with Docker

To launch the database and the automated pipeline together:

**Bash**

```
docker-compose up --build
```

---

## 📊 The Data Pipeline

### Step 1: Raw Extraction

The scraper navigates multiple categories on Avito, capturing raw card text and listing URLs. It handles anti-bot measures through randomized delays and targeted XPATH selection for dynamic elements like "time posted."

### Step 2: SQL Transformation

Data is processed through `cleaning.sql`, which:

* Converts relative French time strings into actual `DATE` objects.
* Extracts numerical values from price strings (removing "DH" and whitespace).
* Filters out duplicate entries using unique listing IDs.

### Step 3: Persistence

* **PostgreSQL** : Data is stored in a multi-layered schema (`staging` -> `bi_schema`).
* **CSV** : A copy of the cleaned data is saved to `data/clean_data.csv` for use in BI tools.

---

## 📝 Monitoring

Monitor the pipeline's health in real-time:

**Bash**

```
docker logs -f avito-realestate
```

All events are also logged in `logs/pipeline.log`.
