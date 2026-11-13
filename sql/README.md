# SQL for the Thamesbridge data (Chapter 22)

* `athena/` — Amazon Athena: `create_tables.sql` describes the CSV files in S3 as
  tables; `queries.sql` holds the stratification, arrears and roll-rate queries of
  Chapter 22.
* `sqlserver/` — the same work in Microsoft SQL Server (T-SQL): create the tables,
  load the CSV files with `BULK INSERT`, run the queries.

The arrears and roll-rate queries give the numbers printed in Chapter 22
(for example a current-to-30 roll rate of 0.602% a month in 2021).
