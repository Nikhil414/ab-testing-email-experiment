-- Exploratory only: repeated subgroup comparisons are not confirmatory evidence.
-- Use pre-treatment history, never post-treatment visit/purchase to define groups.
SELECT
    segment,
    CASE WHEN recency <= 6 THEN 'Purchased within 6 months'
         ELSE 'Purchased 7-12 months ago' END AS recency_group,
    COUNT(*) AS assigned_users,
    AVG(conversion) AS conversion_rate,
    AVG(spend) AS revenue_per_assigned_user
FROM customers
GROUP BY segment, recency_group
ORDER BY recency_group, segment;
