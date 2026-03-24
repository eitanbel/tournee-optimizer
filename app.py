# Interface Streamlit principale - Optimiseur de tournée de livraison
import streamlit as st
import folium
from streamlit_folium import st_folium

from config import DEFAULT_START_ADDRESS
from maps_client import geocode_addresses, build_distance_matrix, build_google_maps_url
from optimizer import resoudre_tsp, formater_duree, calculer_durees_etapes

# Configuration de la page Streamlit
st.set_page_config(
    page_title="Optimiseur de Tournée",
    page_icon="🚚",
    layout="wide"
)

st.title("🚚 Optimiseur de Tournée de Livraison")
st.markdown("*Calcul de l'itinéraire optimal en tenant compte du trafic en temps réel*")

# ─────────────────────────────────────────────
# Barre latérale : aide
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        "**Comment utiliser :**\n"
        "1. Saisissez votre adresse de départ\n"
        "2. Collez vos adresses de livraison\n"
        "3. Cliquez sur **Optimiser**\n"
        "4. Exportez vers Google Maps"
    )

# ─────────────────────────────────────────────
# Zone principale : adresse de départ
# ─────────────────────────────────────────────
st.subheader("🏠 Adresse de départ")
adresse_depart = st.text_input(
    "Entrepôt / domicile",
    value=st.session_state.get("adresse_depart", DEFAULT_START_ADDRESS),
    placeholder="1 Rue de Rivoli, 75001 Paris, France",
    help="Ce sera toujours le point de départ de votre tournée."
)
st.session_state["adresse_depart"] = adresse_depart

st.divider()

# ─────────────────────────────────────────────
# Zone principale : saisie des adresses
# ─────────────────────────────────────────────
st.subheader("📦 Adresses de livraison")

# Adresses d'exemple en Île-de-France pour les tests
exemple_adresses = """Tour Eiffel, Paris
Musée du Louvre, Paris
Château de Versailles, Versailles
Aéroport Charles de Gaulle, Roissy-en-France
Disneyland Paris, Chessy"""

col1, col2 = st.columns([3, 1])
with col1:
    adresses_texte = st.text_area(
        "Collez vos adresses ici (une par ligne)",
        height=200,
        placeholder="10 Rue de la Paix, Paris\n15 Avenue Montaigne, Paris\n..."
    )
with col2:
    st.markdown("**Exemple Île-de-France :**")
    if st.button("📋 Charger l'exemple"):
        st.session_state["exemple_charge"] = True
        st.rerun()

# Chargement de l'exemple si demandé
if st.session_state.get("exemple_charge"):
    adresses_texte = exemple_adresses
    st.session_state["exemple_charge"] = False
    # Afficher directement avec le texte d'exemple
    adresses_texte = exemple_adresses

