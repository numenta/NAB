#! /usr/bin/env python
# ----------------------------------------------------------------------
# Copyright (C) 2018, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------
"""
Use this script to evaluate [Robust Random Cut Forest Based Anomaly Detection On
Streams][4] algorithm on NAB.

This script will create an [AWS Kinesis Analytics][2] application that
will use the [RANDOM_CUT_FOREST][3] function to detect anomalies on NAB data
files as they are streamed via AWS API ("boto3"). The application's output
stream with the anomaly scores will be stored in the "results" folder for
further processing using NAB standard tools ("run.py") to optimize, normalize
and score the results.

See [NAB Entry Points][1] "Option 2" for more information.

The following commands were used calculate NAB scores using this script:

```
# Create results folders
python scripts/create_new_detector.py --detector randomCutForest

# Create kinesis application
python nab/detectors/random_cut_forest/random_cut_forest.py --create

# Stream all NAB data
python nab/detectors/random_cut_forest/random_cut_forest.py --stream

# Clean up
python nab/detectors/random_cut_forest/random_cut_forest.py --delete

# Compute NAB scores
python run.py -d randomCutForest --optimize --score --normalize

```

[1]: https://github.com/numenta/NAB/wiki/NAB-Entry-Points
[2]: https://aws.amazon.com/kinesis/data-analytics/
[3]: https://docs.aws.amazon.com/kinesisanalytics/latest/sqlref/sqlrf-random-cut-forest.html
[4]: http://proceedings.mlr.press/v48/guha16.pdf
"""

import os
import sys
import time

import argparse
import boto3
import pandas

from nab.corpus import Corpus
from nab.labeler import CorpusLabel

SCRIPT_PATH = os.path.abspath(os.path.dirname(__file__))
DATA_PATH = os.path.normpath(os.path.join(SCRIPT_PATH, os.path.pardir,
                                          os.path.pardir, os.path.pardir,
                                          "data"))
RESULTS_PATH = os.path.normpath(os.path.join(SCRIPT_PATH, os.path.pardir,
                                             os.path.pardir, os.path.pardir,
                                             "results"))
LABELS_FILE = os.path.normpath(os.path.join(SCRIPT_PATH, os.path.pardir,
                                            os.path.pardir, os.path.pardir,
                                            "labels", "combined_windows.json"))
APPLICATION_SOURCE_FILE = os.path.join(SCRIPT_PATH, "random_cut_forest.sql")
ROLE_TRUST_POLICY_FILE = os.path.join(SCRIPT_PATH, "role_trust_policy.json")
ROLE_PERMISSION_POLICY_FILE = os.path.join(SCRIPT_PATH,
                                           "role_permission_policy.json")
DETECTOR_NAME = "randomCutForest"
APPLICATION_NAME = "nab_rcf"
OUTPUT_STREAM_NAME = "nab_output"
INPUT_STREAM_NAME = "nab_input"

# Configure kinesis analytics application input stream schema. This schema
# should match the SQL stream definition. See "random_cut_forest.sql"
INPUT_SCHEMA = {
  "RecordColumns": [{
    "Name": "COL_TIMESTAMP",
    "SqlType": "TIMESTAMP"
  }, {
    "Name": "COL_VALUE",
    "SqlType": "DOUBLE"
  }],
  "RecordFormat": {
    "MappingParameters": {
      "CSVMappingParameters": {
        "RecordColumnDelimiter": ",",
        "RecordRowDelimiter": "\n"
      }
    },
    "RecordFormatType": "CSV"
  }
}



def createStreams():
  """
  Creates AWS Kinesis input and output streams
  :return: dictionary with the newly created stream ARNs
  """
  kinesis = boto3.client("kinesis")
  result = {}
  streams = [INPUT_STREAM_NAME, OUTPUT_STREAM_NAME]
  for name in streams:
    kinesis.create_stream(StreamName=name, ShardCount=1)

  # Wait until all streams are created
  waiter = kinesis.get_waiter('stream_exists')
  for name in streams:
    waiter.wait(StreamName=name)
    response = kinesis.describe_stream(StreamName=name)
    result[name] = response["StreamDescription"]["StreamARN"]

  return result



