# Docker Instructions — Linguistic Misinformation Markers

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running on your machine
- A terminal (macOS/Linux) or PowerShell / Command Prompt (Windows)

---

## Project Structure Expected

Before building, your project folder should look like this:

```
your-project/
├── be_search.py
├── be_fast.py
├── linguistic_markers_app.py
├── templates.py
├── styles.css
├── Dockerfile
├── environment.yml          
├── data/
│   ├── annotations.json
│   ├── ai_annotations.json
│   └── corpus.csv
```

---

## Option A — Pull from Docker Hub (Recommended)

If the image has been uploaded to Docker Hub:

```bash
docker pull <team-name>/linguistic-misinformation-markers:latest
docker run -p 8000:8000 -p 8501:8501 <team-name>/linguistic-misinformation-markers:latest
```

Then open your browser and go to **http://localhost:8501**

---

## Option B — Build Locally from Source

### Step 1 — Create the Dockerfile

In your project root, create a file named `Dockerfile` with the following contents:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY environment.yml ./
RUN pip install --no-cache-dir \
    pandas numpy fastapi uvicorn whoosh requests streamlit

# Copy application code and data
COPY be_search.py be_fast.py linguistic_markers_app.py templates.py styles.css ./
COPY data/ ./data/

# Expose backend (FastAPI) and frontend (Streamlit) ports
EXPOSE 8000 8501

# Start both services using a simple shell script
COPY start.sh ./
RUN chmod +x start.sh
CMD ["./start.sh"]
```

### Step 2 — Create the startup script

Create a file named `start.sh` in your project root:

```bash
#!/bin/sh
# Start FastAPI backend in the background
uvicorn be_fast:app --host 0.0.0.0 --port 8000 &

# Start Streamlit frontend in the foreground
streamlit run linguistic_markers_app.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true
```

### Step 3 — Build the image

From your project root, run:

```bash
docker build -t linguistic-misinformation-markers .
```

This may take a few minutes the first time while dependencies are downloaded.

### Step 4 — Run the container

```bash
docker run -p 8000:8000 -p 8501:8501 linguistic-misinformation-markers
```

### Step 5 — Open the app

Once you see output like `You can now view your Streamlit app in your browser`, open:

**http://localhost:8501**

The backend API is also accessible at **http://localhost:8000/health** if you want to confirm it is running.

---

## Stopping the App

Press `Ctrl+C` in the terminal to stop the container. To remove it entirely:

```bash
docker ps                         
docker stop <container-id>
docker rm <container-id>
```

---

## Troubleshooting

**Port already in use** — If port 8501 or 8000 is taken by another process, map to different local ports:
```bash
docker run -p 9000:8000 -p 9501:8501 linguistic-misinformation-markers
```
Then access the app at **http://localhost:9501**

**App loads but shows "Backend unavailable"** — The Streamlit frontend cannot reach the FastAPI backend. This usually means the backend failed to start. Check the terminal output for errors from `uvicorn`.

**Index build takes a long time on first run** — This is expected. The Whoosh index is built from the corpus on first startup. Subsequent runs will be faster if you mount the index directory as a volume:
```bash
docker run -p 8000:8000 -p 8501:8501 \
    -v $(pwd)/whoosh_index:/app/whoosh_index \
    linguistic-misinformation-markers
```

**On Windows**, replace `$(pwd)` with `%cd%` in Command Prompt or `${PWD}` in PowerShell.
