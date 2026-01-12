def bulk_delete_sql(
    session: Session,
    records: List[Dict],
    table_name: str,
    field_name: str,
):
    """
    DELETE batché SQL Server (pattern table temporaire).
    """

    if not records:
        return

    # 1️⃣ table temporaire
    session.execute(text(f"""
        CREATE TABLE #input (
            field_value NVARCHAR(255) NOT NULL
        )
    """))

    # 2️⃣ bulk insert
    insert_sql = text("""
        INSERT INTO #input (field_value)
        VALUES (:field_value)
    """)

    payload = [
        {"field_value": r[field_name]}
        for r in records
    ]

    session.execute(insert_sql, payload)

    # 3️⃣ delete batché
    session.execute(text(f"""
        DELETE t
        FROM {table_name} t
        JOIN #input i ON t.{field_name} = i.field_value
    """))

    session.commit()
