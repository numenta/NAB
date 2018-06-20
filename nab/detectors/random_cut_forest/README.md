# Robust Random Cut Forest Based Anomaly Detection On Streams

Use this script to evaluate [Robust Random Cut Forest Based Anomaly Detection On Streams<sup>1</sup>][1] algorithm on NAB.

This script will create an [AWS Kinesis Analytics][2] application that will use the [RANDOM_CUT_FOREST][3] function to detect anomalies on NAB data files as they are streamed via AWS API ("boto3"). The application's output stream with the anomaly scores will be stored in the "results" folder for further processing using NAB standard tools ("run.py") to optimize, normalize and score the results.  See [NAB Entry Points][4] "Option 2" for more information.

See [random_cut_forest.sql](random_cut_forest.sql) file for more information on the parameters that were used.


### AWS Credentials

Use [AWS CLI][5] to configure your credentials:
```
aws configure
```
 
### Create NAB results folder structure

This command will create the necessary [directories](../../../results/randomCutForest) and entries in the [config/thresholds.json](../../../config/thresholds.json) file:
```
python scripts/create_new_detector.py --detector randomCutForest
```

### Create AWS Kinesis Analytics Application

This command will create and configure a new AWS Kinesis Analytics Application ready to receive NAB data from the input stream and output anomaly scores suitable for NAB to the output stream:
```
python nab/detectors/random_cut_forest/random_cut_forest.py --create
```

### Stream All Files

To stream all NAB data files use the following command:
```
python nab/detectors/random_cut_forest/random_cut_forest.py --stream
```

### Clean up

At the end of the evaluation it's recommend you delete all resources used to compute the anomaly scores. Use the following command to delete all AWS resources created by this script:
```
python nab/detectors/random_cut_forest/random_cut_forest.py --delete
```

### Compute NAB scores

Once you have calculated anomaly scores for all NAB data, you can now use NAB's standard commands to compute NAB scores.
For example, use the following command from NAB's root directory to optimize the anomaly score threshold for your algorithm's detections, run the scoring algorithm, and normalize the raw scores to yield your final NAB scores.
```
python run.py -d randomCutForest --optimize --score --normalize
```

---
[1: Guha, Sudipto, Nina Mishra, Gourav Roy, and Okke Schrijvers. "Robust random cut forest based anomaly detection on streams." In *International Conference on Machine Learning*, pp. 2712-2721. 2016.][1]


[1]: http://proceedings.mlr.press/v48/guha16.pdf  'Guha, Sudipto, Nina Mishra, Gourav Roy, and Okke Schrijvers. "Robust random cut forest based anomaly detection on streams." In International Conference on Machine Learning, pp. 2712-2721. 2016'
[2]: https://aws.amazon.com/kinesis/data-analytics/
[3]: https://docs.aws.amazon.com/kinesisanalytics/latest/sqlref/sqlrf-random-cut-forest.html
[4]: https://github.com/numenta/NAB/wiki/NAB-Entry-Points
[5]: https://aws.amazon.com/cli/
