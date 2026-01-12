def bulk_delete_sql_composite_final(
    session: Session,
    model: DeclarativeMeta,
    records: List[Dict],
    cols_param: List[str],
) -> int:

if not records:
        return 0

    table = model.__table__
    table_name = table.fullname

    # 1️⃣ DÉFINITION DES TYPES ET PRÉPARATION DES DONNÉES
    cols_def = []
    processed_records = []
    
    # On identifie les colonnes de type date pour le traitement
    date_cols = [
        c for c in cols_param 
        if getattr(table.c[c].type, "python_type", None) in (datetime, date)
    ]

    for col_name in cols_param:
        sql_type = table.c[col_name].type.compile(session.bind.dialect)
        cols_def.append(f"[{col_name}] {sql_type}")

    # Nettoyage des données : conversion des strings en vrais objets datetime
    for r in records:
        new_row = dict(r)
        for dc in date_cols:
            val = new_row.get(dc)
            if isinstance(val, str):
                # Convertit '2021-01-01' en objet datetime
                try:
                    new_row[dc] = dateutil.parser.parse(val)
                except Exception:
                    # Si le parsing échoue, on laisse tel quel (ou gérer l'erreur)
                    pass
        processed_records.append(new_row)

    # 2️⃣ CRÉATION TABLE TEMP
    session.execute(text("IF OBJECT_ID('tempdb..#input') IS NOT NULL DROP TABLE #input"))
    session.execute(text(f"CREATE TABLE #input ({', '.join(cols_def)})"))

    # 3️⃣ INSERTION (Le driver gère les objets datetime nativement)
    insert_sql = text(f"""
        INSERT INTO #input ({', '.join(f'[{c}]' for c in cols_param)})
        VALUES ({', '.join(f':{c}' for c in cols_param)})
    """)
    session.execute(insert_sql, processed_records)

    # 4️⃣ INDEX & DELETE
    session.execute(text(f"CREATE CLUSTERED INDEX IX_TEMP_DEL ON #input ({', '.join(f'[{c}]' for c in cols_param)})"))

    join_cond_sql = " AND ".join([f"t.[{c}] = i.[{c}]" for c in cols_param])
    
    result = session.execute(text(f"""
        DELETE t
        FROM {table_name} AS t
        INNER JOIN #input AS i ON {join_cond_sql}
    """))

    session.commit()
    return result.rowcount
