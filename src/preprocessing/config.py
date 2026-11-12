import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")

DATASET1_PATH = os.path.join(BASE_DIR, "dataset1.csv")
DATASET2_PATH = os.path.join(BASE_DIR, "dataset2.csv")

OUTPUT_CSV = os.path.join(OUTPUTS_DIR, "preprocessed_output.csv")
REPORT_TXT = os.path.join(OUTPUTS_DIR, "data_quality_report.txt")
NORMALIZED_CSV = os.path.join(OUTPUTS_DIR, "normalized_output.csv")
TEST_RESULTS_TXT = os.path.join(OUTPUTS_DIR, "test_results.txt")

NEGATIVE_THRESHOLD = 0
PERCENTAGE_UPPER_BOUND = 100
PERCENTAGE_LOWER_BOUND = 0

FEATURE_COLUMNS = [
    "ANC_First_Trimester",
    "TT2_Booster",
    "Institutional_Delivery",
    "Safe_Delivery",
    "Home_Delivery",
    "SBA_Home",
    "PNC_48h",
    "Obstetric_Complications",
]

YEARS_D1 = [2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016]
YEARS_D2 = [2017, 2018, 2019]
