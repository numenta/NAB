#!/bin/bash

echo
echo "========================================"
echo "Running integration tests"

python tests/integration/false_negative_test.py
python tests/integration/false_positive_test.py
python tests/integration/true_positive_test.py

python tests/integration/corpus_test.py

python tests/integration/corpuslabel_test.py

# This should really be in a python script and send output to a temporary
# file outside the repository.

echo
echo "========================================"
echo "Prepping for end to end tests"

rm -rf tests/test_results/numenta
rm -rf tests/test_results/random
rm -rf tests/test_results/skyline
rm -rf tests/test_config
mkdir tests/test_config

echo
echo "========================================"
echo "Running label combiner"

python scripts/combine_labels.py --labelDir tests/test_labels/human \
                    --dataDir tests/test_data \
                    --skipConfirmation \
                    --destPath tests/test_labels/test_ground_truth.json

echo
echo "========================================"
echo "Running analysis with random detector"

time python run.py --numCPUs 3 --dataDir tests/test_data \
             --labelFile tests/test_labels/test_ground_truth.json \
             --thresholdsFile tests/test_config/thresholds.json \
             --resultsDir tests/test_results \
             --skipConfirmation \
             --detectors random

# Add end to end test with just runs optimize

# Add end to end test with just runs scoring
