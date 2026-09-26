# 🛰️ Gagandristhi V2 (गगनदृष्टि)
### Next-Generation Geospatial Intelligence, Multi-Temporal Satellite Change Detection & Real-Time Event Streaming Platform

[![PostgreSQL](https://img.shields.io/badge/PostGIS-16--3.4-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgis.net/)
[![Apache Kafka](https://img.shields.io/badge/Apache_Kafka-4.1.0_KRaft-231F20?style=for-the-badge&logo=apachekafka&logoColor=white)](https://kafka.apache.org/)
[![Debezium](https://img.shields.io/badge/Debezium_CDC-2.6.1-red?style=for-the-badge&logo=apache&logoColor=white)](https://debezium.io/)
[![Redis](https://img.shields.io/badge/Redis-7.0-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![PyTorch](https://img.shields.io/badge/PyTorch-CUDA_Accelerated-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Node.js](https://img.shields.io/badge/Node.js-Express_5-339933?style=for-the-badge&logo=nodedotjs&logoColor=white)](https://nodejs.org/)
[![Vue.js](https://img.shields.io/badge/Vue_3-Vite_7-4FC08D?style=for-the-badge&logo=vuedotjs&logoColor=white)](https://vuejs.org/)

---

## 📌 Executive Overview

**Gagandristhi V2** is an enterprise-grade Earth Observation (EO) and Geospatial Intelligence (GEOINT) surveillance system developed for automated satellite change detection, tactical anomaly recognition, semantic imagery retrieval, and mission-critical alerting.

The platform integrates deep learning computer vision, multi-spectral remote sensing indices, real-time distributed change data capture (CDC), and an interactive military-grade analyst dashboard.

---

## 🏗️ System Architecture

```
               [ SATELLITE IMAGERY (T1 & T2) ]
             (GeoTIFF / COG / JPEG / PNG Multi-Band)
                                │
                                ▼
         ┌──────────────────────────────────────────────┐
         │     PYTHON FASTAPI ML ENGINE (Port 8000)      │
         │  ├─ Siamese U-Net (LEVIR-CD Building DL)     │
         │  ├─ Multi-Spectral NDVI / VARI Engine         │
         │  ├─ Change Vector Analysis (CVA Pixel Diff)  │
         │  ├─ OpenAI CLIP ViT-B/32 Semantic Retrieval  │
         │  └─ GDAL / Rasterio Georeferencing Pipeline  │
         └──────────────────────┬───────────────────────┘
                                │
                                ▼
         ┌──────────────────────────────────────────────┐
         │        POSTGRESQL 16 + POSTGIS 3.4           │
         │  ├─ Database: garuda                         │
         │  ├─ Geospatial AOI Polygon Storage           │
         │  └─ Logical Replication (WAL level: logical) │
         └──────────────────────┬───────────────────────┘
                                │ (Write-Ahead Log CDC)
                                ▼
         ┌──────────────────────────────────────────────┐
         │     DEBEZIUM CONNECTOR (Kafka Connect)       │
         │  └─ Port: 8083 | Topic Prefix: garuda_cdc    │
         └──────────────────────┬───────────────────────┘
                                │ (CDC Event JSON)
                                ▼
         ┌──────────────────────────────────────────────┐
         │        APACHE KAFKA BROKER (Port 9092)       │
         │  └─ Topic: garuda_cdc.public.alerts          │
         └──────────────────────┬───────────────────────┘
                                │ (Subscribed Consumer)
                                ▼
         ┌──────────────────────────────────────────────┐
         │       NODE.JS EXPRESS BACKEND (Port 3000)    │
         │  ├─ Kafka Event Consumer & De-duplicator     │
         │  ├─ Redis 7 In-Memory Cache (Port 6379)      │
         │  ├─ Analyst Review & Audit Trail Manager     │
         │  └─ Server-Sent Events (SSE) Broadcast       │
         └──────────────────────┬───────────────────────┘
                                │ (Real-Time SSE Stream)
                                ▼
         ┌──────────────────────────────────────────────┐
         │          VUE 3 FRONTEND (Port 5173)          │
         │  ├─ Interactive Leaflet GIS Map              │
         │  ├─ Multi-Model Change Detection Studio      │
         │  ├─ GeoTIFF Tactical AOI Bounding Visualizer │
         │  ├─ CLIP Natural Language & Visual Search    │
         │  └─ Military SITREP Dossier Generator        │
         └──────────────────────────────────────────────┘
```

---

## 🚀 Key Capabilities & Features

### 1. Multi-Model Analytical Change Detection
The processing engine provides three specialized, independent analytical channels tailored to specific intelligence requirements:

| Channel Key | Channel Name | Core Model / Algorithm | Primary Use Case |
|---|---|---|---|
| `STRUCTURAL_DL` | **Structural Infrastructure** | PyTorch Siamese U-Net (Pretrained on LEVIR-CD) | Detection of newly erected or demolished man-made structures, fortifications, buildings, roads, and walls while ignoring seasonal ground reflectance changes. |
| `VEGETATION_NDVI` | **Vegetation & Forest Clearance** | True 4-Band NIR NDVI / RGB VARI Multi-Temporal Index | Quantitative biomass shifting, deforestation, perimeter clearing, and distinguishing intentional clearance from seasonal vegetative regrowth. |
| `PIXEL_DIFFERENCE` | **Tactical Surface Disturbance** | Radiometric Change Vector Analysis (CVA) + Adaptive Morphological Filtering | Sensitive detection of ground anomalies: temporary vehicle convoys, fresh unpaved tracks, earth excavation, and military tent pitching. |

### 2. Native Multi-Spectral GeoTIFF & COG Ingestion (PS 2.2.6)
* **High Dynamic Range (16-bit / Multi-band)**: Automatic 2nd-to-98th percentile contrast stretching for visualization while preserving raw radiometry for analytical calculations.
* **Georeferencing & Projections**: Native reading of CRS, Affine geotransforms, and automatic reprojection between projected coordinate reference systems (e.g., UTM Zone 43N / EPSG:32643) and WGS84 GPS latitude/longitude.
* **Map Focus & Tactical AOI**: One-click **"Focus Map on GeoTIFF Bounds"** dynamically centers the Leaflet map onto the satellite scene's exact real-world footprint and displays an amber tactical AOI box with GPS corner coordinates.

### 3. Semantic & Multimodal Retrieval Engine (PS 2.2.1)
* **Zero-Shot Natural Language Search**: Free-text prompt retrieval (e.g., *"military convoy on highway"*, *"industrial fuel depot"*, *"airfield with aircraft"*) using OpenAI CLIP ViT-B/32 multi-modal vision-language embeddings.
* **Query-by-Example Visual Similarity**: Upload any reference tile or drone snippet to discover all visually and semantically related satellite scenes ranked by cosine similarity.

### 4. Human-in-the-Loop Analyst Verification & Military SITREP Dossier (PS 2.2.5)
* **Analyst Review Workflow**: Triage detected alerts into `CONFIRMED`, `FALSE_ALARM`, `INVESTIGATING`, or `REJECTED` with confidence ratings and analyst audit logs.
* **Operational Dossier Export**: Generate and download structured Military Situation Reports (`SITREP`) containing AOI bounds, model severity, timestamps, analyst sign-offs, and geographic coordinates.

### 5. Real-Time Event-Driven Streaming Pipeline
* Instant propagation of satellite alerts from PostGIS table writes through **Debezium CDC** into **Apache Kafka**, consumed by **Node.js**, cached in **Redis**, and pushed to all active analyst browser screens via **Server-Sent Events (SSE)** with zero polling latency.

---

## 🔌 System Ports & Endpoints

| Component | Technology | Default Port | Internal / Public URL |
|---|---|---|---|
| **Frontend** | Vue 3 + Vite 7 + Leaflet | `5173` | `http://localhost:5173` |
| **Backend API** | Node.js Express 5 | `3000` | `http://localhost:3000` |
| **Processing API** | Python FastAPI + PyTorch | `8000` | `http://localhost:8000` |
| **PostgreSQL + PostGIS** | Docker (`postgis/postgis:16-3.4`) | `5432` | `localhost:5432` (DB: `garuda`) |
| **Apache Kafka** | Docker (`apache/kafka:4.1.0`) | `9092` | `localhost:9092` |
| **Debezium Connect** | Docker (`debezium/connect:2.6.1.Final`) | `8083` | `http://localhost:8083` |
| **Redis** | Docker (`redis:7`) | `6379` | `localhost:6379` |

---

## 📋 Prerequisites

Before setting up the project, ensure your workstation has the following installed:

1. **Docker Desktop** (with Docker Compose enabled)
2. **Node.js** (v20.x or v22.x LTS) & **npm** (v10.x+)
3. **Python** (v3.10, v3.11, or v3.12)
4. **Git**
5. *(Optional but recommended)*: NVIDIA GPU with **CUDA 11.8 / 12.x** for accelerated deep learning inference. CPU execution is also supported automatically.

---

## ⚡ 1-Click Automated Quick Start (Recommended)

If you are on Windows, we provide automated batch scripts that handle Docker setup, database restoration, Debezium connector registration, and server launching in one click!

### Step 1: One-Time Automated Setup
Clone the repository and run the setup wizard:
```bash
git clone https://github.com/<your-username>/Gagandristhi-V2.git
cd Gagandristhi-V2
git lfs pull  # Pulls the PyTorch model weights (>100MB) via Git LFS
```
Double-click **`setup.bat`** (or run `.\setup.bat` in PowerShell / Terminal).  
*(On Linux/macOS, run `chmod +x setup.sh start.sh && ./setup.sh`)*

This script automatically:
* Starts Docker containers (PostgreSQL PostGIS, Apache Kafka, Debezium, Redis).
* Restores the database schema (`schema.sql`) and seeds the 3 AI models (`seed_channels.sql`).
* Configures the Debezium CDC real-time alert connector.
* Installs all Node.js and Python dependencies.

---

### Step 2: Daily 1-Click Launch
Whenever you want to run the platform, simply double-click **`start.bat`** (or `./start.sh` on Linux/macOS).

This automatically:
* Ensures Docker containers are active.
* Launches the **Python AI Engine** on `http://localhost:8000`.
* Launches the **Node.js Backend** on `http://localhost:3000`.
* Launches the **Vue 3 Frontend** on `http://localhost:5173`.
* Automatically opens your default web browser to the dashboard!

To stop all services cleanly, run **`stop.bat`**.

---

## 🛠️ Manual Step-by-Step Installation (Alternative)

If you prefer running each component manually step-by-step instead of using the automated scripts:

### Step 1: Start Infrastructure Containers (Docker)

You can launch all required infrastructure services (PostGIS, Kafka, Debezium, Redis) using **either** Docker Compose (Recommended) **or** manual Docker CLI commands.

#### Option A: Using Docker Compose (Recommended)
From the root directory of the repository:
```bash
docker compose up -d
```

#### Option B: Using Individual Docker CLI Commands
```powershell
# 1. Create dedicated bridge network
docker network create gagandristhi-network

# 2. Launch PostgreSQL with PostGIS and Logical Replication enabled
docker run -d --name gagandristhi-postgres --network gagandristhi-network -p 5432:5432 `
  -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=Minar@123 -e POSTGRES_DB=garuda `
  postgis/postgis:16-3.4 `
  postgres -c wal_level=logical -c max_wal_senders=10 -c max_replication_slots=10

# 3. Launch Apache Kafka (KRaft mode)
docker run -d --name gagandristhi-kafka --network gagandristhi-network -p 9092:9092 `
  -e KAFKA_NODE_ID=1 -e KAFKA_PROCESS_ROLES=broker,controller `
  -e KAFKA_LISTENERS=INTERNAL://0.0.0.0:29092,EXTERNAL://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093 `
  -e KAFKA_ADVERTISED_LISTENERS=INTERNAL://gagandristhi-kafka:29092,EXTERNAL://localhost:9092 `
  -e KAFKA_CONTROLLER_QUORUM_VOTERS=1@gagandristhi-kafka:9093 `
  -e KAFKA_CONTROLLER_LISTENER_NAMES=CONTROLLER `
  -e KAFKA_INTER_BROKER_LISTENER_NAME=INTERNAL `
  -e KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=INTERNAL:PLAINTEXT,EXTERNAL:PLAINTEXT,CONTROLLER:PLAINTEXT `
  -e KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 `
  -e KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR=1 `
  -e KAFKA_TRANSACTION_STATE_LOG_MIN_ISR=1 `
  apache/kafka:4.1.0

# 4. Launch Debezium Kafka Connect
docker run -d --name gagandristhi-debezium --network gagandristhi-network -p 8083:8083 `
  -e BOOTSTRAP_SERVERS=gagandristhi-kafka:29092 `
  -e GROUP_ID=1 `
  -e CONFIG_STORAGE_TOPIC=debezium_configs `
  -e OFFSET_STORAGE_TOPIC=debezium_offsets `
  -e STATUS_STORAGE_TOPIC=debezium_statuses `
  -e KEY_CONVERTER=org.apache.kafka.connect.json.JsonConverter `
  -e VALUE_CONVERTER=org.apache.kafka.connect.json.JsonConverter `
  debezium/connect:2.6.1.Final

# 5. Launch Redis
docker run -d --name gagandristhi-redis --network gagandristhi-network -p 6379:6379 redis:7
```

*Verify all 4 containers are healthy:*
```bash
docker ps
```

---

### Step 3: Initialize Database Schema & Seed Data

Load the database tables, PostGIS extensions, and seed data into PostgreSQL:

```powershell
# Load base schema into the 'garuda' database
docker exec -i gagandristhi-postgres psql -U postgres -d garuda < Backend/schema.sql

# Seed the 3 satellite analytical models
docker exec -i gagandristhi-postgres psql -U postgres -d garuda < Backend/seed_channels.sql

# Create the analyst human-in-the-loop audit review table
docker exec -i gagandristhi-postgres psql -U postgres -d garuda < Backend/create_alert_reviews.sql
```

*(On Linux / macOS bash, the same commands apply with standard `<` redirection).*

---

### Step 4: Register Debezium CDC Connector

Once Debezium is running (give it ~15–20 seconds after container start to initialize), register the PostgreSQL CDC connector:

#### On Windows (PowerShell):
```powershell
Invoke-RestMethod -Uri "http://localhost:8083/connectors" -Method Post -ContentType "application/json" -Body '{
  "name": "gagandristhi-alerts-connector",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "tasks.max": "1",
    "plugin.name": "pgoutput",
    "database.hostname": "gagandristhi-postgres",
    "database.port": "5432",
    "database.user": "postgres",
    "database.password": "Minar@123",
    "database.dbname": "garuda",
    "database.server.name": "garuda_server",
    "topic.prefix": "garuda_cdc",
    "table.include.list": "public.alerts",
    "publication.name": "dbz_publication",
    "publication.autocreate.mode": "filtered",
    "schema.history.internal.kafka.bootstrap.servers": "gagandristhi-kafka:29092",
    "schema.history.internal.kafka.topic": "schema-changes.garuda"
  }
}'
```

#### On Linux / macOS (Bash / cURL):
```bash
curl -X POST http://localhost:8083/connectors \
  -H "Content-Type: application/json" \
  -d '{
    "name": "gagandristhi-alerts-connector",
    "config": {
      "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
      "tasks.max": "1",
      "plugin.name": "pgoutput",
      "database.hostname": "gagandristhi-postgres",
      "database.port": "5432",
      "database.user": "postgres",
      "database.password": "Minar@123",
      "database.dbname": "garuda",
      "database.server.name": "garuda_server",
      "topic.prefix": "garuda_cdc",
      "table.include.list": "public.alerts",
      "publication.name": "dbz_publication",
      "publication.autocreate.mode": "filtered",
      "schema.history.internal.kafka.bootstrap.servers": "gagandristhi-kafka:29092",
      "schema.history.internal.kafka.topic": "schema-changes.garuda"
    }
  }'
```

*Verify connector status:*
```bash
curl http://localhost:8083/connectors/gagandristhi-alerts-connector/status
```

---

### Step 5: Start the Python Processing Microservice

Open a new terminal window:

```bash
cd processing

# (Optional) Create and activate a virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server on port 8000
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

*Verify by opening:* `http://localhost:8000/docs` (Interactive Swagger UI).

---

### Step 6: Start the Node.js Express Backend

Open a new terminal window:

```bash
cd Backend

# Verify environment file exists (copy template if needed)
# Windows:
copy .env.example .env
# Linux/macOS:
# cp .env.example .env

# Install dependencies
npm install

# Start backend server on port 3000
npm run dev
```

*Verify console shows:*
```
Database Pool Initialized.
Connected to Kafka broker.
Connected to Redis cache.
Backend listening on port 3000.
```

---

### Step 7: Start the Vue 3 Frontend Dashboard

Open a new terminal window:

```bash
cd Frontend

# Install dependencies
npm install

# Start Vite dev server on port 5173
npm run dev
```

*Open your browser and navigate to:* **`http://localhost:5173`** 🚀

---

## 🧪 Verification & Automated Tests

To verify that the AI models, vegetation analysis, pixel difference, and GeoTIFF georeferencing pipeline are 100% operational on your machine, run the automated test harnesses:

### 1. Test All 3 Change Detection Channels:
```bash
python processing/test_all_channels.py
```
*Expected Output:*
```
============================================================
 GAGANDRISTHI V2: MULTI-CHANNEL MODEL TEST HARNESS
============================================================
[TESTING] Channel: STRUCTURAL...
  [OK] Model: PyTorch Siamese U-Net (LEVIR-CD)
  [OK] Change Detected: True
[TESTING] Channel: VEGETATION...
  [OK] Model: Multi-Temporal Vegetation Index (NDVI/VARI)
  [OK] Loss (Clearance): 3.79% | Gain (Regrowth): 3.65%
[TESTING] Channel: PIXEL_DIFF...
  [OK] Model: Radiometric Change Vector Analysis (CVA)
  [OK] Change Area: 10.36%
============================================================
 ALL 3 CHANNELS TESTED SUCCESSFULLY WITH ZERO ERRORS!
============================================================
```

### 2. Test Multi-Band GeoTIFF Georeferencing & Projections:
```bash
python processing/test_geotiff.py
```
*Expected Output:*
```
=================================================================
 GAGANDRISTHI V2: GEOTIFF INGESTION & COORDINATE TEST HARNESS
=================================================================
--- 1. METADATA EXTRACTION ---
EPSG Code:       32643
Resolution:      10.0 meters
WGS84 Bounds:    [77.087, 28.618, 77.113, 28.641]
--- 2. VEGETATION_NDVI (TRUE 4-BAND NIR) ---
--- 3. STRUCTURAL_DL (SIAMESE U-NET ON GEOTIFF) ---
--- 4. PIXEL_DIFFERENCE (CVA ON GEOTIFF) ---
--- 5. REGRESSION TEST: STANDARD JPG IMAGES ---
=================================================================
 ALL GEOTIFF & BACKWARD-COMPATIBILITY TESTS PASSED SUCCESSFULLY!
=================================================================
```

---

## 📂 Project Directory Structure

```
Gagandristhi V2/
├── docker-compose.yml              # Single-command infrastructure orchestration
├── .gitignore                      # Git exclusion rules
├── README.md                       # Comprehensive setup and documentation
│
├── Backend/                        # Node.js Express 5 Backend
│   ├── .env.example                # Environment variables template
│   ├── package.json                # Node dependencies and scripts
│   ├── schema.sql                  # Full PostGIS database schema dump
│   ├── seed_channels.sql           # Channel catalog migration (3 analytical models)
│   ├── create_alert_reviews.sql    # Analyst human-in-the-loop review table
│   └── src/
│       ├── App.js                  # Express application setup
│       ├── server.js               # Entry point
│       ├── controllers/            # Auth, Alerts, Projects, Processing controllers
│       ├── db/                     # DBClient pool singleton
│       ├── models/                 # PostgreSQL model classes
│       └── services/               # Kafka consumer, Redis cache, SSE publisher
│
├── Frontend/                       # Vue 3 + Vite 7 SPA Dashboard
│   ├── package.json                # Frontend dependencies
│   ├── vite.config.js              # Vite configuration with TailwindCSS
│   └── src/
│       ├── App.vue                 # Root view
│       ├── components/
│       │   ├── Map/
│       │   │   └── MonitorMapView.vue      # Leaflet map, layers, real-time markers
│       │   ├── processing/
│       │   │   └── ChangeDetectionPanel.vue # Change detection studio & GeoTIFF bounds
│       │   ├── retrieval/
│       │   │   └── SemanticRetrievalPanel.vue # CLIP text & image visual search
│       │   ├── AoiVizPanel.vue             # AOI bounding manager
│       │   └── AlertReviewModal.vue        # Human-in-the-loop analyst review
│       └── services/                       # API clients & SSE connection manager
│
└── processing/                     # Python FastAPI AI / ML Microservice
    ├── requirements.txt            # Python dependencies
    ├── api/
    │   └── main.py                 # FastAPI application & REST endpoints
    ├── service/
    │   └── processor.py            # Master change processing coordinator
    ├── inference/
    │   ├── predict.py              # PyTorch Siamese U-Net inference engine
    │   ├── vegetation_analysis.py  # Multi-temporal NDVI / VARI remote sensing
    │   ├── pixel_diff_analysis.py  # Radiometric Change Vector Analysis (CVA)
    │   ├── geotiff_handler.py      # GDAL/Rasterio GeoTIFF & CRS projection pipeline
    │   └── semantic_retrieval.py   # OpenAI CLIP ViT-B/32 multimodal search
    ├── models/
    │   └── siamese_unet.py         # Siamese U-Net neural network architecture
    ├── weights/
    │   └── siamese_unet_levir_cd.pth # Pretrained model weights (LEVIR-CD)
    ├── test_images/                # Sample reference pairs (T1, T2)
    ├── test_all_channels.py        # Multi-model test harness
    └── test_geotiff.py             # GeoTIFF ingestion & projection test harness
```

---

## 📡 REST API Reference

### 1. Multi-Model Change Detection
* **`POST /process`**
  * **Content-Type**: `multipart/form-data`
  * **Parameters**:
    * `t1`: File (Baseline satellite image / GeoTIFF)
    * `t2`: File (Target satellite image / GeoTIFF)
    * `channel_type`: String (`structural` | `vegetation` | `pixel_diff`)
  * **Response**:
    ```json
    {
      "model": "Siamese U-Net (LEVIR-CD)",
      "channel_type": "structural",
      "result_id": "9a7f...",
      "output_mask": "http://localhost:8000/results/9a7f.../mask",
      "overlay_image": "http://localhost:8000/results/9a7f.../overlay",
      "change_detection": {
        "change_detected": true,
        "change_percentage": 4.12,
        "number_of_regions": 12,
        "severity": "HIGH",
        "regions": [...]
      },
      "geotiff_metadata": {
        "is_geotiff": true,
        "epsg": 32643,
        "wgs84_bounds": [77.087, 28.618, 77.113, 28.641],
        "center_gps": [28.6295, 77.1001]
      }
    }
    ```

### 2. Semantic & Multimodal Retrieval
* **`POST /retrieve/text`**: Zero-shot natural language query over satellite catalog.
  * **Body**: `{"query": "military vehicles parked on open airfield", "top_k": 5}`
* **`POST /retrieve/image`**: Reverse visual similarity search using uploaded tile.
  * **Form Data**: `query_image`: File, `top_k`: 5
* **`GET /retrieve/catalog`**: List all indexed satellite scenes with geospatial coordinates.

### 3. Analyst Review & Military SITREP Dossier
* **`POST /api/alerts/:id/reviews`**: Submit analyst review (`CONFIRMED`, `FALSE_ALARM`, `INVESTIGATING`, `REJECTED`).
* **`GET /api/alerts/:id/reviews`**: Fetch full chronological audit trail of human reviews for an alert.

---

## ❓ Troubleshooting & Frequently Asked Questions

### 1. "Debezium connector returns 500 or cannot connect to PostgreSQL"
* Ensure PostgreSQL was started with logical decoding enabled (`-c wal_level=logical -c max_wal_senders=10 -c max_replication_slots=10`).
* Verify that the database `garuda` exists and that `Backend/schema.sql` was executed.
* Check that Kafka and PostgreSQL are on the same Docker network (`gagandristhi-network`).

### 2. "Rasterio or GDAL installation fails on Windows"
* If `pip install -r requirements.txt` fails compiling Rasterio from source on Windows, install the precompiled binary wheel using:
  ```bash
  pip install --only-binary :all: rasterio
  ```

### 3. "CUDA out of memory or no NVIDIA GPU detected"
* Gagandristhi V2 automatically detects GPU availability via `torch.cuda.is_available()`. If no CUDA-capable GPU is found, it automatically falls back to CPU execution without any crashes.

---

## 📜 Problem Statement Alignment
* **Hackathon**: Smart India Hackathon (SIH)
* **Problem Statement ID**: 26227
* **Organization**: Government of India / Defence & Earth Observation Agencies
* **Focus Areas**: Automated Multi-Temporal Satellite Change Detection, Multi-Sensor Fusion (Sentinel-2, Landsat, ISRO Bhuvan), Real-Time Tactical Geospatial Alerting, Zero-Shot Semantic Scene Retrieval, Analyst Human-in-the-Loop Mission Dossiers.

---

## 👨‍💻 Contributing & License
Developed for advanced satellite intelligence research and hackathon demonstration.  
Licensed under the **MIT License**.
