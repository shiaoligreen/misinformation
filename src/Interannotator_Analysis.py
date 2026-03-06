from read_json import json_to_list
import os 
import pandas as pd
import glob
import numpy as np
from statsmodels.stats.inter_rater import fleiss_kappa
from sklearn.metrics import cohen_kappa_score


def calculate_agreement(df):
    """
    Calculate Fleiss' Kappa for each annotation feature using statsmodels.
    """
    print("\n--- Fleiss' Kappa (Overall Agreement) ---")
    
    # Features to analyze (excluding text and ID)
    features = ['all_caps', 'exclamation_marks', 'hedging', 'adjectives', 'unk']
    
    results_list = []
    
    for feature in features:
        # Pivot data: rows = items (ID), columns = annotators
        pivot_df = df.pivot(index='ID', columns='Annotator', values=feature)
        
        # Check if we have enough data
        complete_cases = pivot_df.dropna()
        
        if len(complete_cases) == 0:
            # print(f"  No complete cases found for {feature}")
            continue
        
        # Handle list values by normalizing them (sort to ignore order)
        if isinstance(complete_cases.iloc[0, 0], list):
            # Sort lists so order doesn't matter, then convert to string
            for col in complete_cases.columns:
                complete_cases[col] = complete_cases[col].apply(lambda x: str(sorted(x)) if isinstance(x, list) else str(x))
        
        # Get all unique categories
        all_values = complete_cases.values.flatten()
        categories = sorted(list(set(all_values)))
        
        # Create contingency table for statsmodels fleiss_kappa
        contingency_table = np.zeros((len(complete_cases), len(categories)))
        
        for i, (idx, row) in enumerate(complete_cases.iterrows()):
            for value in row.values:
                cat_idx = categories.index(value)
                contingency_table[i, cat_idx] += 1
        
        # Calculate Fleiss' Kappa using statsmodels
        kappa = fleiss_kappa(contingency_table)
        
        # Interpretation
        if kappa < 0:
            interpretation = "Poor"
        elif kappa < 0.20:
            interpretation = "Slight"
        elif kappa < 0.40:
            interpretation = "Fair"
        elif kappa < 0.60:
            interpretation = "Moderate"
        elif kappa < 0.80:
            interpretation = "Substantial"
        else:
            interpretation = "Almost Perfect"
        
        results_list.append({
            'Feature': feature,
            "Fleiss' Kappa": kappa,
            'Agreement': interpretation,
            'Items': len(complete_cases)
        })
    
    if results_list:
        results_df = pd.DataFrame(results_list).set_index('Feature')
        print(results_df.to_string(formatters={"Fleiss' Kappa": "{:,.3f}".format}))
    else:
        print("No results to display.")
    
    return results_df


def calculate_pairwise_agreement(df):
    """
    Calculate Cohen's Kappa for all pairs of annotators on their overlapping data.
    """
    print("\n--- Cohen's Kappa (Pairwise Agreement) ---")

    # Features to analyze
    features = ['all_caps', 'exclamation_marks', 'hedging', 'adjectives', 'unk']

    # Get unique annotators
    annotators = sorted(df['Annotator'].unique())
    
    # Initialize a dictionary to hold results for each feature
    pairwise_results = {feature: {} for feature in features}

    # --- CORRECTED LOGIC: Find common items for each pair FIRST ---
    common_items_map = {}
    for i in range(len(annotators)):
        for j in range(i + 1, len(annotators)):
            ann1, ann2 = annotators[i], annotators[j]
            
            # Get the set of unique IDs each annotator worked on
            ids1 = set(df[df['Annotator'] == ann1]['ID'])
            ids2 = set(df[df['Annotator'] == ann2]['ID'])
            
            # Find the intersection (common IDs)
            common_ids = ids1.intersection(ids2)
            common_items_map[f"{ann1} & {ann2}"] = list(common_ids)

    for feature in features:
        # Pivot data for the current feature
        pivot_df = df.pivot(index='ID', columns='Annotator', values=feature)

        # Handle list values by normalizing them
        if len(pivot_df) > 0 and isinstance(pivot_df.iloc[0, 0], list):
            for col in pivot_df.columns:
                pivot_df[col] = pivot_df[col].apply(
                    lambda x: str(sorted(x)) if isinstance(x, list) else str(x)
                )

        # --- CORRECTED LOGIC: Calculate Kappa based on pre-calculated common items ---
        for i in range(len(annotators)):
            for j in range(i + 1, len(annotators)):
                ann1, ann2 = annotators[i], annotators[j]
                pair_key = f"{ann1} & {ann2}"
                
                common_ids_for_pair = common_items_map[pair_key]

                if not common_ids_for_pair:
                    pairwise_results[feature][pair_key] = np.nan
                    continue

                # Filter the pivot table to only the common IDs for this pair
                pair_data = pivot_df.loc[common_ids_for_pair][[ann1, ann2]].dropna()

                if len(pair_data) < 2: # Not enough overlapping data for a meaningful score
                    pairwise_results[feature][pair_key] = np.nan
                    continue

                # Calculate Cohen's Kappa
                kappa = cohen_kappa_score(pair_data[ann1], pair_data[ann2])
                pairwise_results[feature][pair_key] = kappa

    # Convert the results dictionary to a DataFrame and print it
    if pairwise_results:
        results_df = pd.DataFrame(pairwise_results).T # Transpose to have features as rows
        results_df.index.name = 'Feature'
        print(results_df.to_string(float_format="%.3f"))
    else:
        print("No pairwise results to display.")
    
    return results_df

def get_dataframe():
    #build list of files in order to build dataframe
    #Default constants:
    PARENT = ".."
    DATA = "data"
    PREPROCESSED = "preprocessed"
    

    #Set path information:
    # Get the absolute path to the directory where this script is located (the 'src' folder)
    script_dir = os.path.dirname(os.path.abspath(__file__))

    #Build the absolute path to the 'data/raw' folder
    data_preproc_dir = os.path.join(script_dir, PARENT, DATA, PREPROCESSED)

    files = glob.glob(os.path.join(data_preproc_dir, "*annotations.json"))
    print(data_preproc_dir)
    print(files)

    all_annotations= pd.DataFrame()
    
    for i, file in enumerate(files):
        annotation = pd.DataFrame(json_to_list(file, "Annotator " + str(i)), columns=['Annotator', 'ID', 'Text', 'all_caps', 'exclamation_marks', 'hedging', 'adjectives', 'unk'])
        all_annotations = pd.concat([all_annotations, annotation])

    # Drop duplicate rows where all columns are identical
    all_annotations = all_annotations.drop_duplicates(subset=['Annotator', 'ID', 'Text'])
    
    return all_annotations


    
    





if __name__ == "__main__":
    # Get the annotation data
    df = get_dataframe()
    
    # Calculate inter-annotator agreement using Fleiss' Kappa (all  annotators)
    fleiss_results = calculate_agreement(df)
    
    # Calculate pairwise agreement using Cohen's Kappa (all pairs of annotators)
    pairwise_results = calculate_pairwise_agreement(df)

