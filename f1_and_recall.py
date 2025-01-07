import numpy as np

def soft_f1_score(ground_truth, prediction, tolerance=0.8):
    """
    Calculate and print the Soft F1 score between two SQL result tables.
    
    Args:
        ground_truth (list of lists): The ground truth table rows.
        prediction (list of lists): The predicted table rows.
        tolerance (float): A value between 0 and 1 indicating how closely 
                           rows should match to be considered similar.
                           
    Returns:
        float: The Soft F1 Score.
    """
    def row_similarity(row1, row2):
        """
        Compute similarity between two rows as the average similarity of elements.
        """
        matches = sum(1 for a, b in zip(row1, row2) if str(a).strip().lower() == str(b).strip().lower())
        return matches / max(len(row1), len(row2))

    # Create similarity matrix
    similarity_matrix = np.zeros((len(ground_truth), len(prediction)))
    for i, gt_row in enumerate(ground_truth):
        for j, pred_row in enumerate(prediction):
            similarity_matrix[i, j] = row_similarity(gt_row, pred_row)

    # Compute precision, recall, and F1
    precision = np.sum(np.max(similarity_matrix, axis=0)) / len(prediction) if prediction else 0
    recall = np.sum(np.max(similarity_matrix, axis=1)) / len(ground_truth) if ground_truth else 0
    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * (precision * recall) / (precision + recall)

    print(f"Soft F1 Score: {f1:.4f}")
    return f1
