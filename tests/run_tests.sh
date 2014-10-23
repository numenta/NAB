echo 
echo "========================================"
echo "Running integration tests"

python tests/integration/false_negative_test.py
python tests/integration/false_positive_test.py 
python tests/integration/true_positive_test.py

echo 
echo "========================================"
echo "Running end to end tests"
rm -rf tests/test_results/numenta
rm tests/test_config/thresholds.json
time python run.py --numCPUs 3 --dataDir tests/test_data \
                   --labelFile tests/test_labels/user_label.json \
                   --thresholdsFile tests/test_config/thresholds.json \
                   --resultsDir tests/test_results \
                   --skipConfirmation
