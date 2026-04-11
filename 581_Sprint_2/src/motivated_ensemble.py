'''
motivated_ensemble.py
─────────────────────
Sprint 2 — Motivated Ensembling for COLX 523 / COLX 581.

Citations: Claude AI supported code writing. Comments are my own.

Motivation
──────────
The simple soft-vote ensemble (simple_ensemble.py) averages probabilities
from all models equally. This is a reasonable starting point, but it ignores
two known properties of our models and dataset:

  1. Models differ in performance.
     For opinion_label, the dev Macro F1 scores are:
       TextCNN                  : 0.7090
       LogReg                   : 0.6931
       LogReg (+ embeddings)    : 0.7076
     Treating all three as equally reliable underweights the stronger models.
     We use each model's Macro F1 as its weight, so better models contribute
     proportionally more to the final probability score.

  2. Class imbalance shifts the optimal decision boundary away from 0.5.
     Dev set composition: 58.5% not-opinion (class 0), 41.5% opinion (class 1).
     All three models were trained with class_weight='balanced' / pos_weight,
     which overcorrects toward the minority class during training. This pushes
     raw predicted probabilities above what the true class prior warrants,
     causing the default 0.5 threshold to over-predict opinion (class 1).
     We correct for this by sweeping candidate thresholds on the dev set and
     selecting the one that maximises Macro F1 — the same criterion used to
     tune the baselines — rather than assuming 0.5 is optimal.

     Macro F1 is the right tuning criterion here because it weights both
     classes equally regardless of support, which directly addresses the
     class imbalance: we care about opinion-class performance as much as
     not-opinion performance.

Documented limitation
─────────────────────
Threshold tuning and final evaluation both use the dev set, introducing a
small optimistic bias. With only 200 dev examples a held-out calibration
fold is not feasible without further fragmenting an already small dataset.
This is acknowledged explicitly in the sprint write-up.

Usage in Sprint_2.ipynb
───────────────────────
    import motivated_ensemble as mot_ens

    for task in TARGETS:
        mot_results = mot_ens.motivated_soft_vote(
            model_outputs=[
                results[f"TextCNN — {task}"],
                results[f"LogReg — {task}"],
                results[f"LogReg (+ embeddings) — {task}"],
            ],
            f1_weights=[0.7090, 0.6931, 0.7076],   # dev Macro F1 per model
        )
        preds, labels, probs = mot_results
        ...
'''

import numpy as np


# ── helpers ───────────────────────────────────────────────────────────────────

def _weighted_average_probs(
    model_outputs: list[tuple[list[int], list[int], list[float]]],
    f1_weights: list[float],
) -> np.ndarray:
    '''
    Compute a weighted average of predicted probabilities across models.

    Each model's probability stream is scaled by its Macro F1 score so that
    higher-performing models contribute more to the ensemble score.
    The weights are normalised inside this function so the caller does not
    need to pre-normalise them.

    Parameters
    ──────────
    model_outputs : list of (preds, labels, probs) tuples, one per model.
    f1_weights    : list of Macro F1 scores, one per model, in the same order
                    as model_outputs.

    Returns
    ───────
    np.ndarray of shape (n_examples,) — one weighted-average probability
    per example, representing the ensemble's confidence that the example
    belongs to class 1.
    '''
    # Convert weights to a numpy array and normalise so they sum to 1.
    # Normalising means the weighted average stays in [0, 1] and is directly
    # comparable to the individual model probabilities.
    weights = np.array(f1_weights, dtype=np.float64)
    weights = weights / weights.sum()

    # Build a (n_models, n_examples) matrix of probabilities, then multiply
    # each row by its normalised weight and sum down the model axis.
    prob_matrix = np.array([output[2] for output in model_outputs])  # (n_models, n_examples)
    weighted_probs = (prob_matrix * weights[:, np.newaxis]).sum(axis=0)  # (n_examples,)

    return weighted_probs


def _tune_threshold(
    avg_probs: np.ndarray,
    labels: list[int],
    candidates: np.ndarray | None = None,
) -> tuple[float, list[dict]]:
    '''
    Sweep candidate decision thresholds and return the one that maximises
    Macro F1 on the provided labels, along with a full sweep table.

    The sweep is intentionally coarse (steps of 0.05 from 0.30 to 0.70).
    A finer sweep would risk overfitting the threshold to the 200-example
    dev set.

    Parameters
    ──────────
    avg_probs  : np.ndarray — weighted-average probabilities (n_examples,).
    labels     : list[int]  — ground-truth labels (0 or 1).
    candidates : optional array of thresholds to try. Defaults to
                 [0.30, 0.35, ..., 0.70].

    Returns
    ───────
    best_threshold : float
        The threshold value that produced the highest Macro F1.
    sweep_table : list[dict]
        One dict per threshold with keys: threshold, macro_f1, f1_class0,
        f1_class1, accuracy. Useful for printing or building a DataFrame.
    '''
    if candidates is None:
        # 0.30 → 0.70 inclusive, step 0.05
        candidates = np.arange(0.30, 0.71, 0.05)

    best_threshold = 0.5
    best_f1 = -1.0
    sweep_table = []

    for thresh in candidates:
        # Apply this threshold to produce hard predictions
        preds = [int(p >= thresh) for p in avg_probs]

        # Compute per-class F1 and macro F1 from scratch so this module has
        # no dependency on sklearn or metrics.py at tuning time.
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


