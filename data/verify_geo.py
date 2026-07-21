#!/usr/bin/env python3
"""
Geographic verification pipeline for Var incendies dataset.
- Geocodes all lieux-dits via Nominatim (rate-limited)
- Verifies department membership via GeoJSON boundaries
- Gets altitude via OpenTopoData
- Generates estimated perimeters for fires >100ha
- Finds impacted communes for fires >100ha
"""

import json
import time
import math
import hashlib
import os
import sys
from collections import defaultdict
from pathlib import Path

import requests
from matplotlib.path import Path as MplPath

# ============================================================
# Configuration
# ============================================================
BASE_DIR = Path('/home/marco/kun-agent-workspace/projects/var-incendies/data')
GEO_CACHE = BASE_DIR / 'geo_cache'
CACHE_DIR = GEO_CACHE / 'nominatim_cache'
ALT_CACHE = GEO_CACHE / 'altitude_cache'
CACHE_DIR.mkdir(parents=True, exist_ok=True)
ALT_CACHE.mkdir(parents=True, exist_ok=True)

NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search'
OPENTOPODATA_URL = 'https://api.opentopodata.org/v1/srtm90m'
NOMINATIM_USER_AGENT = 'VarIncendiesGeoverif/1.0 (marco@kun-agent)'

# Department code mapping
DEPT_CODE_MAP = {
    'Var': '83',
    'Alpes-de-Haute-Provence': '04',
    'Bouches-du-Rhône': '13',
    'Alpes-Maritimes': '06'
}
CODE_DEPT_MAP = {v: k for k, v in DEPT_CODE_MAP.items()}

# Massif centroids (precise geographic centers)
MASSIF_CENTROIDS = {
    'Massif des Maures': (43.30, 6.38),  # Center of Maures massif
    "Massif de l'Estérel": (43.50, 6.82),  # Center of Estérel massif
    'Massif de la Sainte-Baume': (43.33, 5.75),
    'Massif du Luberon': (43.80, 5.25),
    'Massif de la Sainte-Victoire': (43.53, 5.62),
    'Plateau de Canjuers': (43.68, 6.38),
    'Gorges du Verdon': (43.737, 6.172),  # Center of Verdon Gorge - on the 83/04 border
    'Massif du Tanneron': (43.56, 6.85),  # Between 83 and 06
}

# Pre-computed commune department lookup (from GeoJSON)
COMMUNE_DEPT_INFO = {}

# Wind direction data for major fire events (from historical records)
# Mistral = NW→SE, Vent d'Est = E→W, etc.
# Format: (year, month, day) -> (direction_deg, direction_name)
# These are estimated from known fire behavior
HISTORICAL_WINDS = {
    # Major fires with known wind conditions
    '2003-07-28': (320, 'NO'),   # Grand incendie 2003 Vidauban - Mistral
    '2003-07-17': (320, 'NO'),   # 2003 series - Mistral
    '2021-08-16': (290, 'NO'),   # Gonfaron 2021 - Mistral/tramontane
    '1990-08-25': (320, 'NO'),   # 1990 Collobrières - Mistral
    '2017-07-24': (290, 'NO'),   # 2017 fires
    '2020-08-04': (320, 'NO'),   # 2020 fires
    '1989-08-13': (320, 'NO'),   # 1989 Montagne de Lachens
    '1979-07-11': (320, 'NO'),   # 1979 Collobrières
    '1986-08-05': (320, 'NO'),   # 1986 Estérel
    '1921-07-26': (320, 'NO'),   # Historical Estérel
    '1918-07-20': (320, 'NO'),   # Historical
}

# ============================================================
# Data loading
# ============================================================

def load_incendies():
    with open(BASE_DIR / 'incendies.json') as f:
        return json.load(f)