# ─────────────────────────────────────────────
# Bouton principal : lancer l'optimisation
# ─────────────────────────────────────────────
if st.button("🚀 Optimiser la tournée", type="primary", use_container_width=True):

    # Validation des entrées
    lignes = [l.strip() for l in adresses_texte.strip().split("\n") if l.strip()]

    if not adresse_depart.strip():
        st.error("⚠️ Veuillez saisir une adresse de départ.")
        st.stop()

    if len(lignes) == 0:
        st.warning("⚠️ Aucune adresse de livraison saisie. Veuillez en ajouter au moins une.")
        st.stop()

    if len(lignes) == 1:
        st.info("ℹ️ Une seule adresse de livraison : aucune optimisation nécessaire.")

    # ── Étape 1 : Géocodage ──
    with st.spinner("📍 Géocodage des adresses en cours..."):
        toutes_adresses = [adresse_depart] + lignes
        points, erreurs = geocode_addresses(toutes_adresses)

    if erreurs:
        for adresse_erreur in erreurs:
            st.warning(f"⚠️ Adresse non trouvée : **{adresse_erreur}**")

    if len(points) < 2:
        st.error("❌ Impossible de continuer : pas assez d'adresses géocodées avec succès.")
        st.stop()

    # ── Étape 2 : Matrice de distances ──
    st.markdown("**🗺️ Calcul de la matrice de temps de trajet avec trafic...**")
    barre_progression = st.progress(0)

    matrice = build_distance_matrix(points, progress_bar=barre_progression)
    barre_progression.progress(1.0)

    if not matrice:
        st.error("❌ Impossible de calculer la matrice de distances. Vérifiez votre clé API.")
        st.stop()

    # ── Étape 3 : Optimisation OR-Tools ──
    with st.spinner("⚙️ Optimisation de l'itinéraire en cours (jusqu'à 30 secondes)..."):
        itineraire = resoudre_tsp(matrice)

    # Réorganiser les points selon l'itinéraire optimal
    points_ordonnes = [points[i] for i in itineraire]
    durees_etapes = calculer_durees_etapes(itineraire, matrice)
    duree_totale = sum(durees_etapes)

    st.success("✅ Optimisation terminée !")

    # ─────────────────────────────────────────────
    # Affichage des résultats
    # ─────────────────────────────────────────────
    st.divider()
    st.subheader("📋 Itinéraire optimisé")

    # Résumé du temps total
    col_resume1, col_resume2, col_resume3 = st.columns(3)
    with col_resume1:
        st.metric("⏱️ Temps total", formater_duree(duree_totale))
    with col_resume2:
        st.metric("📍 Nombre d'arrêts", len(points_ordonnes) - 1)
    with col_resume3:
        st.metric("🏁 Arrêts inclus", len(points_ordonnes))

    # Liste ordonnée des étapes
    st.markdown("### Détail des étapes")
    for k, point in enumerate(points_ordonnes):
        if k == 0:
            st.markdown(f"**🏠 Départ :** {point['adresse_formatee']}")
        else:
            duree_etape = durees_etapes[k - 1]
            emoji = "🏁" if k == len(points_ordonnes) - 1 else f"📦"
            st.markdown(
                f"{emoji} **Arrêt {k}** : {point['adresse_formatee']}  \n"
                f"&nbsp;&nbsp;&nbsp;&nbsp;⏱️ Depuis l'étape précédente : **{formater_duree(duree_etape)}**"
            )

    # ─────────────────────────────────────────────
    # Carte Folium interactive
    # ─────────────────────────────────────────────
    st.divider()
    st.subheader("🗺️ Carte de l'itinéraire")

    # Centre de la carte : centroïde de tous les points
    lat_centre = sum(p['lat'] for p in points_ordonnes) / len(points_ordonnes)
    lng_centre = sum(p['lng'] for p in points_ordonnes) / len(points_ordonnes)

    carte = folium.Map(location=[lat_centre, lng_centre], zoom_start=10)

    # Couleurs pour les marqueurs
    couleurs = ["green"] + ["blue"] * (len(points_ordonnes) - 2) + ["red"]

    # Ajout des marqueurs numérotés
    for k, point in enumerate(points_ordonnes):
        if k == 0:
            label = "D"  # Départ
            couleur = "green"
            popup_text = f"🏠 Départ : {point['adresse_formatee']}"
        elif k == len(points_ordonnes) - 1:
            label = str(k)
            couleur = "red"
            popup_text = f"🏁 Arrêt final {k} : {point['adresse_formatee']}"
        else:
            label = str(k)
            couleur = "blue"
            popup_text = f"📦 Arrêt {k} : {point['adresse_formatee']}"

        folium.Marker(
            location=[point['lat'], point['lng']],
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=f"Arrêt {k}" if k > 0 else "Départ",
            icon=folium.Icon(color=couleur, icon="info-sign")
        ).add_to(carte)

        # Numéro sur le marqueur via DivIcon
        folium.Marker(
            location=[point['lat'], point['lng']],
            icon=folium.DivIcon(
                html=f'<div style="font-size:12px; font-weight:bold; color:white; '
                     f'background:{("green" if k==0 else "red" if k==len(points_ordonnes)-1 else "#3388ff")}; '
                     f'border-radius:50%; width:22px; height:22px; text-align:center; '
                     f'line-height:22px; margin-top:-11px; margin-left:-11px;">{label}</div>',
                icon_size=(22, 22),
                icon_anchor=(11, 11)
            )
        ).add_to(carte)

    # Tracé de la ligne de l'itinéraire
    coordonnees = [(p['lat'], p['lng']) for p in points_ordonnes]
    folium.PolyLine(
        coordonnees,
        weight=3,
        color="#FF6B35",
        opacity=0.8,
        tooltip="Itinéraire optimal"
    ).add_to(carte)

    # Affichage de la carte dans Streamlit
    st_folium(carte, width=None, height=500, use_container_width=True)

    # ─────────────────────────────────────────────
    # Export Google Maps
    # ─────────────────────────────────────────────
    st.divider()
    st.subheader("📤 Export Google Maps")

    url_gmaps = build_google_maps_url(points_ordonnes)
    if url_gmaps:
        st.markdown(
            f'<a href="{url_gmaps}" target="_blank">'
            f'<button style="background:#4285F4; color:white; border:none; padding:10px 20px; '
            f'border-radius:5px; cursor:pointer; font-size:16px;">🗺️ Ouvrir dans Google Maps</button>'
            f'</a>',
            unsafe_allow_html=True
        )
        st.caption("Ce lien ouvre la navigation complète dans Google Maps avec tous les waypoints dans l'ordre optimal.")

        with st.expander("🔗 Voir l'URL complète"):
            st.code(url_gmaps, language=None)
