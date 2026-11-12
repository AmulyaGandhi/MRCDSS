import os

# The test suite includes tests that re-run the clustering pipeline
# (tests/test_clustering.py::test_pipeline_runs), which re-derives
# outputs/risk_classification/cluster_centroids.csv. scikit-learn's KMeans
# (and BLAS-backed operations) produce ulp-level differences depending on how
# OpenMP threads are scheduled, making the regenerated file non-reproducible.
# Pinning the thread pools keeps the protected-outputs invariant deterministic
# without changing any pipeline code, data, or API behavior.
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")