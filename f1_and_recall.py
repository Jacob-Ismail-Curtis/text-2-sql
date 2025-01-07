import pandas as pd
import numpy as np

# Define the soft_f1_score function
def soft_f1_score(ground_truth, prediction, tolerance=0.8):
    def row_similarity(row1, row2):
        matches = sum(1 for a, b in zip(row1, row2) if str(a).strip().lower() == str(b).strip().lower())
        return matches / max(len(row1), len(row2))

    similarity_matrix = np.zeros((len(ground_truth), len(prediction)))
    for i, gt_row in enumerate(ground_truth):
        for j, pred_row in enumerate(prediction):
            similarity_matrix[i, j] = row_similarity(gt_row, pred_row)

    precision = np.sum(np.max(similarity_matrix, axis=0)) / len(prediction) if prediction else 0
    recall = np.sum(np.max(similarity_matrix, axis=1)) / len(ground_truth) if ground_truth else 0
    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * (precision * recall) / (precision + recall)

    return f1, recall

# Load the CSV file
eval_file = "C:/Users/5609580/Downloads/3.3 - 3.2 Eval .xlsx"
df = pd.read_excel(eval_file, engine='openpyxl')

# Calculate Soft F1 and Recall for each row
soft_f1_scores = []
recalls = []

for index, row in df.iterrows():
    ground_truth = [str(row['GOLD RESULT']).split()]
    prediction = [str(row['3.2 RESULT']).split()]
    f1, recall = soft_f1_score(ground_truth, prediction)
    soft_f1_scores.append(f1)
    recalls.append(recall)

# Add the results to the DataFrame
df['SOFT F1'] = soft_f1_scores
df['RECALL'] = recalls

# Save the updated DataFrame back to an Excel file
df.to_excel("C:/Users/5609580/Downloads/3.3 - 3.2 Eval Updated.xlsx", index=False)

print("Soft F1 scores and recalls have been calculated and saved to the updated Excel file.")
