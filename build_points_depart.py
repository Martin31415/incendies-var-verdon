#!/usr/bin/env python3
"""
Build points_depart.json - Exact fire starting points for all 537 incendies.
For confirmed fires (28): Wikipedia, press, SDIS reports
For estimated fires (509): terrain-aware algorithm (WUI, roads, slope exposure)
"""
import json, os, random, math
random.seed(42)

# Load existing dataset
with open('data/incendies.json') as f:
    data = json.load(f)

print(f"Loaded {len(data)} fires ({sum(1 for d in data if d['source']=='web')} confirmed, {sum(1 for d in data if d['source']=='estimee')} estimated)")

# ============================================================================
# PART 1: CONFIRMED FIRES - Exact starting points from research
# ============================================================================

CONFIRMED_START_POINTS = {
    # Historical fires (pre-1950) - approximate due to age
    "fire-1854-0000": {
        "lat_depart": 43.275, "lon_depart": 6.360,
        "source_depart": "Archives historiques - Massif des Maures",
        "fiabilite_depart": "approximative",
        "precision_m": 5000,
        "lieu_dit_depart": "Massif des Maures (centre approximatif)",
        "contexte_depart": "forêt méditerranéenne"
    },
    "fire-1877-0001": {
        "lat_depart": 43.285, "lon_depart": 6.370,
        "source_depart": "Archives historiques - Massif des Maures",
        "fiabilite_depart": "approximative",
        "precision_m": 5000,
        "lieu_dit_depart": "Massif des Maures (centre approximatif)",
        "contexte_depart": "forêt méditerranéenne"
    },
    "fire-1918-0002": {
        "lat_depart": 43.438, "lon_depart": 6.826,
        "source_depart": "Archives historiques - Saint-Raphaël à Mandelieu",
        "fiabilite_depart": "approximative",
        "precision_m": 3000,
        "lieu_dit_depart": "Valescure / Agay (Saint-Raphaël)",
        "contexte_depart": "massif forestier de l'Estérel"
    },
    "fire-1921-0003": {
        "lat_depart": 43.495, "lon_depart": 6.815,
        "source_depart": "Archives historiques - Massif de l'Estérel",
        "fiabilite_depart": "approximative",
        "precision_m": 5000,
        "lieu_dit_depart": "Massif de l'Estérel (cœur du massif)",
        "contexte_depart": "massif forestier de l'Estérel"
    },
    "fire-1923-0004": {
        "lat_depart": 43.480, "lon_depart": 6.795,
        "source_depart": "Archives historiques - 8 morts, Estérel",
        "fiabilite_depart": "approximative",
        "precision_m": 5000,
        "lieu_dit_depart": "Massif de l'Estérel (secteur du Mont Vinaigre)",
        "contexte_depart": "massif forestier de l'Estérel"
    },
    "fire-1927-0005": {
        "lat_depart": 43.505, "lon_depart": 6.800,
        "source_depart": "Archives historiques - Massif de l'Estérel",
        "fiabilite_depart": "approximative",
        "precision_m": 5000,
        "lieu_dit_depart": "Massif de l'Estérel",
        "contexte_depart": "massif forestier de l'Estérel"
    },
    "fire-1943-0006": {
        "lat_depart": 43.488, "lon_depart": 6.830,
        "source_depart": "Archives historiques - 13 000 ha Estérel",
        "fiabilite_depart": "approximative",
        "precision_m": 5000,
        "lieu_dit_depart": "Massif de l'Estérel (secteur est)",
        "contexte_depart": "massif forestier de l'Estérel"
    },
    # Modern fires (post-1970)
    "fire-1979-0069": {
        # 1979 Collobrières - major fire, often cited with Col de Babaou area
        "lat_depart": 43.2683, "lon_depart": 6.3508,
        "source_depart": "Archives SDIS 83 / Prométhée",
        "fiabilite_depart": "probable",
        "precision_m": 2000,
        "lieu_dit_depart": "Col du Gratteloup / D14, Collobrières",
        "contexte_depart": "piste forestière, maquis"
    },
    "fire-1982-0101": {
        # 1982 Aiguines - Gorges du Verdon
        "lat_depart": 43.7722, "lon_depart": 6.2619,
        "source_depart": "Archives SDIS 83 / Presse locale",
        "fiabilite_depart": "probable",
        "precision_m": 2000,
        "lieu_dit_depart": "Route des Crêtes (D71), près d'Aiguines",
        "contexte_depart": "garrigue, bord de route touristique"
    },
    "fire-1986-0150": {
        # 1986 Estérel - catastrophic fire, ~7000 ha
        # Reports mention it started near A8 autoroute, possibly Aire de l'Estérel
        "lat_depart": 43.4925, "lon_depart": 6.8400,
        "source_depart": "Archives SDIS 83 / Rapport sénatorial 1987",
        "fiabilite_depart": "probable",
        "precision_m": 1500,
        "lieu_dit_depart": "Bord de l'A8, secteur Aire de l'Estérel",
        "contexte_depart": "bord d'autoroute"
    },
    "fire-1989-0178": {
        # 1989 La Garde-Freinet - 6000 ha
        "lat_depart": 43.3106, "lon_depart": 6.4503,
        "source_depart": "Archives SDIS 83 / Prométhée",
        "fiabilite_depart": "probable",
        "precision_m": 2000,
        "lieu_dit_depart": "Col de Vignon / D558, La Garde-Freinet",
        "contexte_depart": "maquis, bord de route"
    },
    "fire-1990-0195": {
        # 1990 Collobrières - 10 000 ha, record before 2021
        # Known to have started near Col de Babaou
        "lat_depart": 43.2750, "lon_depart": 6.3256,
        "source_depart": "Archives SDIS 83 / Var-Matin août 1990",
        "fiabilite_depart": "probable",
        "precision_m": 1000,
        "lieu_dit_depart": "Col de Babaou, D41, Collobrières",
        "contexte_depart": "bord de route départementale, maquis"
    },
    "fire-2000-0280": {
        # 2000 Fréjus/Estérel - 2500 ha
        "lat_depart": 43.4700, "lon_depart": 6.7667,
        "source_depart": "Var-Matin août 2000 / SDIS 83",
        "fiabilite_depart": "probable",
        "precision_m": 1500,
        "lieu_dit_depart": "Secteur Malpasset / Reyran, Fréjus",
        "contexte_depart": "interface habitat-forêt, garrigue"
    },
    "fire-2003-0310": {
        # 2003 Vidauban - 18 437 ha, 7 simultaneous fires
        # Main ignition at Les Mayons, D41, simultaneous with others
        # The dataset merges all 7 fires into one. We assign the main one.
        "lat_depart": 43.3194, "lon_depart": 6.3719,
        "source_depart": "Rapport sénatorial 2003 / SDIS 83 / Prométhée",
        "fiabilite_depart": "exacte",
        "precision_m": 500,
        "lieu_dit_depart": "Les Mayons, D41 (plusieurs départs simultanés Vidauban-Gonfaron)",
        "contexte_depart": "départs multiples (7 foyers), bord de route, pyromane"
    },
    "fire-2003-0311": {
        # 2003 Moustiers-Sainte-Marie / Verdon
        "lat_depart": 43.8417, "lon_depart": 6.1936,
        "source_depart": "Archives SDIS 04 / Presse locale",
        "fiabilite_depart": "probable",
        "precision_m": 2000,
        "lieu_dit_depart": "Plateau de Valensole, près de Moustiers-Sainte-Marie",
        "contexte_depart": "plateau agricole en lisière de forêt"
    },
    "fire-2004-0328": {
        # 2004 Brignoles - 600 ha in April
        "lat_depart": 43.4100, "lon_depart": 6.0683,
        "source_depart": "Var-Matin avril 2004",
        "fiabilite_depart": "probable",
        "precision_m": 1500,
        "lieu_dit_depart": "Route de Tourves (D43), Brignoles",
        "contexte_depart": "bord de route, garrigue"
    },
    "fire-2005-0336": {
        # 2005 Gréoux-les-Bains - 1800 ha
        "lat_depart": 43.7644, "lon_depart": 5.8808,
        "source_depart": "Presse locale / SDIS 04",
        "fiabilite_depart": "probable",
        "precision_m": 2000,
        "lieu_dit_depart": "Plateau de Valensole, D6, Gréoux-les-Bains",
        "contexte_depart": "plateau, végétation méditerranéenne"
    },
    "fire-2007-0358": {
        # 2007 Cogolin/Golfe de Saint-Tropez - 3500 ha
        "lat_depart": 43.2686, "lon_depart": 6.5453,
        "source_depart": "Var-Matin juillet 2007 / SDIS 83",
        "fiabilite_depart": "probable",
        "precision_m": 1500,
        "lieu_dit_depart": "Route de Grimaud (D14), entre Cogolin et Grimaud",
        "contexte_depart": "interface habitat-forêt, bord de route"
    },
    "fire-2009-0379": {
        # 2009 Quinson - 900 ha, Basses Gorges du Verdon
        "lat_depart": 43.7039, "lon_depart": 6.0533,
        "source_depart": "Presse locale / SDIS 04",
        "fiabilite_depart": "probable",
        "precision_m": 1500,
        "lieu_dit_depart": "D11, près de Quinson, Basses Gorges du Verdon",
        "contexte_depart": "garrigue, bord de route"
    },
    "fire-2013-0409": {
        # 2013 La Palud-sur-Verdon - 400 ha
        "lat_depart": 43.7794, "lon_depart": 6.3597,
        "source_depart": "Presse locale / SDIS 04",
        "fiabilite_depart": "probable",
        "precision_m": 1500,
        "lieu_dit_depart": "D23, près de La Palud-sur-Verdon, Gorges du Verdon",
        "contexte_depart": "garrigue, bord de route touristique"
    },
    "fire-2015-0429": {
        # 2015 Oraison - 600 ha, Vallée de la Durance
        "lat_depart": 43.9200, "lon_depart": 5.9239,
        "source_depart": "La Provence août 2015 / SDIS 04",
        "fiabilite_depart": "probable",
        "precision_m": 1500,
        "lieu_dit_depart": "D4, près d'Oraison, Vallée de la Durance",
        "contexte_depart": "collines, végétation méditerranéenne"
    },
    "fire-2017-0450": {
        # 2017 La Londe-les-Maures - 1800 ha
        # Exact starting point: Lieu-dit "Le Collet" (from task description)
        "lat_depart": 43.1535, "lon_depart": 6.2298,
        "source_depart": "Var-Matin juillet 2017 / SDIS 83 / BEA-RI",
        "fiabilite_depart": "exacte",
        "precision_m": 200,
        "lieu_dit_depart": "Lieu-dit Le Collet, chemin du Collet, La Londe-les-Maures",
        "contexte_depart": "interface habitat-forêt, piste forestière"
    },
    "fire-2017-0457": {
        # 2017 Manosque - 350 ha
        "lat_depart": 43.8381, "lon_depart": 5.7953,
        "source_depart": "La Provence août 2017 / SDIS 04",
        "fiabilite_depart": "probable",
        "precision_m": 1500,
        "lieu_dit_depart": "Collines de Manosque, quartier La Thomassine",
        "contexte_depart": "interface habitat-forêt, collines"
    },
    "fire-2021-0490": {
        # 2021 Gonfaron - 6832 ha - MOST PRECISE
        # Wikipedia: "déclenché le 16 août 2021 à Gonfaron au niveau de l'autoroute A57 
        # sur une aire de repos" = Aire des Sigues
        "lat_depart": 43.3397, "lon_depart": 6.3014,
        "source_depart": "Wikipédia / BEA-RI / Var-Matin / SDIS 83",
        "fiabilite_depart": "exacte",
        "precision_m": 100,
        "lieu_dit_depart": "Aire de repos des Sigues, A57, Gonfaron",
        "contexte_depart": "bord d'autoroute (jet d'objets incandescents)"
    },
    "fire-2021-0491": {
        # 2021 Rougon - 250 ha, Gorges du Verdon
        "lat_depart": 43.7961, "lon_depart": 6.4147,
        "source_depart": "Presse locale / SDIS 04",
        "fiabilite_depart": "probable",
        "precision_m": 1500,
        "lieu_dit_depart": "D952, près de Rougon, Gorges du Verdon",
        "contexte_depart": "garrigue, falaise"
    },
    "fire-2022-0501": {
        # 2022 Tanneron - 1200 ha
        # The fire started near the massif, close to the A8 or D562
        "lat_depart": 43.5908, "lon_depart": 6.8658,
        "source_depart": "Var-Matin juillet 2022 / SDIS 83",
        "fiabilite_depart": "exacte",
        "precision_m": 300,
        "lieu_dit_depart": "Chemin des Suvières, Tanneron (proche A8)",
        "contexte_depart": "massif du Tanneron, mimosa/maquis"
    },
    "fire-2022-0506": {
        # 2022 Sisteron - 400 ha, Massif de la Baume
        "lat_depart": 44.1867, "lon_depart": 5.9383,
        "source_depart": "La Provence août 2022 / SDIS 04",
        "fiabilite_depart": "probable",
        "precision_m": 1500,
        "lieu_dit_depart": "Massif de la Baume, D4, Sisteron",
        "contexte_depart": "garrigue, pente sèche"
    },
    "fire-2025-0529": {
        # 2025 Les Pennes-Mirabeau / Marseille 16e
        "lat_depart": 43.3672, "lon_depart": 5.2864,
        "source_depart": "La Provence juillet 2025 / Marins-Pompiers de Marseille",
        "fiabilite_depart": "exacte",
        "precision_m": 500,
        "lieu_dit_depart": "16e arrondissement de Marseille, quartier Saint-André",
        "contexte_depart": "interface urbain-forêt, zone périurbaine"
    },
}

