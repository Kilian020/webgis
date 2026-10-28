from pathlib import Path
import math
from shapely.affinity import scale
import geopandas as gpd
import pandas as pd
import requests

# --- Paden ---------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "docs" / "data"
OUTPUT.mkdir(parents=True, exist_ok=True)

# --- Instellingen --------------------------------------------------------
BASE = "https://api.pdok.nl/kadaster/bag/ogc/v2"
COLLECTIE = "pand"
BBOX = "4.894,52.370,4.904,52.377"  # lon/lat: rond de Nieuwmarkt


# --- 1. Data ophalen -----------------------------------------------------
def haal_features(collectie, bbox):
    url = f"{BASE}/collections/{collectie}/items"
    params = {"f": "json", "limit": 1000, "bbox": bbox}
    features = []
    while url:
        r = requests.get(url, params=params, timeout=60)
        r.raise_for_status()
        data = r.json()
        features += data["features"]
        # volgende pagina, als die er is
        url = next((l["href"] for l in data.get("links", [])
                    if l.get("rel") == "next"), None)
        params = None  # de next-link bevat de parameters al
    return features


features = haal_features(COLLECTIE, BBOX)
print(f"{len(features)} panden opgehaald")

gdf = gpd.GeoDataFrame.from_features(features)
print("Beschikbare kolommen:", list(gdf.columns))

# --- 2. Analyse ----------------------------------------------------------
m_per_lon = 111320 * math.cos(math.radians(52.37))
m_per_lat = 110574
gdf["oppervlakte_m2"] = [
    round(scale(g, m_per_lon, m_per_lat, origin=(0, 0)).area)
    for g in gdf.geometry
]

# gesloopte/ingetrokken panden eruit
if "status" in gdf.columns:
    gdf = gdf[~gdf["status"].str.contains("gesloopt|ingetrokken|niet gerealiseerd",
                                          case=False, na=False)]

gdf["bouwjaar"] = pd.to_numeric(gdf["bouwjaar"], errors="coerce")
gdf = gdf[gdf["bouwjaar"].between(1200, 2100)]  # ongeldige jaren eruit


grenzen = [0, 1700, 1850, 1920, 1945, 1975, 2000, 2100]
labels = ["< 1700", "1700-1849", "1850-1919", "1920-1944",
          "1945-1974", "1975-1999", "2000+"]
kleuren = ["#7f2704", "#a63603", "#d94801", "#f16913",
           "#fd8d3c", "#fdae6b", "#fdd0a2"]

gdf["periode"] = pd.cut(gdf["bouwjaar"], grenzen, labels=labels, right=False).astype(str)
gdf["kleur"] = gdf["periode"].map(dict(zip(labels, kleuren)))

samenvatting = gdf.groupby("periode").agg(
    aantal=("bouwjaar", "size"),
    gem_oppervlakte_m2=("oppervlakte_m2", "mean"),
).round(0).reindex(labels)
print(samenvatting)

# --- 3. Export -----------------------------------------------------------
kolommen = [c for c in ["identificatie", "bouwjaar", "periode",
                        "oppervlakte_m2", "kleur"] if c in gdf.columns]
uit = gdf[kolommen + ["geometry"]]
(OUTPUT / "panden.geojson").write_text(uit.to_json(), encoding="utf-8")