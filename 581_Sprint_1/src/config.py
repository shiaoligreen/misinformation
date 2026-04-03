"""
Central configuration for all baseline models.
Update paths and hyperparameters here — nothing else needs to change.
"""

from pathlib import Path

# PATH info
_BASE = Path(__file__).resolve().parent

DATA_DIR      = _BASE.parents[1] / "data" / "final_splits"

#required for CNN fasttext embeddings
FASTTEXT_PATH = _BASE.parents[2] / "cc.en.300.vec"

# Reproducibility seed
SEED = 581

# CNN hyperparameters based on paper "Convolutional Neural Networks for Sentence Classification" by Yoon Kim 2014
CONFIG = {
    "embed_dim":    300,        # must match the .vec file
    "num_filters":  100,        # feature maps per filter size
    "filter_sizes": [3, 4, 5],  # classic Kim (2014)
    "dropout":      0.5,        # Kim (2014)
    "lr":           1e-3,
    "batch_size":   32,
    "max_epochs":   50,
    "patience":     5,          # early stopping on dev macro-F1
    "max_len":      100,        # truncate sequences longer than this
}