def deleteStreams():
  """
  Deletes AWS Kinesis streams created by "createStreams"
  """
  kinesis = boto3.client("kinesis")
  streams = [INPUT_STREAM_NAME, OUTPUT_STREAM_NAME]
  for name in streams:
    try:
      kinesis.delete_stream(StreamName=name)
    except kinesis.exceptions.ResourceNotFoundException:
      pass

  # Wait until all streams are deleted
  waiter = kinesis.get_waiter('stream_not_exists')
  for name in streams:
    waiter.wait(StreamName=name)



def createRole(inputStream, outputStream):
  """
  Creates a new AWS IAM Role  with access to the input and output AWS Kinesis
  streams created by "createStreams".
  See "role_permission_policy.json" and "role_trust_policy.json"

  :param inputStream: Kinesis input stream ARN
  :param outputStream: Kinesis output stream ARN
  :return: The Role ARN
  """
  iam = boto3.client("iam")
  roleName = "kinesis-analytics-service-{0}-role".format(APPLICATION_NAME)

  # Create new rolte and give it access to the input and output streams
  trustPolicy = open(ROLE_TRUST_POLICY_FILE, "r").read()
  response = iam.create_role(Path="/nab/", RoleName=roleName,
                             AssumeRolePolicyDocument=trustPolicy)
  role = response["Role"]
  permissionPolicy = open(ROLE_PERMISSION_POLICY_FILE, "r").read()
  policyName = "kinesis-analytics-service-{0}-policy".format(APPLICATION_NAME)
  iam.put_role_policy(RoleName=roleName, PolicyName=policyName,
                      PolicyDocument=permissionPolicy % {
                        "inputStream": inputStream,
                        "outputStream": outputStream})

  # FIXME: Wait until IAM role policy update is propagated
  time.sleep(20)

  return role['Arn']



def deleteRole():
  """
  Deletes the role created via "createRole" for the given application
  """
  iam = boto3.client("iam")
  roleName = "kinesis-analytics-service-{0}-role".format(APPLICATION_NAME)
  policyName = "kinesis-analytics-service-{0}-policy".format(APPLICATION_NAME)
  try:
    iam.delete_role_policy(RoleName=roleName, PolicyName=policyName)
  except iam.exceptions.NoSuchEntityException:
    pass
  try:
    iam.delete_role(RoleName=roleName)
  except iam.exceptions.NoSuchEntityException:
    pass



def createApplication():
  """
  Create a new AWS Kinesis Analytics Application used to provide anomaly
  scores from NAB data files. See "random_cut_forest.sql"
  """
  print("Creating kinesis streams")
  streams = createStreams()
  inputStream = streams[INPUT_STREAM_NAME]
  outputStream = streams[OUTPUT_STREAM_NAME]

  print("Creating IAM Role")
  role = createRole(inputStream, outputStream)

  print("Creating kinesis analytics application")
  sourceCode = open(APPLICATION_SOURCE_FILE, "r").read()
  kinesisAnalytics = boto3.client("kinesisanalytics")
  kinesisAnalytics.create_application(
    ApplicationName=APPLICATION_NAME,
    ApplicationCode=sourceCode,
    Inputs=[{
      "NamePrefix": "SOURCE_SQL_STREAM",
      "InputSchema": INPUT_SCHEMA,
      "KinesisStreamsInput": {
        "ResourceARN": inputStream,
        "RoleARN": role
      }
    }],
    Outputs=[{
      "Name": "DESTINATION_SQL_STREAM",
      "DestinationSchema": {
        "RecordFormatType": "CSV"
      },
      "KinesisStreamsOutput": {
        "ResourceARN": outputStream,
        "RoleARN": role
      }
    }])



