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

    param_cols = param_cols or records[0].keys()
    param_values = [tuple(record[k] for k in param_cols) for record in records]
    unique_params = list(set(param_values))

    # Construction de la requête batch
    placeholders = ", ".join([f"({', '.join([':' + k + str(i) for k in param_cols])})" for i in range(len(unique_params))])
    batch_sql = lookup_sql.replace("WHERE user_id = :user_id", f"WHERE ({', '.join(param_cols)}) IN ({placeholders})", 1)

    # Préparation des paramètres
    params = {}
    for i, p in enumerate(unique_params):
        for j, k in enumerate(param_cols):
            params[f"{k}{i}"] = p[j]

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

# Appel de la fonction optimisée
joined_users, rejected_users = join_with_db_batch_optimized(
    session=session,
    records=users,
    lookup_sql="SELECT * FROM user_profiles WHERE user_id = :user_id",
    param_cols=["user_id"],
    return_rejected=True
)

print("Utilisateurs joints :", joined_users)
print("Utilisateurs non trouvés :", rejected_users)
