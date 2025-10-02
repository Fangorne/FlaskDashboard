SELECT 
    OBJECT_NAME(i.object_id) AS TableName,
    i.name AS IndexName,
    s.last_user_update
FROM sys.indexes i
LEFT JOIN sys.dm_db_index_usage_stats s
    ON i.object_id = s.object_id
    AND i.index_id = s.index_id
    AND s.database_id = DB_ID()
WHERE OBJECTPROPERTY(i.object_id,'IsUserTable') = 1;


SELECT 
    OBJECT_NAME(s.object_id) AS TableName,
    i.name AS IndexName,
    STATS_DATE(s.object_id, s.stats_id) AS StatsLastUpdated
FROM sys.stats s
JOIN sys.indexes i
    ON s.object_id = i.object_id
    AND i.index_id = s.stats_id;
