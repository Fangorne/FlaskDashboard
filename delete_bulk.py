def bulk_delete_sql_composite_final(
    session: Session,
    model: DeclarativeMeta,
    records: List[Dict],
    cols_param: List[str],
) -> int:

    if not records:
        return 0

    table: Table = model.__table__
    table_name = table.fullname

    cols_def = []
    for col_name in cols_param:
        col = table.c[col_name]
        # On utilise .compile() pour obtenir le type SQL exact (ex: DATETIME, BIGINT)
        sql_type = col.type.compile(session.bind.dialect)
        cols_def.append(f"[{col_name}] {sql_type}")

    session.execute(text("IF OBJECT_ID('tempdb..#input') IS NOT NULL DROP TABLE #input"))
    
    session.execute(text(f"""
        CREATE TABLE #input (
            {', '.join(cols_def)}
        )
    """))

    # SQLAlchemy/pyodbc va mapper les objets datetime Python vers les colonnes DATETIME SQL
    insert_sql = text(f"""
        INSERT INTO #input ({', '.join(f'[{c}]' for c in cols_param)})
        VALUES ({', '.join(f':{c}' for c in cols_param)})
    """)
    
    session.execute(insert_sql, records)

    session.execute(text(f"CREATE CLUSTERED INDEX IX_TEMP_DEL ON #input ({', '.join(f'[{c}]' for c in cols_param)})"))

    join_cond_sql = " AND ".join([f"t.[{c}] = i.[{c}]" for c in cols_param])

    result = session.execute(text(f"""
        DELETE t
        FROM {table_name} AS t
        INNER JOIN #input AS i ON {join_cond_sql}
    """))

    session.commit()
    return result.rowcount
