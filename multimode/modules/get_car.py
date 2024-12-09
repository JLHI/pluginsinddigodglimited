import requests
def tpcarhere(s_olng, s_olat, s_dlng, s_dlat, keyhere):
    try:
        url = f'https://router.hereapi.com/v8/routes?transportMode=car&origin={s_olat},{s_olng}&destination={s_dlat},{s_dlng}&return=summary&apiKey={keyhere}'
        print("voiture : ", url)
        # Envoyer une requête GET
        response = requests.get(url)
        # Convertir la réponse en JSON
        data = response.json()
        # Extraire les durées
        CarTime = 0
        for route in data.get("routes", []):
            for section in route.get("sections", []):
                # Accéder à la durée dans le résumé
                duration = section.get("summary", {}).get("duration")
                if duration is not None:
                    CarTime += duration
        #On divise les seconde par 60 pour obtenir les minutes
        CarTime = round(CarTime / 60, 2)
        # Retourner les durées trouvées
        return CarTime
    except requests.RequestException as e:
        return e
    except ValueError as e:
        return e
    except Exception as e:
        return e