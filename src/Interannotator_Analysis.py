import os
import glob
import pandas as pd
import numpy as np
from statsmodels.stats.inter_rater import fleiss_kappa
from sklearn.metrics import cohen_kappa_score


def calculate_fleiss(df, include_gemini=True):
    """
    Calculate Fleiss' Kappa for each annotation feature using statsmodels.
    Optionally exclude Gemini's annotations from the calculation.
    """
    if not include_gemini:
        df = df[df['Annotator'] != 'Gemini'].copy()
        print("\n--- Fleiss' Kappa (Overall Agreement - Excluding Gemini) ---")
    else:
        print("\n--- Fleiss' Kappa (Overall Agreement - Including Gemini) ---")
    
    # Features to analyze (excluding text and ID)
    features = ['all_caps', 'exclamation_marks', 'hedging', 'adjectives', 'unk']
    
    results_list = []
    
    for feature in features:
        # Pivot data: rows = items (ID), columns = annotators
        pivot_df = df.pivot(index='ID', columns='Annotator', values=feature)
        
        # Ensure we are comparing strings (especially for lists)
        for col in pivot_df.columns:
            pivot_df[col] = pivot_df[col].apply(lambda x: str(sorted(x)) if isinstance(x, list) else str(x))

        # Check if we have enough data (at least 2 annotators having data for the same ID)
        complete_cases = pivot_df.dropna(thresh=2)
        
        if len(complete_cases) < 2:
            # print(f"  No complete cases found for {feature}")
            continue
        
        # Get all unique categories
        all_values = complete_cases.values.flatten()
        # Filter out 'nan' strings if any appeared
        categories = sorted(list(set([v for v in all_values if v != 'nan'])))
        
        # Create contingency table for statsmodels fleiss_kappa
        # Rows = items, Columns = categories
        contingency_table = np.zeros((len(complete_cases), len(categories)))
        
        for i, (idx, row) in enumerate(complete_cases.iterrows()):
            # count only the actual values, ignoring NaNs
            found_count = 0
            for value in row.values:
                if value in categories:
                    cat_idx = categories.index(value)
                    contingency_table[i, cat_idx] += 1
                    found_count += 1
            
            # Fleiss' Kappa in statsmodels requires every row to sum to the same number of raters.
            # Since some items were seen by 2 raters, some by 3, etc., 
            # we need to skip any row that doesn't have the MAX number of raters for this feature,
            # OR we need to only use items seen by exactly N raters.
            
        # Standardize: statsmodels fleiss_kappa expects all items to have the same number of ratings.
        # We will filter complete_cases to only those items that have the maximum number of ratings found in this subset.
        row_sums = contingency_table.sum(axis=1)
        max_raters = int(row_sums.max())
        
        final_contingency_table = contingency_table[row_sums == max_raters]
        
        if len(final_contingency_table) < 2:
            continue

        # Calculate Fleiss' Kappa using statsmodels
        kappa = fleiss_kappa(final_contingency_table)
        
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


def overall_fleiss_kappa(df, include_gemini=True):
    """
    Calculate a single overall Fleiss' Kappa across all features combined.

    Each (item, feature) pair is treated as one binary rating task: annotators
    either flagged the tag (1) or did not (0).  All such rows are stacked into
    one contingency table and a single kappa is returned.
    """
    if not include_gemini:
        df = df[df['Annotator'] != 'Gemini'].copy()

    features = ['all_caps', 'exclamation_marks', 'hedging', 'adjectives', 'unk']

    def _is_present(x):
        if x is None:
            return False
        if isinstance(x, float) and np.isnan(x):
            return False
        if isinstance(x, list):
            return len(x) > 0
        if isinstance(x, str):
            return x not in ('[]', '', 'nan', 'None')
        return bool(x)

    rows = []
    for feature in features:
        pivot_df = df.pivot(index='ID', columns='Annotator', values=feature)
        # keep only items with at least 2 annotators
        complete = pivot_df.dropna(thresh=2)
        # standardise to the most common rater count so all rows sum to the same n
        rater_counts = complete.notna().sum(axis=1)
        max_raters = int(rater_counts.max())
        complete = complete[rater_counts == max_raters]

        for _, row in complete.iterrows():
            yes = sum(_is_present(v) for v in row if not (isinstance(v, float) and np.isnan(v)))
            no  = max_raters - yes
            rows.append([no, yes])

    if len(rows) < 2:
        print("Not enough data for overall Fleiss' Kappa.")
        return None

    contingency_table = np.array(rows)
    # drop any rows whose sum differs from the majority (edge cases)
    row_sums = contingency_table.sum(axis=1)
    mode_n = int(pd.Series(row_sums).mode()[0])
    contingency_table = contingency_table[row_sums == mode_n]

    kappa = fleiss_kappa(contingency_table)

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

    label = "Excluding Gemini" if not include_gemini else "Including Gemini"
    print(f"\n--- Overall Fleiss' Kappa ({label}) ---")
    print(f"  κ = {kappa:.3f}  ({interpretation})  [{len(contingency_table)} item-feature pairs]")
    return kappa


