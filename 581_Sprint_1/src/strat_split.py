# Stratification & Splitting of dataset

from iterstrat.ml_stratifiers import MultilabelStratifiedShuffleSplit
import numpy as np
import pandas as pd

random_seed = 344

mis_df_ohe = pd.read_csv('../data/mis_df_ohe.csv')


# Below code written with support from Claude AI in using iterstrat package

# labels for stratification
labels_for_strat = mis_df_ohe[['opinion_label', 'misinformation_label', 
                        'jennifer', 'nicole', 'rachelle', 'shiao-li']]

# first split in to train set - combined dev/test set: 60% - 40%
split_1 = MultilabelStratifiedShuffleSplit(n_splits=1, test_size=0.4, random_state=random_seed)
train_idx, temp_idx = next(split_1.split(mis_df_ohe, labels_for_strat))

temp_df = mis_df_ohe.iloc[temp_idx]
temp_labels = labels_for_strat.iloc[temp_idx]

# second split dev set - test set: 50% - 50% 
split_2 = MultilabelStratifiedShuffleSplit(n_splits=1, test_size=0.5, random_state=random_seed)
dev_idx, test_idx = next(split_2.split(temp_df, temp_labels))

# add column for split label
mis_df_ohe['split'] = 'train'
mis_df_ohe.iloc[temp_idx[dev_idx], mis_df_ohe.columns.get_loc('split')] = 'dev'
mis_df_ohe.iloc[temp_idx[test_idx], mis_df_ohe.columns.get_loc('split')] = 'test'

# check splits
print(f"\n---- Verify Splits ----")
print(mis_df_ohe['split'].value_counts())

# check distributions within splits
print(f"\n---- Verify distributions within splits ----")
for split in ['train', 'dev', 'test']:
    print(f"\n---- {split} ----")
    subset = mis_df_ohe[mis_df_ohe['split'] == split]
    print(subset['opinion_label'].value_counts(normalize=True))
    print(subset['misinformation_label'].value_counts(normalize=True))
    print(subset['annotator'].value_counts(normalize=True))

# send dataframe with all sets together to csv
mis_df_ohe.to_csv('../data/sets/mis_df_with_all_splits.csv', index=False)

# split dataframe into separate csvs for each set: train/dev/test
mis_df_ohe[mis_df_ohe['split'] == 'train'].to_csv('../data/sets/mis_df_train.csv', index=False)
mis_df_ohe[mis_df_ohe['split'] == 'dev'].to_csv('../data/sets/mis_df_dev.csv', index=False)
mis_df_ohe[mis_df_ohe['split'] == 'test'].to_csv('../data/sets/mis_df_test.csv', index=False)

# assert statement to check all rows accounted for:
assert mis_df_ohe['split'].isna().sum() == 0  
