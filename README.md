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
| Sprint 3 | [`src/Dataset_Cleaner.py`](src/Dataset_Cleaner.py), [`src/preprocess_data.py`](src/preprocess_data.py), [`src/text_length_distribution.py`](src/text_length_distribution.py), [`src/Interannotator_Analysis.py`](src/Interannotator_Analysis.py) [`src/Interannotator_Analysis.ipynb`](src/Interannotator_Analysis.ipynb) | [`data/preprocessed/consolidated_annotations.json`](data/preprocessed/consolidated_annotations.json) | [`weekly_minutes/`](weekly_minutes/sprint3) |
| Sprint 4 | *(add link)* | *(add link)* | [`weekly_minutes/`](weekly_minutes/sprint4) |
| Sprint 5 | *(add link)* | *(add link)* | [`weekly_minutes/`](weekly_minutes/sprint5) |

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


---


