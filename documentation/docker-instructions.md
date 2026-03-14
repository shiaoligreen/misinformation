# Docker Setup Instructions

## Overview

This project uses a single `Dockerfile` to build both the frontend (Streamlit) and backend (FastAPI) services. Orchestration between the two is handled by `docker-compose.yml`, which overrides the default entrypoint for the backend service at runtime.

---

## Project Structure

```
COLX_523_misinformation/
├── app/
│   ├── data/
│   ├── testing/
│   ├── whoosh_index/
│   ├── be_fast.py                  
│   ├── be_search.py                
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── linguistic_markers_app.py   
│   ├── requirements.txt
│   ├── styles.css
│   └── templates.py
├── data/
├── documentation/
├── img/
├── reports/
├── src/
├── weekly_minutes/
├── environment.yml
├── LICENSE
├── linguistic_markers_app.tar
└── README.md
```

---

## How It Works

**`Dockerfile`** builds a single image based on `python:3.12-slim`. By default, its entrypoint runs the Streamlit app on port `8501`.

**`docker-compose.yml`** spins up two services from that same image:

| Service | Port | Description |
|---|---|---|
| `frontend` | `8501` | Runs the Streamlit app (uses the default Dockerfile entrypoint) |
| `backend` | `8000` | Runs the FastAPI app (overrides the entrypoint to use `uvicorn`) |

The `frontend` service is configured with a `BACKEND_URL` environment variable pointing to the backend container, and waits for the backend to start via `depends_on`.

---

## Running the App

From the project root, run:

```bash
docker-compose up --build
```

Once running, open your browser to:

- **Frontend (Streamlit):** http://localhost:8501
- **Backend (FastAPI):** http://localhost:8000

To stop the services:

```bash
docker-compose down
```

---

## Sharing with Peers (via `.tar`)

The project is distributed as a `.tar` archive. To get it running:

**1. Extract the archive**

```bash
tar -xf linguistic_markers_app.tar
```

**2. Navigate into the project directory**

```bash
cd linguistic_markers_app/app
```

**3. Build and start the services**

```bash
docker-compose up --build
```

> **Prerequisites:** Peers will need [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) installed. No Python environment or dependency installation is required — everything runs inside the containers.