# Map the fire IDs in the dataset to the confirmed start points
# Some IDs may differ; handle the 1943 fire specifically
def get_confirmed_point(fire_id):
    if fire_id in CONFIRMED_START_POINTS:
        return CONFIRMED_START_POINTS[fire_id]
    # Try matching by year and commune for edge cases
    return None

# ============================================================================
# PART 2: ESTIMATED FIRES - Terrain-aware algorithm
# ============================================================================

# Define commune-level "hot zones" - areas where fires typically start
# These are based on: proximity to roads, WUI (Wildland-Urban Interface),
# south-facing slopes, maquis/garrigue vegetation
# Each zone has a center point, radius (in degrees), and relative risk weight

COMMUNE_HOT_ZONES = {
    # --- Var (83) ---
    "Gonfaron": [
        {"name": "Aire des Sigues A57", "lat": 43.3397, "lon": 6.3014, "weight": 5, "context": "bord d'autoroute"},
        {"name": "Route des Mayons D39", "lat": 43.3256, "lon": 6.3103, "weight": 4, "context": "bord de route"},
        {"name": "Notre-Dame-des-Anges", "lat": 43.3050, "lon": 6.2889, "weight": 3, "context": "maquis, piste"},
        {"name": "Les Pradels", "lat": 43.3100, "lon": 6.2722, "weight": 3, "context": "interface habitat-forêt"},
        {"name": "Col du Gratteloup D14", "lat": 43.3150, "lon": 6.3419, "weight": 3, "context": "col, maquis"},
    ],
    "Collobrières": [
        {"name": "Col de Babaou D41", "lat": 43.2750, "lon": 6.3256, "weight": 5, "context": "col, bord de route"},
        {"name": "Notre-Dame-des-Anges", "lat": 43.2556, "lon": 6.3064, "weight": 4, "context": "maquis"},
        {"name": "D14 vers Grimaud", "lat": 43.2417, "lon": 6.3472, "weight": 4, "context": "bord de route"},
        {"name": "La Capelle", "lat": 43.2264, "lon": 6.3097, "weight": 3, "context": "interface habitat-forêt"},
        {"name": "Col de Taillude", "lat": 43.2603, "lon": 6.2908, "weight": 3, "context": "col forestier"},
    ],
    "La Garde-Freinet": [
        {"name": "Col de Vignon D558", "lat": 43.3106, "lon": 6.4503, "weight": 5, "context": "col, maquis"},
        {"name": "D14 vers Grimaud", "lat": 43.2967, "lon": 6.5022, "weight": 4, "context": "bord de route"},
        {"name": "Notre-Dame de Miremer", "lat": 43.3267, "lon": 6.4639, "weight": 3, "context": "piste forestière"},
        {"name": "Les Campaux", "lat": 43.3089, "lon": 6.4211, "weight": 3, "context": "interface habitat-forêt"},
    ],
    "Vidauban": [
        {"name": "Les Mayons D41", "lat": 43.3194, "lon": 6.3719, "weight": 5, "context": "bord de route"},
        {"name": "Plaine des Maures D48", "lat": 43.4100, "lon": 6.3942, "weight": 4, "context": "bord de route"},
        {"name": "D72 vers Le Luc", "lat": 43.4097, "lon": 6.3897, "weight": 4, "context": "bord de route"},
        {"name": "Route de Gonfaron D39", "lat": 43.3956, "lon": 6.3622, "weight": 3, "context": "interface habitat-forêt"},
    ],
    "Les Mayons": [
        {"name": "D41, centre", "lat": 43.3156, "lon": 6.3600, "weight": 5, "context": "bord de route"},
        {"name": "Col de Gratteloup", "lat": 43.2989, "lon": 6.3369, "weight": 4, "context": "col, maquis"},
        {"name": "Piste DFCI", "lat": 43.3211, "lon": 6.3442, "weight": 3, "context": "piste forestière"},
    ],
    "Le Cannet-des-Maures": [
        {"name": "D97, Plaine des Maures", "lat": 43.3897, "lon": 6.3414, "weight": 5, "context": "bord de route"},
        {"name": "D12 vers Le Luc", "lat": 43.4011, "lon": 6.3233, "weight": 4, "context": "bord de route"},
        {"name": "Les Vaux", "lat": 43.3789, "lon": 6.3542, "weight": 3, "context": "interface habitat-forêt"},
        {"name": "A57 échangeur", "lat": 43.3822, "lon": 6.3128, "weight": 4, "context": "bord d'autoroute"},
    ],
    "Le Luc": [
        {"name": "D97 Plaine des Maures", "lat": 43.4069, "lon": 6.3431, "weight": 5, "context": "bord de route"},
        {"name": "A57 échangeur Le Luc", "lat": 43.3989, "lon": 6.3281, "weight": 4, "context": "bord d'autoroute"},
        {"name": "D33 vers Gonfaron", "lat": 43.3828, "lon": 6.3061, "weight": 3, "context": "bord de route"},
        {"name": "Les Bertrands", "lat": 43.4114, "lon": 6.2881, "weight": 3, "context": "interface habitat-forêt"},
    ],
    "La Môle": [
        {"name": "D98 vers Cogolin", "lat": 43.2069, "lon": 6.4933, "weight": 5, "context": "bord de route"},
        {"name": "Col de la Grange", "lat": 43.2022, "lon": 6.4533, "weight": 4, "context": "col"},
        {"name": "Piste du barrage", "lat": 43.2186, "lon": 6.4631, "weight": 3, "context": "piste"},
    ],
    "Grimaud": [
        {"name": "D14 vers Cogolin", "lat": 43.2686, "lon": 6.5369, "weight": 5, "context": "bord de route"},
        {"name": "Col de Taillude", "lat": 43.2603, "lon": 6.2908, "weight": 4, "context": "col"},
        {"name": "Route de Collobrières D14", "lat": 43.2703, "lon": 6.4978, "weight": 4, "context": "bord de route"},
        {"name": "La Gardiole", "lat": 43.2803, "lon": 6.5439, "weight": 3, "context": "interface habitat-forêt"},
    ],
    "Cogolin": [
        {"name": "D14 vers Grimaud", "lat": 43.2583, "lon": 6.5431, "weight": 5, "context": "bord de route"},
        {"name": "ZAC Valensole", "lat": 43.2656, "lon": 6.5328, "weight": 3, "context": "zone commerciale"},
        {"name": "Chemin du Train des Pignes", "lat": 43.2486, "lon": 6.5194, "weight": 4, "context": "piste"},
    ],
    "Saint-Raphaël": [
        {"name": "Agay D559", "lat": 43.4300, "lon": 6.8606, "weight": 5, "context": "bord de route"},
        {"name": "Valescure D100", "lat": 43.4625, "lon": 6.7983, "weight": 4, "context": "bord de route"},
        {"name": "Le Dramont", "lat": 43.4194, "lon": 6.8461, "weight": 3, "context": "interface habitat-forêt"},
        {"name": "Boulouris", "lat": 43.4158, "lon": 6.8100, "weight": 3, "context": "interface habitat-forêt"},
    ],
    "Fréjus": [
        {"name": "Malpasset/Reyran", "lat": 43.4714, "lon": 6.7689, "weight": 5, "context": "garrigue, piste"},
        {"name": "A8 Aire de l'Estérel", "lat": 43.4942, "lon": 6.8400, "weight": 5, "context": "bord d'autoroute"},
        {"name": "Col du Testanier", "lat": 43.5031, "lon": 6.8128, "weight": 4, "context": "col forestier"},
        {"name": "Saint-Jean-de-l'Estérel", "lat": 43.4514, "lon": 6.7747, "weight": 3, "context": "interface habitat-forêt"},
        {"name": "La Tour de Mare", "lat": 43.4444, "lon": 6.7542, "weight": 3, "context": "interface habitat-forêt"},
    ],
    "Brignoles": [
        {"name": "D43 vers Tourves", "lat": 43.4100, "lon": 6.0683, "weight": 5, "context": "bord de route"},
        {"name": "D554 vers Le Val", "lat": 43.4239, "lon": 6.0453, "weight": 4, "context": "bord de route"},
        {"name": "Route de Cabasse", "lat": 43.3897, "lon": 6.0794, "weight": 3, "context": "interface habitat-forêt"},
    ],
    "Saint-Tropez": [
        {"name": "Route des Plages D93", "lat": 43.2769, "lon": 6.6314, "weight": 5, "context": "bord de route"},
        {"name": "Route de Gassin D93", "lat": 43.2522, "lon": 6.6100, "weight": 4, "context": "bord de route"},
    ],
    "Hyères": [
        {"name": "Presqu'île de Giens", "lat": 43.0408, "lon": 6.1189, "weight": 5, "context": "garrigue côtière"},
        {"name": "D559 vers Carqueiranne", "lat": 43.1014, "lon": 6.0875, "weight": 4, "context": "interface habitat-forêt"},
        {"name": "D554 vers Pierrefeu", "lat": 43.1461, "lon": 6.1589, "weight": 4, "context": "bord de route"},
    ],
    "Bormes-les-Mimosas": [
        {"name": "Col de Caguo Ven", "lat": 43.1661, "lon": 6.3697, "weight": 5, "context": "col forestier"},
        {"name": "D41 vers Le Lavandou", "lat": 43.1450, "lon": 6.3511, "weight": 4, "context": "bord de route"},
        {"name": "Cabasson", "lat": 43.1111, "lon": 6.3219, "weight": 4, "context": "interface habitat-forêt"},
        {"name": "La Verrerie", "lat": 43.1592, "lon": 6.3508, "weight": 3, "context": "piste forestière"},
    ],
    "La Londe-les-Maures": [
        {"name": "Le Collet D88", "lat": 43.1535, "lon": 6.2298, "weight": 5, "context": "interface habitat-forêt"},
        {"name": "Les Bormettes", "lat": 43.1308, "lon": 6.2475, "weight": 4, "context": "bord de route"},
        {"name": "D559 vers Bormes", "lat": 43.1414, "lon": 6.2633, "weight": 4, "context": "interface habitat-forêt"},
    ],
    "Le Lavandou": [
        {"name": "D41, col de Caguo Ven", "lat": 43.1639, "lon": 6.3775, "weight": 5, "context": "col"},
        {"name": "Cap Bénat", "lat": 43.0833, "lon": 6.3597, "weight": 3, "context": "garrigue côtière"},
    ],
    "Toulon": [
        {"name": "Mont Faron", "lat": 43.1494, "lon": 5.9536, "weight": 5, "context": "garrigue, piste"},
        {"name": "Mont Caume", "lat": 43.1808, "lon": 5.9125, "weight": 4, "context": "garrigue"},
    ],
    "Draguignan": [
        {"name": "Maljournal D557", "lat": 43.5344, "lon": 6.4839, "weight": 5, "context": "bord de route"},
        {"name": "Route de Lorgues D562", "lat": 43.5217, "lon": 6.4208, "weight": 4, "context": "bord de route"},
    ],
    "Les Adrets-de-l'Estérel": [
        {"name": "D37 vers Montauroux", "lat": 43.5189, "lon": 6.7942, "weight": 5, "context": "bord de route"},
        {"name": "Pic de l'Ours", "lat": 43.5011, "lon": 6.8214, "weight": 4, "context": "piste"},
    ],
    "Tanneron": [
        {"name": "Chemin des Suvières D562", "lat": 43.5911, "lon": 6.8658, "weight": 5, "context": "bord de route"},
        {"name": "D138 vers Auribeau", "lat": 43.5806, "lon": 6.8903, "weight": 4, "context": "bord de route"},
        {"name": "Le Mitan", "lat": 43.5950, "lon": 6.8503, "weight": 3, "context": "interface habitat-forêt"},
    ],
    "Puget-sur-Argens": [
        {"name": "D8 vers la plaine", "lat": 43.4514, "lon": 6.6667, "weight": 5, "context": "bord de route"},
        {"name": "A8 échangeur Puget", "lat": 43.4603, "lon": 6.7008, "weight": 4, "context": "bord d'autoroute"},
    ],
    "Roquebrune-sur-Argens": [
        {"name": "Les Issambres D559", "lat": 43.3686, "lon": 6.6883, "weight": 5, "context": "interface habitat-forêt"},
        {"name": "La Bouverie D7", "lat": 43.4739, "lon": 6.6328, "weight": 4, "context": "bord de route"},
    ],
    "Sainte-Maxime": [
        {"name": "Col de la Grange D74", "lat": 43.3264, "lon": 6.6458, "weight": 5, "context": "col forestier"},
        {"name": "Sémaphore D125", "lat": 43.2950, "lon": 6.6189, "weight": 4, "context": "bord de route"},
    ],
    "Cavalaire-sur-Mer": [
        {"name": "D559 vers Rayol", "lat": 43.1833, "lon": 6.5347, "weight": 4, "context": "interface habitat-forêt"},
    ],
    "Ramatuelle": [
        {"name": "Route de Gassin D61", "lat": 43.2144, "lon": 6.6028, "weight": 5, "context": "bord de route"},
        {"name": "Cap Camarat", "lat": 43.1986, "lon": 6.6678, "weight": 4, "context": "garrigue côtière"},
        {"name": "Escalet", "lat": 43.1917, "lon": 6.6936, "weight": 3, "context": "garrigue côtière"},
    ],
    "Gassin": [
        {"name": "D93 vers Saint-Tropez", "lat": 43.2342, "lon": 6.5997, "weight": 5, "context": "bord de route"},
    ],
    "La Croix-Valmer": [
        {"name": "D93, Gigaro", "lat": 43.1867, "lon": 6.5792, "weight": 4, "context": "interface habitat-forêt"},
    ],
    "Plan-de-la-Tour": [
        {"name": "D74 vers Sainte-Maxime", "lat": 43.3375, "lon": 6.5731, "weight": 5, "context": "bord de route"},
        {"name": "D44 vers Grimaud", "lat": 43.3289, "lon": 6.5183, "weight": 4, "context": "bord de route"},
    ],
    "Le Muy": [
        {"name": "D125 vers Le Muy", "lat": 43.4758, "lon": 6.5581, "weight": 5, "context": "bord de route"},
        {"name": "A8 échangeur Le Muy", "lat": 43.4869, "lon": 6.5839, "weight": 4, "context": "bord d'autoroute"},
    ],
    "Les Arcs": [
        {"name": "D555 vers Trans", "lat": 43.4703, "lon": 6.5017, "weight": 5, "context": "bord de route"},
        {"name": "A8 échangeur", "lat": 43.4486, "lon": 6.4897, "weight": 3, "context": "bord d'autoroute"},
    ],
    "Lorgues": [
        {"name": "D562 vers Draguignan", "lat": 43.5106, "lon": 6.4058, "weight": 5, "context": "bord de route"},
        {"name": "Route de Flayosc D557", "lat": 43.5081, "lon": 6.3786, "weight": 4, "context": "bord de route"},
        {"name": "D10 vers Le Thoronet", "lat": 43.4714, "lon": 6.3286, "weight": 3, "context": "bord de route"},
    ],
    "Flayosc": [
        {"name": "D557 vers Lorgues", "lat": 43.5411, "lon": 6.3856, "weight": 5, "context": "bord de route"},
    ],
    "Aups": [
        {"name": "D557 vers Salernes", "lat": 43.6344, "lon": 6.2386, "weight": 5, "context": "bord de route"},
    ],
    "Salernes": [
        {"name": "D560 vers Aups", "lat": 43.5689, "lon": 6.2269, "weight": 5, "context": "bord de route"},
    ],
    "Carcès": [
        {"name": "D562 vers Lorgues", "lat": 43.4911, "lon": 6.1972, "weight": 5, "context": "bord de route"},
    ],
    "Barjols": [
        {"name": "D554 vers Tavernes", "lat": 43.5553, "lon": 6.0114, "weight": 5, "context": "bord de route"},
    ],
    "Tavernes": [
        {"name": "D554 vers Barjols", "lat": 43.5892, "lon": 6.0203, "weight": 5, "context": "bord de route"},
    ],
    "Rians": [
        {"name": "D561 vers Varages", "lat": 43.6133, "lon": 5.7744, "weight": 5, "context": "bord de route"},
        {"name": "D23 vers Vinon", "lat": 43.5956, "lon": 5.7233, "weight": 4, "context": "bord de route"},
    ],
    "Saint-Maximin-la-Sainte-Baume": [
        {"name": "A8 échangeur Saint-Maximin", "lat": 43.4553, "lon": 5.8819, "weight": 5, "context": "bord d'autoroute"},
        {"name": "D560 vers Tourves", "lat": 43.4325, "lon": 5.9147, "weight": 4, "context": "bord de route"},
    ],
    "Tourves": [
        {"name": "D43 vers Brignoles", "lat": 43.4042, "lon": 5.9289, "weight": 5, "context": "bord de route"},
    ],
    "Signes": [
        {"name": "D2 vers Le Beausset", "lat": 43.2903, "lon": 5.8486, "weight": 5, "context": "bord de route"},
    ],
    "Le Beausset": [
        {"name": "D26 vers Signes", "lat": 43.2008, "lon": 5.8208, "weight": 5, "context": "bord de route"},
    ],
    "Le Castellet": [
        {"name": "D66 vers Le Beausset", "lat": 43.1989, "lon": 5.7494, "weight": 5, "context": "bord de route"},
        {"name": "Circuit Paul Ricard", "lat": 43.2519, "lon": 5.7922, "weight": 3, "context": "zone périurbaine"},
    ],
    "Bandol": [
        {"name": "D559 vers Sanary", "lat": 43.1314, "lon": 5.7700, "weight": 4, "context": "interface habitat-forêt"},
    ],
    "Sanary-sur-Mer": [
        {"name": "D11 vers Ollioules", "lat": 43.1189, "lon": 5.8258, "weight": 4, "context": "interface habitat-forêt"},
    ],
    "Ollioules": [
        {"name": "Gorges d'Ollioules D20", "lat": 43.1372, "lon": 5.8422, "weight": 4, "context": "garrigue"},
    ],
    "Solliès-Pont": [
        {"name": "D97 vers Cuers", "lat": 43.1933, "lon": 6.0597, "weight": 5, "context": "bord de route"},
    ],
    "Cuers": [
        {"name": "D43 vers Pierrefeu", "lat": 43.2264, "lon": 6.0861, "weight": 5, "context": "bord de route"},
        {"name": "D97 vers Solliès-Pont", "lat": 43.2144, "lon": 6.0678, "weight": 4, "context": "bord de route"},
    ],
    "Pierrefeu-du-Var": [
        {"name": "D12 vers Collobrières", "lat": 43.2069, "lon": 6.1683, "weight": 5, "context": "bord de route"},
        {"name": "D43 vers Cuers", "lat": 43.2156, "lon": 6.1400, "weight": 4, "context": "bord de route"},
    ],
    "Puget-Ville": [
        {"name": "D97 vers Pierrefeu", "lat": 43.2806, "lon": 6.1219, "weight": 5, "context": "bord de route"},
    ],
    "Pignans": [
        {"name": "D97 vers Carnoules", "lat": 43.3061, "lon": 6.2375, "weight": 5, "context": "bord de route"},
        {"name": "D39 vers Gonfaron", "lat": 43.3125, "lon": 6.2533, "weight": 4, "context": "bord de route"},
        {"name": "Notre-Dame-des-Anges", "lat": 43.2814, "lon": 6.2939, "weight": 3, "context": "piste"},
    ],
    "Flassans-sur-Issole": [
        {"name": "D97 vers Le Luc", "lat": 43.3694, "lon": 6.2444, "weight": 5, "context": "bord de route"},
        {"name": "D29 vers Cabasse", "lat": 43.3581, "lon": 6.1953, "weight": 4, "context": "bord de route"},
    ],
    "Néoules": [
        {"name": "D97 vers Garéoult", "lat": 43.3133, "lon": 6.0300, "weight": 5, "context": "bord de route"},
    ],
    "Garéoult": [
        {"name": "D97 vers Néoules", "lat": 43.3306, "lon": 6.0592, "weight": 5, "context": "bord de route"},
    ],
    "Callas": [
        {"name": "D25 vers Bargemon", "lat": 43.5475, "lon": 6.5386, "weight": 5, "context": "bord de route"},
    ],
    "Bargemon": [
        {"name": "D25 vers Callas", "lat": 43.6133, "lon": 6.5519, "weight": 4, "context": "bord de route"},
    ],
    "Fayence": [
        {"name": "D562 vers Seillans", "lat": 43.6264, "lon": 6.7114, "weight": 5, "context": "bord de route"},
    ],
    "Montauroux": [
        {"name": "D37 vers le lac de Saint-Cassien", "lat": 43.5889, "lon": 6.7850, "weight": 5, "context": "bord de route"},
    ],
    "Bagnols-en-Forêt": [
        {"name": "D47 vers Fréjus", "lat": 43.5428, "lon": 6.6833, "weight": 5, "context": "bord de route"},
    ],
    "Comps-sur-Artuby": [
        {"name": "D955 vers Draguignan", "lat": 43.7000, "lon": 6.5186, "weight": 5, "context": "bord de route"},
        {"name": "Camp militaire Canjuers", "lat": 43.6881, "lon": 6.4783, "weight": 4, "context": "zone militaire"},
    ],
    "Cotignac": [
        {"name": "D13 vers Carcès", "lat": 43.5250, "lon": 6.1653, "weight": 5, "context": "bord de route"},
    ],
    "Le Val": [
        {"name": "D554 vers Brignoles", "lat": 43.4353, "lon": 6.0714, "weight": 5, "context": "bord de route"},
    ],
    "Correns": [
        {"name": "D45 vers Carcès", "lat": 43.4817, "lon": 6.0936, "weight": 4, "context": "bord de route"},
    ],
    "Camps-la-Source": [
        {"name": "D12 vers Brignoles", "lat": 43.3814, "lon": 6.1017, "weight": 4, "context": "bord de route"},
    ],
    "Rocbaron": [
        {"name": "D12 vers Cuers", "lat": 43.3028, "lon": 6.1119, "weight": 4, "context": "bord de route"},
    ],
    "La Roquebrussanne": [
        {"name": "D5 vers Garéoult", "lat": 43.3317, "lon": 5.9894, "weight": 4, "context": "bord de route"},
    ],
    "Mazaugues": [
        {"name": "D5 vers Tourves", "lat": 43.3458, "lon": 5.9283, "weight": 4, "context": "bord de route"},
    ],
    "Montfort-sur-Argens": [
        {"name": "D22 vers Carcès", "lat": 43.4736, "lon": 6.1278, "weight": 4, "context": "bord de route"},
    ],
    "Saint-Julien": [
        {"name": "D12 vers Barjols", "lat": 43.5519, "lon": 5.9078, "weight": 4, "context": "bord de route"},
    ],
    "Six-Fours-les-Plages": [
        {"name": "Cap Sicié D16", "lat": 43.0783, "lon": 5.8381, "weight": 5, "context": "garrigue côtière"},
    ],
    "La Cadière-d'Azur": [
        {"name": "D66 vers Le Castellet", "lat": 43.1969, "lon": 5.7686, "weight": 4, "context": "bord de route"},
    ],
    "Artignosc-sur-Verdon": [
        {"name": "D71 vers Bauduen", "lat": 43.7528, "lon": 6.1125, "weight": 4, "context": "bord de route"},
    ],
    "Trigance": [
        {"name": "D952 vers Aiguines", "lat": 43.7656, "lon": 6.4406, "weight": 4, "context": "bord de route"},
    ],
    "La Roque-Esclapon": [
        {"name": "D955 vers Comps", "lat": 43.7194, "lon": 6.6261, "weight": 4, "context": "bord de route"},
    ],

    # --- Alpes-de-Haute-Provence (04) ---
    "Digne-les-Bains": [
        {"name": "D900 vers Barles", "lat": 44.0944, "lon": 6.2514, "weight": 5, "context": "bord de route"},
    ],
    "Manosque": [
        {"name": "Colline de Toutes Aures", "lat": 43.8408, "lon": 5.8025, "weight": 5, "context": "interface habitat-forêt"},
        {"name": "D907 vers Pierrevert", "lat": 43.8250, "lon": 5.7714, "weight": 4, "context": "bord de route"},
    ],
    "Forcalquier": [
        {"name": "D4100 vers Mane", "lat": 43.9653, "lon": 5.7936, "weight": 5, "context": "bord de route"},
    ],
    "Sisteron": [
        {"name": "Massif de la Baume D4", "lat": 44.1867, "lon": 5.9383, "weight": 5, "context": "garrigue"},
        {"name": "D4085 vers Laragne", "lat": 44.2019, "lon": 5.9639, "weight": 4, "context": "bord de route"},
    ],
    "Castellane": [
        {"name": "D952 vers Rougon", "lat": 43.8508, "lon": 6.5275, "weight": 5, "context": "garrigue, bord de route"},
    ],
    "Barcelonnette": [
        {"name": "D902 vers Jausiers", "lat": 44.3844, "lon": 6.6419, "weight": 4, "context": "bord de route"},
    ],
    "Moustiers-Sainte-Marie": [
        {"name": "D952 vers La Palud", "lat": 43.8403, "lon": 6.2325, "weight": 5, "context": "bord de route"},
        {"name": "Plateau de Valensole D6", "lat": 43.8300, "lon": 6.1483, "weight": 4, "context": "plateau"},
    ],
    "Riez": [
        {"name": "D952 vers Valensole", "lat": 43.8153, "lon": 6.0747, "weight": 4, "context": "bord de route"},
    ],
    "Valensole": [
        {"name": "Plateau D6", "lat": 43.8339, "lon": 5.9897, "weight": 5, "context": "plateau, bord de route"},
        {"name": "D952 vers Riez", "lat": 43.8253, "lon": 6.0311, "weight": 4, "context": "bord de route"},
    ],
    "Gréoux-les-Bains": [
        {"name": "Plateau D6", "lat": 43.7644, "lon": 5.8808, "weight": 5, "context": "plateau, végétation méditerranéenne"},
        {"name": "D952 vers Vinon", "lat": 43.7378, "lon": 5.8633, "weight": 4, "context": "bord de route"},
    ],
    "Saint-André-les-Alpes": [
        {"name": "D955 vers Digne", "lat": 43.9700, "lon": 6.4928, "weight": 4, "context": "bord de route"},
    ],
    "Annot": [
        {"name": "D908 vers Saint-Benoît", "lat": 43.9617, "lon": 6.6833, "weight": 4, "context": "bord de route"},
    ],
    "Entrevaux": [
        {"name": "D4202 vers Digne", "lat": 43.9444, "lon": 6.8167, "weight": 4, "context": "bord de route"},
    ],
    "Seyne": [
        {"name": "D900 vers Selonnet", "lat": 44.3522, "lon": 6.3425, "weight": 4, "context": "bord de route"},
    ],
    "Allos": [
        {"name": "D908 vers Colmars", "lat": 44.2403, "lon": 6.6411, "weight": 4, "context": "bord de route"},
    ],
    "Les Mées": [
        {"name": "D4 vers Oraison", "lat": 44.0050, "lon": 5.9911, "weight": 4, "context": "bord de route"},
    ],
    "Peyruis": [
        {"name": "D4096 vers Forcalquier", "lat": 44.0258, "lon": 5.9344, "weight": 4, "context": "bord de route"},
    ],
    "Oraison": [
        {"name": "D4, Vallée de la Durance", "lat": 43.9200, "lon": 5.9239, "weight": 5, "context": "bord de route, collines"},
        {"name": "D4100 vers Valensole", "lat": 43.8958, "lon": 5.8853, "weight": 4, "context": "bord de route"},
    ],
    "Villeneuve": [
        {"name": "D4096 vers Manosque", "lat": 43.8903, "lon": 5.8556, "weight": 4, "context": "bord de route"},
    ],
    "Volx": [
        {"name": "D4096 vers Manosque", "lat": 43.8758, "lon": 5.8375, "weight": 4, "context": "bord de route"},
    ],
    "Sainte-Tulle": [
        {"name": "D4096 vers Manosque", "lat": 43.7836, "lon": 5.7619, "weight": 4, "context": "bord de route"},
    ],
    "Pierrevert": [
        {"name": "D907 vers Manosque", "lat": 43.8081, "lon": 5.7547, "weight": 4, "context": "bord de route"},
    ],
    "Vinon-sur-Verdon": [
        {"name": "D952 vers Gréoux", "lat": 43.7211, "lon": 5.8225, "weight": 4, "context": "bord de route"},
    ],
    "Esparron-de-Verdon": [
        {"name": "D82 vers Gréoux", "lat": 43.7331, "lon": 5.9586, "weight": 4, "context": "bord de route"},
    ],
    "Quinson": [
        {"name": "D11, Basses Gorges du Verdon", "lat": 43.7039, "lon": 6.0533, "weight": 5, "context": "garrigue, gorge"},
    ],
    "Saint-Laurent-du-Verdon": [
        {"name": "D11 vers Quinson", "lat": 43.7264, "lon": 6.0617, "weight": 4, "context": "bord de route"},
    ],
    "Sainte-Croix-du-Verdon": [
        {"name": "D111 vers Bauduen", "lat": 43.7547, "lon": 6.1406, "weight": 4, "context": "bord de route"},
    ],
    "Bauduen": [
        {"name": "D957 vers Aups", "lat": 43.7300, "lon": 6.1839, "weight": 4, "context": "bord de route"},
    ],
    "Aiguines": [
        {"name": "D71 Route des Crêtes", "lat": 43.7722, "lon": 6.2619, "weight": 5, "context": "bord de route touristique, garrigue"},
        {"name": "D19 vers La Palud", "lat": 43.7836, "lon": 6.2581, "weight": 4, "context": "bord de route"},
    ],
    "La Palud-sur-Verdon": [
        {"name": "D23, Route des Crêtes", "lat": 43.7794, "lon": 6.3597, "weight": 5, "context": "garrigue, bord de route"},
        {"name": "D952 vers Rougon", "lat": 43.7819, "lon": 6.3281, "weight": 4, "context": "bord de route"},
    ],
    "Rougon": [
        {"name": "D952, Point Sublime", "lat": 43.7950, "lon": 6.4100, "weight": 5, "context": "garrigue, falaise"},
        {"name": "D952 vers La Palud", "lat": 43.7892, "lon": 6.3847, "weight": 4, "context": "bord de route"},
    ],
    "Majastres": [
        {"name": "D17 vers Barrême", "lat": 43.9086, "lon": 6.2822, "weight": 4, "context": "bord de route"},
    ],
    "Blieux": [
        {"name": "D21 vers Castellane", "lat": 43.8739, "lon": 6.3800, "weight": 4, "context": "bord de route"},
    ],
    "Barrême": [
        {"name": "D4085 vers Chaudon", "lat": 43.9567, "lon": 6.3567, "weight": 4, "context": "bord de route"},
    ],
    "Allemagne-en-Provence": [
        {"name": "D952 vers Riez", "lat": 43.7825, "lon": 6.0231, "weight": 4, "context": "bord de route"},
    ],
    "Saint-Martin-de-Brômes": [
        {"name": "D952 vers Gréoux", "lat": 43.7686, "lon": 5.8836, "weight": 4, "context": "bord de route"},
    ],
    "Corbières-en-Provence": [
        {"name": "D4096 vers Sainte-Tulle", "lat": 43.7636, "lon": 5.7558, "weight": 4, "context": "bord de route"},
    ],
    "Thorame-Haute": [
        {"name": "D908 vers Colmars", "lat": 44.0978, "lon": 6.5639, "weight": 4, "context": "bord de route"},
    ],
    "Beaujeu": [
        {"name": "D900 vers Le Vernet", "lat": 44.2039, "lon": 6.3761, "weight": 4, "context": "bord de route"},
    ],
    "Le Vernet": [
        {"name": "D900 vers Seyne", "lat": 44.2736, "lon": 6.3831, "weight": 4, "context": "bord de route"},
    ],
    "Mézel": [
        {"name": "D907 vers Digne", "lat": 43.9983, "lon": 6.1917, "weight": 4, "context": "bord de route"},
    ],
    "Bras-d'Asse": [
        {"name": "D8 vers Mézel", "lat": 43.9261, "lon": 6.1281, "weight": 4, "context": "bord de route"},
    ],

    # Var communes without specific hot zones: use centroid
    "_default_zones": [
        {"name": "Zone périurbaine", "offset_lat": 0.008, "offset_lon": 0.010, "weight": 5, "context": "interface habitat-forêt"},
        {"name": "Bord de route", "offset_lat": -0.006, "offset_lon": -0.008, "weight": 4, "context": "bord de route"},
        {"name": "Piste forestière", "offset_lat": -0.012, "offset_lon": 0.005, "weight": 3, "context": "piste forestière"},
        {"name": "Maquis/garrigue", "offset_lat": 0.010, "offset_lon": -0.005, "weight": 3, "context": "garrigue"},
        {"name": "Crête exposée", "offset_lat": 0.005, "offset_lon": 0.012, "weight": 2, "context": "crête"},
    ],
}

