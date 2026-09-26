# 🚀 Garuda V1 Real-Time Alert System
## Complete Setup & Installation Guide

**Version:** 1.0  
**Last Updated:** December 2025  
**Architecture:** CDC Pipeline with Kafka KRaft + Debezium + PostgreSQL + Redis

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [System Requirements](#system-requirements)
3. [Pre-Installation Checks](#pre-installation-checks)
4. [PostgreSQL Setup](#postgresql-setup)
5. [Kafka & Debezium Configuration](#kafka-debezium-configuration)
6. [Redis Installation](#redis-installation)
7. [Application Setup](#application-setup)
8. [Running the System](#running-the-system)
9. [Verification & Testing](#verification-testing)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

Garuda V1 is a real-time alert system built on Change Data Capture (CDC) architecture. It monitors PostgreSQL database changes and delivers instant notifications through a Vue.js frontend.

**Key Components:**
- **PostgreSQL 16** with logical replication
- **Apache Kafka 4.1.0** in KRaft mode (no Zookeeper)
- **Debezium 2.6.1** for CDC
- **Redis** for caching and session management
- **Node.js Backend** with Express and KafkaJS
- **Vue.js Frontend** with Vite

**Architecture Flow:**
```
PostgreSQL (Logical Replication) 
    ↓
Debezium Connector 
    ↓
Kafka Topics 
    ↓
Node.js Consumer 
    ↓
Redis Cache 
    ↓
SSE/WebSocket → Vue.js Frontend
```

---

## 💻 System Requirements

### Minimum Hardware Requirements
- **CPU:** 4 cores
- **RAM:** 8GB minimum, 16GB recommended
- **Storage:** 20GB free space
- **OS:** Ubuntu 20.04+, macOS 11+, or compatible Linux distribution

### Software Version Requirements

| Component | Required Version | Notes |
|-----------|-----------------|-------|
| Java JDK | 21 (recommended) or 17 | OpenJDK compatible |
| Node.js | 18+ LTS | Latest stable version |
| PostgreSQL | 16 | With PostGIS extension |
| Redis | 6.0+ | Latest stable |
| Kafka | 4.1.0 | KRaft mode only |
| Debezium | 2.6.1.Final | PostgreSQL connector |

---

## 🔍 Pre-Installation Checks

Before starting installation, verify existing components and their versions.

### Check Installed Versions

```bash
# Java Version
java -version
# Should show: openjdk version "21.x.x" or "17.x.x"

# Node.js Version
node -v
# Should show: v18.x.x or higher

# PostgreSQL Version
psql --version
# Should show: psql (PostgreSQL) 16.x

# Redis (if running)
redis-cli ping
# Should respond: PONG

# Check if Kafka directory exists
ls -la ~/kafka
```

### Installing Missing Components

#### Java JDK 21
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install openjdk-21-jdk -y

# macOS (Homebrew)
brew install openjdk@21
```

#### Node.js LTS
```bash
# Ubuntu/Debian (using NodeSource)
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs

# macOS (Homebrew)
brew install node

# Verify installation
node -v && npm -v
```

---

## 🗄️ PostgreSQL Setup

### Step 1: Install PostgreSQL 16 with PostGIS

#### Ubuntu/Debian
```bash
# Install PostgreSQL 16
sudo apt update
sudo apt install postgresql-16 postgresql-contrib -y

# Install PostGIS extension
sudo apt install postgis postgresql-16-postgis-3 -y

# Verify installation
psql --version
```

#### macOS
```bash
brew install postgresql@16 postgis
brew services start postgresql@16
```

### Step 2: Configure PostgreSQL User and Database

```bash
# Switch to postgres user
sudo -i -u postgres

# Create database and user
psql
```

In the PostgreSQL prompt:
```sql
-- Create the database
CREATE DATABASE garuda;

-- Create PostGIS extension
\c garuda
CREATE EXTENSION postgis;

-- Verify extension
\dx

-- Exit
\q
exit
```

### Step 3: Enable Network Access (Important!)

#### A. Edit postgresql.conf

Find your config file location:
```bash
sudo -u postgres psql -c "SHOW config_file;"
# Typically: /etc/postgresql/16/main/postgresql.conf
```

Edit the configuration:
```bash
sudo nano /etc/postgresql/16/main/postgresql.conf
```

Add or modify these lines:
```ini
# Network Connections
listen_addresses = '*'

# Logical Replication Settings (CRITICAL for Debezium)
wal_level = logical
max_replication_slots = 10
max_wal_senders = 10
```

#### B. Edit pg_hba.conf

```bash
sudo nano /etc/postgresql/16/main/pg_hba.conf
```

Add this line to allow network connections:
```
# Allow connections from all IPs (use your network range for production)
host    all             all             0.0.0.0/0               md5
```

**Security Note:** For production, replace `0.0.0.0/0` with your specific IP range (e.g., `192.168.1.0/24`)

#### C. Restart PostgreSQL

```bash
# Ubuntu/Debian
sudo systemctl restart postgresql

# macOS
brew services restart postgresql@16

# Verify it's running
sudo systemctl status postgresql
```

### Step 4: Create Database Schema

#### Using pgAdmin (Recommended)

1. **Install pgAdmin 4**
   ```bash
   # Ubuntu
   curl -fsS https://www.pgadmin.org/static/packages_pgadmin_org.pub | sudo gpg --dearmor -o /usr/share/keyrings/packages-pgadmin-org.gpg
   sudo sh -c 'echo "deb [signed-by=/usr/share/keyrings/packages-pgadmin-org.gpg] https://ftp.postgresql.org/pub/pgadmin/pgadmin4/apt/$(lsb_release -cs) pgadmin4 main" > /etc/apt/sources.list.d/pgadmin4.list'
   sudo apt update
   sudo apt install pgadmin4
   
   # macOS
   brew install --cask pgadmin4
   ```

2. **Configure Server Connection**
   - Open pgAdmin 4
   - Right-click "Servers" → "Register" → "Server"
   - **General Tab:**
     - Name: `Garuda PostgreSQL`
   - **Connection Tab:**
     - Host: `localhost`
     - Port: `5432`
     - Database: `garuda`
     - Username: `postgres`
     - Password: `qazwsx123`

3. **Run Schema SQL**
   - Connect to the `garuda` database
   - Open Query Tool
   - Copy and paste the SQL schema from the end of this document
   - Execute (F5)

#### Using Command Line

If you have a schema dump file:
```bash
psql -U postgres -d garuda -h localhost < garuda_v1_schema_dump.sql
```

### Step 5: Enable CDC for Alerts Table

Connect to the database and configure replication:

```bash
psql -U postgres -d garuda -h localhost
```

Execute these SQL commands:
```sql
-- Set REPLICA IDENTITY to FULL (required for Debezium)
ALTER TABLE alerts REPLICA IDENTITY FULL;

-- Create publication for Debezium
CREATE PUBLICATION debezium_pub1 FOR TABLE alerts;

-- Verify publication
SELECT * FROM pg_publication;

-- Verify replication slot will be created
SELECT * FROM pg_replication_slots;

-- Exit
\q
```

### Step 6: Update Environment Configuration

Create or update your `.env` file in the backend:

```bash
cd garuda_app_v1/backend
nano .env
```

Add these configurations:
```env
# Database Configuration
DB_HOST=localhost
DB_USER=postgres
DB_PASSWORD=qazwsx123
DB_DATABASE=garuda
DB_PORT=5432

# Server Configuration
HOST=0.0.0.0
PORT=3000
NODE_ENV=development
```

---

## ⚡ Kafka & Debezium Configuration

### Step 1: Install Kafka 4.1.0 (KRaft Mode)

```bash
# Navigate to home directory
cd ~

# Download Kafka 4.1.0
wget https://archive.apache.org/dist/kafka/4.1.0/kafka_2.13-4.1.0.tgz

# Extract
tar -xvzf kafka_2.13-4.1.0.tgz

# Rename for convenience
mv kafka_2.13-4.1.0 kafka

# Create plugins directory for Debezium
mkdir -p ~/kafka/plugins

# Clean up
rm kafka_2.13-4.1.0.tgz
```

### Step 2: Configure Kafka in KRaft Mode

Edit the KRaft broker configuration:
```bash
nano ~/kafka/config/kraft-broker.properties
```

**Complete Configuration:**
```ini
# KRaft Process Roles
process.roles=broker,controller
node.id=1
controller.quorum.voters=1@localhost:9093

# Listeners
listeners=PLAINTEXT://:9092,CONTROLLER://:9093
advertised.listeners=PLAINTEXT://localhost:9092
controller.listener.names=CONTROLLER

# Log Configuration
log.dirs=/tmp/kraft-combined-logs

# Broker Configuration (CRITICAL for consumers)
broker.id=1
offsets.topic.replication.factor=1
transaction.state.log.min.isr=1
transaction.state.log.replication.factor=1


```

### Step 3: Format Kafka Storage

**Important:** This step must be done only once, before first startup.

```bash
cd ~/kafka

# Clean any previous logs
rm -rf /tmp/kraft-combined-logs

# Generate a cluster ID
KAFKA_CLUSTER_ID="$(bin/kafka-storage.sh random-uuid)"
echo "Cluster ID: $KAFKA_CLUSTER_ID"

# Format the storage directory
bin/kafka-storage.sh format -t $KAFKA_CLUSTER_ID -c config/kraft-broker.properties
```

You should see output confirming the formatting was successful.

### Step 4: Install Debezium PostgreSQL Connector

```bash
cd ~

# Download Debezium 2.6.1 PostgreSQL connector
wget https://repo1.maven.org/maven2/io/debezium/debezium-connector-postgres/2.6.1.Final/debezium-connector-postgres-2.6.1.Final-plugin.tar.gz

# Extract
tar -xvzf debezium-connector-postgres-2.6.1.Final-plugin.tar.gz

# Move to Kafka plugins directory
mv debezium-connector-postgres ~/kafka/plugins/

# Clean up
rm debezium-connector-postgres-2.6.1.Final-plugin.tar.gz

# Verify installation
ls -la ~/kafka/plugins/debezium-connector-postgres/
```

### Step 5: Configure Kafka Connect (Standalone Mode)

#### A. Create Connect Worker Configuration

```bash
nano ~/kafka/config/connect-standalone.properties
```

**Configuration:**
```ini
# Kafka Bootstrap Servers
bootstrap.servers=localhost:9092

# Converter Configuration
key.converter=org.apache.kafka.connect.json.JsonConverter
value.converter=org.apache.kafka.connect.json.JsonConverter
key.converter.schemas.enable=false
value.converter.schemas.enable=false

# Offset Storage
offset.storage.file.filename=/tmp/connect.offsets
offset.flush.interval.ms=10000

# Plugin Path (IMPORTANT: Replace YOUR_USER_NAME)
plugin.path=/home/YOUR_USER_NAME/kafka/plugins

# Connect Configuration
group.id=connect-cluster
```

**⚠️ Critical:** Replace with your plugin path


#### B. Create Debezium Connector Configuration

```bash
nano ~/kafka/config/register-postgres.properties
```

**Configuration:**
```ini
# Connector Identity
name=garuda-alerts-connector
connector.class=io.debezium.connector.postgresql.PostgresConnector

# PostgreSQL Connection
database.hostname=localhost
database.port=5432
database.user=postgres
database.password=qazwsx123
database.dbname=garuda

# Debezium Configuration
plugin.name=pgoutput
database.server.name=garuda_cdc
topic.prefix=garuda_cdc

# Replication Configuration
slot.name=debezium_slot1
publication.name=debezium_pub1
snapshot.mode=initial

# Table Filtering
table.include.list=public.alerts

# Converters
key.converter=org.apache.kafka.connect.json.JsonConverter
value.converter=org.apache.kafka.connect.json.JsonConverter

# Tombstone Configuration
tombstones.on.delete=false
```

---

## 🔴 Redis Installation

### Ubuntu/Debian
```bash
# Install Redis
sudo apt update
sudo apt install redis-server -y

# Enable and start Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Verify Redis is running
redis-cli ping
# Should respond: PONG
```

### macOS
```bash
# Install Redis
brew install redis

# Start Redis service
brew services start redis

# Verify
redis-cli ping
```

### Test Redis Connection
```bash
# Connect to Redis CLI
redis-cli

# Test commands
127.0.0.1:6379> SET test "Hello Garuda"
127.0.0.1:6379> GET test
127.0.0.1:6379> DEL test
127.0.0.1:6379> exit
```

---

## 📦 Application Setup

### Step 1: Clone Repositories

```bash
# Create project directory
mkdir -p ~/garuda_app_v1
cd ~/garuda_app_v1

# Clone backend repository
git clone https://github.com/rajkrsingh9/GARUDA-Backend.git backend

# Clone frontend repository
git clone https://github.com/rajkrsingh9/GARUDA-Frontend.git frontend
```

### Step 2: Backend Setup

```bash
cd ~/garuda_app_v1/backend

# Install dependencies
npm install

# Create .env file (if not exists)
cat > .env << EOF
DB_HOST=localhost
DB_USER=postgres
DB_PASSWORD=qazwsx123
DB_DATABASE=garuda
DB_PORT=5432

HOST=0.0.0.0
PORT=3000
NODE_ENV=development

REDIS_HOST=localhost
REDIS_PORT=6379

KAFKA_BROKER=localhost:9092
KAFKA_TOPIC=garuda_cdc.public.alerts
EOF

# Verify .env file
cat .env
```

### Step 3: Frontend Setup

```bash
cd ~/garuda_app_v1/frontend

# Install dependencies
npm install
```

### Step 4: Configure Vite Proxy for SSE

Edit the Vite configuration:
```bash
nano vite.config.ts
```

Ensure the proxy configuration is present:
```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:3000',
        changeOrigin: true,
        secure: false,
        ws: true
      }
    }
  }
})
```

---

## 🚀 Running the System

The system requires **5 terminal windows** running simultaneously in the correct order.

### Terminal 1: Start Kafka Broker

```bash
cd ~/kafka

# Start Kafka in KRaft mode
bin/kafka-server-start.sh config/kraft-broker.properties
```

**Expected Output:**
```
[KafkaServer id=1] started (kafka.server.KafkaServer)
```

**Wait for 10-15 seconds** before proceeding to ensure Kafka is fully started.

### Terminal 2: Start Debezium Connect

```bash
cd ~/kafka

# Start Kafka Connect with Debezium connector
bin/connect-standalone.sh \
  config/connect-standalone.properties \
  config/register-postgres.properties
```

**Expected Output:**
```
INFO Connector garuda-alerts-connector config updated
INFO Creating connector garuda-alerts-connector of type io.debezium.connector.postgresql.PostgresConnector
INFO WorkerConnector{id=garuda-alerts-connector} Connector started successfully
```

**Common Issues:**
- If you see plugin errors, verify the `plugin.path` in `connect-standalone.properties`
- If PostgreSQL connection fails, check your database credentials

### Terminal 3: Start Redis

```bash
# If not already running as a service
redis-server

# Or check status
sudo systemctl status redis-server
```

### Terminal 4: Start Backend Server

```bash
cd ~/garuda_app_v1/backend

# Start the Node.js backend
npm run start
```

**Expected Output:**
```
Server running on http://0.0.0.0:3000
Connected to PostgreSQL
Connected to Redis
Kafka consumer connected
Subscribed to topic: garuda_cdc.public.alerts
```

### Terminal 5: Start Frontend Development Server

```bash
cd ~/garuda_app_v1/frontend

# Start Vite dev server
npm run dev
```

**Expected Output:**
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

---

## ✅ Verification & Testing

### Step 1: Verify Kafka Topics

In a new terminal:
```bash
cd ~/kafka

# List all topics
bin/kafka-topics.sh --bootstrap-server localhost:9092 --list
```

**Expected Topics:**
- `garuda_cdc.public.alerts`
- `connect-configs`
- `connect-offsets`
- `connect-status`

### Step 2: Monitor Kafka Messages

```bash
# Consume messages from alerts topic
bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic garuda_cdc.public.alerts \
  --from-beginning
```

### Step 3: Test CDC Pipeline

Open pgAdmin or psql and insert a test alert:

```sql
-- Connect to database
psql -U postgres -d garuda -h localhost

-- Insert test alert
INSERT INTO alerts (content, subscription_id, feature_geojson) 
VALUES (
  '{"message": "Test Alert", "severity": "high"}'::jsonb,
  1,
  '{"type": "Point", "coordinates": [88.3639, 22.5726]}'::jsonb
);

-- Verify insertion
SELECT * FROM alerts ORDER BY id DESC LIMIT 1;
```

**What Should Happen:**
1. Kafka consumer in Terminal should show the new message
2. Backend logs should show message processing
3. Frontend should display the alert in real-time

### Step 4: Check Database Replication Slot

```sql
-- Verify Debezium replication slot
SELECT * FROM pg_replication_slots WHERE slot_name = 'debezium_slot1';

-- Check publication
SELECT * FROM pg_publication_tables WHERE pubname = 'debezium_pub1';
```

### Step 5: Frontend Access

1. Open browser: `http://localhost:5173`
2. You should see the Garuda V1 interface
3. Insert an alert in the database and verify it appears immediately

---

## 🔧 Troubleshooting

### Kafka Won't Start

**Problem:** Kafka fails to start with "log directory already exists"

**Solution:**
```bash
# Stop Kafka if running
# Clean old logs
rm -rf /tmp/kraft-combined-logs

# Re-format storage
cd ~/kafka
KAFKA_CLUSTER_ID="$(bin/kafka-storage.sh random-uuid)"
bin/kafka-storage.sh format -t $KAFKA_CLUSTER_ID -c config/kraft-broker.properties

# Restart Kafka
bin/kafka-server-start.sh config/kraft-broker.properties
```

### Debezium Connection Failed

**Problem:** "Failed to connect to PostgreSQL"

**Solutions:**
1. Check PostgreSQL is running:
   ```bash
   sudo systemctl status postgresql
   ```

2. Verify network access in `pg_hba.conf`:
   ```bash
   sudo nano /etc/postgresql/16/main/pg_hba.conf
   # Ensure this line exists:
   host    all    all    0.0.0.0/0    md5
   ```

3. Restart PostgreSQL:
   ```bash
   sudo systemctl restart postgresql
   ```

### No Kafka Topics Created

**Problem:** `garuda_cdc.public.alerts` topic not appearing

**Solution:**
1. Check Debezium connector status:
   ```bash
   curl http://localhost:8083/connectors/garuda-alerts-connector/status
   ```

2. Verify publication and replication:
   ```sql
   SELECT * FROM pg_publication WHERE pubname = 'debezium_pub1';
   SELECT * FROM pg_replication_slots;
   ```

3. Restart Debezium Connect (Terminal 2)

### Frontend Can't Connect to Backend

**Problem:** SSE connection fails or 502 errors

**Solutions:**
1. Verify backend is running on port 3000
2. Check Vite proxy configuration in `vite.config.ts`
3. Ensure `HOST=0.0.0.0` in backend `.env`
4. Check firewall rules:
   ```bash
   sudo ufw status
   sudo ufw allow 3000
   sudo ufw allow 5173
   ```

### Redis Connection Failed

**Problem:** Backend can't connect to Redis

**Solutions:**
```bash
# Check Redis status
sudo systemctl status redis-server

# Restart Redis
sudo systemctl restart redis-server

# Test connection
redis-cli ping

# Check Redis logs
sudo tail -f /var/log/redis/redis-server.log
```

### Plugin Path Error in Kafka Connect

**Problem:** "Failed to find any class that implements Connector"

**Solution:**
```bash
# Verify plugin directory exists
ls -la ~/kafka/plugins/debezium-connector-postgres/

# Update plugin.path with correct username
nano ~/kafka/config/connect-standalone.properties

# Correct format:
plugin.path=/home/YOUR_ACTUAL_USERNAME/kafka/plugins

# Restart Connect (Terminal 2)
```

---

## 📊 Complete Database Schema

Execute this SQL in pgAdmin or psql after creating the `garuda` database:

```sql
-- Enable PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;

-- Users Table
CREATE TABLE public.users (
    user_id TEXT NOT NULL,
    username TEXT,
    password_hash TEXT,
    contactno TEXT,
    email TEXT,
    CONSTRAINT pk_users PRIMARY KEY (user_id)
);

-- Project Table
CREATE TABLE public.project (
    id SERIAL NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    creation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_modified_timestamp TIMESTAMP WITH TIME ZONE,
    created_by_userid TEXT NOT NULL,
    auxdata JSONB,
    CONSTRAINT pk_project PRIMARY KEY (id)
);

-- Users to Project Mapping
CREATE TABLE public.users_to_project (
    id SERIAL NOT NULL,
    user_id TEXT NOT NULL,
    project_id INTEGER NOT NULL,
    user_role INTEGER[] DEFAULT ARRAY[]::INTEGER[],
    CONSTRAINT pk_users_to_project PRIMARY KEY (id),
    CONSTRAINT unique_user_project UNIQUE (user_id, project_id),
    CONSTRAINT fk_utp_user FOREIGN KEY (user_id)
        REFERENCES public.users (user_id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_utp_project FOREIGN KEY (project_id)
        REFERENCES public.project (id) ON UPDATE CASCADE ON DELETE CASCADE
);

-- Role Token Table
CREATE TABLE public.role_token (
    id SERIAL NOT NULL,
    role TEXT NOT NULL,
    CONSTRAINT role_token_pkey PRIMARY KEY (id)
);

-- Area of Interest Table
CREATE TABLE public.area_of_interest (
    id SERIAL NOT NULL,
    project_id INTEGER NOT NULL,
    aoi_id TEXT NOT NULL,
    name TEXT NOT NULL,
    geom GEOMETRY NOT NULL,
    last_modified_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    geom_properties JSONB,
    auxdata JSONB,
    status INTEGER NOT NULL DEFAULT 1,
    CONSTRAINT pk_area_of_interest PRIMARY KEY (id),
    CONSTRAINT area_of_interest_aoi_id_project_id_key UNIQUE (aoi_id, project_id),
    CONSTRAINT fk_aoi_project FOREIGN KEY (project_id)
        REFERENCES public.project (id) ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE INDEX idx_aoi_geom ON public.area_of_interest USING GIST (geom);

-- Alert Channel Catalogue
CREATE TABLE public.alert_channel_catalogue (
    id SERIAL NOT NULL,
    script_id TEXT NOT NULL,
    script_name TEXT NOT NULL,
    channel_name TEXT NOT NULL,
    category TEXT NOT NULL,
    args JSONB,
    auxdata JSONB,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    CONSTRAINT alert_channel_catalogue_pkey PRIMARY KEY (id),
    CONSTRAINT alert_channel_catalogue_script_id_key UNIQUE (script_id)
);

-- Subscription Table
CREATE TABLE public.subscription (
    id SERIAL NOT NULL,
    project_id INTEGER NOT NULL,
    aoi_id TEXT NOT NULL,
    channel_id INTEGER NOT NULL,
    user_ids TEXT[] NOT NULL,
    alert_dissemination_mode TEXT[] NOT NULL DEFAULT ARRAY['notify'::TEXT],
    auxdata JSONB,
    status INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    last_modified TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    CONSTRAINT subscription_pkey PRIMARY KEY (id),
    CONSTRAINT subscription_project_id_fkey FOREIGN KEY (project_id)
        REFERENCES public.project (id) ON DELETE CASCADE,
    CONSTRAINT subscription_channel_id_fkey FOREIGN KEY (channel_id)
        REFERENCES public.alert_channel_catalogue (id),
    CONSTRAINT fk_project_aoi FOREIGN KEY (project_id, aoi_id)
        REFERENCES public.area_of_interest (project_id, aoi_id) ON DELETE CASCADE
);

-- Alerts Table (CDC Source)
CREATE TABLE public.alerts (
    id SERIAL NOT NULL,
    content JSONB NOT NULL,
    alert_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    subscription_id INTEGER NOT NULL,
    auxdata JSONB,
    feature_geojson JSONB,
    CONSTRAINT alerts_pkey PRIMARY KEY (id),
    CONSTRAINT fk_alert_subscription FOREIGN KEY (subscription_id)
        REFERENCES public.subscription (id) ON DELETE RESTRICT
);

-- Configure CDC for alerts table
ALTER TABLE alerts REPLICA IDENTITY FULL;
CREATE PUBLICATION debezium_pub1 FOR TABLE alerts;
```

---

## 🎓 Quick Start Checklist

Use this checklist to ensure all steps are completed:

- [ ] Java 21 installed and verified
- [ ] Node.js 18+ installed
- [ ] PostgreSQL 16 with PostGIS installed
- [ ] Database `garuda` created with schema
- [ ] PostgreSQL configured for logical replication
- [ ] `alerts` table has REPLICA IDENTITY FULL
- [ ] Publication `debezium_pub1` created
- [ ] Kafka 4.1.0 downloaded and extracted to `~/kafka`
- [ ] Kafka storage formatted with cluster ID
- [ ] Debezium connector installed in `~/kafka/plugins/`
- [ ] Connect worker configuration updated with correct username
- [ ] Redis installed and running
- [ ] Backend repository cloned and dependencies installed
- [ ] Frontend repository cloned and dependencies installed
- [ ] `.env` file configured in backend
- [ ] Vite proxy configured in frontend
- [ ] All 5 terminals running successfully
- [ ] Test alert inserted and received in frontend

---

## 📞 Support & Resources

**GitHub Repositories:**
- Backend: https://github.com/rajkrsingh9/GARUDA-Backend
- Frontend: https://github.com/rajkrsingh9/GARUDA-Frontend

**Documentation References:**
- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
- [Debezium PostgreSQL Connector](https://debezium.io/documentation/reference/stable/connectors/postgresql.html)
- [PostgreSQL Logical Replication](https://www.postgresql.org/docs/16/logical-replication.html)

---

**Document Version:** 1.0  
**Last Updated:** December 2025  
**Maintained by:** Garuda Development Team
