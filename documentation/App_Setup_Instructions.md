# How to set up the Linguistic Markers app

------------------------------------------------------------------------

### 1. Clone the repo found here:

<https://github.ubc.ca/shiaolig/COLX_523_misinformation/tree/main>

### 2. Create the conda environment.

**From the root of the repo run the following in the terminal:**

-   conda env create -f environment.yml

**Switch environment by running the following in the terminal:**

-   conda activate colx_523

### 3. Start up the fastapi back end server.

**From the terminal, change directory to the app directory and run the following:**

-   uvicorn be_fast:app --reload --port 8000

### 4. Start up the streamlit front end.

**From the terminal, stay in the app directory and run the following:**

-   streamlit run linguistic_markers_app.py
