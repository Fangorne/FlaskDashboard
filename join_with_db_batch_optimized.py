def join_with_db_batch_optimized(
    session: Session,
    records: List[Dict],
    lookup_sql: str,
    param_cols: Optional[List[str]] = None,
    transform: Optional[Callable[[Dict], Dict]] = None,
    return_rejected: bool = False,
):
    if not records:
        return []

    # Si param_cols n'est pas précisé, on utilise toutes les clés du premier record
    param_cols = param_cols or list(records[0].keys())

    # On extrait les valeurs uniques des paramètres pour la requête batch
    param_values = [tuple(record[k] for k in param_cols) for record in records]
    unique_params = list(set(param_values))

    # Construction de la requête batch
    # Exemple: WHERE (col1, col2) IN ((val1, val2), (val3, val4), ...)
    placeholders = ", ".join(
        [f"({', '.join([f':{k}_{i}' for k in param_cols])})" for i in range(len(unique_params))]
    )
    where_clause = f"WHERE ({', '.join(param_cols)}) IN ({placeholders})"

    # On remplace le WHERE de la requête d'origine
    batch_sql = lookup_sql.split("WHERE")[0] + where_clause

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
