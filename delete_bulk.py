Pas de souci, on va s'en passer. On va utiliser le module standard de Python datetime qui est déjà installé par défaut.

Le problème de l'erreur ('IR', '2021-01-01', ...) est que Python envoie une chaîne de caractères (String), alors que SQL Server attend un format binaire pour une colonne DATETIME.

Voici la fonction corrigée. Elle utilise datetime.fromisoformat (disponible depuis Python 3.7) pour transformer vos chaînes '2021-01-01' en vrais objets Python que SQL Server acceptera sans broncher.

Python

from datetime import datetime, date
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.ext.declarative import DeclarativeMeta

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

    # 1️⃣ DÉTERMINER LES TYPES ET PRÉPARER LES DONNÉES
    cols_def = []
    date_cols = []

    for col_name in cols_param:
        col = table.c[col_name]
        # On compile le type SQL réel (DATETIME, INT, etc.)
        sql_type = col.type.compile(session.bind.dialect)
        cols_def.append(f"[{col_name}] {sql_type}")
        
        # On repère les colonnes qui attendent des dates en base
        if getattr(col.type, "python_type", None) in (datetime, date):
            date_cols.append(col_name)

    # Nettoyage : conversion manuelle des strings en objets datetime Python
    processed_records = []
    for r in records:
        row = dict(r)
        for dc in date_cols:
            val = row.get(dc)
            if isinstance(val, str) and val:
                # Gère 'YYYY-MM-DD' ou 'YYYY-MM-DD HH:MM:SS'
                # On remplace l'espace par 'T' pour que fromisoformat soit content
                iso_val = val.replace(' ', 'T')
                try:
                    row[dc] = datetime.fromisoformat(iso_val)
                except ValueError:
                    # Si le format est vraiment exotique, on laisse tel quel 
                    # mais SQL risque de râler à l'insert
                    pass
        processed_records.append(row)

    # 2️⃣ CRÉATION TABLE TEMP AVEC TYPES NATIFS
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
