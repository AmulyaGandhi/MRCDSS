# Supervised Classification of Derived District-Year Risk Profiles

**Methodology**: Supervised classification of derived district-year risk profiles
**Note**: K-Means risk classes are DERIVED labels, not independent clinical ground truth.

## Data Split
- Training size: 6724
- Test size: 1681
- Split: 80/20 stratified, random_state=42
- Class distribution (train): {'Low Risk': 3557, 'High Risk': 2091, 'Medium Risk': 1076}
- Class distribution (test): {'Low Risk': 889, 'High Risk': 523, 'Medium Risk': 269}

## Model Comparison (Test Set)

| Model | Accuracy | Precision (macro) | Recall (macro) | F1 (macro) | ROC-AUC (macro OVR) |
|-------|----------|-------------------|----------------|------------|---------------------|
| Logistic Regression | 0.9958 | 0.9957 | 0.9943 | 0.9950 | 1.0000 |
| Decision Tree | 0.9417 | 0.9430 | 0.9473 | 0.9451 | 0.9569 |
| Random Forest | 0.9649 | 0.9650 | 0.9695 | 0.9672 | 0.9979 |
| XGBoost | 0.9697 | 0.9680 | 0.9705 | 0.9693 | 0.9987 |

## Per-Class Metrics

### Logistic Regression
| Class | Precision | Recall | F1 | Support |
|-------|-----------|--------|----|---------|
| High Risk | 0.9943 | 0.9962 | 0.9952 | 523 |
| Low Risk | 0.9966 | 0.9978 | 0.9972 | 889 |
| Medium Risk | 0.9963 | 0.9888 | 0.9925 | 269 |


### Decision Tree
| Class | Precision | Recall | F1 | Support |
|-------|-----------|--------|----|---------|
| High Risk | 0.9147 | 0.9025 | 0.9086 | 523 |
| Low Risk | 0.9505 | 0.9505 | 0.9505 | 889 |
| Medium Risk | 0.9638 | 0.9888 | 0.9761 | 269 |


### Random Forest
| Class | Precision | Recall | F1 | Support |
|-------|-----------|--------|----|---------|
| High Risk | 0.9364 | 0.9579 | 0.9471 | 523 |
| Low Risk | 0.9771 | 0.9618 | 0.9694 | 889 |
| Medium Risk | 0.9816 | 0.9888 | 0.9852 | 269 |


### XGBoost
| Class | Precision | Recall | F1 | Support |
|-------|-----------|--------|----|---------|
| High Risk | 0.9560 | 0.9560 | 0.9560 | 523 |
| Low Risk | 0.9774 | 0.9741 | 0.9758 | 889 |
| Medium Risk | 0.9706 | 0.9814 | 0.9760 | 269 |

## Confusion Matrices

### Logistic Regression
Predicted: ['High Risk', 'Low Risk', 'Medium Risk']
Actual rows: ['High Risk', 'Low Risk', 'Medium Risk']
  High Risk: 521  2  0
  Low Risk: 1  887  1
  Medium Risk: 2  1  266


### Decision Tree
Predicted: ['High Risk', 'Low Risk', 'Medium Risk']
Actual rows: ['High Risk', 'Low Risk', 'Medium Risk']
  High Risk: 472  43  8
  Low Risk: 42  845  2
  Medium Risk: 2  1  266


### Random Forest
Predicted: ['High Risk', 'Low Risk', 'Medium Risk']
Actual rows: ['High Risk', 'Low Risk', 'Medium Risk']
  High Risk: 501  18  4
  Low Risk: 33  855  1
  Medium Risk: 1  2  266


### XGBoost
Predicted: ['High Risk', 'Low Risk', 'Medium Risk']
Actual rows: ['High Risk', 'Low Risk', 'Medium Risk']
  High Risk: 500  18  5
  Low Risk: 20  866  3
  Medium Risk: 3  2  264

## Best Model
**Best model**: Logistic Regression
**Reason**: Highest macro F1-score (0.9950), indicating best balanced performance across all three risk classes.

## Methodological Limitations
1. **Derived labels**: Risk classes are from K-Means clustering, not clinical ground truth. Model performance measures consistency with unsupervised profiles, not clinical accuracy.
2. **Class imbalance**: Risk classes have unequal sizes, which may bias accuracy toward majority classes.
3. **Feature-target leakage potential**: Features and risk labels are derived from the same underlying data, which may inflate performance metrics.
4. **No external validation**: Performance is measured on a split of the same dataset. External validation is needed for generalizability.
5. **No clinical claims**: Results should not be interpreted as clinical prediction accuracy.