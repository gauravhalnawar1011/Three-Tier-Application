# Docker on AWS EC2: Deploy a Flask API with PostgreSQL

## 1. Objective

In this practical, we will deploy a frontend, a Flask backend, and a PostgreSQL database using Docker on an AWS EC2 Linux instance.

By the end of this practical, students will understand:

- Docker images and containers
- Docker networks and volumes
- PostgreSQL container deployment
- Flask API deployment using Gunicorn
- Environment variables and database connectivity
- Database table initialization
- CORS configuration
- API testing with `curl`
- Docker troubleshooting on Linux

## 2. Prerequisites

Required resources:

- AWS account
- EC2 Linux instance running Ubuntu or Amazon Linux
- SSH access to the EC2 instance
- Docker Engine
- Frontend source code
- Flask backend source code
- PostgreSQL database image

Connect to EC2 using SSH from your local terminal:

```bash
ssh -i my-key.pem ubuntu@EC2_PUBLIC_IP
```

For Amazon Linux, the default username is commonly `ec2-user` instead of `ubuntu`.

Replace `my-key.pem` and `EC2_PUBLIC_IP` with your actual key file and EC2 public IP address.

Verify the operating system:

```bash
cat /etc/os-release
```

Verify Docker:

```bash
docker --version
docker info
```

If Docker is not installed, install it according to your EC2 operating system.

### Install Docker on Ubuntu

```bash
sudo apt-get update

sudo apt-get install -y docker.io

sudo systemctl enable --now docker

sudo docker --version
```

For this practical, use `sudo docker` if your user does not have permission to access Docker.

Alternatively, configure Docker access for your user according to the official Docker documentation. Membership in the `docker` group effectively grants root-level privileges.

## 3. Project Directory Structure

The project will use this structure:

```text
docker-project/
├── backend/
│   ├── Dockerfile
│   ├── app.py
│   └── requirements.txt
    └── .env
├── frontend/
│   ├── Dockerfile
│   ├── index.html
│   ├── style.css
│   └── app.js
├── database/
│   └── create_table.sql
├── .env
└── .gitignore
```

The backend contains the Flask API. The frontend contains the web application. The database directory contains SQL initialization scripts.

Create the project directory if needed:

```bash
mkdir -p ~/docker-project

cd ~/docker-project
```

Copy or clone your application source code into the corresponding directories before building the images.

## 4. Create a Docker Network

A Docker network allows the backend and PostgreSQL containers to communicate using container names.

Create the network:

```bash
docker network create mynetwork
```

Verify it:

```bash
docker network ls

docker network inspect mynetwork
```

If the network already exists, reuse it instead of creating another one.

## 5. Create a Persistent Docker Volume

Create a named volume for PostgreSQL data:

```bash
docker volume create pgdata
```

Verify the volume:

```bash
docker volume ls

docker volume inspect pgdata
```

The volume will be mounted at:

```text
/var/lib/postgresql/data
```

The database files will persist when the PostgreSQL container is stopped or recreated.

Do not remove this volume unless you intentionally want to delete the stored database data.

## 6. Configure Environment Variables

Create the `.env` file in the project root:

```bash
cd ~/docker-project

nano .env
```

Add the following configuration:

```dotenv
POSTGRES_USER=admin
POSTGRES_PASSWORD=ReplaceWithAStrongPassword
POSTGRES_DB=mydatabase

DB_HOST=my_postgres
DB_PORT=5432
DB_NAME=mydatabase
DB_USERNAME=admin
DB_PASSWORD=ReplaceWithAStrongPassword
DB_SSLMODE=disable

CORS_ORIGINS=http://localhost:3000
```

Replace `ReplaceWithAStrongPassword` with a strong password. The two password values must match.

For a browser accessing the frontend from another computer, replace the CORS origin with the actual frontend origin, for example:

```dotenv
CORS_ORIGINS=http://EC2_PUBLIC_IP:3000
```

Use HTTPS and your actual domain when the application is deployed behind a production web server or reverse proxy.

For this local container-to-container database connection, `DB_SSLMODE=disable` is appropriate only if PostgreSQL is not configured for TLS and the connection remains on the private Docker network. For managed databases, use the required TLS settings.

Protect the environment file:

```bash
chmod 600 .env
```

Create a `.gitignore` file:

```bash
nano .gitignore
```

Add:

```text
.env
__pycache__/
*.pyc
.venv/
```

Never commit real credentials to Git. For production, prefer AWS Secrets Manager or another appropriate secrets-management solution.

## 7. Run the PostgreSQL Container

Use the official PostgreSQL image.

For a new learning environment, PostgreSQL 16 is used here instead of the older PostgreSQL 13 image.

Run:

```bash
docker run -d \
  --name my_postgres \
  --network mynetwork \
  --env-file .env \
  -v pgdata:/var/lib/postgresql/data \
  --restart unless-stopped \
  postgres:16
```

