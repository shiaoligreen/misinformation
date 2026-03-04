import json
import os
import pandas as pd

# compile the results
results = []

def json_to_list(filename, annotator):
    '''
    Function that takes a filepath and annotator string and iterates through the items
    to format the key info in a way that all annotations can be compiled into a dataframe
    for easy retrieval later when setting up the API interface.
    '''
    # steps to get the right path given that the files will be in different folders
    script_path = os.path.abspath(__file__)
    script_dir = os.path.dirname(script_path)
    parent_dir = os.path.dirname(script_dir)
    filepath = os.path.join(parent_dir, 'data', 'preprocessed', filename)
    
    with open(filepath, 'r') as file:
        data = json.load(file)
    # iterate through each text line
    for item in data:
        num_id = item['data']['Unnamed: 0']
        text = item['data']['text']

        # prep the annotation labels
        annotations = {
            'all_caps': [], 
            'exclamation_marks': [], 
            'hedging': [], 
            'adjectives': [], 
            'unk': []
        }

        # check that there are annotations and not blank
        if item['annotations'] and item['annotations'][0]['result']:
            for annotation in item['annotations'][0]['result']:
                label = annotation['value']['labels'][0]
                value = annotation['value']['text']
                
                if label in annotations:
                    annotations[label].append(value)
    
        # create the row
        row = [
            annotator, 
            num_id, 
            text, 
            annotations['all_caps'], 
            annotations['exclamation_marks'], 
            annotations['hedging'], 
            annotations['adjectives'], 
            annotations['unk']
        ]

        # add the row to the results
        results.append(row)

    # return list of results
    return results

# example usage in another file in main directory
# from src.read_json import json_to_list
# results = pd.DataFrame(json_to_list('shiao-li_annotations.json', "Annotator 1"), columns=['Annotator', 'ID', 'Text', 'all_caps', 'exclamation_marks', 'hedging', 'adjectives', 'unk'])