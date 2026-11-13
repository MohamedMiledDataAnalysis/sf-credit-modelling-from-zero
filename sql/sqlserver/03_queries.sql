-- SQL Server (T-SQL) versions of the Athena queries of Chapter 22.
USE Thamesbridge;
GO
-- 1. Pool stratification by current LTV band
SELECT ltv_band,
       COUNT(*)                                        AS loans,
       ROUND(SUM(current_balance) / 1e6, 1)            AS balance_m,
       ROUND(SUM(current_balance * interest_rate)
             / SUM(current_balance), 3)                AS wa_rate
FROM (
  SELECT *,
         CASE WHEN current_ltv < 60 THEN '1: below 60'
              WHEN current_ltv < 75 THEN '2: 60 to 75'
              WHEN current_ltv < 85 THEN '3: 75 to 85'
              ELSE '4: 85 and above' END AS ltv_band
  FROM dbo.loans) AS banded
GROUP BY ltv_band            -- T-SQL does not accept GROUP BY 1
ORDER BY ltv_band;

-- 2. Share of live loans in arrears, selected months
SELECT period,
       ROUND(100.0 * SUM(CASE WHEN status IN ('30','60','90')
                              THEN 1 ELSE 0 END)
             / COUNT(*), 2) AS arrears_pct
FROM dbo.performance
WHERE status NOT IN ('DEF', 'PRE')
  AND period IN ('2020-06','2021-06','2022-06','2023-06')
GROUP BY period
ORDER BY period;

-- 3. Monthly roll rate from current to 30, averaged by year (Chapter 11)
WITH moves AS (
  SELECT period, status,
         LAG(status) OVER (PARTITION BY loan_id
                           ORDER BY period) AS prev
  FROM dbo.performance)
SELECT LEFT(period, 4) AS [year],
       ROUND(100.0 * SUM(CASE WHEN status = '30'
                              THEN 1 ELSE 0 END)
             / COUNT(*), 3) AS c_to_30_pct
FROM moves
WHERE COALESCE(prev, 'C') = 'C'
GROUP BY LEFT(period, 4)
ORDER BY [year];

-- 4. The ten largest loans (TOP instead of LIMIT)
SELECT TOP 10 loan_id, current_balance, current_ltv, region
FROM dbo.loans
ORDER BY current_balance DESC;
