# 🚚 Optimiseur de Tournée de Livraison

Outil d'optimisation de tournée de livraison utilisant Google Maps (trafic en temps réel) et OR-Tools.

## Installation

### 1. Cloner / télécharger le projet

```bash
cd tournee-optimizer
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Configurer la clé API Google Maps

Copier le fichier d'exemple et remplir vos informations :

```bash
cp .env.example .env
```

Éditer `.env` :
```
GOOGLE_MAPS_API_KEY=votre_clé_api_ici
DEFAULT_START_ADDRESS=votre adresse de départ
```

**APIs Google Maps à activer dans votre projet Google Cloud :**
- Geocoding API
- Distance Matrix API

### 4. Lancer l'application

```bash
streamlit run app.py
```

L'application s'ouvre automatiquement sur http://localhost:8501

## Utilisation

1. **Adresse de départ** : saisissez votre entrepôt/domicile dans la barre latérale
2. **Adresses de livraison** : collez vos adresses (une par ligne) dans la zone principale
3. **Optimiser** : cliquez sur le bouton pour lancer le calcul
4. **Résultats** : consultez l'itinéraire ordonné, les temps d'étape et la carte interactive
5. **Export** : ouvrez directement dans Google Maps pour la navigation

## Architecture

| Fichier | Rôle |
|---------|------|
| `app.py` | Interface Streamlit |
| `optimizer.py` | Solveur OR-Tools (TSP) |
| `maps_client.py` | Client Google Maps |
| `config.py` | Configuration |

## Algorithme

- **Géocodage** : conversion des adresses en coordonnées GPS
- **Matrice de distances** : durées réelles avec trafic via Distance Matrix API
- **Optimisation** : TSP ouvert (sans retour) avec PATH_CHEAPEST_ARC + GUIDED_LOCAL_SEARCH
- **Visualisation** : carte Folium avec marqueurs numérotés et tracé de l'itinéraire
