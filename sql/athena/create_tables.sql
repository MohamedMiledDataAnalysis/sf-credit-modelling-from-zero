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
  original_balance      DECIMAL(12,2),
  current_balance       DECIMAL(12,2),
  property_value        DECIMAL(12,2),
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
  income                DECIMAL(12,2),
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
  opening_balance   DECIMAL(12,2),
  scheduled_payment DECIMAL(12,2),
  principal_paid    DECIMAL(12,2),
  interest_due      DECIMAL(12,2),
  prepayment        DECIMAL(12,2),
  default_balance   DECIMAL(12,2),
  closing_balance   DECIMAL(12,2)
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
LOCATION 's3://my-sf-rating-data/athena/performance/'
TBLPROPERTIES ('skip.header.line.count' = '1');
