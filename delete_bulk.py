def _autocast_value(value, col):
    """
    Auto-cast Python → type SQLAlchemy
    """
    if value is None:
        return None

    python_type = getattr(col.type, "python_type", None)

    # DATE / DATETIME
    if python_type in (date, datetime):
        if isinstance(value, (date, datetime)):
            return value
        if isinstance(value, str):
            # ISO only (safe)
            try:
                dt = datetime.fromisoformat(value)
                return dt.date() if python_type is date else dt
            except ValueError:
                raise ValueError(
                    f"Invalid date format for column {col.name}: {value}"
                )

    # Autres types → passthrough
    return value


def bulk_delete_sql_composite(
    session: Session,
    model: DeclarativeMeta,
    records: List[Dict],
    cols_param: List[str],
) -> int:
    """
    DELETE batché SQL Server avec clé composite.
    Auto-cast des valeurs avant INSERT.
    """

    if not records:
        return 0

    table = model.__table__
    table_name = table.fullname

    # 1️⃣ CREATE TABLE #input avec types exacts
    cols_def = []
    for col_name in cols_param:
        col = table.c[col_name]
        sql_type = col.type.compile(dialect=session.bind.dialect)
        cols_def.append(f"{col_name} {sql_type}")

    session.execute(text(f"""
        CREATE TABLE #input (
            {", ".join(cols_def)}
        )
    """))

    # 2️⃣ INSERT BULK avec auto-cast
    insert_sql = text(f"""
        INSERT INTO #input ({", ".join(cols_param)})
        VALUES ({", ".join(f":{c}" for c in cols_param)})
    """)

    payload = []
    for r in records:
        row = {}
        for c in cols_param:
            col = table.c[c]
            row[c] = _autocast_value(r.get(c), col)
        payload.append(row)

    session.execute(insert_sql, payload)

    # 3️⃣ DELETE JOIN
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
