
# Docker Project Monitoring

This monitoring stack integrates **Prometheus and Grafana** with the existing Docker Project.

It collects Flask backend application metrics through the `/metrics` endpoint, stores them in Prometheus, and visualizes them using Grafana dashboards.

## 1. Architecture

```
                 Docker Project
                       |
          +------------+------------+
          |            |            |
       Frontend      Backend     PostgreSQL
       Port 3000    Port 5000     Port 5432
                        |
                    /metrics
                        |
                        v
                  Prometheus
                   Port 9091
                        |
                        v
                    Grafana
                   Port 9090
                        |
                        v
                   Dashboard
```

Both monitoring and application containers communicate through the Docker network.

## 2. Project Structure

```
Docker-Project/
│
├── backend/
├── database/
├── frontend/
│
├── monitoring/
│   │
│   ├── docker-compose.yml
│   ├── README.md
│   │
│   ├── prometheus/
│   │   └── prometheus.yml
│   │
│   └── grafana/
│       ├── provisioning/
│       │   ├── datasources/
│       │   │   └── prometheus.yml
│       │   │
│       │   └── dashboards/
│       │       └── dashboards.yml
│       │
│       └── dashboards/
│           └── docker-project-overview.json
│
└── docker-compose.yml
```

## 3. Prerequisites

Before starting monitoring, make sure the application stack is running.

### Step 1: Check application containers

Run from the project root:

```
docker compose ps
```

Expected services:

- frontend
- backend
- postgres

### Step 2: Check Docker network

```
docker network ls
```

Expected application network:

```
docker-project_mynetwork
```

### Step 3: Verify backend metrics

```
Invoke-WebRequest http://localhost:5000/metrics -UseBasicParsing
```

Check available metric names:

```
(Invoke-WebRequest http://localhost:5000/metrics -UseBasicParsing).Content |
    Select-String "^# HELP"
```

Expected Flask metrics include:

```
flask_http_request_duration_seconds
flask_http_request_total
flask_http_request_exceptions_total
```

If these metrics are unavailable, check the Flask Prometheus exporter configuration before proceeding.

## 4. Start Monitoring Stack

Run all commands from the project root:

```
cd C:\Docker-Project
```

### Step 1: Validate Docker Compose configuration

```
docker compose -f monitoring/docker-compose.yml config
```

### Step 2: Start Prometheus and Grafana

```
docker compose -f monitoring/docker-compose.yml up -d
```

### Step 3: Check monitoring containers

```
docker compose -f monitoring/docker-compose.yml ps
```

Expected monitoring services:

```
prometheus
grafana
```

### Step 4: Check monitoring logs

Prometheus:

```
docker compose -f monitoring/docker-compose.yml logs prometheus
```

Grafana:

```
docker compose -f monitoring/docker-compose.yml logs grafana
```

Follow logs continuously:

```
docker compose -f monitoring/docker-compose.yml logs -f
```

## 5. Access Monitoring Services

