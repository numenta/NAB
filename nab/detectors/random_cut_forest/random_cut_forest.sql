-- ** Anomaly detection **
-- Compute an anomaly score for each record in the source stream using Random Cut Forest
-- Creates a temporary stream and defines a schema
CREATE OR REPLACE STREAM "TEMP_STREAM" (
   "COL_TIMESTAMP"  TIMESTAMP,
   "COL_VALUE"      DOUBLE,
   "ANOMALY_SCORE"  DOUBLE);
-- Creates an output stream and defines a schema
CREATE OR REPLACE STREAM "DESTINATION_SQL_STREAM" (
   "COL_TIMESTAMP"  TIMESTAMP,
   "COL_VALUE"      DOUBLE,
   "ANOMALY_SCORE"  DOUBLE);

-- NAB raw anomaly scores must be a number between 0 and 1
-- See NAB requirements https://arxiv.org/pdf/1510.03336.pdf
-- RANDOM_CUT_FOREST anomaly score is a number between 0 and LOG2(subSampleSize)
-- See RANDOM_CUT_FOREST anomaly score explanation https://forums.aws.amazon.com/message.jspa?messageID=751928
-- Normalize the "ANOMALY_SCORE" value to be compatible with NAB by dividing it by LOG2(subSampleSize)
--
-- The parameters used in this query yields the best NAB scores. 
-- We also Experimented with different values for the following parameters without improving the final NAB score:
--   "shingleSize": 4, 24, 48
--    "numberOfTrees" : 100, 200
CREATE OR REPLACE PUMP "STREAM_PUMP" AS INSERT INTO "TEMP_STREAM"
SELECT STREAM "COL_TIMESTAMP", "COL_VALUE", "ANOMALY_SCORE" / 8.0 FROM
  TABLE(RANDOM_CUT_FOREST(
    CURSOR(SELECT STREAM * FROM "SOURCE_SQL_STREAM_001"), -- inputStream
    100, -- numberOfTrees
    256, -- subSampleSize
    100000, -- timeDecay
    1 -- shingleSize
  )
);

CREATE OR REPLACE PUMP "OUTPUT_PUMP" AS INSERT INTO "DESTINATION_SQL_STREAM"
SELECT STREAM * FROM "TEMP_STREAM"
ORDER BY "TEMP_STREAM".ROWTIME ASC;
