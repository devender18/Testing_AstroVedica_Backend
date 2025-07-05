# astrology_backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import swisseph as swe
import pytz

app = Flask(__name__)
CORS(app)

swe.set_ephe_path("./ephe")  # Ensure Swiss ephemeris files are downloaded here

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

PLANETS = [
    (swe.SUN, "Sun"),
    (swe.MOON, "Moon"),
    (swe.MERCURY, "Mercury"),
    (swe.VENUS, "Venus"),
    (swe.MARS, "Mars"),
    (swe.JUPITER, "Jupiter"),
    (swe.SATURN, "Saturn"),
    (swe.TRUE_NODE, "Rahu"),  # North Node
]

def get_sign_from_longitude(lon):
    return int(lon / 30)

def get_navamsa_sign(longitude):
    """Calculate Navamsa (D9) sign from longitude"""
    sign = get_sign_from_longitude(longitude)
    degree_in_sign = longitude % 30
    navamsa_part = int(degree_in_sign / 3.333333)  # Each navamsa is 3°20'
    
    # Navamsa calculation based on sign type
    if sign % 3 == 0:  # Movable signs (Aries, Cancer, Libra, Capricorn)
        navamsa_sign = (sign + navamsa_part) % 12
    elif sign % 3 == 1:  # Fixed signs (Taurus, Leo, Scorpio, Aquarius)
        navamsa_sign = (sign + 8 + navamsa_part) % 12
    else:  # Dual signs (Gemini, Virgo, Sagittarius, Pisces)
        navamsa_sign = (sign + 4 + navamsa_part) % 12
    
    return navamsa_sign

@app.route("/api/kundli", methods=["POST"])
def generate_kundli():
    data = request.get_json()
    name = data.get("name")
    date_of_birth = data.get("date_of_birth")  # format: YYYY-MM-DD
    time_of_birth = data.get("time_of_birth")  # format: HH:MM
    timezone = data.get("timezone")  # e.g., 'Asia/Kolkata'
    lat = float(data.get("latitude"))
    lon = float(data.get("longitude"))

    # Parse datetime and convert to UTC
    dt_str = f"{date_of_birth} {time_of_birth}"
    tz = pytz.timezone(timezone)
    local_dt = tz.localize(datetime.strptime(dt_str, "%Y-%m-%d %H:%M"))
    utc_dt = local_dt.astimezone(pytz.utc)
    jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, 
                    utc_dt.hour + utc_dt.minute / 60.0)

    # House and Ascendant calculations
    ascmc, _ = swe.houses(jd, lat, lon, b"P")  # Placidus house system
    asc_sign = get_sign_from_longitude(ascmc[0])

    # Initialize charts
    d1_chart = {sign: [] for sign in ZODIAC_SIGNS}
    d9_chart = {sign: [] for sign in ZODIAC_SIGNS}

    # Calculate planetary positions
    for p, pname in PLANETS:
        try:
            lon_tuple, _ = swe.calc_ut(jd, p)
            planet_lon = lon_tuple[0]
            
            # D1 Chart (Rasi/Lagna Chart)
            sign_index = get_sign_from_longitude(planet_lon)
            sign_name = ZODIAC_SIGNS[sign_index]
            d1_chart[sign_name].append(pname)
            
            # D9 Chart (Navamsa Chart)
            navamsa_sign_index = get_navamsa_sign(planet_lon)
            navamsa_sign_name = ZODIAC_SIGNS[navamsa_sign_index]
            d9_chart[navamsa_sign_name].append(pname)
            
        except Exception as e:
            print(f"Error calculating {pname}: {e}")

    # Calculate Ketu (South Node) - opposite to Rahu
    try:
        rahu_lon_tuple, _ = swe.calc_ut(jd, swe.TRUE_NODE)
        rahu_lon = rahu_lon_tuple[0]
        ketu_lon = (rahu_lon + 180) % 360
        
        # Ketu in D1
        ketu_sign_index = get_sign_from_longitude(ketu_lon)
        ketu_sign_name = ZODIAC_SIGNS[ketu_sign_index]
        d1_chart[ketu_sign_name].append("Ketu")
        
        # Ketu in D9
        ketu_navamsa_sign_index = get_navamsa_sign(ketu_lon)
        ketu_navamsa_sign_name = ZODIAC_SIGNS[ketu_navamsa_sign_index]
        d9_chart[ketu_navamsa_sign_name].append("Ketu")
        
    except Exception as e:
        print(f"Error calculating Ketu: {e}")

    response = {
        "name": name,
        "ascendant": ZODIAC_SIGNS[asc_sign],
        "d1_chart": d1_chart,
        "d9_chart": d9_chart,
        "birth_info": {
            "date": date_of_birth,
            "time": time_of_birth,
            "timezone": timezone,
            "latitude": lat,
            "longitude": lon
        }
    }

    return jsonify(response)

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "message": "Astrology API is running"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5050, debug=True)