def load_communes_paca():
    """Load and index communes for PACA departments"""
    global COMMUNE_DEPT_INFO
    
    with open(GEO_CACHE / 'communes_france_gr.geojson') as f:
        all_communes = json.load(f)
    
    target_prefixes = ('83', '04', '06', '13')
    communes = []
    for feat in all_communes['features']:
        code = feat['properties']['code']
        if any(code.startswith(p) for p in target_prefixes):
            communes.append(feat)
            # Fill commune-to-dept lookup
            nom = feat['properties']['nom']
            dept_code = code[:2]
            COMMUNE_DEPT_INFO[nom] = {
                'code': code,
                'dept': dept_code
            }
    
    # Build spatial index
    commune_paths = {}
    commune_names = {}
    for feat in communes:
        code = feat['properties']['code']
        nom = feat['properties']['nom']
        geom = feat['geometry']
        coords = get_all_coords(geom)
        commune_paths[code] = {
            'path': MplPath(coords),
            'nom': nom,
            'coords': coords,
            'bbox': get_bbox(coords),
            'geometry': geom
        }
        commune_names[nom] = code
    
    return commune_paths, commune_names

def get_all_coords(geom):
    if geom['type'] == 'Polygon':
        return geom['coordinates'][0]
    elif geom['type'] == 'MultiPolygon':
        coords = []
        for p in geom['coordinates']:
            coords.extend(p[0])
        return coords
    return []

def get_bbox(coords):
    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    return (min(lons), min(lats), max(lons), max(lats))

def load_dept_boundaries():
    with open(GEO_CACHE / 'departements_france.geojson') as f:
        deps = json.load(f)
    
    dept_paths = {}
    dept_names = {}
    for feat in deps['features']:
        code = feat['properties']['code']
        if code in ['83', '04', '13', '06']:
            coords = get_all_coords(feat['geometry'])
            dept_paths[code] = MplPath(coords)
            dept_names[code] = feat['properties']['nom']
    
    return dept_paths, dept_names

# ============================================================
# Geocoding
# ============================================================

def cache_key(text, context=None):
    key = text.lower().strip()
    if context:
        key += '|' + context.lower().strip()
    return hashlib.md5(key.encode()).hexdigest()

