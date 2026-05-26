"""
Statistical evaluation and classification utilities for EIT stroke classification.
"""

import numpy as np
from scipy.stats import rankdata, binomtest

# Configuration
N_PERM = 2000


def balanced_accuracy(y_true, y_pred):
    """
    Compute balanced accuracy with sensitivity and specificity.
    
    Args:
        y_true: True labels (0/1)
        y_pred: Predicted labels (0/1)
        
    Returns:
        tuple: (balanced_accuracy, sensitivity, specificity)
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    
    pos_mask = (y_true == 1)
    neg_mask = (y_true == 0)
    
    if pos_mask.any():
        sensitivity = (y_pred[pos_mask] == 1).mean()
    else:
        sensitivity = 0.0
        
    if neg_mask.any():
        specificity = (y_pred[neg_mask] == 0).mean()
    else:
        specificity = 0.0
    
    ba = 0.5 * (sensitivity + specificity)
    return ba, sensitivity, specificity


def auc_score(y_true, scores):
    """
    Compute Area Under ROC Curve using Mann-Whitney U statistic.
    
    Args:
        y_true: True labels (0/1)
        scores: Prediction scores (higher = more likely positive)
        
    Returns:
        float: AUC score
    """
    y_true = np.asarray(y_true)
    scores = np.asarray(scores)
    
    pos_scores = scores[y_true == 1]
    neg_scores = scores[y_true == 0]
    
    if pos_scores.size == 0 or neg_scores.size == 0:
        return np.nan
    
    # Use ranking for AUC computation
    all_scores = np.concatenate([pos_scores, neg_scores])
    ranks = rankdata(all_scores)
    
    pos_ranks = ranks[:pos_scores.size]
    auc = (pos_ranks.sum() - pos_scores.size * (pos_scores.size + 1) / 2) / (pos_scores.size * neg_scores.size)
    
    return float(auc)


def wilson_confidence_interval(k, n, confidence=0.95):
    """
    Wilson confidence interval for binomial proportion.
    
    Args:
        k: Number of successes
        n: Total trials
        confidence: Confidence level (default 95%)
        
    Returns:
        tuple: (lower_bound, upper_bound)
    """
    if n == 0:
        return (np.nan, np.nan)
    
    z = 1.959964 if confidence == 0.95 else 1.644854  # 95% or 90%
    p = k / n
    
    denominator = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denominator
    margin = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    
    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)
    
    return (lower, upper)


def single_threshold_lopo(features, labels):
    """
    Leave-One-Patient-Out classification with optimal threshold selection.
    
    Args:
        features: Feature values per subject
        labels: True labels (0/1)
        
    Returns:
        numpy array: Predicted labels
    """
    features = np.asarray(features)
    labels = np.asarray(labels)
    n = len(labels)
    
    predictions = np.zeros(n, dtype=int)
    
    for i in range(n):
        if not np.isfinite(features[i]):
            predictions[i] = 0
            continue
            
        # Training set (all except subject i)
        train_mask = np.array([j != i for j in range(n)])
        train_features = features[train_mask]
        train_labels = labels[train_mask]
        
        # Remove NaN values from training
        valid_train = np.isfinite(train_features)
        if valid_train.sum() < 2:
            predictions[i] = 0
            continue
            
        train_features = train_features[valid_train]
        train_labels = train_labels[valid_train]
        
        # Find unique threshold candidates
        unique_vals = np.sort(np.unique(train_features))
        if unique_vals.size < 2:
            predictions[i] = 0
            continue
            
        threshold_candidates = 0.5 * (unique_vals[:-1] + unique_vals[1:])
        
        # Select best threshold by balanced accuracy
        best_ba = -1
        best_threshold = np.nan
        best_direction = 1
        
        for threshold in threshold_candidates:
            for direction in [1, -1]:  # > threshold or < threshold
                if direction == 1:
                    train_preds = (train_features > threshold).astype(int)
                else:
                    train_preds = (train_features < threshold).astype(int)
                
                ba, _, _ = balanced_accuracy(train_labels, train_preds)
                if ba > best_ba:
                    best_ba = ba
                    best_threshold = threshold
                    best_direction = direction
        
        # Make prediction for test subject
        if best_direction == 1:
            predictions[i] = int(features[i] > best_threshold)
        else:
            predictions[i] = int(features[i] < best_threshold)
    
    return predictions


def permutation_test(features, labels, n_permutations=N_PERM, random_state=42):
    """
    Permutation test for classifier significance.
    
    Args:
        features: Feature values
        labels: True labels
        n_permutations: Number of permutation samples
        random_state: Random seed
        
    Returns:
        float: p-value (fraction of permutations with BA >= observed BA)
    """
    rng = np.random.default_rng(random_state)
    
    # Observed performance
    observed_preds = single_threshold_lopo(features, labels)
    observed_ba, _, _ = balanced_accuracy(labels, observed_preds)
    
    # Null distribution
    null_ba = np.zeros(n_permutations)
    
    for i in range(n_permutations):
        shuffled_labels = rng.permutation(labels)
        null_preds = single_threshold_lopo(features, shuffled_labels)
        null_ba[i], _, _ = balanced_accuracy(shuffled_labels, null_preds)
    
    p_value = (null_ba >= observed_ba).mean()
    return float(p_value)


def mcnemar_test(predictions_a, predictions_b, true_labels):
    """
    McNemar's test for comparing paired classifiers.
    
    Args:
        predictions_a: Predictions from classifier A
        predictions_b: Predictions from classifier B  
        true_labels: True labels
        
    Returns:
        tuple: (p_value, n_a_correct_b_wrong, n_a_wrong_b_correct)
    """
    correct_a = (predictions_a == true_labels)
    correct_b = (predictions_b == true_labels)
    
    # McNemar table: focus on disagreements
    a_correct_b_wrong = int((correct_a & ~correct_b).sum())
    a_wrong_b_correct = int((~correct_a & correct_b).sum())
    
    # Exact binomial test
    total_disagreements = a_correct_b_wrong + a_wrong_b_correct
    
    if total_disagreements == 0:
        return 1.0, a_correct_b_wrong, a_wrong_b_correct
    
    # Two-tailed test
    p_value = binomtest(
        min(a_correct_b_wrong, a_wrong_b_correct), 
        total_disagreements, 
        0.5, 
        alternative='two-sided'
    ).pvalue
    
    return float(p_value), a_correct_b_wrong, a_wrong_b_correct


def evaluate_classifier(name, features, labels, n_permutations=N_PERM, random_state=42):
    """
    Complete evaluation of a single classifier.
    
    Args:
        name: Classifier name for display
        features: Feature values
        labels: True labels
        n_permutations: Number of permutation tests
        random_state: Random seed
        
    Returns:
        dict: Evaluation results
    """
    print(f"\n{name}:")
    print("-" * (len(name) + 1))
    
    # LOPO predictions
    predictions = single_threshold_lopo(features, labels)
    
    # Performance metrics
    ba, sensitivity, specificity = balanced_accuracy(labels, predictions)
    auc = auc_score(labels, features)
    
    # Count correct predictions
    n_pos = int((labels == 1).sum())
    n_neg = int((labels == 0).sum())
    tp = int(((labels == 1) & (predictions == 1)).sum())
    tn = int(((labels == 0) & (predictions == 0)).sum())
    correct = tp + tn
    total = n_pos + n_neg
    
    # Confidence intervals
    ci_acc = wilson_confidence_interval(correct, total)
    ci_sens = wilson_confidence_interval(tp, n_pos)
    ci_spec = wilson_confidence_interval(tn, n_neg)
    
    # Balanced accuracy CI (approximate from sensitivity and specificity CIs)
    ba_lower = 0.5 * (ci_sens[0] + ci_spec[0]) 
    ba_upper = 0.5 * (ci_sens[1] + ci_spec[1])
    
    # Permutation test
    p_perm = permutation_test(features, labels, n_permutations, random_state)
    
    # Display results
    print(f"  Accuracy:          {correct/total:.3f} [95% CI: {ci_acc[0]:.3f}, {ci_acc[1]:.3f}] ({correct}/{total})")
    print(f"  Sensitivity:       {sensitivity:.3f} [95% CI: {ci_sens[0]:.3f}, {ci_sens[1]:.3f}] ({tp}/{n_pos})")
    print(f"  Specificity:       {specificity:.3f} [95% CI: {ci_spec[0]:.3f}, {ci_spec[1]:.3f}] ({tn}/{n_neg})")
    print(f"  AUC:               {auc:.3f}")
    print(f"  Permutation p:     {p_perm:.4f} (vs chance)")
    
    return {
        'name': name,
        'predictions': predictions,
        'ba': ba,
        'sensitivity': sensitivity, 
        'specificity': specificity,
        'auc': auc,
        'accuracy': correct/total,
        'tp': tp,
        'tn': tn,
        'n_pos': n_pos,
        'n_neg': n_neg,
        'ci_ba': (ba_lower, ba_upper),
        'ci_sens': ci_sens,
        'ci_spec': ci_spec,
        'ci_acc': ci_acc,
        'p_perm': p_perm
    }