import pandas as pd
import os
import csv


def clean_dataset(input_path=None, output_path=None):
    """
    clean_dataset() removes duplicate rows from a .csv file.  Removes rows with NaN text. Removes rows with empty strings.
    Adds index numbers while outputting file to 
    
    Parameters: optional input and output paths for .csv files. 
    """
     
    #Default constants:
    PARENT = ".."
    DATA = "data"
    RAW = "raw"
    PREPROCESSED = "preprocessed"
    DEFAULT_INPUT = "complete_dataset.csv"
    DEFAULT_OUTPUT = "cleaned_dataset.csv"


    #Set path information:
    # Get the absolute path to the directory where this script is located (the 'src' folder)
    script_dir = os.path.dirname(os.path.abspath(__file__))

    #Build the absolute path to the 'data/raw' folder
    data_raw_dir = os.path.join(script_dir, PARENT, DATA, RAW)

    #Build the absolute path to the 'data/processed' folder
    data_processed_dir = os.path.join(script_dir, PARENT, DATA, PREPROCESSED)

    ##set defaults for optional parameters ##

    #set default file path of csv file containing the links to data files
    if input_path is None:
        input_path = os.path.join(data_raw_dir, DEFAULT_INPUT)

    if output_path is None:
        output_path = os.path.join(data_processed_dir,DEFAULT_OUTPUT )

    # Now read the file, with the header specified, skipping any title, or other, rows before the actual header
    df = pd.read_csv(input_path, usecols=["text", "label"])

    #Drop duplicate rows
    df = df.drop_duplicates()

    #only keep rows with label = 1 or 0
    df = df.query('label == 0 or label == 1')

    # Remove rows where 'text' is NaN or empty string
    df = df[df['text'].notna() & (df['text'].str.strip() != '')]

    #write file with index numbers. Quote the content of columns, so commas within the text do not cause unwanted columns.
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=True, quoting=csv.QUOTE_ALL)
    print(f"Saved cleaned dataset to {output_path}")



    #Don't run anything automatically, if imported.
if __name__ == "__main__":
    clean_dataset()


