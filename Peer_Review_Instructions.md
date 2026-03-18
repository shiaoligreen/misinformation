# Linguistic Misinformation Markers

# Project Overview

We aim to build an annotated corpus that captures linguistic patterns distinguishing misinformation, opinion/editorial, from verified news. Our goal is to produce a dataset resource useful for researchers studying how language signals credibility — or the lack of it. We plan to enhance the Twitter Misinformation Dataset that is currently available on Hugging Face with the goal of contributing the enhanced dataset to Hugging Face.

## Sharing with Peers (via `.tar`)

The project is distributed as a `.tar` archive. To get it running:

> **Prerequisites:** Peers will need [Docker Desktop](https://docs.docker.com/get-docker/) installed. No Python environment or dependency installation is required — everything runs inside the containers.
> 

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
cd app
```

**5. Build and start the services**

```bash
docker-compose up --build
```

**6. Open the app in your browser**

Once the services are running, the app is accessible at:

- **Frontend (Streamlit):** [http://localhost:8501](http://localhost:8501/)

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

⚠️ This dataset includes profanity, particularly from the social media source of tweets, however we do not condone this use of language.

---

## Project Structure

```
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
```

---

## How It Works

## UI Layout

The app renders top-to-bottom in a single column (wide layout). Each section re-renders on every Streamlit re-run.

### Header

Two-column layout:

- **Left:** App title and subtitle (count of examples, annotator counts).
- **Right:** Fleiss's κ scores for humans-only annotations and humans + AI annotations.

### Search Bar

Two-column layout:

- **Left:** search input box for the search query.
- **Right:** `SEARCH` button.

Two checkboxes below:

- **Annotated examples only** — allows the user to restrict their search to examples from the corpus that are annotated. 
- **Show AI (Gemini) annotations** — allows the user to view AI annotated examples when available, below each human annotated example for comparison. 

A search re-run is triggered when either the button is clicked or the query text changes.

### Tag Filter Buttons

One button per tag (`ALL`, `ADJECTIVES`, `ALL_CAPS`, `EXCLAMATION_MARKS`, `HEDGING`, `UNK`). The active button is highlighted in its tag colour.

### Annotation Tags Legend

This reference section lists all five tags with descriptions and colour swatches. The `ALL_CAPS + TAG` overlap rendering rule is also explained here with an inline example.

### Result Cards

Each result is rendered in a result card. If no results match, an info message is shown. Results are limited to 50 items.

### AI-Paired Results Section

These appear when the `Show AI (Gemini) annotations` check-box is selected. The same tag filter is applied to both the human and corresponding AI annotated search results.

### Tag Distribution Bar Chart

Below the result cards is a tag distribution chart. Counts are computed over the **unfiltered** search results (not filtered by tag), so the chart always reflects the full search result distribution for each tag, regardless of the active tag button.
