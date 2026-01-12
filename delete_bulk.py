def bulk_delete_sql_composite(
    session: Session,
    records: List[Dict],
    table_name: str,
    cols_param: List[str],
):
    """
    DELETE batché SQL Server 2016 avec clé composite.
    """

    if not records:
        return

    # 1️⃣ CREATE TABLE #input
    cols_def = []
    for col in cols_param:
        if col.lower().endswith("date"):
            cols_def.append(f"{col} DATE")
        else:
            cols_def.append(f"{col} NVARCHAR(255)")

    session.execute(text(f"""
        CREATE TABLE #input (
            {", ".join(cols_def)}
        )
    """))

    # 2️⃣ INSERT BULK
    insert_sql = text(f"""
        INSERT INTO #input ({", ".join(cols_param)})
        VALUES ({", ".join(f":{c}" for c in cols_param)})
    """)

    payload = [
        {c: r[c] for c in cols_param}
        for r in records
    ]

    session.execute(insert_sql, payload)

    # 3️⃣ DELETE JOIN
    join_cond = " AND ".join(
        f"t.{c} = i.{c}" for c in cols_param
    )

    session.execute(text(f"""
        DELETE t
        FROM {table_name} t
        JOIN #input i ON {join_cond}
    """))

    session.commit()
