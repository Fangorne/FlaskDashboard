def bulk_delete_sql_composite(
    session: Session,
    model: Type,
    records: List[Dict],
    cols_param: List[str],
) -> int:
    """
    DELETE batché SQL Server avec clé composite.
    Retourne le nombre de lignes supprimées.

    - Pas de ligne à ligne
    - Temp table + JOIN
    - Compatible SQL Server 2016
    """

    if not records:
        return 0

    mapper = inspect(model)
    table_name = model.__table__.fullname

    # 1️⃣ Définition des colonnes depuis le modèle ORM
    cols_def = []
    for col_name in cols_param:
        col = mapper.columns[col_name]
        sql_type = col.type.compile(dialect=session.bind.dialect)
        cols_def.append(f"{col_name} {sql_type}")

    # 2️⃣ CREATE TABLE #input
    session.execute(text(f"""
        CREATE TABLE #input (
            {", ".join(cols_def)}
        )
    """))

    # 3️⃣ INSERT BULK
    insert_sql = text(f"""
        INSERT INTO #input ({", ".join(cols_param)})
        VALUES ({", ".join(f":{c}" for c in cols_param)})
    """)

    payload = [
        {c: r[c] for c in cols_param}
        for r in records
    ]

    session.execute(insert_sql, payload)

    # 4️⃣ DELETE JOIN
    join_cond = " AND ".join(
        f"t.{c} = i.{c}" for c in cols_param
    )

    result = session.execute(text(f"""
        DELETE t
        FROM {table_name} t
        JOIN #input i ON {join_cond}
    """))

    session.commit()

    return result.rowcount
