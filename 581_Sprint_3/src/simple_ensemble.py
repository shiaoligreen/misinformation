'''
Simple Ensembling method using soft-voting

Citations: Claude AI supported code writing. Comments are my own.

'''

import numpy as np
from metrics import compute_metrics, print_report

def soft_vote(model_outputs: list[tuple[list[int], list[int], list[float]]], 
              threshold: float = 0.5):
    '''
    Ensembles predictions from multiple models with 
    probability averaging (soft-voting).

    Parameters:
        model_outputs:  one list of (preds, labels, probs) tuples per model.
                        Outputs should be from the same data split for each model.
        threshold:      decision boundary for class assignment, 
                        applied to the averaged probability, default = 0.5

    Returns:
        (preds, labels, probs) in the same format as individual models,
        where probs are the averaged probabilities across all models.
    '''
    # Check that ground-truth labels are all matching to ensure that 
    # correct data has been passed to function
    labels_list = [output[1] for output in model_outputs]
    if not all(l == labels_list[0] for l in labels_list):
        raise ValueError(
            "Labels differ across models — ensure all outputs are from "
            "the same split and task."
        )

    # probability matrix shape (n_models, n_examples)
    prob_matrix = np.array([output[2] for output in model_outputs])
    # average across models, one mean probability per example
    avg_probs = prob_matrix.mean(axis=0)
    # turns mean probability into binary class prediction
    preds = [int(p >= threshold) for p in avg_probs.tolist()]
    labels = model_outputs[0][1]
    
    return preds, labels, avg_probs.tolist()

