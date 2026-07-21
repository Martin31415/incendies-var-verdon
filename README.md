# Carte interactive — Incendies Var / Verdon / Alpes-de-Haute-Provence

Carte interactive de visualisation des incendies historiques dans le Var, le Verdon et les Alpes-de-Haute-Provence.

## Déploiement (GitHub Pages)

1. Pusher ce dépôt sur GitHub :
   ```bash
   git remote add origin git@github.com:USER/incendies-var.git
   git push -u origin main
   ```

2. Activer GitHub Pages dans **Settings → Pages** :
   - Source : `Deploy from a branch`
   - Branch : `main` (ou `gh-pages`)
   - Dossier : `/ (root)`

3. La carte est accessible à `https://USER.github.io/incendies-var/`

## Ouverture en local

Ouvrir `index.html` directement dans un navigateur (file://) OU via un serveur statique :

```bash
python3 -m http.server 8080
# Puis ouvrir http://localhost:8080
```

## Fonctionnalités

- **Calque polygones** : périmètres approximatifs (cercles basés sur la surface) colorés par intensité
- **Calque points** : points de départ avec taille proportionnelle à la surface
- **Calque communes** : agrégation par commune
- **Filtre temporel** : slider année début/fin + animation par décennie
- **Filtre surface** : tous, >100 ha, >1000 ha, >5000 ha
- **Filtre département** : Var, Alpes-de-Haute-Provence, Bouches-du-Rhône
- **Filtre cause** : naturelle, humaine (accidentelle/volontaire), inconnue
- **Click** → popup détaillée (nom, date, surface, durée, cause, notes, source)
- **Survol** → info-bulle rapide
- **Zoom automatique** sur la région au chargement
- **Design sombre** avec dégradé de couleurs chaudes
- **Responsive** (mobile-friendly)

## Stack technique

- **[deck.gl](https://deck.gl/)** (CDN, v8.9) — moteur de rendu géospatial d'Uber/vis.gl qui équipe Kepler.gl
- **CARTO dark** — fond de carte raster sombre gratuit (pas de clé API)
- **Vanilla JS** — interface de filtres, popups, interactions
- **Aucun build step** — un seul fichier HTML auto-suffisant (~220 Ko)

> **Note :** Kepler.gl nécessite React + Redux + un bundler, incompatible avec la contrainte
> « un seul fichier HTML statique ». deck.gl, son moteur de rendu sous-jacent, expose la
> même API de calques (GeoJsonLayer, ScatterplotLayer, TileLayer) en vanilla JS via CDN.

## Source des données

Les données (`data/incendies.json`, également embarquées dans `index.html`) proviennent
d'une recherche web compilant les incendies historiques de la région.
Les polygones sont approximés (cercles basés sur la surface déclarée) en l'absence de
périmètres géoréférencés officiels. Quand `data/incendies_verified.json` sera produit avec
les vrais périmètres, le code les utilisera automatiquement.