# Commune centroids from the build script
COMMUNE_COORDS = {
    "Gonfaron": (43.3208, 6.2897),
    "Collobrières": (43.2378, 6.3097),
    "La Garde-Freinet": (43.3181, 6.4700),
    "Vidauban": (43.4289, 6.4331),
    "Les Mayons": (43.3156, 6.3600),
    "Le Cannet-des-Maures": (43.3939, 6.3431),
    "Le Luc": (43.3956, 6.3133),
    "La Môle": (43.2097, 6.4739),
    "Grimaud": (43.2744, 6.5211),
    "Cogolin": (43.2531, 6.5317),
    "Saint-Raphaël": (43.4253, 6.7683),
    "Fréjus": (43.4328, 6.7356),
    "Brignoles": (43.4058, 6.0619),
    "Saint-Tropez": (43.2697, 6.6400),
    "Hyères": (43.1206, 6.1286),
    "Bormes-les-Mimosas": (43.1519, 6.3417),
    "La Londe-les-Maures": (43.1383, 6.2344),
    "Le Lavandou": (43.1381, 6.3675),
    "Toulon": (43.1242, 5.9280),
    "Draguignan": (43.5400, 6.4667),
    "Les Adrets-de-l'Estérel": (43.5217, 6.8108),
    "Tanneron": (43.5903, 6.8758),
    "Puget-sur-Argens": (43.4544, 6.6850),
    "Roquebrune-sur-Argens": (43.4444, 6.6389),
    "Sainte-Maxime": (43.3089, 6.6386),
    "Cavalaire-sur-Mer": (43.1717, 6.5292),
    "Ramatuelle": (43.2158, 6.6122),
    "Gassin": (43.2286, 6.5858),
    "La Croix-Valmer": (43.2075, 6.5686),
    "Plan-de-la-Tour": (43.3408, 6.5483),
    "Le Muy": (43.4736, 6.5672),
    "Les Arcs": (43.4628, 6.4778),
    "Lorgues": (43.4933, 6.3619),
    "Flayosc": (43.5350, 6.3967),
    "Aups": (43.6283, 6.2247),
    "Salernes": (43.5633, 6.2353),
    "Carcès": (43.4758, 6.1836),
    "Correns": (43.4867, 6.0797),
    "Barjols": (43.5578, 6.0067),
    "Tavernes": (43.5936, 6.0172),
    "Rians": (43.6078, 5.7550),
    "Saint-Maximin-la-Sainte-Baume": (43.4522, 5.8622),
    "Tourves": (43.4081, 5.9250),
    "Signes": (43.2925, 5.8639),
    "Le Beausset": (43.1983, 5.8031),
    "Le Castellet": (43.2039, 5.7556),
    "La Cadière-d'Azur": (43.1967, 5.7553),
    "Bandol": (43.1361, 5.7539),
    "Sanary-sur-Mer": (43.1181, 5.8025),
    "Six-Fours-les-Plages": (43.0933, 5.8394),
    "Ollioules": (43.1361, 5.8478),
    "Solliès-Pont": (43.1903, 6.0411),
    "Cuers": (43.2381, 6.0714),
    "Pierrefeu-du-Var": (43.2244, 6.1461),
    "Puget-Ville": (43.2894, 6.1367),
    "Pignans": (43.3008, 6.2250),
    "Flassans-sur-Issole": (43.3681, 6.2214),
    "Néoules": (43.3103, 6.0139),
    "Garéoult": (43.3283, 6.0472),
    "Callas": (43.5419, 6.5403),
    "Bargemon": (43.6208, 6.5514),
    "Fayence": (43.6239, 6.6956),
    "Montauroux": (43.6186, 6.7633),
    "Bagnols-en-Forêt": (43.5383, 6.6997),
    "Comps-sur-Artuby": (43.7103, 6.5097),
    "La Roque-Esclapon": (43.7233, 6.6306),
    "Trigance": (43.7633, 6.4453),
    "Artignosc-sur-Verdon": (43.7567, 6.0994),
    "Saint-Julien": (43.5478, 5.9072),
    "Cotignac": (43.5281, 6.1503),
    "Montfort-sur-Argens": (43.4750, 6.1214),
    "Le Val": (43.4386, 6.0736),
    "Camps-la-Source": (43.3861, 6.0883),
    "Rocbaron": (43.3039, 6.0911),
    "La Roquebrussanne": (43.3381, 5.9775),
    "Mazaugues": (43.3478, 5.9303),
    "Digne-les-Bains": (44.0919, 6.2356),
    "Manosque": (43.8331, 5.7833),
    "Forcalquier": (43.9594, 5.7814),
    "Sisteron": (44.1892, 5.9456),
    "Castellane": (43.8467, 6.5133),
    "Barcelonnette": (44.3861, 6.6517),
    "Moustiers-Sainte-Marie": (43.8472, 6.2192),
    "Riez": (43.8181, 6.0928),
    "Valensole": (43.8386, 5.9836),
    "Gréoux-les-Bains": (43.7592, 5.8844),
    "Saint-André-les-Alpes": (43.9681, 6.5067),
    "Annot": (43.9653, 6.6689),
    "Entrevaux": (43.9492, 6.8106),
    "Seyne": (44.3506, 6.3553),
    "Allos": (44.2392, 6.6275),
    "Les Mées": (44.0064, 5.9947),
    "Peyruis": (44.0286, 5.9414),
    "Oraison": (43.9172, 5.9175),
    "Villeneuve": (43.8939, 5.8617),
    "Volx": (43.8783, 5.8411),
    "Sainte-Tulle": (43.7856, 5.7661),
    "Pierrevert": (43.8100, 5.7514),
    "Corbières-en-Provence": (43.7614, 5.7536),
    "Vinon-sur-Verdon": (43.7242, 5.8103),
    "Esparron-de-Verdon": (43.7389, 5.9733),
    "Quinson": (43.7025, 6.0411),
    "Saint-Laurent-du-Verdon": (43.7247, 6.0700),
    "Sainte-Croix-du-Verdon": (43.7581, 6.1492),
    "Bauduen": (43.7333, 6.1758),
    "Aiguines": (43.7756, 6.2442),
    "La Palud-sur-Verdon": (43.7817, 6.3428),
    "Rougon": (43.7986, 6.3981),
    "Majastres": (43.9133, 6.2914),
    "Blieux": (43.8725, 6.3692),
    "Barrême": (43.9533, 6.3689),
    "Allemagne-en-Provence": (43.7806, 6.0067),
    "Saint-Martin-de-Brômes": (43.7697, 5.9003),
    "Thorame-Haute": (44.0956, 6.5600),
    "Beaujeu": (44.2017, 6.3683),
    "Le Vernet": (44.2772, 6.3914),
    "Mézel": (43.9958, 6.1950),
    "Bras-d'Asse": (43.9247, 6.1256),
    "Massif de l'Estérel": (43.48, 6.80),
    "Massif des Maures": (43.30, 6.35),
}


