import pandas as pd
import os
import csv

def build_dataset(file_containing_paths=None, path_col=None, data_cols=None, output_path=None,temp_file=None ):
    """
    Parameters (optional):
    file_containing_paths: parameter to specify file path for a file containing links to csv datafiles.

    path_col: parameter to specify the name of the column within the file_containing_paths csv file that has path specification

    data_cols: columns to be extracted from source data files and used to build the complete dataset

    output_path: parameter to specify a file path for where the complete dataset will be built.

    temp_path: parameter to specify a file path for process file that tracks progress during dataset building.
    
    Purpose:
    build_dataset() builds a single dataset store in a .csv file from multiple datasets that are stored at the urls or file paths contained in 
    another csv file. The default path given here is relative to the src directory, where this code is expected to be run.
    
    """
    #Set default file and path info as constants
    PARENT = ".."
    DATA = "data"
    RAW = "raw"
    TEMP_FILE = "processed_urls_temp.txt"
    DEFAULT_OUTPUT = "complete_dataset.csv"
    LINK_FILE = "links_to_data.csv"

    #Set path information:
    # Get the absolute path to the directory where this script is located (the 'src' folder)
    script_dir = os.path.dirname(os.path.abspath(__file__))

    #Build the absolute path to the 'data/raw' folder
    data_raw_dir = os.path.join(script_dir, PARENT, DATA, RAW)


    ##set defaults for optional parameters ##

    #set default file path of csv file containing the links to data files
    if file_containing_paths is None:
        file_containing_paths = os.path.join(data_raw_dir, LINK_FILE)

    #set default column name of links or paths contained in file_containing_paths
    if path_col is None:
        path_col = "url"

    #set default path + filename where the full corpus will be created
    if output_path is None:
        output_path = os.path.join(data_raw_dir, DEFAULT_OUTPUT)

    #set default columns names from source datafile to be extracted to build the corpus
    data_cols=["text", "label"]
    
    #set default temp file for tracking which files have been processed
    temp_file = os.path.join(data_raw_dir, TEMP_FILE)

    ##Start processing the source datasets ##
    
    #  get list of links to datasets that will be included in the complete dataset
    links_df = pd.read_csv(file_containing_paths, usecols=[path_col])
    
    # Keep track of which URLs have already been successfully processed
    processed_urls = set()
    
    #if the file containing the processed urls exists, then, open it and add the urls to a set.
    if os.path.exists(temp_file):
        with open(temp_file, "r") as f:
            processed_urls = set(line.strip() for line in f)
            
    present_df = []

    # If the dataset already exists in an output file, append to it, do not overwrite it.
    # Load it into present_df so it gets concatenated with any new data
    if os.path.exists(output_path):
        # If the tracking file doesn't exist but the output file does, it means a previous run 
        # finished completely. We should warn the user and exit to prevent duplicating the whole dataset.
        if not os.path.exists(temp_file):
            print(f"Error: The output file '{output_path}' already exists, and there is no interrupted progress to resume.")
            print("If you want to rebuild the dataset from scratch, please delete the existing output file first.")
            return
            
        print(f"Found existing dataset at {output_path}. Loading it to append new data...")
        existing_df = pd.read_csv(output_path)
        present_df.append(existing_df)
    
    # Iterate through the URLs 
    print("Starting dataset creation. Press Ctrl+C at any time to safely stop the process.")
    interrupted = False
    try:
        for url in links_df[path_col]:

            #if the url is in the temporary processed_urls file, skip it so that work is not duplicated and continue 
            #to the next url in the loop
            if url in processed_urls:
                print(f"Skipping already processed URL: {url}")
                continue

            #if the url is not contained in the processed_urls file:
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
                df = pd.read_csv(url, header=header_row_idx, usecols=data_cols)

                #append this dataframe to the present_df dataframe
                present_df.append(df)
                print(f"Successfully read: {url}")
                
                # Mark this URL as successfully processed by adding it to the temp file
                processed_urls.add(url)
                with open(temp_file, "a") as f:
                    f.write(f"{url}\n")
                    
            except Exception as e:
                print(f"Failed to read {url}: {e}")

    #handle user interrupts by acknowledging it onscreen and             
    except KeyboardInterrupt:
        interrupted = True
        print("\nProcess interrupted by user (Ctrl+C). Saving progress so far...")
        
    # Concatenate the dataframe that is currently being processed to the if the complete dataset dataframe if
    # there is more than 1 row or i there is only 1 row and the output file does not exist.
    if len(present_df) > 1 or (len(present_df) == 1 and not os.path.exists(output_path)):
        complete_dataset = pd.concat(present_df, ignore_index=True)
        
        # Output as a new CSV file
        complete_dataset.to_csv(output_path, index=False, quoting=csv.QUOTE_ALL)
        print(f"Saved complete dataset to {output_path}")
        
        # Remove the temporary processed URLs file since we successfully finished
        if not interrupted and os.path.exists(temp_file):
            os.remove(temp_file)
            print("Removed temporary tracking file.")
            
    elif len(present_df) == 1 and os.path.exists(output_path):
        print("No new data to add. Dataset is already up to date.")
        # Remove the temporary processed URLs file since we successfully finished
        if not interrupted and os.path.exists(temp_file):
            os.remove(temp_file)
            print("Removed temporary tracking file.")
    else:
        print("No dataframes were created. Check your URLs.")



    








    #Don't run anything automatically, if imported.
if __name__ == "__main__":
    build_dataset()


