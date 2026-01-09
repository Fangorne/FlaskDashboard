def bulk_lookup_aggregated_sql(
    session: Session,
    records: List[Dict],
    lookup_sql: str,
    param_cols: List[str],
    transform: Optional[Callable[[Dict], Dict]] = None,
    return_rejected: bool = False,
) -> List[Dict] | Tuple[List[Dict], List[Dict]]:

    if not records:
        return ([], []) if return_rejected else []

    cols_def = ", ".join(f"{c} NVARCHAR(255)" for c in param_cols)

    session.execute(text(f"""
        CREATE TABLE #input (
            __row_id INT NOT NULL,
            {cols_def}
        )
    """))

    insert_sql = text(f"""
        INSERT INTO #input (__row_id, {", ".join(param_cols)})
        VALUES (:__row_id, {", ".join(f":{c}" for c in param_cols)})
    """)

    payload = [
        {"__row_id": i, **{c: r[c] for c in param_cols}}
        for i, r in enumerate(records)
    ]

    session.execute(insert_sql, payload)

    rows = session.execute(text(lookup_sql)).mappings().all()

    result = [r.copy() for r in records]
    matched = set()

    for row in rows:
        rid = row["__row_id"]
        matched.add(rid)

        joined = dict(row)
        joined.pop("__row_id")

        result[rid].update(joined)

        if transform:
            result[rid] = transform(result[rid])

    if not return_rejected:
        return result

    rejected = [
        records[i]
        for i in range(len(records))
        if i not in matched
    ]

    return result, rejected