| Service            | URL                                                            | Port |
| ------------------ | -------------------------------------------------------------- | ---- |
| Frontend           | [http://localhost:3000](http://localhost:3000)                 | 3000 |
| Flask Backend      | [http://localhost:5000](http://localhost:5000)                 | 5000 |
| Grafana            | [http://localhost:9090](http://localhost:9090)                 | 9090 |
| Prometheus         | [http://localhost:9091](http://localhost:9091)                 | 9091 |
| Prometheus Targets | [http://localhost:9091/targets](http://localhost:9091/targets) | 9091 |

### Grafana Login

```
Username: admin
Password: Your configured Grafana password
```

The password is configured in:

```
monitoring/docker-compose.yml
```

Change the default password before using this setup outside a local lab.

## 6. Configure and Verify Prometheus

Open:

[http://localhost:9091/targets](http://localhost:9091/targets)

Expected scrape targets:

| Job           | Target          | Expected Status |
| ------------- | --------------- | --------------- |
| prometheus    | prometheus:9090 | UP              |
| flask-backend | backend:5000    | UP              |

The Flask backend must show **UP**.

### Test Prometheus Queries

Open:

[http://localhost:9091](http://localhost:9091)

Execute the following PromQL queries individually.

**1. Total HTTP requests**

```
flask_http_request_total
```

**2. HTTP requests per second**

```
sum(rate(flask_http_request_total[5m]))
```

**3. Backend process memory**

```
process_resident_memory_bytes
```

**4. Backend CPU usage**

```
rate(process_cpu_seconds_total[5m])
```

**5. Prometheus target health**

```
up
```

A value of `1` means the target is reachable. A value of `0` means scraping is failing.

## 7. Load Grafana Dashboard

Open Grafana:

[http://localhost:9090](http://localhost:9090)

Follow these steps:

1. Login using your Grafana credentials.
2. Open the left navigation menu.
3. Select **Dashboards**.
4. Open the **Docker Project** folder.
5. Select **Docker Project - Application & Infrastructure**.

The dashboard is automatically provisioned from:

```
monitoring/grafana/dashboards/docker-project-overview.json
```

The Prometheus datasource is automatically configured through:

```
monitoring/grafana/provisioning/datasources/prometheus.yml
```

You do not need to configure the datasource or manually import the dashboard.

## 8. Generate Application Traffic

Dashboards may initially show empty graphs because Prometheus needs time to collect application metrics.

Generate test traffic using PowerShell.

### Generate 100 HTTP requests

```
1..100 | ForEach-Object {
    Invoke-WebRequest `
        -Uri "http://localhost:5000/health" `
        -UseBasicParsing

    Start-Sleep -Milliseconds 500
}
```

### Generate continuous traffic

Run this in a separate PowerShell terminal:

```
while ($true) {
    try {
        Invoke-WebRequest `
            -Uri "http://localhost:5000/health" `
            -UseBasicParsing | Out-Null

        Write-Host "Request successful" -ForegroundColor Green
    }
    catch {
        Write-Host "Request failed" -ForegroundColor Red
    }

    Start-Sleep -Seconds 1
}
```

Stop continuous traffic using:

```
CTRL + C
```

### Verify generated metrics

```
(Invoke-WebRequest http://localhost:5000/metrics -UseBasicParsing).Content |
    Select-String "flask_http_request_total"
```

Wait 30–60 seconds and refresh your Grafana dashboard.

## 9. Troubleshooting

### Problem 1: Flask backend target is DOWN

Check backend container:

```
docker compose ps
```

Check backend logs:

```
docker compose logs backend
```

Test metrics endpoint:

```
Invoke-WebRequest http://localhost:5000/metrics -UseBasicParsing
```

Verify both Compose stacks use the same Docker network:

```
docker network inspect docker-project_mynetwork
```

Prometheus must be connected to this network to resolve the backend hostname.

### Problem 2: Grafana dashboard is missing

Check Grafana logs:

```
docker compose -f monitoring/docker-compose.yml logs grafana
```

Verify the dashboard JSON exists:

```
Test-Path monitoring/grafana/dashboards/docker-project-overview.json
```

Expected output:

```
True
```

### Problem 3: Grafana cannot connect to Prometheus

Verify the datasource configuration:

```
monitoring/grafana/provisioning/datasources/prometheus.yml
```

The internal Docker URL must remain:

```
url: http://prometheus:9090
```

Do not change it to `localhost:9091`. Grafana accesses Prometheus through the internal Docker network, not the host-published port.

### Problem 4: Port already allocated

Check port usage:

```
netstat -ano | findstr :9090
netstat -ano | findstr :9091
```

The expected allocation is:

- Frontend: 3000
- Grafana: 9090
- Prometheus: 9091

## 10. Restart Monitoring

Restart both monitoring services:

```
docker compose -f monitoring/docker-compose.yml restart
```

Recreate Grafana if you change its environment configuration:

```
docker compose -f monitoring/docker-compose.yml up -d --force-recreate grafana
```

Recreate the monitoring stack:

```
docker compose -f monitoring/docker-compose.yml up -d --force-recreate
```

## 11. Stop Monitoring

Stop monitoring containers:

```
docker compose -f monitoring/docker-compose.yml down
```

This does not stop your frontend, backend, or PostgreSQL application containers.

### Delete Monitoring Data

**Warning:** This permanently deletes the Prometheus and Grafana persistent volumes, including their stored data.

```
docker compose -f monitoring/docker-compose.yml down -v
```

Do not run this command unless you intentionally want to reset monitoring data.

## 12. Current Monitoring Scope

| Component         | Monitoring                                   |
| ----------------- | -------------------------------------------- |
| Flask Backend     | HTTP requests, latency, exceptions           |
| Python Process    | CPU, memory, file descriptors                |
| Prometheus        | Scrape target health and time-series storage |
| Grafana           | Dashboards and visualization                 |
| PostgreSQL        | Not yet integrated                           |
| Docker Containers | Not yet integrated with cAdvisor             |
| Windows Host      | Not yet integrated with Windows Exporter     |

**Note:** Node Exporter and cAdvisor are not part of the current validated monitoring stack. Docker Desktop on Windows has different host-mount behavior from native Linux Docker.

## 13. Future Enhancements

Planned monitoring improvements:

1. PostgreSQL Exporter for database monitoring.
2. Windows Exporter for Windows host metrics.
3. Container resource monitoring.
4. Prometheus alert rules.
5. Grafana alert notifications.
6. Application availability monitoring.
7. CPU, memory and disk usage dashboards.
8. Migration of monitoring components to Kubernetes.

---

**Project:** Docker Project

**Monitoring Stack:** Prometheus + Grafana

**Environment:** Docker Desktop on Windows

**Application Metrics:** Flask Prometheus Exporter

