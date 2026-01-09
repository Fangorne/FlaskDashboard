
def bulk_lookup_sql(
    session: Session,
    records: List[Dict],
    lookup_sql: str,
    param_cols: List[str],
    chunk_size: int = 1000,
    transform: Optional[Callable[[Dict], Dict]] = None,
    return_rejected: bool = False,
) -> List[Dict] | Tuple[List[Dict], List[Dict]]:

    if not records:
        return ([], []) if return_rejected else []

    accepted: List[Dict] = []
    rejected: List[Dict] = []

    keys_iter = iter(records)

    while True:
        chunk = list([r for _, r in zip(range(chunk_size), keys_iter)])
        if not chunk:
            break

        # (c1 = :c1_0 AND c2 = :c2_0) OR ...
        where_clauses = []
        params = {}

        for idx, record in enumerate(chunk):
            ands = []
            for col in param_cols:
                pname = f"{col}_{idx}"
                ands.append(f"{col} = :{pname}")
                params[pname] = record[col]
            where_clauses.append(f"({' AND '.join(ands)})")

        where_sql = " OR ".join(where_clauses)

        # injection SAFE du WHERE (lookup_sql reste intact)
        sql = f"""
        SELECT *
        FROM (
            {lookup_sql}
        ) AS _lookup
        WHERE {where_sql}
        """

        rows = session.execute(text(sql), params).mappings().all()

        matched = set()

        for row in rows:
            key = tuple(row[col] for col in param_cols)
            matched.add(key)

            for record in chunk:
                if tuple(record[col] for col in param_cols) == key:
                    joined = {**record, **row}
                    if transform:
                        joined = transform(joined)
                    accepted.append(joined)

        if return_rejected:
            for record in chunk:
                key = tuple(record[col] for col in param_cols)
                if key not in matched:
                    rejected.append(record)

    if return_rejected:
        return accepted, rejected

    return accepted
