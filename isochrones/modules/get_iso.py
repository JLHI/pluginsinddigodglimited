import requests
import json
import sys
import subprocess
import platform
from PyQt5.Qt import QMessageBox
from qgis.core import QgsGeometry, QgsPointXY

try:
    import flexpolyline
    print('import completed')
except ModuleNotFoundError:
    print('installing flexpolyline')
    if platform.system() == 'Windows':
        # subprocess.call(['pip3', 'install', 'flexpolyline', '--user'])
        subprocess.check_call([sys.executable, "-m", 'pip', 'install', 'openpyxl'])
    else:
        subprocess.call(['python3', '-m', 'pip', 'install', 'flexpolyline' , "--user"])
    try:
        import flexpolyline
        print('installation completed')
    except ModuleNotFoundError:
        QMessageBox.information(None, 'ERROR', "Oops ! L'installation du module flexpolyline à échouée. Désolé de ne pas pouvoir aller plus loin...")

def iso(lat_origin, lon_origin, mode, selected_range_value, type_heure, type_lieu, formatted_datetime, value, Herekey):
    try:
        # Construction de l'URL
        if mode == 'vae' :
            modes = 'bicycle'
            if selected_range_value == 'time' : 
                value = ','.join(str(int(float(v) * 1.33)) for v in value.split(','))
        else :
            modes = mode

        url= (
            f'https://isoline.router.hereapi.com/v8/isolines?transportMode={modes}&'
            f'{type_heure}{formatted_datetime}&{type_lieu}{lat_origin},{lon_origin}&'
            f'range[type]={selected_range_value}&range[values]={value}&apikey={Herekey}'
        )
        
        print("requête :", url)

        # Envoyer une requête GET
        response = requests.get(url)
        response.raise_for_status()
        # Convertir la réponse en JSON
        data = response.json()
        print(data)

        polygons = []

        for isoline in data['isolines']:
            value = isoline['range']['value']
            if mode == 'vae' and selected_range_value == 'time':
                value = int(float(value) / 1.33)
            for polygon in isoline['polygons']:
                outer = polygon['outer']
                if not outer:
                    continue
                data_decode = flexpolyline.decode(outer)
                print("géométries décodées : ", data_decode)

                # Préparation des données afin de construire la géométrie des isolignes
                data_reversed = [(y, x) for x, y in data_decode]

                polygon_iso = QgsGeometry.fromPolygonXY([[QgsPointXY(x, y) for x, y in data_reversed]])
                
                print("polygone : ", polygon_iso)

                polygons.append((polygon_iso, value))


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