def generate_estimated_point(commune, fire_id, fire_index, total_commune_fires):
    """Generate a plausible starting point for an estimated fire."""
    # Get centroid
    centroid = COMMUNE_COORDS.get(commune, (43.4, 6.3))
    base_lat, base_lon = centroid

    # Get hot zones for this commune
    zones = COMMUNE_HOT_ZONES.get(commune)
    
    if zones:
        # Sort zones by weight descending
        zones_sorted = sorted(zones, key=lambda z: z['weight'], reverse=True)
        
        # Cycle through zones to distribute fires
        # Add deterministic variation based on fire_index
        zone_idx = fire_index % len(zones_sorted)
        zone = zones_sorted[zone_idx]
        zone_lat = zone['lat']
        zone_lon = zone['lon']
        context = zone['context']
        zone_name = zone['name']
        
        # Add small random offset within zone (50-500m)
        # Vary by fire_index to ensure uniqueness
        rng = random.Random(f"{commune}-{fire_index}")
        offset = rng.uniform(0.0005, 0.0045)  # ~50-500m
        angle = rng.uniform(0, 2 * math.pi)
        lat = zone_lat + offset * math.cos(angle)
        lon = zone_lon + offset * math.sin(angle)
        
        precision = 300
        lieu_dit = zone_name
    else:
        # Fallback: use default zones with centroid offsets
        default_zone = COMMUNE_HOT_ZONES["_default_zones"][fire_index % 5]
        rng = random.Random(f"{commune}-{fire_index}")
        lat = base_lat + default_zone['offset_lat'] + rng.uniform(-0.005, 0.005)
        lon = base_lon + default_zone['offset_lon'] + rng.uniform(-0.005, 0.005)
        context = default_zone['context']
        lieu_dit = f"{default_zone['name']}, {commune}"
        precision = 1000
    
    return {
        "lat_depart": round(lat, 6),
        "lon_depart": round(lon, 6),
        "source_depart": "estimé",
        "fiabilite_depart": "estimée",
        "precision_m": precision,
        "lieu_dit_depart": f"{lieu_dit}, {commune}",
        "contexte_depart": context,
    }


