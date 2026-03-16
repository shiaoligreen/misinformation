# COLX_523_misinformation: 


# Overview

This repository contains all code, data, documentation, and reports for the Misinformation project. It is organized to support iterative sprint-based development.

---

## Repository Structure

- **`data/`** — Raw and preprocessed datasets
- **`documentation/`** — Technical documentation for project sprints
- **`reports/`** — Project proposal, teamwork contract, and other sprint deliverables
- **`src/`** — Source code
- **`weekly_minutes/`** — Sprint meeting notes and action items

---

## Sprint Navigation

| Sprint | Code | Data | Notes |
|--------|------|------|-------|
| Sprint 1 | [`src/News_Scraper.py`](src/News_Scraper.py) | [`data/raw/`](data/raw/) | [`weekly_minutes/`](weekly_minutes/sprint1) |
| Sprint 2 | [`src/Dataset_Builder.py`](src/Dataset_Builder.py), [`src/Pilot_Dataset_Builder.py`](src/Pilot_Dataset_Builder.py)  | [`data/preprocessed/`](data/preprocessed/) | [`weekly_minutes/`](weekly_minutes/sprint2) |
| Sprint 3 | [`src/Dataset_Cleaner.py`](src/Dataset_Cleaner.py), [`src/preprocess_data.py`](src/preprocess_data.py), [`src/text_length_distribution.py`](src/text_length_distribution.py), [`src/Interannotator_Analysis.py`](src/Interannotator_Analysis.py) [`src/Interannotator_Analysis.ipynb`](src/Interannotator_Analysis.ipynb) [`src/consolidated_annotations.py`](src/consolidated_annotations.py) | [`data/preprocessed/consolidated_annotations.json`](data/preprocessed/consolidated_annotations.json) | [`weekly_minutes/`](weekly_minutes/sprint3) |
| Sprint 4 |  [`app/linguistic_markers_app.py`](app/linguistic_markers_app.py),[`app/styles.css`](app/styles.css), [`app/templates.py`](app/templates.py), [`app/be_fast.py`](app/be_fast.py), [`app/be_search.py`](app/be_search.py),  [`app/testing/test_be_search.py`](app/testing/test_be_search.py), [`app/testing/test_be_fast.py`](app/testing/test_be_fast.py) | [`app/data/cleaned_dataset.csv`](app/data/cleaned_dataset.csv), [`app/data/consolidated_annotations.json`](app/data/consolidated_annotations.json), [`app/data/Gemini_annotations_cleaned.json`](app/data/Gemini_annotations_cleaned.json) | [`weekly_minutes/`](weekly_minutes/sprint4) |
| Sprint 5 | [`app/requirements.txt`](app/requirements.txt), [`app/Dockerfile`](app/Dockerfile), [`app/docker-compose.yml`](app/docker-compose.yml) | [`app/data/cleaned_dataset.csv`](app/data/cleaned_dataset.csv), [`app/data/consolidated_annotations.json`](app/data/consolidated_annotations.json), [`app/data/Gemini_annotations_cleaned.json`](app/data/Gemini_annotations_cleaned.json) | [`weekly_minutes/`](weekly_minutes/sprint5) |

---

## Conda environment setup

To set up the necessary packages for running the labs and lecture material, [download the environment file to your computer](https://github.ubc.ca/shiaolig/COLX_523_misinformation/blob/main/environment.yml) (hit "Raw" and then `Ctrl` + `s` to save it, or copy paste the content). Then create a virtual environment by using `conda` with the environment file you just downloaded:

```         
conda env create --file environment.yml
```

This will setup Python with the correct versions of all required packages.

## Data Directory Details:

- **`data/raw`**

| File | Creation Method | Purpose |
|--------|------|------|
| [`data/raw/links_to_data.csv`](data/raw/links_to_data.csv) | Developer created | Contains links to remote data and is used by Dataset_Builder.py to create the complete dataset  |
| [`data/raw/all_huggingface_links.csv`](data/raw/all_huggingface_links.csv) | Developer created | Contains links to all remote data stored on Hugging Face   |
| [`data/raw/complete_dataset.csv`](data/raw/complete_dataset.csv) | Dataset_Builder.py creates | Contains entire dataset, including data from Hugging Face misinformation dataset and scraping |
| [`data/raw/pilot_dataset.csv`](data/raw/pilot_dataset.csv) | Pilot_Builder.py creates | Contains pilot dataset, includes 10 items total, drawn from Hugging Face misinformation dataset and scraping |

## Documentation Directory Details:

| File | Description |
|------|-------------|
| [`documentation/News_Scraper.md`](documentation/News_Scraper.md) | Setup and usage instructions for `News_Scraper.py`, which scrapes news titles and URLs from RSS feeds using `feedparser` |
| [`documentation/Annotation Walkthrough.mov`](documentation/Annotation%20Walkthrough.mov) | Video walkthrough of the annotation process |
| [`documentation/App_Setup_Instructions.md`](documentation/App_Setup_Instructions.md) | Step-by-step instructions for cloning the repo, creating the conda environment, and launching the FastAPI backend and Streamlit frontend |
| [`documentation/be_fast.md`](documentation/be_fast.md) | Technical documentation for `be_fast.py` — the FastAPI entry point that manages server lifecycle, index loading at startup, and the `/search` and `/health` endpoints |
| [`documentation/be_search.md`](documentation/be_search.md) | Technical documentation for `be_search.py` — the search engine layer that builds and queries the Whoosh index over annotated, AI-annotated, and corpus documents |
| [`documentation/linguistic_markers_app.md`](documentation/linguistic_markers_app.md) | Technical documentation for `linguistic_markers_app.py` — the Streamlit frontend that renders the search UI, tag filters, result cards, and bar chart |
| [`documentation/templates.md`](documentation/templates.md) | Technical documentation for `templates.py` — the HTML rendering helpers that generate highlighted result cards and the tag distribution bar chart |
| [`documentation/docker-instructions.md`](documentation/docker-instructions.md) | Instructions for installing and using the app with Docker for Peer Review |

---