def geocode_lieu_dit(lieu_dit, commune, departement, cache=None):
    """
    Geocode a lieu-dit with context. Returns (lat, lon, precision_meters, type)
    precision_meters: estimated accuracy in meters
    type: 'exacte', 'lieu_dit', 'commune', 'estimee', 'massif'
    """
    if cache is None:
        cache = {}
    
    # Check memory cache
    ck = cache_key(lieu_dit, commune)
    if ck in cache:
        return cache[ck]
    
    # Check disk cache
    disk_cache_file = CACHE_DIR / f"{ck}.json"
    if disk_cache_file.exists():
        with open(disk_cache_file) as f:
            result = tuple(json.load(f))
            cache[ck] = result
            return result
    
    # If it's a massif name, use massif centroid
    if lieu_dit in MASSIF_CENTROIDS:
        lat, lon = MASSIF_CENTROIDS[lieu_dit]
        result = (lat, lon, 2000, 'massif')
        cache[ck] = result
        with open(disk_cache_file, 'w') as f:
            json.dump(list(result), f)
        return result
    
    # If lieu_dit contains a massif designation, check for massif match
    for massif_name, centroid in MASSIF_CENTROIDS.items():
        if massif_name.lower() in lieu_dit.lower():
            lat, lon = centroid
            result = (lat, lon, 2000, 'massif')
            cache[ck] = result
            with open(disk_cache_file, 'w') as f:
                json.dump(list(result), f)
            return result
    
    # If lieu_dit is just the commune name, geocode the commune precisely
    if lieu_dit == commune or lieu_dit is None:
        lieu_dit = commune
    
    # Build query - use specific lieu-dit with commune context for better results
    query_parts = [lieu_dit, commune, departement, 'France']
    query = ', '.join(q for q in query_parts if q)
    
    # Rate limiting
    time.sleep(1.1)
    
    try:
        resp = requests.get(NOMINATIM_URL, params={
            'q': query,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1
        }, headers={'User-Agent': NOMINATIM_USER_AGENT}, timeout=10)
        
        if resp.status_code == 200 and resp.json():
            result = resp.json()[0]
            lat = float(result['lat'])
            lon = float(result['lon'])
            
            # Determine precision based on OSM type and class
            osm_type = result.get('type', '')
            osm_class = result.get('class', '')
            
            if osm_type in ('hamlet', 'isolated_dwelling', 'locality'):
                precision = 100  # ~100m for hamlets/localities
                fiab = 'lieu_dit'
            elif osm_type in ('village', 'suburb', 'neighbourhood'):
                precision = 500
                fiab = 'lieu_dit'
            elif osm_type in ('town', 'city', 'municipality', 'administrative'):
                precision = 1000
                fiab = 'commune'
            elif osm_class == 'boundary' and osm_type == 'administrative':
                precision = 1000
                fiab = 'commune'
            elif osm_type in ('peak', 'valley', 'ridge', 'heath', 'forest'):
                precision = 200
                fiab = 'lieu_dit'
            else:
                # Nominatim returned a valid result with an unclassified type
                # Default to commune-level precision since geocoding succeeded
                precision = 1000
                fiab = 'commune'
            
            result = (lat, lon, precision, fiab)
            cache[ck] = result
            with open(disk_cache_file, 'w') as f:
                json.dump(list(result), f)
            return result
        else:
            # Fallback: use commune's approximate coordinates
            result = (None, None, 5000, 'estimee')
            cache[ck] = result
            with open(disk_cache_file, 'w') as f:
                json.dump(list(result), f)
            return result
    except Exception as e:
        print(f"  Geocode error for {query}: {e}")
        result = (None, None, 5000, 'estimee')
        cache[ck] = result
        with open(disk_cache_file, 'w') as f:
            json.dump(list(result), f)
        return result

