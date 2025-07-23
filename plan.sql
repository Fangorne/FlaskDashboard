🧪 Exemple : voir ce qui s'exécute maintenant
sql
Copier
Modifier
SELECT 
    r.session_id,
    s.login_name,
    r.status,
    t.text AS sql_text
FROM 
    sys.dm_exec_requests r
JOIN 
    sys.dm_exec_sessions s ON r.session_id = s.session_id
CROSS APPLY 
    sys.dm_exec_sql_text(r.sql_handle) t
WHERE 
    s.is_user_process = 1;



1. Voir les requêtes les plus lentes récemment exécutées
sql
Copier
Modifier
SELECT TOP 20
    qs.total_elapsed_time / qs.execution_count AS AvgElapsedTimeMs,
    qs.total_elapsed_time AS TotalElapsedTimeMs,
    qs.execution_count,
    qs.total_logical_reads,
    qs.total_worker_time,
    SUBSTRING(st.text, (qs.statement_start_offset/2)+1,
        ((CASE qs.statement_end_offset
          WHEN -1 THEN DATALENGTH(st.text)
          ELSE qs.statement_end_offset
          END - qs.statement_start_offset)/2) + 1) AS QueryText,
    st.text AS FullText
FROM 
    sys.dm_exec_query_stats AS qs
CROSS APPLY 
    sys.dm_exec_sql_text(qs.sql_handle) AS st
ORDER BY 
    AvgElapsedTimeMs DESC;



2. Voir les requêtes actuellement en cours (et lentes)
sql
Copier
Modifier
SELECT 
    r.session_id,
    r.status,
    r.start_time,
    r.command,
    r.wait_type,
    r.cpu_time,
    r.total_elapsed_time,
    t.text AS SqlText
FROM 
    sys.dm_exec_requests r
CROSS APPLY 
    sys.dm_exec_sql_text(r.sql_handle) t
WHERE 
    r.status != 'background'
ORDER BY 
    r.total_elapsed_time DESC;



3. Identifier les plans de requête coûteux
sql
Copier
Modifier
SELECT TOP 10
    cp.usecounts,
    cp.size_in_bytes / 1024 AS SizeKB,
    qs.total_worker_time AS CpuTime,
    qs.total_elapsed_time AS ElapsedTime,
    st.text AS QueryText
FROM 
    sys.dm_exec_cached_plans AS cp
JOIN 
    sys.dm_exec_query_stats AS qs ON cp.plan_handle = qs.plan_handle
CROSS APPLY 
    sys.dm_exec_sql_text(cp.plan_handle) AS st
ORDER BY 
    qs.total_elapsed_time DESC;



4. Requête avec plan d'exécution lent (I/O, CPU, etc.)
Active "Include Actual Execution Plan" dans SSMS (Ctrl + M avant d’exécuter) pour voir :

Opérations lentes (ex: Index Scan, Sort, Hash Match)

Requêtes non indexées

Goulots d'étranglement (ex: Key Lookup)




5. Audit automatique avec Query Store (si activé)
sql
Copier
Modifier
SELECT 
    qsrs.avg_duration/1000.0 AS AvgDurationMs,
    qsrs.execution_type_desc,
    qsqt.query_sql_text
FROM 
    sys.query_store_runtime_stats qsrs
JOIN 
    sys.query_store_plan qsp ON qsrs.plan_id = qsp.plan_id
JOIN 
    sys.query_store_query qsq ON qsp.query_id = qsq.query_id
JOIN 
    sys.query_store_query_text qsqt ON qsq.query_text_id = qsqt.query_text_id
ORDER BY 
    AvgDurationMs DESC;



1. Query Store (si activé) – recommandé depuis SQL Server 2016+
Tu peux interroger le Query Store pour voir les requêtes longues entre deux heures précises.

sql
Copier
Modifier
DECLARE @StartTime DATETIME = '2025-07-23 13:00:00';
DECLARE @EndTime   DATETIME = '2025-07-23 14:00:00';

SELECT 
    qt.query_sql_text,
    rs.avg_duration / 1000.0 AS AvgDurationMs,
    rs.last_execution_time,
    rs.execution_count
FROM 
    sys.query_store_runtime_stats rs
JOIN 
    sys.query_store_plan p ON rs.plan_id = p.plan_id
JOIN 
    sys.query_store_query q ON p.query_id = q.query_id
JOIN 
    sys.query_store_query_text qt ON q.query_text_id = qt.query_text_id
WHERE 
    rs.last_execution_time BETWEEN @StartTime AND @EndTime
ORDER BY 
    rs.avg_duration DESC;
✅ Avantages : permet d’analyser a posteriori ce qui s’est exécuté autour d’une heure précise.


2. SQL Server Extended Events / Profiler (si activé)
Si tu as activé un trace, tu peux voir les requêtes exécutées entre deux timestamps.

Tu peux filtrer par StartTime et Duration directement dans les vues ou les fichiers .xel.

Exemple de requête si les données sont stockées :

sql
Copier
Modifier
SELECT 
    event_data.value('(event/@timestamp)[1]', 'datetime') AS [Time],
    event_data.value('(event/action[@name="sql_text"]/value)[1]', 'nvarchar(max)') AS [SQL]
FROM 
    sys.fn_xe_file_target_read_file('C:\traces\*.xel', null, null, null)
WHERE 
    event_data.value('(event/@timestamp)[1]', 'datetime') 
    BETWEEN '2025-07-23T13:00:00' AND '2025-07-23T14:00:00';



