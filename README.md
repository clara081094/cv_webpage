# Portfolio website

This repository contains a React frontend, a Flask API, and a PostgreSQL database. The quickest way to run all three is with Docker Compose.

## Requirements

- Docker Desktop (or Docker Engine) with the Compose plugin
- Git, if you are cloning the repository

## Start the website

Open a terminal in the repository root—the directory containing `docker-compose.yml`—and run:

```bash
cp .env.example .env
```

For local development, the example values work as-is. For a deployment, replace the placeholder secrets in `.env` with secure values. Do not commit `.env`.

Build the images and start the database, backend, and frontend:

```bash
docker compose up -d --build
```

Open the frontend at [http://localhost:8080](http://localhost:8080). The API is at `http://localhost:5001`; its health endpoint is `http://localhost:5001/api/v1/health`. nginx also proxies `/api` and serves uploaded images at `/static/uploads`, so the site works from port 8080 alone.

Useful commands:

```bash
docker compose ps                 # check service status
docker compose logs -f             # follow logs for all services
docker compose logs -f frontend    # follow logs for just the frontend
```

## Stop the website

To stop and remove the running containers and network:

```bash
docker compose down
```

This keeps the PostgreSQL data volume and uploaded files, so they will still be there when you start the website again with `docker compose up -d`.

To stop the containers without removing them, use:

```bash
docker compose stop
```

To start those stopped containers again:

```bash
docker compose start
```

**Delete all database data:** `docker compose down -v` also removes the PostgreSQL volume. This is destructive and cannot be undone. Uploaded files in `backend/uploads/` are stored on the host and are not deleted by this command.

## Run frontend development mode

To run the frontend with Vite's development server instead of the Docker frontend, leave the database and backend running, then open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Vite prints the local URL when it starts (typically `http://localhost:5173`). Stop this development server with **Ctrl+C**. To stop the database and backend too, return to the repository root and run `docker compose down`.

For backend setup, API details, and admin commands, see [backend/README.md](backend/README.md).