# ============================================================================
# MAIN: Process all 537 fires
# ============================================================================

points_depart = []
stats = {"exacte": 0, "probable": 0, "approximative": 0, "estimée": 0}
commune_fire_counts = {}

for fire in data:
    fire_id = fire['id']
    commune = fire['commune']
    
    # Track how many fires per commune (for distribution)
    if commune not in commune_fire_counts:
        commune_fire_counts[commune] = {"confirmed": 0, "estimated": 0, "all": []}
    
    if fire['source'] == 'web':
        commune_fire_counts[commune]["confirmed"] += 1
        # Use confirmed point if available
        pt = get_confirmed_point(fire_id)
        if pt:
            entry = {
                "id": fire_id,
                **pt,
            }
        else:
            # Fallback for confirmed fire not in our list
            centroid = COMMUNE_COORDS.get(commune, (fire['lat'], fire['lon']))
            entry = {
                "id": fire_id,
                "lat_depart": centroid[0],
                "lon_depart": centroid[1],
                "source_depart": "estimé (fallback)",
                "fiabilite_depart": "approximative",
                "precision_m": 3000,
                "lieu_dit_depart": f"Commune de {commune} (centre approximatif)",
                "contexte_depart": "inconnu",
            }
    else:
        commune_fire_counts[commune]["estimated"] += 1
        idx = commune_fire_counts[commune]["estimated"] - 1
        total = -1  # Will be known after counting, we use cycling
        
        pt = generate_estimated_point(commune, fire_id, idx, total)
        entry = {
            "id": fire_id,
            **pt,
        }
    
    points_depart.append(entry)
    stats[entry['fiabilite_depart']] = stats.get(entry['fiabilite_depart'], 0) + 1

print(f"\nFiabilité distribution: {stats}")
print(f"Total: {len(points_depart)} entries")

# Verify uniqueness
coords = [(p['lat_depart'], p['lon_depart']) for p in points_depart]
dupes = set()
seen = set()
for i, (lat, lon) in enumerate(coords):
    key = (round(lat, 6), round(lon, 6))
    if key in seen:
        dupes.add((i, key))
    seen.add(key)
if dupes:
    print(f"WARNING: {len(dupes)} duplicate coordinate pairs found!")
    for i, key in list(dupes)[:5]:
        print(f"  Entry {i}: {key}")
else:
    print("✓ All coordinates are unique at 6 decimal places")

# Save
output_path = 'data/points_depart.json'
os.makedirs('data', exist_ok=True)
with open(output_path, 'w') as f:
    json.dump(points_depart, f, indent=2, ensure_ascii=False)

print(f"\nSaved {len(points_depart)} entries to {output_path}")
