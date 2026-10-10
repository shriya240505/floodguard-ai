import numpy as np


def haversine_distance(lat1, lon1, lat2, lon2):
    # Sab kuch radians me convert karo (formula ki requirement hai)
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    
    earth_radius_km = 6371
    return earth_radius_km * c