# 🔥 Incendies Var · Verdon · Alpes-de-Haute-Provence

Site web interactif de visualisation et d'analyse des incendies historiques dans le Var, le Verdon et les Alpes-de-Haute-Provence.

**Un seul fichier HTML statique** — publiable immédiatement sur GitHub Pages, sans build.

## 🚀 Déploiement (GitHub Pages)

1. **Créer un dépôt GitHub** et pousser ce dossier :
   ```bash
   git init
   git add .
   git commit -m "Site incendies Var - carte interactive & analyses"
   git remote add origin git@github.com:USER/incendies-var.git
   git push -u origin main
   ```

2. **Activer GitHub Pages** dans **Settings → Pages** :
   - Source : `Deploy from a branch`
   - Branch : `main`
   - Dossier : `/ (root)`

3. Le site est accessible à `https://USER.github.io/incendies-var/`

## 💻 Ouverture en local

Ouvrir `index.html` directement dans un navigateur, ou via un serveur statique :

```bash
python3 -m http.server 8080
# Puis http://localhost:8080
```

## 🗺️ Fonctionnalités

### Onglet Carte (deck.gl)
- **Calque polygones** : périmètres approximatifs (cercles basés sur la surface) colorés par intensité
- **Calque points** : points de départ avec taille proportionnelle à la surface
- **Calque communes** : agrégation par commune
- **Filtres** : période (sliders + animation par décennie), surface minimale, département, cause
- **Interactions** : clic → popup détaillée, survol → info-bulle
- **Fond de carte** : CARTO dark (gratuit, pas de clé API)

### Onglet Stats (Plotly.js)
- **Cartes de synthèse** : nombre total d'incendies, surface cumulée, plus grand incendie, etc.
- **Graphiques** : incendies par année, répartition par cause, par département, surface par décennie

### Onglets d'analyse (en cours)
- 🔥 **Heatmap** — densité spatiale des feux
- 💨 **Corridors** — axes de propagation
- ⚠️ **Risque** — carte de risque synthétique
- 📈 **Climat** — corrélations climat-incendie + projections

## 📊 Données

537 incendies recensés de 1854 à 2025. Données compilées par recherche web et archives historiques.

Fichiers source :
- `data/incendies_verified.json` — dataset complet (3.1 MB)
- `data/points_depart.json` — points de départ (151 KB)

Les polygones sont approximés (cercles basés sur la surface déclarée) en l'absence de périmètres géoréférencés officiels.

## 🛠️ Stack technique

| Librairie | Usage | CDN |
|-----------|-------|-----|
| [deck.gl](https://deck.gl/) v8.9 | Carte interactive, calques géospatiaux | unpkg |
| [Plotly.js](https://plotly.com/) v2.32 | Graphiques statistiques | cdn.plot.ly |
| CARTO dark | Fond de carte raster sombre | cartocdn.com |

- **Vanilla JS** — Aucun framework, aucun build step
- **CSS custom** — Design sombre (#0a0a0f), accent feu (#f0a050)
- **Responsive** — Mobile-friendly

## 📝 Sources & méthodologie

Les données proviennent de recherches web, archives Prométhée et documentation historique. Les surfaces antérieures à 1950 sont des estimations basées sur les archives disponibles. Les polygones sont des cercles approximatifs centrés sur les coordonnées du lieu-dit, avec un rayon calculé à partir de la surface déclarée.
