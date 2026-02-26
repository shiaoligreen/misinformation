import pandas as pd
import os

def build_pilot_dataset():
    """"
    Build a pilot dataset including 10 examples total: two from web scrappign, 8 from huggingface twitter misinformation data set.
    
    """
    #urls of source datasets. we will take 2 examples from google_comp_ling_articles.csv and 8 from training.csv
    PILOT_URLS = ["https://huggingface.co/datasets/jenniferflake/COLX_523/resolve/main/training_data.csv", 
                  "https://huggingface.co/datasets/jenniferflake/COLX_523/resolve/main/google_comp_ling_articles.csv"]
    
    #initialize dataframe that will hold pilot data
    pilot_df = pd.DataFrame()

    # Get the absolute path to the directory where this script is located (the 'src' folder)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Build the absolute path to the 'data/raw' folder
    data_raw_dir = os.path.join(script_dir, "..", "data", "raw")


    #set default path + filename where the pilot dataset will be created
    output_path = os.path.join(data_raw_dir, "pilot_dataset.csv")

    #set default columns names from source datafile to be extracted to build the corpus
    data_cols=["text", "label"]
    
    ##Start processing the source datasets ##
    
    for url in PILOT_URLS:

        try:
            # Read the contents of the URL into a dataframe
            # First, read the file without assuming headers to inspect the first few rows
            #Two of the source raw datafiles do not have column names in the first row.
            temp_df = pd.read_csv(url, header=None, nrows=2)
                
            # Find which row contains our target column names
            header_row_idx = 0

            for idx, row in temp_df.iterrows():
                #if all of the column names in the data_cols list is present in the values of the
                #current row, then this row must be the header row that contains the column names
                if all(col in row.values for col in data_cols):
                    header_row_idx = idx
                    break
                
            # Now read the file, with the header specified, skipping any title, or other, rows before the actual header
            if url.endswith("google_comp_ling_articles.csv"):
                #This is our scraped data. Get 2 examples only
                df = pd.read_csv(url, header=header_row_idx, usecols=data_cols, nrows=2 )
            elif url.endswith("training_data.csv"):
                df = pd.read_csv(url, header=header_row_idx, usecols=data_cols, nrows=8 )

            pilot_df = pd.concat([pilot_df, df], ignore_index=True)     
        except Exception as e:
            print(f"Failed to read {url}: {e}")

    #Print out basic info about pilot_df
    print(f"Pilot dataset includes {len(pilot_df)} rows" )
    print(f"Pilot dataset includes {pilot_df["text"].str.split().str.len().sum()} tokens")

    # Output as a new CSV file
    pilot_df.to_csv(output_path, index=False)
    print(f"Saved pilot dataset to {output_path}")


    #Don't run anything automatically, if imported.
if __name__ == "__main__":
    build_pilot_dataset()
