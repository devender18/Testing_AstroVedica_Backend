import swisseph as swe
import datetime

def calculate_kundli(name, dob, tob, lat, lon):
    lat = float(lat)
    lon = float(lon)
    # Combine date and time
    dt_str = f"{dob} {tob}"
    dt = datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0)

    swe.set_topo(lon, lat, 0)  # longitude, latitude, altitude

    planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    planet_data = {}

    for i, planet in enumerate(planets):
        lon, ret = swe.calc_ut(jd, i)
        planet_data[planet] = round(lon[0], 2)

    return {
        "name": name,
        "dob": dob,
        "tob": tob,
        "lat": lat,
        "lon": lon,
        "planets": planet_data
    }
