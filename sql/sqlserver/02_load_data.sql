-- SQL Server: load the CSV files with BULK INSERT. Chapter 22 bonus.
-- BULK INSERT reads files from the SQL Server machine's disk, and it does not
-- read gzip files: first unzip data/rmbs_performance.csv.gz to
-- outputs/rmbs_performance.csv, then replace C:\sfcm\data\ with your own folder.
-- Unzip on Windows or macOS, from the repository root:
--   python -c "import gzip, shutil; shutil.copyfileobj(gzip.open('data/rmbs_performance.csv.gz'), open('outputs/rmbs_performance.csv', 'wb'))"
-- On Windows, use a folder the SQL Server service account can read, such
-- as C:\sfcm\data\ (not your Documents folder).
-- With SQL Server in Docker (macOS), copy the files into the container
-- and use its paths, for example '/tmp/rmbs_loans.csv':
--   docker cp data/rmbs_loans.csv sqlserver:/tmp/
--   docker cp outputs/rmbs_performance.csv sqlserver:/tmp/
-- ROWTERMINATOR = '0x0a': the files end each line with a line feed only
-- (.gitattributes stops Git for Windows from adding carriage returns).
-- SQL Server 2017 or later is needed for FORMAT = 'CSV'.
USE Thamesbridge;
GO
BULK INSERT dbo.loans
FROM 'C:\sfcm\data\rmbs_loans.csv'
WITH (FORMAT = 'CSV', FIRSTROW = 2, FIELDTERMINATOR = ',',
      ROWTERMINATOR = '0x0a', TABLOCK);

BULK INSERT dbo.performance
FROM 'C:\sfcm\data\rmbs_performance.csv'
WITH (FORMAT = 'CSV', FIRSTROW = 2, FIELDTERMINATOR = ',',
      ROWTERMINATOR = '0x0a', TABLOCK);
GO
-- Checks: 10,000 loans, 449,052 performance rows
SELECT COUNT(*) AS loans FROM dbo.loans;
SELECT COUNT(*) AS performance_rows FROM dbo.performance;
