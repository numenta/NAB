#!/bin/bash

echo
echo "========================================"
echo "Running integration tests"

python tests/integration/false_negative_test.py
python tests/integration/false_positive_test.py 
python tests/integration/true_positive_test.py

# This should really be in a python script and send output to a temporary
# file outside the repository.
echo 
echo "========================================"
echo "Running end to end tests"
rm -rf tests/test_results/numenta
rm tests/test_config/thresholds.json
time python run.py --numCPUs 3 --dataDir tests/test_data \
                   --labelFile tests/test_labels/user_label.json \
                   --thresholdsFile tests/test_config/thresholds.json \
                   --resultsDir tests/test_results \
                   --skipConfirmation \
                   --detectors random

# Add end to end test with just does optimize

# Add end to end test with just does scoring