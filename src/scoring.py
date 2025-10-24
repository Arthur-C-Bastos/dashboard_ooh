import pandas as pd

def compute_score(df, weights=None):
    """Calcula score 0-100 a partir de colunas: pop_500m, avg_bus_count, pib_percapita."""
    if weights is None:
        weights = {'pop': 0.5, 'bus': 0.3, 'pib': 0.2}
    pop = df.get('pop_500m', pd.Series(0)).fillna(0)
    bus = df.get('avg_bus_count', pd.Series(0)).fillna(0)
    pib = df.get('pib_percapita', pd.Series(0)).fillna(0)
    raw = weights['pop'] * pop + weights['bus'] * bus + weights['pib'] * pib
    minv, maxv = raw.min(), raw.max()
    if maxv - minv == 0:
        df['score'] = 50
    else:
        df['score'] = ((raw - minv) / (maxv - minv)) * 100
    return df
