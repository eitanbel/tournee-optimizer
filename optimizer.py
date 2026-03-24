# Moteur d'optimisation OR-Tools - résolution du problème TSP (open route)
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from config import SOLVER_TIMEOUT


def resoudre_tsp(matrice_distances: list[list[int]]) -> list[int]:
    """
    Résout le problème du voyageur de commerce (TSP) avec OR-Tools.

    - Point de départ fixe : index 0
    - Pas de retour au départ (open route / tournée ouverte)
    - Optimise le temps de trajet total

    Args:
        matrice_distances: matrice n×n de durées en secondes

    Retourne:
        Liste ordonnée des indices des points dans l'ordre optimal
    """
    n = len(matrice_distances)

    if n == 0:
        return []
    if n == 1:
        return [0]

    # Pour simuler une route ouverte (sans retour), on ajoute un nœud fictif "dépôt fantôme"
    # avec des distances nulles vers tous les autres nœuds
    # Cela permet à OR-Tools (qui nécessite un retour au dépôt) de simuler une route ouverte
    n_etendu = n + 1
    noeud_fantome = n  # index du dépôt fantôme

    # Construction de la matrice étendue
    matrice_etendue = [[0] * n_etendu for _ in range(n_etendu)]
    for i in range(n):
        for j in range(n):
            matrice_etendue[i][j] = matrice_distances[i][j]
        # Distance vers le nœud fantôme = 0 (retour fictif gratuit)
        matrice_etendue[i][noeud_fantome] = 0
        matrice_etendue[noeud_fantome][i] = 0

    # Création du modèle OR-Tools
    manager = pywrapcp.RoutingIndexManager(n_etendu, 1, [0], [noeud_fantome])
    routing = pywrapcp.RoutingModel(manager)

    def callback_distance(from_index, to_index):
        """Callback retournant la durée de trajet entre deux nœuds."""
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return matrice_etendue[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(callback_distance)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Paramètres de recherche
    parametres = pywrapcp.DefaultRoutingSearchParameters()

    # Solution initiale : arc le moins coûteux
    parametres.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    # Amélioration : recherche locale guidée
    parametres.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )

    # Timeout de 30 secondes
    parametres.time_limit.FromSeconds(SOLVER_TIMEOUT)

    # Résolution
    solution = routing.SolveWithParameters(parametres)

    if not solution:
        # Si pas de solution optimale, retourner l'ordre initial
        return list(range(n))

    # Extraction de l'itinéraire depuis la solution
    itineraire = []
    index = routing.Start(0)
    while not routing.IsEnd(index):
        node = manager.IndexToNode(index)
        if node != noeud_fantome:
            itineraire.append(node)
        index = solution.Value(routing.NextVar(index))

    return itineraire


def formater_duree(secondes: int) -> str:
    """Convertit des secondes en chaîne lisible (ex: '1h 23min')."""
    heures = secondes // 3600
    minutes = (secondes % 3600) // 60
    if heures > 0:
        return f"{heures}h {minutes:02d}min"
    else:
        return f"{minutes}min"


def calculer_durees_etapes(itineraire: list[int], matrice: list[list[int]]) -> list[int]:
    """
    Calcule la durée de chaque étape dans l'itinéraire optimisé.

    Retourne une liste de durées en secondes (longueur = len(itineraire) - 1)
    """
    durees = []
    for k in range(len(itineraire) - 1):
        i = itineraire[k]
        j = itineraire[k + 1]
        durees.append(matrice[i][j])
    return durees
