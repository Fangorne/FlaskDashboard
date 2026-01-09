from typing import List, Dict, Optional, Callable
from sqlalchemy.orm import Session
import pandas as pd

def join_with_db_batch_sqlserver(
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

    # 1. Exécuter la requête SQL sans filtre pour récupérer tous les résultats
    all_results = session.execute(lookup_sql).fetchall()

    # 2. Convertir les résultats en DataFrame pour un lookup efficace
    df_results = pd.DataFrame([dict(r._asdict()) for r in all_results])

    # 3. Préparer les records en DataFrame
    df_records = pd.DataFrame(records)

    # 4. Effectuer le merge (lookup) sur les colonnes param_cols
    df_merged = pd.merge(
        df_records,
        df_results,
        on=param_cols,
        how="left"
    )

    # 5. Convertir le résultat en liste de dictionnaires
    joined = df_merged.where(pd.notnull(df_merged), None).to_dict("records")

    # 6. Appliquer la transformation si nécessaire
    if transform:
        joined = [transform(r) for r in joined if any(v is not None for v in r.values())]

    # 7. Filtrer les records non trouvés
    rejected = [r for r in records if not df_merged[df_merged[param_cols] == r].any().any()]

    if return_rejected:
        return joined, rejected
    return joined
