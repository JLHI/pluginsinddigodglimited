import requests
def tpVoitTC(s_olng, s_olat, s_dlng, s_dlat,type_heure,formatted_datetime, keyhere):
    try:
        url =   f'https://intermodal.router.hereapi.com/v8/routes?destination={s_dlat},{s_dlng}&origin={s_olat},{s_olng}&departureTime={formatted_datetime}&taxi[enable]=&rented[enable]&via=place:parkingLot;strategy=diverseChoices&vehicle[enable]=routeHead&vehicle[modes]=car&transit[enable]=routeTail&return=travelSummary&apiKey={keyhere}'
        # Envoyer une requête GET
        response = requests.get(url)
        # Convertir la réponse en JSON
        data = response.json()
        # Extraire les durées
        voiture_tc_time = 0
        # Parcours des sections de l'itinéraire
        for section in data.get("routes", [])[0].get("sections", []):
            # Ajouter la durée du trajet
            if "travelSummary" in section and "duration" in section["travelSummary"]:
                voiture_tc_time += section["travelSummary"]["duration"]

            # Ajouter le temps de stationnement s'il existe
            if "postActions" in section:
                for action in section["postActions"]:
                    if action.get("action") == "park":
                        voiture_tc_time += action.get("duration", 0)

        voiture_tc_time = round(voiture_tc_time / 60, 2)
        print(f"Temps en voiture + tc : {voiture_tc_time} minutes")

        # Retourner les durées trouvées
        return voiture_tc_time
    except Exception as e:
        return e
def tpVeloTC(s_olng, s_olat, s_dlng, s_dlat,type_heure,formatted_datetime, keyhere):
    try:
        url =   f'https://intermodal.router.hereapi.com/v8/routes?destination={s_dlat},{s_dlng}&origin={s_olat},{s_olng}&departureTime={formatted_datetime}&taxi[enable]=&rented[enable]&vehicle[enable]=routeHead&vehicle[modes]=bicycle&transit[enable]=routeTail&return=travelSummary&apiKey={keyhere}'
        # Envoyer une requête GET
        response = requests.get(url)
        # Convertir la réponse en JSON
        data = response.json()
        # Extraire les durées
        velo_tc_time = 0
        # Parcours des sections de l'itinéraire
        for section in data.get("routes", [])[0].get("sections", []):
            # Ajouter la durée du trajet
            if "travelSummary" in section and "duration" in section["travelSummary"]:
                velo_tc_time += section["travelSummary"]["duration"]

            # Ajouter le temps de stationnement s'il existe
            if "postActions" in section:
                for action in section["postActions"]:
                    if action.get("action") == "park":
                        velo_tc_time += action.get("duration", 0)

        velo_tc_time = round(velo_tc_time / 60, 2)
        print(f"Temps en vélo + tc : {velo_tc_time} minutes")

        # Retourner les durées trouvées
        return velo_tc_time
    except Exception as e:
        print(e)
        return e

