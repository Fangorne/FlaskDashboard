def bulk_delete_sql_composite(
    session: Session,
    model: DeclarativeMeta,
    records: List[Dict],
    cols_param: List[str],
) -> int:
    """
    DELETE batché SQL Server avec clé composite.
    CAST explicite des colonnes DATE / DATETIME dans le DELETE JOIN.
    """

    if not records:
        return 0

    table = model.__table__
    table_name = table.fullname

    # 1️⃣ CREATE TABLE #input (types simples)
    cols_def = []
    for col_name in cols_param:
        col = table.c[col_name]
        py_type = getattr(col.type, "python_type", str)
        if py_type in (date, datetime):
            sql_type = "DATETIME"  # couvre DATE et DATETIME
        elif py_type in (int, float):
            sql_type = "NUMERIC"
        else:
            sql_type = "NVARCHAR(255)"
        cols_def.append(f"{col_name} {sql_type}")

    session.execute(text(f"""
        CREATE TABLE #input (
            {', '.join(cols_def)}
        )
    """))

    # 2️⃣ INSERT BULK
    insert_sql = text(f"""
        INSERT INTO #input ({', '.join(cols_param)})
        VALUES ({', '.join(f':{c}' for c in cols_param)})
    """)

    payload = [
        {c: r[c] for c in cols_param}
        for r in records
    ]

    session.execute(insert_sql, payload)

    # 3️⃣ DELETE JOIN avec CAST DATE / DATETIME
    join_cond = []
    for col_name in cols_param:
        col = table.c[col_name]
        py_type = getattr(col.type, "python_type", str)
        if py_type in (date, datetime):
            join_cond.append(f"t.{col_name} = CAST(i.{col_name} AS DATETIME)")
        else:
            join_cond.append(f"t.{col_name} = i.{col_name}")

    join_cond_sql = " AND ".join(join_cond)

    result = session.execute(text(f"""
        DELETE t
        FROM {table_name} t
        JOIN #input i ON {join_cond_sql}
    """))

    session.commit()
