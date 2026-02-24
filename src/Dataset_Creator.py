import pandas as pd
import os

#default file path of csv file containing the links to data files
LINKS_TO_DATA="../data/raw/links_to_data.csv"

#column name of links contained in LINKS_TO_DATA
LINK_COL_NAME = "url"

#Column names inside each datafile that we will use to build the corpus
DATA_COL_NAMES=["text", "label"]

#default path + filename where the full corpus will be outputted when built
OUTPUT_PATH = "../data/raw/complete_dataset.csv"

#temp file for tracking which files have been processed
PROCESSED_URLS_FILE = "../data/raw/processed_urls_temp.txt"

def create_dataset(input_path=LINKS_TO_DATA, output_path=OUTPUT_PATH):
    """
    create_dataset() builds the complete dataset from the datasets that are stored at the urls contained in the
    "../data/raw/links_to_data.csv" by default, but that option can be changed via the optional links_to_data parameter
    The default path given here is relative to the src directory, where this code is expected to be run.
    
    Similarly, the output filename and path can be specificed by the optional output_path parameter. The default
    will be "../data/raw/complete_dataset.csv"

    This function only extracts the columns named "text" and "label" from the .csv files. 
    """
    
    # get list of links to datasets that will be included in the complete dataset
    links_df = pd.read_csv(input_path, usecols=[LINK_COL_NAME])
    
    # Keep track of which URLs have already been successfully processed
    
    processed_urls = set()
    
    #if the file containing the processed urls exists, then, open it and add the urls to a set.
    if os.path.exists(PROCESSED_URLS_FILE):
        with open(PROCESSED_URLS_FILE, "r") as f:
            processed_urls = set(line.strip() for line in f)
            
    list_of_dfs = []

    # If the dataset already exists in an output file, append to it, do not overwrite it.
    # Load it into list_of_dfs so it gets concatenated with any new data
    if os.path.exists(output_path):
        print(f"Found existing dataset at {output_path}. Loading it to append new data...")
        existing_df = pd.read_csv(output_path)
        list_of_dfs.append(existing_df)
    
    # Iterate through the URLs 
    print("Starting dataset creation. Press Ctrl+C at any time to safely stop the process.")
    interrupted = False
    try:
        for url in links_df[LINK_COL_NAME]:
            if url in processed_urls:
                print(f"Skipping already processed URL: {url}")
                continue
                
            try:
                # Read the contents of the URL into a dataframe
                # First, read the file without assuming headers to inspect the first few rows
                temp_df = pd.read_csv(url, header=None, nrows=5)
                
                # Find which row contains our target column names
                header_row_idx = 0
                for idx, row in temp_df.iterrows():
                    if all(col in row.values for col in DATA_COL_NAMES):
                        header_row_idx = idx
                        break
                
                # Now read the file properly, skipping any title rows before the actual header
                df = pd.read_csv(url, header=header_row_idx, usecols=DATA_COL_NAMES)
                list_of_dfs.append(df)
                print(f"Successfully read: {url}")
                
                # Mark this URL as successfully processed
                processed_urls.add(url)
                with open(PROCESSED_URLS_FILE, "a") as f:
                    f.write(f"{url}\n")
                    
            except Exception as e:
                print(f"Failed to read {url}: {e}")
                
    except KeyboardInterrupt:
        interrupted = True
        print("\nProcess interrupted by user (Ctrl+C). Saving progress so far...")
        
    # Combine all dataframes
    if len(list_of_dfs) > 1 or (len(list_of_dfs) == 1 and not os.path.exists(output_path)):
        complete_dataset = pd.concat(list_of_dfs, ignore_index=True)
        
        # Output as a new CSV file
        complete_dataset.to_csv(output_path, index=False)
        print(f"Successfully saved complete dataset to {output_path}")
        
        # Clean up the temporary processed URLs file since we successfully finished
        if not interrupted and os.path.exists(PROCESSED_URLS_FILE):
            os.remove(PROCESSED_URLS_FILE)
            print("Cleaned up temporary tracking file.")
            
    elif len(list_of_dfs) == 1 and os.path.exists(output_path):
        print("No new data to add. Dataset is already up to date.")
        # Clean up the temporary processed URLs file since we successfully finished
        if not interrupted and os.path.exists(PROCESSED_URLS_FILE):
            os.remove(PROCESSED_URLS_FILE)
            print("Cleaned up temporary tracking file.")
    else:
        print("No dataframes were created. Check your URLs.")

if __name__ == "__main__":
    create_dataset()