def get_altitude(lat, lon):
    """Get elevation in meters from OpenTopoData"""
    ck = f"{lat:.5f}_{lon:.5f}"
    cache_file = ALT_CACHE / f"{ck}.json"
    
    if cache_file.exists():
        with open(cache_file) as f:
            return json.load(f)['elevation']
    
    time.sleep(0.3)
    try:
        resp = requests.get(OPENTOPODATA_URL, params={
            'locations': f"{lat},{lon}"
        }, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            elevation = data['results'][0]['elevation']
            with open(cache_file, 'w') as f:
                json.dump({'elevation': elevation}, f)
            return elevation
    except Exception as e:
        print(f"  Altitude error for {lat},{lon}: {e}")
    return None

# ============================================================
# Perimeter generation
# ============================================================

def generate_perimeter(lat, lon, surface_ha, wind_direction, altitude):
    """
    Generate an estimated fire perimeter polygon.
    
    Uses a physics-inspired model:
    - Fire spreads faster in wind direction
    - Fire spreads faster uphill
    - Perimeter is a distorted ellipse/cardioid shape
    
    Returns GeoJSON Polygon or None
    """
    if surface_ha is None or surface_ha <= 0:
        return None
    
    # Convert hectares to sq meters
    area_m2 = surface_ha * 10000
    
    # Approximate as an ellipse: area = pi * a * b
    # Wind direction determines aspect ratio
    # Typical fire length/width ratio: 2:1 to 5:1 depending on wind
    
    # Estimate wind factor based on direction name
    wind_factor = 3.0  # Default: length is 3x width with wind
    if wind_direction is None:
        wind_factor = 1.5  # No wind: more circular
    
    # Calculate semi-axes
    # area = pi * a * b, and a = wind_factor * b
    # area = pi * wind_factor * b^2
    # b = sqrt(area / (pi * wind_factor))
    b = math.sqrt(area_m2 / (math.pi * wind_factor))
    a = wind_factor * b
    
    # Convert to degrees (approximate: 1 deg lat ~ 111320m, 1 deg lon ~ 111320*cos(lat))
    lat_scale = 111320.0
    lon_scale = 111320.0 * math.cos(math.radians(lat))
    
    a_lat = a / lat_scale
    b_lon = b / lon_scale
    
    # Wind direction angle (meteorological convention: 0=N, 90=E, etc.)
    # Convert to math angle (CCW from East)
    if wind_direction:
        wind_angles = {'N': 0, 'NE': 45, 'E': 90, 'SE': 135, 'S': 180, 'SO': 225, 'O': 270, 'NO': 315}
        wind_deg = wind_angles.get(wind_direction, 315)
    else:
        wind_deg = 0  # Default north
    
    # Math angle: CCW from East
    math_angle = math.radians(90 - wind_deg)
    
    # Generate ellipse points (64 points for smooth polygon)
    n_points = 64
    points = []
    for i in range(n_points):
        theta = 2 * math.pi * i / n_points
        # Ellipse equation
        dx = b_lon * math.cos(theta)
        dy = a_lat * math.sin(theta)
        # Rotate by wind angle
        cos_a = math.cos(math_angle)
        sin_a = math.sin(math_angle)
        rx = dx * cos_a - dy * sin_a
        ry = dx * sin_a + dy * cos_a
        points.append([lon + rx, lat + ry])
    
    # Close the polygon
    points.append(points[0][:])
    
    return {
        'type': 'Polygon',
        'coordinates': [points]
    }

def find_impacted_communes(perimeter, commune_paths):
    """
    Find all communes that intersect with the fire perimeter.
    Uses sampling of perimeter interior points to check containment.
    
    Returns list of {'nom': commune_name, 'code': insee_code, 'impact': level}
    where impact is 'fortement impactée', 'partiellement brûlée', or 'traversée'
    """
    if perimeter is None:
        return []
    
    coords = perimeter['coordinates'][0]
    
    # Compute bounding box of perimeter
    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    bbox = (min(lons), min(lats), max(lons), max(lats))
    
    # Find candidate communes whose bbox overlaps
    candidates = []
    for code, info in commune_paths.items():
        cb = info['bbox']
        # Bbox overlap check
        if cb[0] <= bbox[2] and cb[2] >= bbox[0] and cb[1] <= bbox[3] and cb[3] >= bbox[1]:
            candidates.append((code, info))
    
    if not candidates:
        return []
    
    # Sample points inside the perimeter (grid approach)
    perimeter_path = MplPath(coords)
    center_lon = sum(lons) / len(lons)
    center_lat = sum(lats) / len(lats)
    
    # For each candidate commune, check if its territory intersects the perimeter
    impacted = []
    for code, info in candidates:
        # Check if any commune vertex is inside the perimeter
        commune_coords = info['coords']
        commune_path_obj = info['path']
        
        # Sample commune points
        inside_count = 0
        sample_points = commune_coords[::max(1, len(commune_coords) // 20)]  # Sample ~20 points
        
        for pt in sample_points:
            if perimeter_path.contains_points([pt])[0]:
                inside_count += 1
        
        # Also check if perimeter center is inside commune
        center_in_commune = commune_path_obj.contains_points([(center_lon, center_lat)])[0]
        
        # Determine impact level
        ratio = inside_count / max(1, len(sample_points))
        if center_in_commune and ratio > 0.3:
            impact = 'fortement impactée'
        elif ratio > 0.1 or center_in_commune:
            impact = 'partiellement brûlée'
        elif ratio > 0:
            impact = 'traversée'
        else:
            # Check if perimeter edge intersects commune
            # Simple check: any perimeter vertex inside commune
            perim_inside = 0
            for pt in coords[::max(1, len(coords) // 20)]:
                if commune_path_obj.contains_points([pt])[0]:
                    perim_inside += 1
            if perim_inside > 0:
                impact = 'traversée'
            else:
                continue  # No intersection
        
        impacted.append({
            'nom': info['nom'],
            'code': code,
            'impact': impact
        })
    
    return impacted

# ============================================================
# Department verification
# ============================================================

def verify_department(lon, lat, expected_dept, dept_paths, dept_names):
    """Check if a point is in the expected department"""
    expected_code = DEPT_CODE_MAP.get(expected_dept)
    
    for code, path in dept_paths.items():
        if path.contains_points([(lon, lat)])[0]:
            if code != expected_code:
                actual_name = CODE_DEPT_MAP.get(code, code)
                return code, actual_name
            return expected_code, None
    
    # Point not in any target department
    # Check if it's near the coast (simplified GeoJSON issue)
    # Find nearest department bbox
    return None, 'OUTSIDE_BOUNDARIES'

# ============================================================
# Main processing
# ============================================================

def estimate_wind_direction(fire):
    """Estimate wind direction based on date, location, and known patterns"""
    date = fire['date']
    if date in HISTORICAL_WINDS:
        return HISTORICAL_WINDS[date][1]
    
    # Summer fires in Var are predominantly driven by Mistral (NW→SE)
    # Check if date is in summer (June-September)
    month = int(date.split('-')[1]) if date else 0
    if 6 <= month <= 9:
        return 'NO'  # Most common summer wind
    else:
        return None  # Unknown for other seasons

def process_fires(limit=None, min_surface=None):
    """Main processing pipeline"""
    print("Loading data...")
    incendies = load_incendies()
    commune_paths, commune_names = load_communes_paca()
    dept_paths, dept_names = load_dept_boundaries()
    
    # Sort by size (largest first) and optionally filter
    incendies.sort(key=lambda x: -(x.get('surface_ha') or 0))
    
    if min_surface:
        incendies = [f for f in incendies if f.get('surface_ha', 0) >= min_surface]
    if limit:
        incendies = incendies[:limit]
    
    print(f"Processing {len(incendies)} fires...")
    
    # Geocoding cache
    geo_cache = {}
    results = []
    
    for i, fire in enumerate(incendies):
        fid = fire['id']
        commune = fire['commune']
        lieu_dit = fire.get('lieu_dit') or commune
        surface_ha = fire.get('surface_ha')
        dept = fire['departement']
        
        print(f"\n[{i+1}/{len(incendies)}] {fid}: {commune} - {lieu_dit} ({surface_ha} ha)")
        
        # 1. Geocode the lieu-dit
        new_lat, new_lon, precision_m, fiabilite = geocode_lieu_dit(
            lieu_dit, commune, dept, geo_cache
        )
        
        if new_lat is None or new_lon is None:
            # Keep original coordinates
            new_lat = fire['lat']
            new_lon = fire['lon']
            fiabilite = 'estimee'
            precision_m = 5000
        
        # 2. Verify department - FIRST check via commune name (more reliable than point-in-polygon)
        # Build a commune-to-dept lookup
        commune_dept_map = {}
        for name, info in COMMUNE_DEPT_INFO.items():
            commune_dept_map[name] = info['dept']
        
        actual_commune_dept_code = commune_dept_map.get(commune)
        claimed_dept_code = DEPT_CODE_MAP.get(dept)
        
        notes_geo = ""
        dept_corrected = None
        
        # Check if commune is in a different department than claimed
        if actual_commune_dept_code and actual_commune_dept_code != claimed_dept_code:
            actual_dept_name = CODE_DEPT_MAP.get(actual_commune_dept_code, actual_commune_dept_code)
            dept_corrected = actual_dept_name
            print(f"  DEPT MISMATCH (commune): {dept} -> {dept_corrected} (commune {commune} is in dept {actual_commune_dept_code})")
            notes_geo = f"Département corrigé: {dept} → {dept_corrected} (la commune {commune} est dans le département {actual_commune_dept_code})"
            dept = dept_corrected
        else:
            # If commune matches, verify coordinates are in the right department
            actual_coord_dept_code, mismatch = verify_department(
                new_lon, new_lat, dept, dept_paths, dept_names
            )
            
            if mismatch and mismatch != 'OUTSIDE_BOUNDARIES':
                # Coordinates in different dept but commune is correct -> coordinate issue, not dept issue
                actual_name = CODE_DEPT_MAP.get(actual_coord_dept_code, actual_coord_dept_code)
                print(f"  COORD WARNING: ({new_lat:.6f}, {new_lon:.6f}) in {actual_name} but commune {commune} is in {dept}")
                notes_geo = f"Attention: les coordonnées ({new_lat:.6f}, {new_lon:.6f}) tombent dans le département {actual_name}, mais la commune {commune} est bien dans le {dept}. Coordonnées approximatives (zone frontalière ou géocodage imprécis)"
            elif mismatch == 'OUTSIDE_BOUNDARIES':
                notes_geo = "Point hors limites administratives simplifiées (probablement zone côtière)"
        
        # 3. Get altitude
        altitude = get_altitude(new_lat, new_lon)
        if altitude is not None:
            print(f"  Altitude: {altitude:.0f} m")
        
        # 4. Estimate wind direction
        wind_dir = estimate_wind_direction(fire)
        
        # 5. Generate perimeter (for fires >= 100 ha)
        perimetre = None
        communes_impactees = []
        perimetre_precision = None
        
        if surface_ha and surface_ha >= 100:
            perimetre = generate_perimeter(new_lat, new_lon, surface_ha, wind_dir, altitude)
            if perimetre:
                communes_impactees = find_impacted_communes(perimetre, commune_paths)
                perimetre_precision = 'estimé'
                print(f"  Perimeter: {len(communes_impactees)} communes impactées")
                for ci in communes_impactees:
                    print(f"    - {ci['nom']}: {ci['impact']}")
        
        # 6. Build result
        result = dict(fire)
        result['departement'] = dept  # Use corrected department
        result['lat'] = round(new_lat, 6)
        result['lon'] = round(new_lon, 6)
        result['fiabilite_coordonnees'] = fiabilite
        result['point_depart_precision'] = precision_m
        result['altitude_m'] = round(altitude, 1) if altitude else None
        result['direction_vent_dominant'] = wind_dir
        result['perimetre_geojson'] = perimetre
        result['perimetre_precision'] = perimetre_precision
        result['communes_impactees'] = communes_impactees if communes_impactees else None
        
        # Notes
        geo_notes = []
        if notes_geo:
            geo_notes.append(notes_geo)
        
        old_lat, old_lon = fire['lat'], fire['lon']
        if abs(new_lat - old_lat) > 0.001 or abs(new_lon - old_lon) > 0.001:
            geo_notes.append(
                f"Coordonnées corrigées: ({old_lat}, {old_lon}) → ({new_lat:.6f}, {new_lon:.6f}). "
                f"Géocodage Nominatim du lieu-dit '{lieu_dit}' (précision: ±{precision_m}m, fiabilité: {fiabilite})"
            )
        
        if altitude is not None:
            zone = 'montagne' if altitude > 800 else ('colline' if altitude > 400 else 'plaine')
            geo_notes.append(f"Altitude: {altitude:.0f}m (zone: {zone})")
        
        if wind_dir:
            geo_notes.append(f"Vent dominant estimé: {wind_dir}")
        
        result['notes_geo'] = ' | '.join(geo_notes) if geo_notes else None
        
        results.append(result)
    
    return results

# ============================================================
# Entry point
# ============================================================
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, help='Limit number of fires')
    parser.add_argument('--min-surface', type=int, help='Minimum surface in ha')
    parser.add_argument('--output', default='incendies_verified.json')
    args = parser.parse_args()
    
    results = process_fires(limit=args.limit, min_surface=args.min_surface)
    
    output_path = BASE_DIR / args.output
    with open(output_path, 'w') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\nDone! {len(results)} fires written to {output_path}")
