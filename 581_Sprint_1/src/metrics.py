"""
Evaluation utilities that can be used for any model

All functions accept  Python lists (ints/floats), so they should work with any model type.

"""

#Using sklearn for all metrics
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score, classification_report


def compute_metrics(preds: list[int], labels: list[int], probs: list[float])
   
    """
    Compute classification metrics.

    Args:
        preds:  Hard predictions (0 or 1).
        labels: Ground-truth labels (0 or 1).
        probs:  Predicted probabilities for class 1. Needed for AUC-ROC.

    Returns:
        Dict with accuracy, macro_f1, f1_class0, f1_class1,
        and auc_roc (if probs are passed as a parameter).
    """
    #Calculate f1
    f1s = f1_score(labels, preds, average=None, labels=[0, 1])

    #Create the dictionary of metrics
    metrics = {
        "accuracy":  accuracy_score(labels, preds),
        "macro_f1":  f1_score(labels, preds, average="macro"),
        "f1_class0": f1s[0],
        "f1_class1": f1s[1],
    }

    #if probabilities are included in parameters, calculate auc_roc and add it to the metrics dict.
    if probs is not None:
        metrics["auc_roc"] = roc_auc_score(labels, probs)
    return metrics


def print_report(metrics: dict, name: str = ""):
    """
    Print a metrics dict returned by compute_metrics()
    parameters: metrics dictionary, name should be model name
    returns: nothing
    """
    #Print results
    header = f"── {name} ──" if name else "── Results ──"
    print(header)
    print(f"  Accuracy:         {metrics['accuracy']:.4f}")
    print(f"  Macro F1:         {metrics['macro_f1']:.4f}")
    print(f"  F1 (not-opinion): {metrics['f1_class0']:.4f}")
    print(f"  F1 (opinion):     {metrics['f1_class1']:.4f}")

    #auc_roc might not be included, so check before printing.
    if "auc_roc" in metrics:
        print(f"  AUC-ROC:          {metrics['auc_roc']:.4f}")


def print_confusion_matrix(preds: list[int], labels: list[int]):
    #Got help from Claude on the advice to use a confusion matrix, as well as the implementation.
    """
    Prints a 2x2 confusion matrix (rows=true, cols=predicted).
    parameters: list of predictions and list of ground-truth labels
    """
    tp = sum(p == 1 and l == 1 for p, l in zip(preds, labels))
    tn = sum(p == 0 and l == 0 for p, l in zip(preds, labels))
    fp = sum(p == 1 and l == 0 for p, l in zip(preds, labels))
    fn = sum(p == 0 and l == 1 for p, l in zip(preds, labels))

    print("Confusion matrix (rows=true, cols=predicted):")
    print(f"                 pred=0  pred=1")
    print(f"  true=0 (not-op):  {tn:4d}    {fp:4d}")
    print(f"  true=1 (opinion): {fn:4d}    {tp:4d}")


def print_sklearn_report(preds: list[int], labels: list[int]) :
    """
    Prints full sklearn classification_report with per-class precision/recall.
    parameters: list of predictions and list of ground-truth labels
    """
    print(classification_report(
        labels, preds, target_names=["not-opinion", "opinion"]
    ))


def error_analysis( raw_rows: list[dict], preds: list[int], labels: list[int], n: int = 5) 
    """Print raw text for up to n false positives and n false negatives.
    Parameters: 
    raw_rows: list of dictionaries that you get from load_csv(), to get original data
    preds: list of predictions
    labels = list of ground truth labels
    raw_rows, preds, and labels must be the same length
    """

    #help from claude for how to do these two lines at the code level. I knew what I 
    #wanted but wasn't sure how to do it, in terms lof list comprehension and zip
    fps = [r for r, p, l in zip(raw_rows, preds, labels) if p == 1 and l == 0][:n]
    fns = [r for r, p, l in zip(raw_rows, preds, labels) if p == 0 and l == 1][:n]

    print(f"False Positives (predicted opinion, actually not) — {len(fps)} shown:")
    for r in fps:
        print(f"  [{r['id']}] {r['text'][:120]!r}")

    print(f"\nFalse Negatives (predicted not-opinion, actually opinion) — {len(fns)} shown:")
    for r in fns:
        print(f"  [{r['id']}] {r['text'][:120]!r}")
