# Data prep: adding one-hot encoded columns for each 
# annotation label and each annotator

import pandas as pd

mis_df = pd.read_csv('../data/annotations_1000.csv')

# ONE-HOT ENCODING

# Labels
mis_df['exclamation_marks_bin'] = mis_df['exclamation_marks'].apply(lambda x: 0 if x == '[]' else 1)
mis_df['all_caps_bin'] = mis_df['all_caps'].apply(lambda x: 0 if x == '[]' else 1)
mis_df['hedging_bin'] = mis_df['hedging'].apply(lambda x: 0 if x == '[]' else 1)
mis_df['adjectives_bin'] = mis_df['adjectives'].apply(lambda x: 0 if x == '[]' else 1)
mis_df['unk_bin'] = mis_df['unk'].apply(lambda x: 0 if x == '[]' else 1)

# Annotators
# Given Majority Vote, Jasmine & AI only represent 10% annotations, not included in stratification
ann_ohe = pd.get_dummies(mis_df['annotator'], dtype=int)
ann_ohe = ann_ohe.drop(columns=['Majority Vote', 'jasmine', 'ai'])

# Concatenate mis_df and one-hot encoded annotator dataframe
mis_df = pd.concat([mis_df, ann_ohe], axis=1)

# assert statements
# check one-hot encoded columns only contain 0 or 1:
assert set(mis_df['exclamation_marks_bin'].unique()).issubset({0, 1})
assert set(mis_df['all_caps_bin'].unique()).issubset({0, 1})
assert set(mis_df['hedging_bin'].unique()).issubset({0, 1})
assert set(mis_df['adjectives_bin'].unique()).issubset({0, 1})
assert set(mis_df['unk_bin'].unique()).issubset({0, 1})
# check correct annotator columns added to dataframe:
assert all(col in mis_df.columns for col in ['jennifer', 'nicole', 'rachelle', 'shiao-li'])

# Send dataframe to data folder in preparation for stratified splitting
mis_df.to_csv('../data/mis_df_ohe.csv', index=False)