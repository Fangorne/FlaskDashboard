def join_with_db_batch(
    session: Session,
    records: List[Dict],
    lookup_sql: str,
    param_cols: Optional[List[str]] = None,
    transform: Optional[Callable[[Dict], Dict]] = None,
    return_rejected: bool = False,
):
    if not records:
        return []

    param_cols = param_cols or list(records[0].keys())
    param_values = [tuple(record[k] for k in param_cols) for record in records]
    unique_params = list(set(param_values))

    # Construction de la condition IN pour chaque champ
    in_conditions = []
    for k in param_cols:
        placeholders = ", ".join([f":{k}_{i}" for i in range(len(unique_params))])
        in_conditions.append(f"{k} IN ({placeholders})")

    # Ajout de la condition avec AND
    where_clause = " AND ".join(in_conditions)
    if "WHERE" in lookup_sql.upper():
        batch_sql = f"{lookup_sql} AND {where_clause}"
    else:
        batch_sql = f"{lookup_sql} WHERE {where_clause}"

    # Préparation des paramètres
    params = {}
    for i, p in enumerate(unique_params):
        for j, k in enumerate(param_cols):
            params[f"{k}_{i}"] = p[j]

    # Exécution de la requête batch
    results = session.execute(batch_sql, params).fetchall()

    # Mapping pour un appariement rapide
    result_map = {tuple(getattr(r, k) for k in param_cols): r for r in results}

    # Jointure des résultats
    joined = []
    rejected = []
    for record in records:
        key = tuple(record[k] for k in param_cols)
        if key in result_map:
            joined_record = dict(record)
            joined_record.update(result_map[key]._asdict())
            if transform:
                joined_record = transform(joined_record)
            joined.append(joined_record)
        else:
            rejected.append(record)

    if return_rejected:
        return joined, rejected
    return joined
