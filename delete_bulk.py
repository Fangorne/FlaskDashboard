def bulk_delete_sql_composite_final(
    session: Session,
    model: DeclarativeMeta,
    records: List[Dict],
    cols_param: List[str],
) -> int:
    """
    DELETE batché SQL Server avec gestion robuste des dates via CONVERT style 120.
    """
    if not records:
        return 0

    table = model.__table__
    # Utilisation de quoted_name pour éviter les erreurs de syntaxe sur les schémas
    table_name = table.fullname

    # 1️⃣ CREATE TABLE #input
    cols_def = []
    for col_name in cols_param:
        col = table.c[col_name]
        py_type = getattr(col.type, "python_type", str)
        
        if py_type in (date, datetime):
            # On stocke en NVARCHAR(25) pour "YYYY-MM-DD HH:MM:SS.mmm"
            sql_type = "NVARCHAR(25)"
        elif py_type == int:
            sql_type = "BIGINT"
        elif py_type == float:
            sql_type = "FLOAT"
        else:
            sql_type = "NVARCHAR(max)"
        cols_def.append(f"[{col_name}] {sql_type}")

    # Nettoyage au cas où une table #input existe déjà dans la session
    session.execute(text("IF OBJECT_ID('tempdb..#input') IS NOT NULL DROP TABLE #input"))
    
    session.execute(text(f"""
        CREATE TABLE #input (
            {', '.join(cols_def)}
        )
    """))

    # 2️⃣ PREPARATION DU PAYLOAD
    payload = []
    for r in records:
        row = {}
        for c in cols_param:
            val = r.get(c)
            col = table.c[c]
            py_type = getattr(col.type, "python_type", str)
            
            if py_type in (date, datetime) and val is not None:
                # Format ISO universel pour SQL Server: YYYY-MM-DD HH:MM:SS
                if isinstance(val, (date, datetime)):
                    row[c] = val.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    row[c] = str(val)
            else:
                row[c] = val
        payload.append(row)

    # INSERT par paquets
    insert_sql = text(f"""
        INSERT INTO #input ({', '.join(f'[{c}]' for c in cols_param)})
        VALUES ({', '.join(f':{c}' for c in cols_param)})
    """)
    session.execute(insert_sql, payload)

    # 3️⃣ INDEXATION (Crucial pour la performance du JOIN)
    session.execute(text(f"CREATE CLUSTERED INDEX IX_TEMP_DELETE ON #input ({', '.join(f'[{c}]' for c in cols_param)})"))

    # 4️⃣ DELETE JOIN avec CONVERT style 120 (Format canonique ODBC)
    join_cond = []
    for col_name in cols_param:
        col = table.c[col_name]
        py_type = getattr(col.type, "python_type", str)
        
        if py_type in (date, datetime):
            # Style 120 = 'yyyy-mm-dd hh:mi:ss' (indépendant de SET DATEFORMAT)
            join_cond.append(f"t.[{col_name}] = CONVERT(DATETIME2, i.[{col_name}], 120)")
        else:
            join_cond.append(f"t.[{col_name}] = i.[{col_name}]")

    join_cond_sql = " AND ".join(join_cond)

    result = session.execute(text(f"""
        DELETE t
        FROM {table_name} AS t
        INNER JOIN #input AS i ON {join_cond_sql}
    """))

    session.commit()
    return result.rowcount