def startApplication():
  """
  Starts the application created via "createApplication"
  """
  kinesisAnalytics = boto3.client("kinesisanalytics")
  response = kinesisAnalytics.describe_application(
    ApplicationName=APPLICATION_NAME)
  application = response["ApplicationDetail"]
  inputId = application['InputDescriptions'][0]['InputId']
  kinesisAnalytics.start_application(ApplicationName=APPLICATION_NAME,
                                     InputConfigurations=[{
                                       "Id": inputId,
                                       "InputStartingPositionConfiguration": {
                                         "InputStartingPosition": "NOW"
                                       }
                                     }])
  # Wait until application starts running
  response = kinesisAnalytics.describe_application(
    ApplicationName=APPLICATION_NAME)
  status = response["ApplicationDetail"]["ApplicationStatus"]
  sys.stdout.write('Starting ')
  while status != "RUNNING":
    sys.stdout.write('.')
    sys.stdout.flush()
    time.sleep(1)
    response = kinesisAnalytics.describe_application(
      ApplicationName=APPLICATION_NAME)
    status = response["ApplicationDetail"]["ApplicationStatus"]
  sys.stdout.write(os.linesep)



def stopApplication():
  """
  Stops the application created via "createApplication"
  """
  kinesisAnalytics = boto3.client("kinesisanalytics")
  kinesisAnalytics.stop_application(ApplicationName=APPLICATION_NAME)

  # Wait until application stops running
  response = kinesisAnalytics.describe_application(
    ApplicationName=APPLICATION_NAME)
  status = response["ApplicationDetail"]["ApplicationStatus"]
  sys.stdout.write('Stopping ')
  while status != "READY":
    sys.stdout.write('.')
    sys.stdout.flush()
    time.sleep(1)
    response = kinesisAnalytics.describe_application(
      ApplicationName=APPLICATION_NAME)
    status = response["ApplicationDetail"]["ApplicationStatus"]

  sys.stdout.write(os.linesep)



def deleteApplication():
  """
  Deletes the application created via "createApplication"
  """
  print("Deleting IAM Role")
  deleteRole()

  print("Deleting kinesis streams")
  deleteStreams()

  print("Deleting kinesis analytics application")
  kinesisAnalytics = boto3.client("kinesisanalytics")
  try:
    response = kinesisAnalytics.describe_application(
      ApplicationName=APPLICATION_NAME)
    kinesisAnalytics.delete_application(
      ApplicationName=response["ApplicationDetail"]["ApplicationName"],
      CreateTimestamp=response["ApplicationDetail"]["CreateTimestamp"])
  except kinesisAnalytics.exceptions.ResourceNotFoundException:
    pass



def streamFile(corpus, corpusLabel, resultsdir, name):
  """
  Streams a single NAB data file to Kinesis Analytics Application saving the
  results for further processing by NAB tools
  :param corpus:  NAB corpus created via "corpus = Corpus(datadir)"
  :param corpusLabel:  NAB corpus labels
  :param resultsdir: Path to store the results. Make sure to run
                    'scripts/create_new_detector.py --detector randomCutForest'
                    first
  :param name: NAB data file name (i.e. "realKnownCause/nyc_taxi.csv")
  :return: The result file absolute path
  """
  print("Streaming", name)

  startApplication()

  # Get latest position from the output stream before streaming new records
  kinesis = boto3.client("kinesis")
  response = kinesis.describe_stream(StreamName=OUTPUT_STREAM_NAME)
  shardId = response["StreamDescription"]["Shards"][0]["ShardId"]
  response = kinesis.get_shard_iterator(StreamName=OUTPUT_STREAM_NAME,
                                        ShardId=shardId,
                                        ShardIteratorType="LATEST")
  shardIterator = response["ShardIterator"]

  # Send NAB data as a single CSV file to the input stream
  datafile = corpus.dataFiles[name]
  total = datafile.data.shape[0]
  kinesis.put_record(StreamName=INPUT_STREAM_NAME,
                     PartitionKey=name,
                     Data=datafile.data.to_csv(header=False, index=False))

  # Make sure to read all records from output stream
  rows = []
  sys.stdout.write("\rProcessed 0/{} ".format(total))
  sys.stdout.flush()
  while len(rows) < total:
    response = kinesis.get_records(ShardIterator=shardIterator)
    records = response["Records"]
    if len(records) > 0:
      parsed_records = []
      for rec in records:
        parsed_record = str(rec["Data"], "utf-8")
        parsed_record = parsed_record.strip('\n')
        parsed_record = parsed_record.split(",")
        parsed_records.append(parsed_record)
      rows.extend(parsed_records)
      shardIterator = response["NextShardIterator"]
      sys.stdout.write("\rProcessed {}/{} ".format(len(rows), total))
      sys.stdout.flush()
    else:
      # Back off until the application starts streaming the anomalies
      sys.stdout.write(".")
      sys.stdout.flush()
      time.sleep(1)

  sys.stdout.write(os.linesep)

  # Streaming results may arrive out of order
  rows.sort()

  results = pandas.DataFrame(rows, columns=["timestamp", "value",
                                            "anomaly_score"])

  # Add NAB corpus labels
  results["label"] = corpusLabel.labels[name]["label"]

  # Save results
  relativeDir, fileName = os.path.split(name)
  resultFile = os.path.join(resultsdir, DETECTOR_NAME, relativeDir,
                            "{}_{}".format(DETECTOR_NAME, fileName))
  results.to_csv(resultFile, index=False)

  # Stop application after every data file to reset the algorithm
  stopApplication()

  return resultFile



