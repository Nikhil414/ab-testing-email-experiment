-- One source row represents one assigned customer. Keep all assigned customers.
-- customer_row_id is an import row number, not a publisher-supplied customer ID.
SELECT
    segment,
    COUNT(*) AS assigned_users,
    SUM(visit) AS visitors,
    SUM(conversion) AS purchases,
    AVG(conversion) AS conversion_rate,
    SUM(spend) AS total_revenue,
    AVG(spend) AS revenue_per_assigned_user
FROM customers
GROUP BY segment
ORDER BY segment;