### Explanation

| Option | Purpose |
|---|---|
| `-d` | Runs the container in the background |
| `--name my_postgres` | Names the container |
| `--network mynetwork` | Connects it to the Docker network |
| `--env-file .env` | Supplies PostgreSQL configuration |
| `-v pgdata:...` | Persists database data | 
| `--restart unless-stopped` | Restarts the container unless explicitly stopped |
| `postgres:16` | Selects the PostgreSQL image |

Notice that we do not publish port 5432 to the EC2 host. The Flask container can reach PostgreSQL through the Docker network, so external database access is unnecessary for this architecture.

### Verify PostgreSQL

```bash
docker ps

docker logs my_postgres

docker exec my_postgres \
  pg_isready -U admin -d mydatabase
```

Expected readiness output:

```text
/var/run/postgresql:5432 - accepting connections
```

If you already have a database initialized in `pgdata`, changing the PostgreSQL image tag or environment variables does not automatically migrate the database or reset its password. Back up existing data before changing major PostgreSQL versions.

## 8. Build the Python Backend Image

Verify that `backend/requirements.txt` contains the dependencies required by your application, including:

```text
Flask
Flask-Cors
psycopg2-binary
prometheus-flask-exporter
gunicorn
```

Your `backend/Dockerfile` should use a compatible Python image and start Gunicorn, for example:

```dockerfile
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
```

Build the backend image from the project root:

```bash
cd ~/docker-project

docker build -t my-webapp:fctp-dev ./backend
```

Verify the image:

```bash
docker images
```

The image `my-webapp:fctp-dev` should appear in the output.

## 9. Run the Flask Backend Container

Start the backend:

```bash
docker run -d \
  --name my-python-container \
  --network mynetwork \
  --env-file .env \
  -p 5000:5000 \
  --restart unless-stopped \
  my-webapp:fctp-dev
```

The Flask application receives the database configuration through environment variables.

Verify:

```bash
docker ps

docker logs my-python-container
```

Check the environment variables:

```bash
docker exec my-python-container printenv DB_HOST

docker exec my-python-container printenv DB_PORT

docker exec my-python-container printenv DB_NAME

docker exec my-python-container printenv DB_USERNAME
```

Expected output:

```text
my_postgres
5432
mydatabase
admin
```

The backend connects to `my_postgres:5432` because both containers share `mynetwork`.

## 10. Initialize the Database Tables

The Flask application requires two tables: `students` and `items`.

Create `database/create_table.sql`:

```sql
CREATE TABLE IF NOT EXISTS students (
    student_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    birth_date DATE,
    email VARCHAR(100),
    enrolled_date DATE
);

CREATE TABLE IF NOT EXISTS items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT
);
```

Execute the SQL against the existing PostgreSQL container:

```bash
docker exec -i my_postgres \
  psql -U admin -d mydatabase \
  < database/create_table.sql
```

Expected output:

```text
CREATE TABLE
CREATE TABLE
```

Verify the tables:

```bash
docker exec my_postgres \
  psql -U admin -d mydatabase -c '\dt'
```

This initialization step is required before testing the endpoints. In a production workflow, use a controlled database migration process.

## 11. Build and Run the Frontend

Build the frontend image from its directory:

```bash
docker build -t frontend:dev ./frontend
```

Run the frontend container:

```bash
docker run -d \
  --name my-frontend-container \
  --network mynetwork \
  -p 3000:80 \
  --restart unless-stopped \
  frontend:dev
```

Verify:

```bash
docker ps

docker logs my-frontend-container
```

The frontend will be available on port 3000 of the EC2 host if the security group permits access.

**Important:** Frontend JavaScript runs in the user's browser. If the browser calls `http://localhost:5000`, it will attempt to reach port 5000 on the user's own computer, not the EC2 instance. Configure the frontend API URL to use the reachable EC2 hostname or domain.

## 12. Verify the Complete Application

List all running containers:

```bash
docker ps
```

Expected containers:

```text
my-frontend-container
my-python-container
my_postgres
```

Verify the Docker network:

```bash
docker network inspect mynetwork
```

All three containers should be attached to the network if they were launched with the commands above.

### Test the API locally on EC2

Test the root endpoint:

```bash
curl -i http://localhost:5000/
```

Test application health:

```bash
curl -i http://localhost:5000/health
```

Test database readiness:

```bash
curl -i http://localhost:5000/ready
```

Retrieve students:

```bash
curl -i http://localhost:5000/students
```

Retrieve items:

```bash
curl -i http://localhost:5000/items
```

If the tables exist and contain no records, the collection endpoints should return:

```json
[]
```

## 13. Create a Student Record

Run:

```bash
curl -i \
  -X POST \
  http://localhost:5000/students \
  -H 'Content-Type: application/json' \
  -d '{
    "first_name": "Rahul",
    "last_name": "Sharma",
    "birth_date": "2000-01-15",
    "email": "rahul@example.com",
    "enrolled_date": "2026-10-28"
  }'
```

Expected result: HTTP `201 Created`, with the new student's ID.

Retrieve the records:

```bash
curl -i http://localhost:5000/students
```

## 14. Create an Item

Run:

```bash
curl -i \
  -X POST \
  http://localhost:5000/items \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Docker Book",
    "description": "Learning Docker fundamentals"
  }'
```

Retrieve all items:

```bash
curl -i http://localhost:5000/items
```

These commands verify that the API can accept requests, query PostgreSQL and return JSON responses.

## 15. Configure AWS EC2 Security Groups

For a basic classroom deployment, configure the EC2 security group according to the access you need.

| Port | Purpose | Recommended access |
|---|---|---|
| 22 | SSH | Your trusted public IP only |
| 3000 | Frontend | Your trusted public IP for testing |
| 5000 | Flask API | Your trusted public IP for direct API testing |
| 5432 | PostgreSQL | Do not expose publicly |

For a production deployment, serve the frontend and API through a reverse proxy or load balancer using HTTPS on port 443. Keep PostgreSQL private and do not expose its port to the internet.

If the frontend cannot reach the API, verify the browser's API URL, CORS configuration and security group rules.

## 16. Troubleshoot Common Errors

### Error 1: Password authentication failed

Example:

```text
FATAL: password authentication failed for user "admin"
```

Check the backend's environment variables:

```bash
docker exec my-python-container printenv DB_USERNAME
docker exec my-python-container printenv DB_HOST
```

The password supplied to Flask must match the actual password of the PostgreSQL user.

Changing `.env` alone does not change the password in an already-initialized database. Recreate the backend container after changing its environment configuration.

### Error 2: Relation does not exist

Example:

```text
relation "students" does not exist
```

Run the SQL initialization command from Section 10.

### Error 3: Connection refused

Check PostgreSQL:

```bash
docker ps

docker logs my_postgres

docker exec my_postgres \
  pg_isready -U admin -d mydatabase
```

Check the network:

```bash
docker inspect my_postgres \
  --format '{{json .NetworkSettings.Networks}}'

docker inspect my-python-container \
  --format '{{json .NetworkSettings.Networks}}'
```

Both containers need a shared network.

### Error 4: CORS error

Check the CORS configuration in `app.py` and make sure it allows the frontend's actual origin.

For example:

```text
http://EC2_PUBLIC_IP:3000
```

The application must explicitly read `CORS_ORIGINS` if you intend to configure it through the environment.

### Error 5: Backend container exits

Check the logs:

```bash
docker logs --tail 100 my-python-container
```

Inspect stopped containers:

```bash
docker ps -a
```

### Error 6: Frontend cannot reach the API

Confirm that the browser is calling the EC2 public IP or domain, rather than `localhost` or the internal Docker container name.

Also confirm that the relevant security group rule permits access to the API port when direct access is intended.

## 17. Useful Docker Commands

View running containers:

```bash
docker ps
```

View all containers:

```bash
docker ps -a
```

View images:

```bash
docker images
```

Follow backend logs:

```bash
docker logs -f my-python-container
```

Follow PostgreSQL logs:

```bash
docker logs -f my_postgres
```

Restart the backend:

```bash
docker restart my-python-container
```

Restart PostgreSQL:

```bash
docker restart my_postgres
```

Stop the backend:

```bash
docker stop my-python-container
```

Stop PostgreSQL:

```bash
docker stop my_postgres
```

Remove the backend container:

```bash
docker rm -f my-python-container
```

Remove the PostgreSQL container:

```bash
docker rm -f my_postgres
```

Removing the PostgreSQL container does not remove the `pgdata` volume.

Do not run `docker volume rm pgdata` unless you intentionally want to delete the database data.

## 18. Final Architecture

```text
User Browser
     |
     | HTTP :3000
     v
Frontend Container
     |
     | HTTP API :5000
     v
Flask + Gunicorn Container
     |
     | PostgreSQL TCP :5432
     v
PostgreSQL Container
     |
     v
Docker Volume: pgdata
```

The frontend and backend ports are published on the EC2 host for this learning setup. The backend reaches PostgreSQL through the private Docker network. PostgreSQL stores its data in the named volume.

## Conclusion

In this practical, students deployed a frontend, a Flask API and a PostgreSQL database using Docker on AWS EC2.

The main concepts covered are:

1. Docker images and containers
2. Docker networking
3. Persistent storage with Docker volumes
4. Environment variables
5. Flask and Gunicorn deployment
6. PostgreSQL initialization
7. API testing with `curl`
8. CORS and network troubleshooting
9. AWS security group configuration

For production, use supported software versions, secure secret management, database migrations, HTTPS, restricted network access and proper monitoring.
