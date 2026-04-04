# Data exploration and Stratified Splitting

### Scripts: 

`eda.py`

`data_prep.py`  

`strat_split.py`

Found at filepath: `581_Sprint_1/src`

#### Associated Notebooks:

`data_split_eda.ipynb`

`strat_split.ipynb`

The scripts listed above contain the modularized code from these notebooks. They are found in: `581_Sprint_1/src/notebooks`

---

## Pipeline

This pipeline starts with `annotations_1000.csv`, which contains all examples with their respective annotations, gold standard annotator and the target "opinion_label" column. It is located in the data folder.

Run scripts in order:

1. `eda.py`<n>  
    reads in `annotations_1000.csv`, produces basic data distributions.

2. `data_prep.py`<n>  
    reads in `annotations_1000.csv`, completes one-hot encoding of columns with the annotation labels and the four main annotators. Names the dataframe `mis_df_ohe.csv` and sends it to `/data/mis_df_ohe.csv`.

3. `strat_split.py`<n>  
    reads in `mis_df_ohe.csv`, completes the stratified splitting of the data in to train (60%), dev (20%) and test (20%) sets. For reproducibility, assigns random seed = 344.

    Produces the following .csv files:

    `data/sets/mis_df_with_all_splits.csv`: dataset with column labeling each example with its assigned split

    `data/sets/mis_df_train.csv`: training set

    `data/sets/mis_df_dev.csv`: dev set

    `data/sets/mis_df_test.csv`: test set


Note: `eda.py` is not necessary in the pipeline, for exploratory data analysis only.

## Prerequisites

 Installation of the conda environment `colx_523` (see `environment.yaml` in the main repo).