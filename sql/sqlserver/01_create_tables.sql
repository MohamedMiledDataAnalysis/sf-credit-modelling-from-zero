-- SQL Server (T-SQL): tables for the Thamesbridge data. Chapter 22 bonus.
IF DB_ID('Thamesbridge') IS NULL CREATE DATABASE Thamesbridge;
GO
USE Thamesbridge;
GO
DROP TABLE IF EXISTS dbo.loans;
CREATE TABLE dbo.loans (
  loan_id               VARCHAR(10)   NOT NULL PRIMARY KEY,
  origination_date      DATE          NOT NULL,
  original_balance      DECIMAL(12,2) NOT NULL,
  current_balance       DECIMAL(12,2) NOT NULL,
  property_value        DECIMAL(12,2) NOT NULL,
  original_ltv          DECIMAL(5,1)  NOT NULL,
  current_ltv           DECIMAL(5,1)  NOT NULL,
  interest_rate         DECIMAL(5,2)  NOT NULL,
  fixed_rate_years      INT           NOT NULL,
  product_end_date      DATE          NOT NULL,
  term_months           INT           NOT NULL,
  remaining_term_months INT           NOT NULL,
  seasoning_months      INT           NOT NULL,
  repayment_type        VARCHAR(20)   NOT NULL,
  occupancy             VARCHAR(20)   NOT NULL,
  property_type         VARCHAR(20)   NOT NULL,
  region                VARCHAR(30)   NOT NULL,
  employment            VARCHAR(20)   NOT NULL,
  income                DECIMAL(12,2) NOT NULL,
  loan_to_income        DECIMAL(6,2)  NOT NULL,
  credit_score          INT           NOT NULL
);

DROP TABLE IF EXISTS dbo.performance;
CREATE TABLE dbo.performance (
  loan_id           VARCHAR(10)   NOT NULL,
  period            CHAR(7)       NOT NULL,
  status            VARCHAR(3)    NOT NULL,
  opening_balance   DECIMAL(12,2) NOT NULL,
  scheduled_payment DECIMAL(12,2) NOT NULL,
  principal_paid    DECIMAL(12,2) NOT NULL,
  interest_due      DECIMAL(12,2) NOT NULL,
  prepayment        DECIMAL(12,2) NOT NULL,
  default_balance   DECIMAL(12,2) NOT NULL,
  closing_balance   DECIMAL(12,2) NOT NULL,
  CONSTRAINT pk_performance PRIMARY KEY (loan_id, period)
);
GO
