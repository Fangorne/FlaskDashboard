    if not records:
        return []

    param_cols = param_cols or list(records[0].keys())
    param_values = [tuple(record[k] for k in param_cols) for record in records]
    unique_params = list(set(param_values))

    # Construction de la sous-requête VALUES
    values_clauses = []
    params = {}
    for i, p in enumerate(unique_params):
        values_clauses.append(f"({', '.join([f':{k}_{i}' for k in param_cols])})")
        for j, k in enumerate(param_cols):
            params[f"{k}_{i}"] = p[j]

    values_str = ", ".join(values_clauses)
    temp_table = f"SELECT * FROM (VALUES {values_str}) AS TempTable({', '.join(param_cols)})"

    # Construction de la requête avec INNER JOIN
    if "WHERE" in lookup_sql.upper():
        batch_sql = f"{lookup_sql} AND ({', '.join(param_cols)}) IN (SELECT {', '.join(param_cols)} FROM ({temp_table}) AS T)"
    else:
        batch_sql = f"{lookup_sql} WHERE ({', '.join(param_cols)}) IN (SELECT {', '.join(param_cols)} FROM ({temp_table}) AS T)"

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
