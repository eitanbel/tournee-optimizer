# Client Google Maps - géocodage et matrice de distances
import googlemaps
from datetime import datetime
import streamlit as st
from config import GOOGLE_MAPS_API_KEY


def get_gmaps_client():
    """Initialise et retourne le client Google Maps."""
    if not GOOGLE_MAPS_API_KEY:
        st.error("Clé API Google Maps manquante. Vérifiez votre fichier .env.")
        return None
    return googlemaps.Client(key=GOOGLE_MAPS_API_KEY)


def geocode_addresses(addresses: list[str]) -> tuple[list[dict], list[str]]:
    """
    Convertit une liste d'adresses texte en coordonnées GPS.

    Retourne:
        - liste de dict {'adresse': str, 'lat': float, 'lng': float}
        - liste d'adresses non trouvées (erreurs)
    """
    client = get_gmaps_client()
    if not client:
        return [], addresses

    geocoded = []
    erreurs = []

    for adresse in addresses:
        adresse = adresse.strip()
        if not adresse:
            continue
        try:
            resultats = client.geocode(adresse)
            if resultats:
                location = resultats[0]['geometry']['location']
                geocoded.append({
                    'adresse': adresse,
                    'adresse_formatee': resultats[0]['formatted_address'],
                    'lat': location['lat'],
                    'lng': location['lng']
                })
            else:
                erreurs.append(adresse)
        except Exception as e:
            erreurs.append(adresse)

    return geocoded, erreurs


def build_distance_matrix(points: list[dict], progress_bar=None) -> list[list[int]]:
    """
    Construit la matrice de durées de trajet (en secondes) entre tous les points.
    Utilise le trafic en temps réel via departure_time=now.

    Args:
        points: liste de dict avec 'lat' et 'lng'
        progress_bar: barre de progression Streamlit (optionnel)

    Retourne:
        Matrice n×n de durées en secondes
    """
    client = get_gmaps_client()
    if not client:
        return []

    n = len(points)
    # Initialisation de la matrice avec des valeurs infinies
    matrice = [[0] * n for _ in range(n)]

    # Google Maps accepte max 10 origines × 10 destinations par requête
    taille_chunk = 10
    total_requetes = ((n + taille_chunk - 1) // taille_chunk) ** 2
    requete_actuelle = 0

    for i_debut in range(0, n, taille_chunk):
        i_fin = min(i_debut + taille_chunk, n)
        origines = [{'lat': points[k]['lat'], 'lng': points[k]['lng']} for k in range(i_debut, i_fin)]

        for j_debut in range(0, n, taille_chunk):
            j_fin = min(j_debut + taille_chunk, n)
            destinations = [{'lat': points[k]['lat'], 'lng': points[k]['lng']} for k in range(j_debut, j_fin)]

            try:
                resultat = client.distance_matrix(
                    origins=origines,
                    destinations=destinations,
                    mode="driving",
                    departure_time=datetime.now(),
                    traffic_model="best_guess"
                )

                for i_local, row in enumerate(resultat['rows']):
                    for j_local, element in enumerate(row['elements']):
                        i_global = i_debut + i_local
                        j_global = j_debut + j_local

                        if element['status'] == 'OK':
                            # Priorité à duration_in_traffic (avec trafic), fallback sur duration
                            if 'duration_in_traffic' in element:
                                duree = element['duration_in_traffic']['value']
                            else:
                                duree = element['duration']['value']
                            matrice[i_global][j_global] = duree
                        else:
                            # En cas d'erreur pour ce trajet, valeur très élevée
                            matrice[i_global][j_global] = 999999

            except Exception as e:
                st.warning(f"Erreur lors du calcul de la matrice : {e}")

            requete_actuelle += 1
            if progress_bar:
                progress_bar.progress(requete_actuelle / total_requetes)

    return matrice


def build_google_maps_url(points: list[dict]) -> str:
    """
    Génère l'URL Google Maps pour la navigation avec tous les waypoints dans l'ordre.

    Format: https://www.google.com/maps/dir/?api=1&origin=...&destination=...&waypoints=...
    """
    if len(points) < 2:
        return ""

    def encode_point(p):
        return f"{p['lat']},{p['lng']}"

    origine = encode_point(points[0])
    destination = encode_point(points[-1])

    if len(points) > 2:
        waypoints = "|".join(encode_point(p) for p in points[1:-1])
        url = (
            f"https://www.google.com/maps/dir/?api=1"
            f"&origin={origine}"
            f"&destination={destination}"
            f"&waypoints={waypoints}"
            f"&travelmode=driving"
        )
    else:
        url = (
            f"https://www.google.com/maps/dir/?api=1"
            f"&origin={origine}"
            f"&destination={destination}"
            f"&travelmode=driving"
        )

    return url
