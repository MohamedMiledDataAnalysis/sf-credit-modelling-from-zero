-- SQL Server (T-SQL): the SQL Server-only statements of Chapter 22,
-- section "SQL fundamentals for quant work", in the order of the book.
-- Run them one block at a time in SSMS or VS Code after 01_create_tables.sql
-- and 02_load_data.sql. Some blocks change the tables: read each one first.
USE Thamesbridge;
GO

-- ---- Block 1 --------------------------------------------------
ALTER TABLE dbo.loans ADD high_ltv BIT NOT NULL
      CONSTRAINT df_high_ltv DEFAULT 0;
ALTER TABLE dbo.loans ALTER COLUMN region VARCHAR(40) NOT NULL;
ALTER TABLE dbo.loans ADD CONSTRAINT ck_ltv
      CHECK (current_ltv BETWEEN 0 AND 200);
ALTER TABLE dbo.loans DROP CONSTRAINT ck_ltv, df_high_ltv;
ALTER TABLE dbo.loans DROP COLUMN high_ltv;
DROP VIEW IF EXISTS dbo.v_snapshot;
DROP INDEX IF EXISTS ix_perf_period ON dbo.performance;
DROP TABLE IF EXISTS dbo.loans_backup;
GO

-- ---- Block 2 --------------------------------------------------
CREATE OR ALTER PROCEDURE dbo.usp_pool_by_status
    @period CHAR(7)              -- e.g. '2022-06'
AS
BEGIN
    SET NOCOUNT ON;              -- no "rows affected" messages
    SELECT status, COUNT(*) AS loans,
           SUM(closing_balance) AS balance
    FROM dbo.performance
    WHERE period = @period
    GROUP BY status
    ORDER BY status;
END;
GO
EXEC dbo.usp_pool_by_status @period = '2022-06';
GO

-- ---- Block 3 --------------------------------------------------
CREATE OR ALTER FUNCTION dbo.fn_ltv_band (@ltv DECIMAL(5,1))
RETURNS VARCHAR(16)
AS
BEGIN
    RETURN CASE WHEN @ltv < 60 THEN '1: below 60'
                WHEN @ltv < 75 THEN '2: 60 to 75'
                WHEN @ltv < 85 THEN '3: 75 to 85'
                ELSE '4: 85 and above' END;
END;
GO
SELECT dbo.fn_ltv_band(current_ltv) AS band, COUNT(*) AS loans
FROM dbo.loans
GROUP BY dbo.fn_ltv_band(current_ltv);
GO

-- ---- Block 4 --------------------------------------------------
CREATE NONCLUSTERED INDEX ix_perf_period_status
    ON dbo.performance (period, status)
    INCLUDE (closing_balance);
GO

-- ---- Block 5 (full ten-column version of the book's shortened load) --------------------------------------------------
BEGIN TRY
  BEGIN TRANSACTION;
  -- Staging table with the same ten columns as dbo.performance
  CREATE TABLE #stage (
    loan_id VARCHAR(10), period CHAR(7), status VARCHAR(3),
    opening_balance DECIMAL(12,2), scheduled_payment DECIMAL(12,2),
    principal_paid DECIMAL(12,2), interest_due DECIMAL(12,2),
    prepayment DECIMAL(12,2), default_balance DECIMAL(12,2),
    closing_balance DECIMAL(12,2));
  BULK INSERT #stage FROM 'C:\sfcm\data\2025-01.csv'
       WITH (FORMAT = 'CSV', FIRSTROW = 2, ROWTERMINATOR = '0x0a');
  MERGE dbo.performance AS t
  USING #stage AS s
     ON t.loan_id = s.loan_id AND t.period = s.period
  WHEN MATCHED THEN UPDATE SET
       t.status = s.status,
       t.opening_balance = s.opening_balance,
       t.scheduled_payment = s.scheduled_payment,
       t.principal_paid = s.principal_paid,
       t.interest_due = s.interest_due,
       t.prepayment = s.prepayment,
       t.default_balance = s.default_balance,
       t.closing_balance = s.closing_balance
  WHEN NOT MATCHED THEN INSERT
       (loan_id, period, status, opening_balance, scheduled_payment,
        principal_paid, interest_due, prepayment, default_balance,
        closing_balance)
       VALUES (s.loan_id, s.period, s.status, s.opening_balance,
               s.scheduled_payment, s.principal_paid, s.interest_due,
               s.prepayment, s.default_balance, s.closing_balance);
  COMMIT TRANSACTION;
END TRY
BEGIN CATCH
  IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
  THROW;                       -- report the original error
END CATCH;
GO
