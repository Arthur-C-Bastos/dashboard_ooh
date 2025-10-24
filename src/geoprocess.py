# src/geoprocess.py - operações espaciais com GeoPandas
import geopandas as gpd
from shapely.geometry import Point

def pois_to_gdf(df_pois, crs='EPSG:4326'):
    """Converte DataFrame com colunas lat/lon para GeoDataFrame."""
    gdf = gpd.GeoDataFrame(df_pois.copy(), geometry=[Point(xy) for xy in zip(df_pois.lon, df_pois.lat)], crs=crs)
    return gdf

def create_buffers(gdf_points, radius_m=500):
    """Cria buffers em metros ao redor dos pontos (reprojeta para EPSG:3857)."""
    gdf_m = gdf_points.to_crs(epsg=3857)
    gdf_m['geometry'] = gdf_m.geometry.buffer(radius_m)
    return gdf_m.to_crs(epsg=4326)

def spatial_join_population(gdf_buffers, gdf_setores, agg_col='pop'):
    """Faz join espacial entre buffers e setores censitários e soma a população por ponto."""
    joined = gpd.sjoin(gdf_buffers, gdf_setores, how='left', predicate='intersects')
    agg = joined.groupby(joined.index).agg({agg_col: 'sum'})
    res = gdf_buffers.join(agg); res[agg_col] = res[agg_col].fillna(0); return res
