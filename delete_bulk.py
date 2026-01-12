def bulk_delete_sql_composite_safe(
    session: Session,
    model: DeclarativeMeta,
    records: List[Dict],
    cols_param: List[str],
) -> int:
    """
    DELETE batché SQL Server 2016 avec clé composite, safe pour les dates.
    
    - Table temporaire utilise NVARCHAR pour les colonnes DATE/DATETIME
    - DELETE JOIN avec CAST explicite DATETIME
    - Retourne le nombre de lignes supprimées
    """

    if not records:
        return 0

    table = model.__table__
    table_name = table.fullname

    # 1️⃣ CREATE TABLE #input avec NVARCHAR pour toutes les dates/datetime
    cols_def = []
    for col_name in cols_param:
        col = table.c[col_name]
        py_type = getattr(col.type, "python_type", str)
        if py_type in (date, datetime):
            sql_type = "NVARCHAR(30)"  # suffisant pour ISO dates
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

    # 2️⃣ INSERT BULK (on passe tout en string pour les dates)
    insert_sql = text(f"""
        INSERT INTO #input ({', '.join(cols_param)})
        VALUES ({', '.join(f':{c}' for c in cols_param)})
    """)

    payload = []
    for r in records:
        row = {}
        for c in cols_param:
            val = r.get(c)
            col = table.c[c]
            py_type = getattr(col.type, "python_type", str)
            if py_type in (date, datetime):
                # convert date/datetime en ISO string
                if isinstance(val, (date, datetime)):
                    row[c] = val.isoformat()
                else:
                    row[c] = str(val)  # supposé ISO YYYY-MM-DD ou YYYY-MM-DDTHH:MM:SS
            else:
                row[c] = val
        payload.append(row)

    session.execute(insert_sql, payload)

    # 3️⃣ DELETE JOIN avec CAST pour DATE/DATETIME
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
    return result.rowcount
