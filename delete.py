from typing import List, Dict, Iterable, Tuple, Type, Optional, Callable
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session


def bulk_lookup_composite(
    session: Session,
    model: Type,
    records: List[Dict],
    column_names: Iterable[str],
    chunk_size: int = 1000,
    transform: Optional[Callable[[Dict], Dict]] = None,
    return_rejected: bool = False,
) -> List[Dict] | tuple[List[Dict], List[Dict]]:
    """
    Lookup batché SQL Server avec clé composite (pattern bulk_delete_composite).

    - Pas de ligne à ligne
    - Une requête SQL par chunk
    - Compatible SQL Server 2016

    :param session: session SQLAlchemy
    :param model: modèle ORM à joindre
    :param records: données en mémoire
    :param column_names: colonnes de jointure (clé composite)
    :param chunk_size: taille des batchs
    :param transform: transformation optionnelle
    :param return_rejected: retourne les non-matchés
    """

    col_names = list(column_names)

    accepted: List[Dict] = []
    rejected: List[Dict] = []

    # index mémoire pour rattacher les résultats
    index = {
        tuple(record[col] for col in col_names): record
        for record in records
    }

    keys = list(index.keys())
    keys_iter = iter(keys)

    while True:
        chunk = list([k for _, k in zip(range(chunk_size), keys_iter)])
        if not chunk:
            break

        # WHERE (c1=v1 AND c2=v2) OR ...
        conditions = [
            and_(*[
                getattr(model, col) == key[i]
                for i, col in enumerate(col_names)
            ])
            for key in chunk
        ]

        stmt = select(model).where(or_(*conditions))
        rows = session.execute(stmt).scalars().all()

        matched_keys = set()

        for row in rows:
            key = tuple(getattr(row, col) for col in col_names)
            matched_keys.add(key)

            joined = {
                **index[key],
                **row.__dict__,
            }
            joined.pop("_sa_instance_state", None)

            if transform:
                joined = transform(joined)

            accepted.append(joined)

        if return_rejected:
            for key in chunk:
                if key not in matched_keys:
                    rejected.append(index[key])

    if return_rejected:
        return accepted, rejected

    return accepted