def streamAll(corpus, corpusLabel, resultsdir):
  """
  Streams all files in the NAB corpus
  :param corpus:  NAB corpus created via "corpus = Corpus(dataDir)"
  :param corpusLabel:  NAB corpus labels
  :param resultsdir: Path to store the results. Make sure to run
                    'scripts/create_new_detector.py --detector randomCutForest'
                    first
  """
  for name in list(corpus.dataFiles.keys()):
    streamFile(corpus, corpusLabel, resultsdir, name)



def main(args):
  if args.create:
    createApplication()

  if args.start:
    startApplication()

  if args.stop:
    stopApplication()

  if args.file:
    corpus = Corpus(args.data)
    labels = CorpusLabel(path=args.labels, corpus=corpus)
    streamFile(corpus, labels, args.results, args.file)

  if args.stream:
    corpus = Corpus(args.data)
    labels = CorpusLabel(path=args.labels, corpus=corpus)
    streamAll(corpus, labels, args.results)

  if args.delete:
    deleteApplication()



if __name__ == "__main__":
  parser = argparse.ArgumentParser(
    description="Use this script to evaluate 'Robust Random Cut Forest Based "
                "Anomaly Detection On Streams' algorithm on NAB.",
    epilog="Make sure to run 'scripts/create_new_detector.py --detector "
           "randomCutForest' before using this script. See README.md for "
           "details",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--data",
                      default=DATA_PATH,
                      help="Path to NAB data files.")
  parser.add_argument("--labels",
                      default=LABELS_FILE,
                      help="JSON file containing ground truth labels for the "
                           "corpus.")
  parser.add_argument("--results",
                      default=RESULTS_PATH,
                      help="Path to NAB results path.")
  parser.add_argument("--create", "-c",
                      help="Create AWS Kinesis application",
                      default=False,
                      action="store_true")
  parser.add_argument("--delete", "-d",
                      help="Delete AWS Kinesis application",
                      default=False,
                      action="store_true")
  parser.add_argument("--start",
                      help="Start AWS Kinesis application",
                      default=False,
                      action="store_true")
  parser.add_argument("--stop",
                      help="Stop AWS Kinesis application",
                      default=False,
                      action="store_true")
  parser.add_argument("--stream", "-s",
                      default=False,
                      help="Stream all NAB data files to AWS Kinesis "
                           "application",
                      action="store_true")
  parser.add_argument("--file", "-f",
                      help="Stream a single NAB data file name to AWS Kinesis "
                           "application")

  args = parser.parse_args()

  if args.create or args.start or args.file or args.stream or args.stop \
      or args.delete:
    main(args)
  else:
    parser.print_help()
