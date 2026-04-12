'''

Citations: 
Claude AI supported code writing. Comments are my own.

Motivation:
The simple soft-vote ensemble method averages the probabilities of the logistic 
regression and the CNN models equally. This ensemble method addressed the class 
imbalances and differences between the models.

'''

import numpy as np

def _weighted_average_probs(
    model_outputs: list[tuple[list[int], list[int], list[float]]],
    f1_weights: list[float],
) -> np.ndarray:
    '''
    Calculates the weighted average. 

    The Macro F1 score was used to scaled the probabilities, and the weights are
    normalized. 

    Parameters
    ──────────
    model_outputs : one list of (preds, labels, probs) tuples per model.
    f1_weights    : list of Macro F1 scores for each model in the same order
                    as model_outputs.

    Returns
    ───────
    An array with the weighted-average probabilities for each instance. This measure
    is used as the ensemble's confidence that an instance is in the predicted class
    (opinion, misinformation).
    '''
    # Normalize and change weights to an array
    weights = np.array(f1_weights, dtype=np.float64)
    weights = weights / weights.sum()

    # Create the probability matrix   
    prob_matrix = np.array([output[2] for output in model_outputs])  

    # Apply weighted averages to probability matrix
    weighted_probs = (prob_matrix * weights[:, np.newaxis]).sum(axis=0) 

    return weighted_probs


def _tune_threshold(
    avg_probs: np.ndarray,
    labels: list[int],
    candidates: np.ndarray | None = None,
) -> tuple[float, list[dict]]:
    '''
    Check different decision thresholds and return the one corresponding to the best
    Macro F1 score. 

    Parameters
    ──────────
    avg_probs  : np.ndarray — weighted-average probabilities.
    labels     : list[int]  — ground-truth labels.
    candidates : array of thresholds to try. 

    Returns
    ───────
    best_threshold : float
        The threshold value that produced the highest Macro F1.
    sweep_table : list[dict]
        One dict per threshold with keys: threshold, macro_f1, f1_class0,
        f1_class1, accuracy.
    '''
    if candidates is None:
        # thresholds to try
        candidates = np.arange(0.30, 0.71, 0.05)

    best_threshold = 0.5
    best_f1 = -1.0
    sweep_table = []

    for thresh in candidates:
        # Applies the threshold 
        preds = [int(p >= thresh) for p in avg_probs]

        # Calculates class F1 and Macro F1
        f1_scores = []
        for cls in (0, 1):
            tp = sum(p == cls and l == cls for p, l in zip(preds, labels))
            fp = sum(p == cls and l != cls for p, l in zip(preds, labels))
            fn = sum(p != cls and l == cls for p, l in zip(preds, labels))
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (2 * precision * recall / (precision + recall)
                  if (precision + recall) > 0 else 0.0)
            f1_scores.append(f1)

        macro_f1 = float(np.mean(f1_scores))
        accuracy = sum(p == l for p, l in zip(preds, labels)) / len(labels)

        sweep_table.append({
            "threshold": round(float(thresh), 2),
            "macro_f1":  round(macro_f1, 4),
            "f1_class0": round(f1_scores[0], 4),
            "f1_class1": round(f1_scores[1], 4),
            "accuracy":  round(accuracy, 4),
        })

        if macro_f1 > best_f1:
            best_f1 = macro_f1
            best_threshold = float(thresh)

    return best_threshold, sweep_table



def motivated_soft_vote(
    model_outputs: list[tuple[list[int], list[int], list[float]]],
    f1_weights: list[float],
    threshold: float | None = None,
    print_sweep: bool = True,
) -> tuple[list[int], list[int], list[float]]:
    '''
    Combines the models (CNN, logistic regression, logistic regression + embeddings)
    into one prediction according to weights and finds the best cut-off for target
    decisions.  

    1. Weighted average
    Scaled probabilities by Macro F1 to weigh better models higher and normalized 
    weights.

    2. Threshold tuning
    Check thresholds from 0.30 to 0.70 in steps of 0.05. 
    Select the threshold that maximises Macro F1. 

    3. Hard predictions
    Apply the best threshold to the weighted-average probabilities

    Parameters
    ──────────
    model_outputs : list of (preds, labels, probs) tuples per model. 
                    All from the same data split and task.
    f1_weights    : list of Macro F1 scores (floats) per model in the
                    same order as model_outputs. 
    threshold     : float or None.
                    If None, the threshold is tuned automatically on the dev labels.
                    If a float is provided, that value is used.
    print_sweep   : bool, default True.
                    If True and threshold is None, prints the full sweep table
                    so the threshold choice is shown and reproducible.

    Returns
    ───────
    (preds, labels, probs) in the same format as models and 
    simple_ensemble.soft_vote().

        preds  : list[int]   — hard binary predictions (0 or 1)
        labels : list[int]   — ground-truth labels (unchanged from input)
        probs  : list[float] — weighted-average probabilities for class 1
    '''


    # Check that the models were run on the same split 
    labels_list = [output[1] for output in model_outputs]
    if not all(l == labels_list[0] for l in labels_list):
        raise ValueError(
            "Labels differ across models — ensure all outputs are from "
            "the same split and task."
        )

    if len(f1_weights) != len(model_outputs):
        raise ValueError(
            f"f1_weights has {len(f1_weights)} entries but model_outputs "
            f"has {len(model_outputs)} — lengths must match."
        )

    if any(w <= 0 for w in f1_weights):
        raise ValueError("All f1_weights must be positive floats.")

    labels = labels_list[0]

    # weighted average
    avg_probs = _weighted_average_probs(model_outputs, f1_weights)

    # threshold selection
    if threshold is None:
        # Tune on the dev labels
        best_threshold, sweep_table = _tune_threshold(avg_probs, labels)

        if print_sweep:
            # Print sweep table
            print("\n  Threshold sweep (Macro F1 criterion):")
            print(f"  {'Threshold':>10}  {'Macro F1':>10}  "
                  f"{'F1 (cl.0)':>10}  {'F1 (cl.1)':>10}  {'Accuracy':>10}")
            print(f"  {'-'*58}")
            for row in sweep_table:
                # Mark selected threshold
                marker = " ◄" if row["threshold"] == round(best_threshold, 2) else ""
                print(f"  {row['threshold']:>10.2f}  {row['macro_f1']:>10.4f}  "
                      f"{row['f1_class0']:>10.4f}  {row['f1_class1']:>10.4f}  "
                      f"{row['accuracy']:>10.4f}{marker}")
            print(f"\n  Selected threshold: {best_threshold:.2f}")

        threshold = best_threshold

    # Hard predictions. Apply threshold to weighted-average probabilities
    preds = [int(p >= threshold) for p in avg_probs.tolist()]
    return preds, labels, avg_probs.tolist()
