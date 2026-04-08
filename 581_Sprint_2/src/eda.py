# EDA in preparation for splitting data into train/dev/test sets

import pandas as pd


mis_df = pd.read_csv('../data/annotations_1000.csv')

# LABEL DISTRIBUTION

# define function to explore distributions
def label_distribution(df, labels):
    '''
    Takes a dataframe and a list of column names corresponding to an annotation label.
    Calculates the distribution of each label. 
    '''
    for label in labels:
        print(f"\n---- {label} -----")
        label_dist = df[label].value_counts(normalize=True)
        print(label_dist)

labels = ['misinformation_label', 'opinion_label', 'annotator']
label_distribution(mis_df, labels)

# TEXT LENGTH DISTRIBUTION & TROUBLE-SHOOTING

mis_df['text_length'] = mis_df['text'].astype(str).str.len()
text_len_dist = mis_df['text_length'].describe()
print(f"\n---- Text Length ----")
print(text_len_dist)

# check for texts that did not correctly transfer from json
mis_df[mis_df['text_length'] < 10]

# COMBINATIONS IN DATASET

# Verify unique combinations of misinformation label, opinion label and annotator 
unique_combos = mis_df.groupby(labels).size().reset_index(
    name='count').sort_values('count', ascending=False)
print(f"\n---- Unique Combinations ----\n")
print(unique_combos)

# COMBINATIONS WITH JASMINE, MAJORITY VOTE & AI GROUPED

# Verify unique combinations of misinformation label, opinion label and annotator, with Jasmine & Majority vote grouped
unique_combos_collapse_annot = mis_df.replace(
    {'Majority Vote': 'Majority Vote, Jasmine, AI', 
     'jasmine': 'Majority Vote, Jasmine, AI', 
     'ai': 'Majority Vote, Jasmine, AI'}).groupby(labels).size().reset_index(name='count')#.sort_values('count', ascending=False)
print(f"\n---- Unique Combinations (Maj Vote, Jasmine, AI grouped) ----\n")
print(unique_combos_collapse_annot)

