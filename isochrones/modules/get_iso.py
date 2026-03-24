import requests
import sys
import subprocess
import platform
from PyQt5.Qt import QMessageBox
from qgis.core import QgsGeometry, QgsPointXY
import time
from ...flexpolyline import decode


def iso(lat_origin, lon_origin, mode, selected_range_value, type_heure, type_lieu, formatted_datetime, value, Herekey,
                speed_ped_ms=None, speed_car_cap_ms=None, speed_bike_kmh=None, speed_truck_cap_ms=None, base_bike_kmh=15.0):
    try:
        time.sleep(0.5)
        # Construction de l'URL
        # Gestion de la vitesse, si utilisée pour le vélo
        chosen_speed_kmh = None
        
        if mode == 'bicycle' :
            modes = 'bicycle'
            chosen_speed_kmh = speed_bike_kmh if speed_bike_kmh and speed_bike_kmh > 0 else base_bike_kmh
        else :
            modes = mode # Autres modes

        
        # --- [AJUSTEMENT TEMPS POUR BICYCLE] ---
        # Si l'utilisateur demande des isochrones TEMPS pour bicycle, on applique un coefficient.
        # Exemple : base=15 km/h ; VAE=25 km/h -> coeff = 15/25 = 0.6 => on "réduit" le temps envoyé à HERE.
        scaling_coeff = 1.0
        adjusted_value = value  # string "sec,sec,..."
        if selected_range_value == 'time' and modes == 'bicycle' and chosen_speed_kmh:
            scaling_coeff = float(chosen_speed_kmh) / float(base_bike_kmh)
            adjusted_value = ','.join(str(int(round(float(v) * scaling_coeff))) for v in value.split(','))

        url= (
            f'https://isoline.router.hereapi.com/v8/isolines?transportMode={modes}&optimizeFor=quality&'
            f'{type_heure}{formatted_datetime}&{type_lieu}{lat_origin},{lon_origin}&'
            f'range[type]={selected_range_value}&range[values]={adjusted_value}&apikey={Herekey}'
        )

        # Paramètre natif PIÉTON : pedestrian[speed] (m/s)
        if modes == 'pedestrian' and speed_ped_ms and speed_ped_ms > 0 and selected_range_value == 'time':
            url += (f"&pedestrian[speed]={speed_ped_ms}")

        # Paramètre natif VOITURE : vehicle[speedCap] (m/s) [optionnel]
        if modes == 'car' and speed_car_cap_ms and speed_car_cap_ms > 0:
            url += (f"&vehicle[speedCap]={speed_car_cap_ms}")

        # Paramètre natif CAMION : vehicle[speedCap] (m/s) [optionnel]
        if modes == 'truck' and speed_truck_cap_ms and speed_truck_cap_ms > 0:
            url += (f"&vehicle[speedCap]={speed_truck_cap_ms}")

        print("requête :", url)

        # Envoyer une requête GET
        response = requests.get(url)
        response.raise_for_status()
        # Convertir la réponse en JSON
        data = response.json()
        # print(data)

        polygons = []

        for isoline in data['isolines']:
            value = isoline['range']['value']

            # --- [RESTITUTION DE LA VALEUR UTILISATEUR POUR bicycle en mode TEMPS] ---
            user_value = value
            if selected_range_value == 'time' and modes == 'bicycle' and scaling_coeff != 1.0:
                # On "annule" l'effet du scaling pour afficher la valeur utilisateur dans le champ 'Valeur'
                # user_value = api_value / coeff  (inverse de l'ajustement appliqué à la requête)
                user_value = int(round(float(value) / scaling_coeff))

            for polygon in isoline['polygons']:
                outer = polygon['outer']
                if not outer:
                    continue
                data_decode = decode(outer)
                # print("géométries décodées : ", data_decode)

                # Préparation des données afin de construire la géométrie des isolignes
                data_reversed = [(y, x) for x, y in data_decode]

                polygon_iso = QgsGeometry.fromPolygonXY([[QgsPointXY(x, y) for x, y in data_reversed]])
                
                # print("polygone : ", polygon_iso)

                polygons.append((polygon_iso, user_value))


        if polygons:
            # Retourne un multipolygon si plusieurs géométries
            return polygons
        else:
            raise ValueError("Aucune géométrie trouvée dans la réponse API.")

    except requests.RequestException as e:
        print(e)
        return e
    except ValueError as e:
        print(e)
        return e
    except Exception as e:
        print(e)
        return e