def calculate_pairwise_agreement(df):
    """
    Calculate Cohen's Kappa for all pairs of annotators on their overlapping data.
    """
    print("\n--- Cohen's Kappa (Pairwise Agreement) ---")

    features = ['all_caps', 'exclamation_marks', 'hedging', 'adjectives', 'unk']
    annotators = sorted(df['Annotator'].unique())
    
    if len(annotators) < 2:
        print("Not enough annotators to calculate pairwise agreement.")
        return pd.DataFrame()

    pairwise_results = {feature: {} for feature in features}

    # Iterate through each unique pair of annotators
    for i in range(len(annotators)):
        for j in range(i + 1, len(annotators)):
            ann1, ann2 = annotators[i], annotators[j]
            pair_key = f"{ann1} & {ann2}"

            # Filter the original DataFrame to just the data for this pair
            df_pair = df[df['Annotator'].isin([ann1, ann2])]

            for feature in features:
                # Pivot the pair's data to align their annotations by item ID
                pivot_pair = df_pair.pivot(index='ID', columns='Annotator', values=feature)

                # Normalize list values to strings for comparison
                for col in pivot_pair.columns:
                    pivot_pair[col] = pivot_pair[col].apply(lambda x: str(sorted(x)) if isinstance(x, list) else str(x))

                # Drop rows where AT LEAST ONE of the annotators has a missing value.
                # In this specific case, pivot produced strings or 'nan' for the IDs that don't match exactly.
                # However, pivot usually results in NaN (float) for missing columns/rows which dropna handles.
                # We need to drop rows effectively.
                aligned_data = pivot_pair.replace('nan', np.nan).dropna()

                # If there are fewer than 2 overlapping items, Kappa is not meaningful
                if len(aligned_data) < 2:
                    pairwise_results[feature][pair_key] = np.nan
                    continue

                # Extract the two columns of annotations to compare
                col1 = aligned_data[ann1]
                col2 = aligned_data[ann2]
                
                # Calculate Cohen's Kappa for the aligned annotations
                kappa = cohen_kappa_score(col1, col2)
                pairwise_results[feature][pair_key] = kappa

    # Convert results to a DataFrame
    results_df = pd.DataFrame(pairwise_results).T
    results_df.index.name = 'Feature'
    
    if results_df.isnull().all().all():
        print("No overlapping data found for any annotator pairs to calculate Kappa.")
        # Return an empty frame so the notebook doesn't try to plot nulls
        return pd.DataFrame()

    print(results_df.to_string(float_format="%.3f"))
    return results_df

def get_dataframe():
    """
    Reads all preprocessed '*_annotations_cleaned.json' files from the 
    '../data/preprocessed' directory, combines them into a single DataFrame,
    and assigns annotator names based on the filenames.
    """
    # --- Define Paths ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    preprocessed_dir = os.path.abspath(os.path.join(script_dir, '..', 'data', 'preprocessed'))

    # --- Find Preprocessed Files ---
    cleaned_files = glob.glob(os.path.join(preprocessed_dir, "*_annotations_cleaned.json"))
    
    if not cleaned_files:
        print(f"Warning: No '*_annotations_cleaned.json' files found in {preprocessed_dir}")
        return pd.DataFrame()
        
    print(f"Found {len(cleaned_files)} cleaned annotation files.")

    all_annotations_df = pd.DataFrame()
    
    # --- Process Each Cleaned File ---
    for filepath in cleaned_files:
        # Read the cleaned JSON file directly into a DataFrame
        temp_df = pd.read_json(filepath, orient='records')
        
        # Extract the annotator's name from the filename
        base_name = os.path.basename(filepath)
        annotator_name = base_name.replace('_annotations_cleaned.json', '').replace('_annotations.json', '')
        
        # Add the 'Annotator' column
        temp_df['Annotator'] = annotator_name

        # Standardize ID and Text columns in case they were not cleaned properly
        for col in ['id', 'ID', 'Unnamed: 0']:
            if col in temp_df.columns:
                temp_df.rename(columns={col: 'ID'}, inplace=True)
                break
        for col in ['text', 'Text']:
            if col in temp_df.columns:
                temp_df.rename(columns={col: 'Text'}, inplace=True)
                break
        
        # Append to the main DataFrame
        all_annotations_df = pd.concat([all_annotations_df, temp_df], ignore_index=True)

    print("All cleaned files have been loaded and combined.")

    # --- Final Cleanup ---
    if not all_annotations_df.empty:
        # Deduplicate across the final combined dataset
        all_annotations_df.drop_duplicates(subset=['Annotator', 'ID', 'Text'], keep='first', inplace=True)
    
    return all_annotations_df


    
    





if __name__ == "__main__":
    # Get the annotation data
    df = get_dataframe()
    
    # Calculate inter-annotator agreement using Fleiss' Kappa (including Gemini)
    fleiss_results = calculate_fleiss(df, include_gemini=True)
    
    # Calculate inter-annotator agreement using Fleiss' Kappa (excluding Gemini)
    human_only_results = calculate_fleiss(df, include_gemini=False)
    

    
    # Calculate overall Fleiss' Kappa (single value across all features)
    overall_fleiss_kappa(df, include_gemini=True)
    overall_fleiss_kappa(df, include_gemini=False)

    # Calculate pairwise agreement using Cohen's Kappa (all pairs of annotators)
    pairwise_results = calculate_pairwise_agreement(df)

