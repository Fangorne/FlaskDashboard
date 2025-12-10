def bulk_delete_by_ids(session: Session, ModelClass, composite_keys: list[tuple], pk_column_names: list[str] = None):
    """
    Supprime en masse des enregistrements identifiés par une liste de clés composites.

    Ceci exécute une seule requête DELETE utilisant la comparaison de tuples SQL:
    DELETE FROM <table> WHERE (pk1, pk2, ...) IN ((val1_1, val1_2, ...), (val2_1, val2_2, ...))

    :param session: La session SQLAlchemy active.
    :param ModelClass: La classe du modèle (ex: ItemStock) dont les objets doivent être supprimés.
    :param composite_keys: Une liste de tuples, chaque tuple représentant une clé composite complète à supprimer.
                           Ex: [(1, 101), (2, 102), ...]
    :param pk_column_names: (OPTIONNEL) Une liste des noms de colonnes de la clé primaire 
                            dans l'ordre où elles apparaissent dans `composite_keys`.
                            Ex: ['item_id', 'location_id']. Si None, utilise l'ordre par défaut du mapper.
    :return: Le nombre de lignes supprimées.
    """
    if not composite_keys:
        print("La liste de clés composites est vide. Aucune suppression effectuée.")
        return 0

    mapper = class_mapper(ModelClass)
    
    # 1. Détermination et validation des colonnes PK
    
    # Si les noms de colonnes sont fournis, utilisez-les pour construire le tuple de colonnes SQLAlchemy
    if pk_column_names:
        if len(pk_column_names) != len(mapper.primary_key):
            print(f"Erreur: Le nombre de colonnes PK fournies ({len(pk_column_names)}) ne correspond pas au nombre de clés primaires dans le modèle ({len(mapper.primary_key)}).")
            return 0
        
        try:
            # Créer un tuple des objets Colonne dans l'ordre spécifié
            pk_tuple = tuple(getattr(ModelClass, name) for name in pk_column_names)
        except AttributeError as e:
            print(f"Erreur: Colonne spécifiée introuvable dans le modèle: {e}")
            return 0
            
    # Sinon, utilisez l'ordre par défaut du mapper
    else:
        # Récupérer les colonnes de la clé primaire de manière dynamique
        pk_columns = [c for c in mapper.primary_key]
        if len(pk_columns) == 0:
            print(f"Le modèle {ModelClass.__name__} n'a pas de clé primaire définie.")
            return 0
        pk_tuple = tuple(pk_columns)

    # 2. Validation de la taille des tuples de données
    expected_pk_len = len(pk_tuple)
    if composite_keys and len(composite_keys[0]) != expected_pk_len:
        print(f"Erreur: Les tuples de clés composites doivent contenir {expected_pk_len} éléments (basé sur les colonnes PK déterminées).")
        return 0

    # 3. Construction de la condition de suppression (Tuple Comparison)
    # Ex: (ItemStock.item_id, ItemStock.location_id).in_([(1, 101), (2, 102), ...])
    filter_condition = pk_tuple.in_(composite_keys)

    # 4. Construction de l'instruction DELETE
    stmt = (
        delete(ModelClass)
        .where(filter_condition)
    )
    
    # 5. Exécution de l'instruction
    result = session.execute(stmt)
    
    deleted_count = result.rowcount
    print(f"{deleted_count} enregistrements du modèle {ModelClass.__name__} supprimés en masse.")

    session.commit()
    return deleted_count


from sqlalchemy.orm import Session
from sqlalchemy import delete
from typing import Iterable, Type

def bulk_delete_in_chunks(
    session: Session,
    model: Type,
    ids: Iterable[int],
    chunk_size: int = 1000
):
    """
    Supprime en masse des lignes SQL Server en batchs.
    Ne charge pas les objets en mémoire.

    Parameters
    ----------
    session : SQLAlchemy session
    model   : ORM model (class)
    ids     : iterable of primary keys
    chunk_size : batch size (default 1000 for SQL Server)
    """
    ids_iter = iter(ids)

    while True:
        chunk = list([x for _, x in zip(range(chunk_size), ids_iter)])
        if not chunk:
            break

        stmt = delete(model).where(model.id.in_(chunk))

        session.execute(stmt)
        session.commit()  # commit par batch, plus safe



def bulk_delete_composite(
    session: Session,
    model: Type,
    keys: Iterable[Tuple],
    column_names: Iterable[str],
    chunk_size: int = 1000,
):
    """
    Suppression en masse de lignes SQL Server avec clé composite.
    
    Parameters:
        session : SQLAlchemy session
        model : ORM model class
        keys : iterable de tuples représentant la clé composite
        column_names : noms des colonnes de la clé composite dans le même ordre
        chunk_size : taille d'un batch SQL (défaut 1000)
    """
    keys_iter = iter(keys)

    while True:
        chunk = list([k for _, k in zip(range(chunk_size), keys_iter)])
        if not chunk:
            break

        # Construction dynamique de la clause WHERE
        conditions = [
            and_(*[
                getattr(model, col) == key[i]
                for i, col in enumerate(column_names)
            ])
            for key in chunk
        ]

        stmt = delete(model).where(or_(*conditions))
        session.execute(stmt)
        session.commit()
