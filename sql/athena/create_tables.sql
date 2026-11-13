-- Athena (Trino SQL): tables over the Thamesbridge files in S3.
-- Chapter 22. Replace my-sf-rating-data with your own bucket name.
-- Run one statement at a time in the Athena query editor.
-- Upload first:
--   aws s3 cp data/rmbs_loans.csv s3://my-sf-rating-data/athena/loans/
--   aws s3 cp data/rmbs_performance.csv.gz s3://my-sf-rating-data/athena/performance/

CREATE DATABASE IF NOT EXISTS thamesbridge;

CREATE EXTERNAL TABLE IF NOT EXISTS thamesbridge.loans (
  loan_id               STRING,
  origination_date      DATE,
  original_balance      DOUBLE,
  current_balance       DOUBLE,
  property_value        DOUBLE,
  original_ltv          DOUBLE,
  current_ltv           DOUBLE,
  interest_rate         DOUBLE,
  fixed_rate_years      INT,
  product_end_date      DATE,
  term_months           INT,
  remaining_term_months INT,
  seasoning_months      INT,
  repayment_type        STRING,
  occupancy             STRING,
  property_type         STRING,
  region                STRING,
  employment            STRING,
  income                DOUBLE,
  loan_to_income        DOUBLE,
  credit_score          INT
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
LOCATION 's3://my-sf-rating-data/athena/loans/'
TBLPROPERTIES ('skip.header.line.count' = '1');

CREATE EXTERNAL TABLE IF NOT EXISTS thamesbridge.performance (
  loan_id           STRING,
  period            STRING,
  status            STRING,
  opening_balance   DOUBLE,
  scheduled_payment DOUBLE,
  principal_paid    DOUBLE,
  interest_due      DOUBLE,
  prepayment        DOUBLE,
  default_balance   DOUBLE,
  closing_balance   DOUBLE
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
LOCATION 's3://my-sf-rating-data/athena/performance/'
TBLPROPERTIES ('skip.header.line.count' = '1');
