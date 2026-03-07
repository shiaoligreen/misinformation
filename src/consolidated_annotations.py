import sys
import os
import pandas as pd
from collections import Counter
from Interannotator_Analysis import get_dataframe, calculate_pairwise_agreement

def get_row_majority_vote(group, rankings_df):
    """
    Implements majority voting with a fallback to the best-ranked 
    annotator if no two people agree on the same annotation set.
    """
    features = ['all_caps', 'exclamation_marks', 'hedging', 'adjectives', 'unk']
    
    def get_annotator_combined(row):
        # only grab text-like strings
        combined = []
        for f in features:
            # Handle both list of lists and simple list of strings
            vals = [item[0] if isinstance(item, list) and len(item) > 0 else item for item in row[f]]
            combined.extend(vals)
        
        # sort alphabetically
        combined.sort()
        return tuple(combined)

    # Generate the 'combined' labels for every row in this ID group
    group['combined'] = group.apply(get_annotator_combined, axis=1)
    
    # Check for agreement
    counts = Counter(group['combined'])
    most_common, count = counts.most_common(1)[0]
    
    if count >= 2:
        # Return majority consensus
        winning_row = group[group['combined'] == most_common].iloc[0].copy()
    else:
        # Fallback to highest Cohen's Kappa ranking
        # Ensure name casing matches rankings_df
        group['Annotator'] = pd.Categorical(
            group['Annotator'], 
            categories=rankings_df["Annotator"], 
            ordered=True
        )
        winning_row = group.sort_values('Annotator').iloc[0].copy()
        
    return winning_row

def main():
    # Load the data and clean IDs
    print("Loading data...")
    df = get_dataframe()
    # Ensure ID starts at 0 and is an integer
    df['ID'] = df['ID'].fillna(0).astype(int)

    # Standardize annotator names
    df['Annotator'] = df['Annotator'].str.lower()
    annotators = ['jasmine', 'jennifer', 'nicole', 'rachelle', 'shiao-li']

    # Calculate rankings
    print("Calculating inter-annotator rankings...")
    pairwise_results_df = calculate_pairwise_agreement(df)
    human_averages = {}
    
    for person in annotators:
        cols = [col for col in pairwise_results_df.columns 
                if person in col.lower().split(' & ') and 'gemini' not in col.lower()]
        
        if cols:
            mean_val = pairwise_results_df[cols].values.mean()
            human_averages[person] = mean_val

    # Rank humans by their average Cohen's Kappa
    average_df = pd.DataFrame(list(human_averages.items()), columns=['Annotator', 'Average Kappa (No Gemini)'])
    average_df = average_df.sort_values(by='Average Kappa (No Gemini)', ascending=False).reset_index(drop=True)

    # majority vote
    print("Consolidating IDs 0-40 (Majority Vote)...")
    consolidated_df = (
        df[df['ID'].between(0, 40)].groupby('ID', group_keys=False)
        .apply(lambda x: get_row_majority_vote(x, average_df))
        .reset_index(drop=True)
    )
    consolidated_df["Annotator"] = "Majority Vote"
    if 'combined' in consolidated_df.columns:
        consolidated_df = consolidated_df.drop(columns=['combined'])

    # ranking by cohen's kappa
    print("Consolidating IDs 41+ (Ranked Selection)...")

    best_kappa = df[df['ID'] >= 41].copy()
    best_kappa['Annotator'] = pd.Categorical(
        best_kappa['Annotator'], 
        categories=average_df['Annotator'].tolist(), 
        ordered=True
    )

    best_kappa = (
        best_kappa.sort_values(['ID', 'Annotator'])
        .drop_duplicates(subset=['ID'], keep='first')
    )

    # Finalize and Export
    print("Finalizing and exporting...")
    final_df = pd.concat([consolidated_df, best_kappa], ignore_index=False)
    final_df = final_df.drop(columns=['ID'])

    # Setup export directory and path
    export_dir = '../data/preprocessed/'
    os.makedirs(export_dir, exist_ok=True)
    output_path = os.path.join(export_dir, 'consolidated_annotations.json')

    # Save to JSON
    final_df.to_json(output_path, orient='records', indent=2)
    print(f"Export complete: {output_path}")
    print(len(final_df))

if __name__ == "__main__":
    main()