# ── public API ────────────────────────────────────────────────────────────────

def motivated_soft_vote(
    model_outputs: list[tuple[list[int], list[int], list[float]]],
    f1_weights: list[float],
    threshold: float | None = None,
    print_sweep: bool = True,
) -> tuple[list[int], list[int], list[float]]:
    '''
    Motivated ensemble: performance-weighted probability average with
    automatic threshold tuning to correct for class imbalance.

    Step 1 — Weighted average
        Each model's probabilities are scaled by its Macro F1 score so that
        better models carry more weight. Weights are normalised to sum to 1.

    Step 2 — Threshold tuning  (skipped if threshold is provided)
        Sweep thresholds from 0.30 to 0.70 in steps of 0.05. Select the
        threshold that maximises Macro F1 on the dev labels. This corrects
        for the upward probability bias introduced by balanced-class training
        without requiring full probability calibration.

    Step 3 — Hard predictions
        Apply the chosen threshold to the weighted-average probabilities to
        produce final binary predictions.

    Parameters
    ──────────
    model_outputs : list of (preds, labels, probs) tuples, one per model,
                    all from the same data split and task.
    f1_weights    : list of Macro F1 scores (floats), one per model, in the
                    same order as model_outputs. These are used as raw weights
                    and are normalised internally.
    threshold     : float or None.
                    If None (default), the threshold is tuned automatically on
                    the dev labels via the sweep described above.
                    If a float is provided, that value is used directly and the
                    sweep is skipped — useful for applying a pre-tuned threshold
                    to a held-out test set.
    print_sweep   : bool, default True.
                    If True and threshold is None, prints the full sweep table
                    so the threshold selection is transparent and reproducible.

    Returns
    ───────
    (preds, labels, probs) in the same format as individual models and
    simple_ensemble.soft_vote(), so results can be passed directly to
    compute_metrics(), print_confusion_matrix(), etc.

        preds  : list[int]   — hard binary predictions (0 or 1)
        labels : list[int]   — ground-truth labels (unchanged from input)
        probs  : list[float] — weighted-average probabilities for class 1
    '''
    # ── validation ────────────────────────────────────────────────────────────

    # Confirm all models were run on the same split by checking label identity
    labels_list = [output[1] for output in model_outputs]
    if not all(l == labels_list[0] for l in labels_list):
        raise ValueError(
            "Labels differ across models — ensure all outputs are from "
            "the same split and task."
        )

    # One weight per model is required
    if len(f1_weights) != len(model_outputs):
        raise ValueError(
            f"f1_weights has {len(f1_weights)} entries but model_outputs "
            f"has {len(model_outputs)} — lengths must match."
        )

    # All weights must be positive (a model with F1 = 0 should not be included)
    if any(w <= 0 for w in f1_weights):
        raise ValueError("All f1_weights must be positive floats.")

    labels = labels_list[0]

    # ── step 1: weighted average ───────────────────────────────────────────────

    avg_probs = _weighted_average_probs(model_outputs, f1_weights)

    # ── step 2: threshold selection ───────────────────────────────────────────

    if threshold is None:
        # Tune automatically on the dev labels
        best_threshold, sweep_table = _tune_threshold(avg_probs, labels)

        if print_sweep:
            # Print the sweep table so the reader can see exactly how the
            # threshold was chosen and what the precision/recall tradeoff
            # looks like across the range
            print("\n  Threshold sweep (Macro F1 criterion):")
            print(f"  {'Threshold':>10}  {'Macro F1':>10}  "
                  f"{'F1 (cl.0)':>10}  {'F1 (cl.1)':>10}  {'Accuracy':>10}")
            print(f"  {'-'*58}")
            for row in sweep_table:
                # Mark the selected threshold with an arrow
                marker = " ◄" if row["threshold"] == round(best_threshold, 2) else ""
                print(f"  {row['threshold']:>10.2f}  {row['macro_f1']:>10.4f}  "
                      f"{row['f1_class0']:>10.4f}  {row['f1_class1']:>10.4f}  "
                      f"{row['accuracy']:>10.4f}{marker}")
            print(f"\n  Selected threshold: {best_threshold:.2f}")

        threshold = best_threshold

    # ── step 3: hard predictions ───────────────────────────────────────────────

    # Apply the chosen threshold to the weighted-average probabilities.
    # Predict opinion (1) when the ensemble score meets or exceeds the threshold.
    preds = [int(p >= threshold) for p in avg_probs.tolist()]

    return preds, labels, avg_probs.tolist()
