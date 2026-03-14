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
│   ├── be_fast.py                  # FastAPI backend
│   ├── be_search.py                # Search backend logic
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── linguistic_markers_app.py   # Streamlit frontend
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

> **Prerequisites:** Peers will need [Docker Desktop](https://docs.docker.com/get-docker/) installed. No Python environment or dependency installation is required — everything runs inside the containers.

**1. Download the archive**

Download the `linguistic_markers_app.tar` file from the repository root.

**2. Extract the archive**

```bash
tar -xvf linguistic_markers_app.tar
```

This will extract the contents into a folder. The `Dockerfile` and `docker-compose.yml` are located inside the `app/` subdirectory.

**3. Open Docker Desktop**

Make sure Docker Desktop is open and running before proceeding — the `docker-compose` command requires the Docker daemon to be active.

**4. Navigate into the `app` directory**

```bash
cd linguistic_markers_app/app
```

**5. Build and start the services**

```bash
docker-compose up --build
```

**6. Open the app in your browser**

Once the services are running, the app is accessible at:

- **Frontend (Streamlit):** http://localhost:8501

To stop the services:

```bash
docker-compose down
```

---

## Things to Try

Once the app is running, here are a few things worth exploring:

- **AI vs. human disagreements** — can you find an item where the AI (Gemini) and human annotations don't match? Enable *Show AI (Gemini) annotations* in the search bar to compare side by side.
- **Tag density** — what's the most tags a single annotation has?
- **Empty tag results** — note that some annotated items had no content that fell into any tag category, so not every result will have tags.
