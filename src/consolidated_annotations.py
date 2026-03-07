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
        # Combine all values from all features into one list
        combined = []
        for f in features:
            combined.extend(row[f])
        # Order by start character to ensure same order for comparison
        combined.sort(key=lambda x: x[1] if len(x) > 1 else 0)
        return tuple(tuple(item) for item in combined)

    # 1. Generate the 'combined' labels for every row in this ID group
    group['combined'] = group.apply(get_annotator_combined, axis=1)
    
    # 2. Check for agreement
    counts = Counter(group['combined'])
    most_common, count = counts.most_common(1)[0]
    
    if count >= 2:
        # Return majority consensus
        winning_row = group[group['combined'] == most_common].iloc[0].copy()
    else:
        # Fallback to highest Cohen's Kappa ranking
        group['Annotator'] = pd.Categorical(
            group['Annotator'], 
            categories=rankings_df["Annotator"], 
            ordered=True
        )
        winning_row = group.sort_values('Annotator').iloc[0].copy()
        
    return winning_row

def main():
    # 1. Load the data and clean IDs
    print("Loading data...")
    df = get_dataframe()
    df['ID'] = df['ID'].fillna(0).astype(int)

    # 2. Calculate Pairwise Agreement rankings
    print("Calculating inter-annotator rankings...")
    pairwise_results_df = calculate_pairwise_agreement(df)
    
    annotators = ['Jasmine', 'Jennifer', 'nicole', 'rachelle', 'shiao-li']
    human_averages = {}
    
    for person in annotators:
        # Calculate the average for each person across all human pairs
        cols = [col for col in pairwise_results_df.columns 
                if person in col.split(' & ') and 'Gemini' not in col]
        
        if cols:
            mean_val = pairwise_results_df[cols].values.mean()
            human_averages[person] = mean_val

    # Rank humans by their average Cohen's Kappa
    average_df = pd.DataFrame(list(human_averages.items()), columns=['Annotator', 'Average Kappa (No Gemini)'])
    average_df = average_df.sort_values(by='Average Kappa (No Gemini)', ascending=False).reset_index(drop=True)

    # 3. Apply Majority Voting to IDs 0-40
    print("Consolidating IDs 0-40 (Majority Vote)...")
    consolidated_df = (
        df[df['ID'].between(0, 40)].groupby('ID', group_keys=False)
        .apply(lambda x: get_row_majority_vote(x, average_df))
        .reset_index(drop=True)
    )
    consolidated_df["Annotator"] = "Majority Vote"
    consolidated_df = consolidated_df.drop(columns=['combined'])

    # 4. Apply Ranked Selection for remaining IDs (41+)
    print("Consolidating IDs 41+ (Ranked Selection)...")
    human_priority = average_df['Annotator'].tolist()
    full_priority = human_priority + ['Gemini']

    best_kappa = df[df['ID'] >= 41].copy()
    best_kappa['Annotator'] = pd.Categorical(
        best_kappa['Annotator'], 
        categories=full_priority, 
        ordered=True
    )

    # Sort and keep the highest-ranked annotator for each ID
    best_kappa = (
        best_kappa.sort_values(['ID', 'Annotator'])
        .drop_duplicates(subset=['ID'], keep='first')
    )

    # 5. Finalize and Export
    print("Finalizing and exporting...")
    final_df = pd.concat([consolidated_df, best_kappa], ignore_index=True)
    final_df = final_df.drop(columns=['ID'])

    # Setup export directory and path
    export_dir = '../data/preprocessed/'
    os.makedirs(export_dir, exist_ok=True)
    output_path = os.path.join(export_dir, 'consolidated_annotations.json')

    # Save to JSON
    final_df.to_json(output_path, orient='records', indent=2)
    print(f"Export complete: {output_path}")

if __name__ == "__main__":
    main()