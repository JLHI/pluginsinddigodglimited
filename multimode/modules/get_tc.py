import requests
import pytz
from dateutil.parser import isoparse
from ..utils.utils import parse_time, extract_correspondence

def tptchere(s_olng, s_olat, s_dlng, s_dlat, formatted_datetime, type_heure, tps_marche_max, Herekey):
    try:
        # Construire et envoyer la requête
        url = f"https://transit.router.hereapi.com/v8/routes?origin={s_olat},{s_olng}&destination={s_dlat},{s_dlng}&pedestrian[maxDistance]={tps_marche_max}{type_heure}{formatted_datetime}&apiKey={Herekey}"
        response = requests.get(url)
        data = response.json()
        print(data)
        # Vérifier les routes disponibles
        routes = data.get("routes", [])
        if not routes:
            return "Aucun itinéraire disponible.", *[None] * 5

        # Initialiser les variables
        tz = pytz.timezone('Europe/Paris')
        sections = routes[0].get("sections", [])
        start_time = parse_time(sections[0]["departure"]["time"], tz, None)
        end_time = parse_time(sections[-1].get("arrival", {}).get("time"), tz, None)

        # Calculer la durée et les différences de temps
        total_duration = (isoparse(end_time) - isoparse(start_time)).total_seconds() / 60 if end_time else 0
        reference_time = isoparse(formatted_datetime).astimezone(tz)
        time_difference = ((isoparse(start_time) - reference_time) if type_heure == "&departureTime=" else (reference_time - isoparse(end_time))).total_seconds() / 60 if end_time else 0

        # Extraire les correspondances
        correspondences = [extract_correspondence(s, tz) for s in sections if s["type"] == "transit"]

        # Résultat final
        return total_duration, str(start_time), str(end_time) , len(correspondences), time_difference, correspondences

    except Exception as e:
        print(e)
        return str(e), *[None] * 5