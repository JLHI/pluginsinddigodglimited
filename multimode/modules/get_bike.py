import requests,json 
def tpgvelogoogle(self, s_id, s_olng, s_olat, s_dlng, s_dlat, keytpvelo):
        """Fonction de recherche des temps marche
        theorique avec l'API Google Map
        A MODIFIER POUR LE PROCESSING"""

        self.keytpvelo = keytpvelo
        self.s_id = s_id
        self.s_olat = s_olat
        self.s_olng = s_olng
        self.s_dlat = s_dlat
        self.s_dlng = s_dlng
        self.s_destination = str(self.s_dlat + "," + self.s_dlng)
        self.s_origine = str(self.s_olat + "," + self.s_olng)
        self.s_ndestination = str(self.s_dlat + ";" + self.s_dlng)
        self.s_norigine = str(self.s_olat + ";" + self.s_olng)
        self.url = "https://maps.googleapis.com/maps/api/distancematrix/json?origins="
        self.urlb = "&destinations="
        self.urlc = "&mode=bicycling&language=fr&sensor=false"
        self.urlk = "&key="
        self.urlq = self.url + self.s_origine + self.urlb + self.s_destination + self.urlk + self.keytpvelo + self.urlc
        self.resp = requests.get(self.urlq)
        self.dic = json.loads(self.resp.text)
        self.maps_output = self.resp.json()
        self.maps_output_str = json.dumps(self.maps_output, sort_keys=True, indent=2)
        self.results_list = self.maps_output["rows"]
        self.Element = self.results_list[0]["elements"]
        self.statu = self.Element[0]["status"]

        try:
            print(self.maps_output)
            self.statu == "OK"
            self.distance = self.Element[0]["distance"]["value"]
            self.distkm = "{:.2f}".format(self.distance / 1000)
            self.duree = self.Element[0]["duration"]["value"]
            self.duree = round(self.duree / 60, 2)
            self.dureevae = round(self.duree / 1.4, 2)
            self.mdureemin = "{:.2f}".format(self.duree)
            self.mdureeminvae = "{:.2f}".format(self.dureevae)
            return self.duree, self.dureevae

        except:
            vide = 99999
            videvae = 9999
            return vide,9999

def tpgvelohere(s_olng, s_olat, s_dlng, s_dlat, keyvelohere,feedback):
    try:
        url = f'https://router.hereapi.com/v8/routes?transportMode=bicycle&origin={s_olat},{s_olng}&destination={s_dlat},{s_dlng}&return=summary&apiKey={keyvelohere}'
        # Envoyer une requête GET
        response = requests.get(url)
        # Convertir la réponse en JSON
        data = response.json()
        # Extraire les durées
        HereBikeTime = 0
        routes = data.get("routes", [])
        if not routes:
            feedback.pushWarning("Pas de route disponible")

            return 9999,9999
        for route in data.get("routes", []):
            for section in route.get("sections", []):
                # Accéder à la durée dans le résumé
                duration = section.get("summary", {}).get("duration")
                if duration is not None:
                    HereBikeTime += duration
        #On divise les seconde par 60 pour obtenir les minutes, et on rajoute un rapport 1/4 pour le VAE
        HereBikeTime = round(HereBikeTime / 60, 2)
        HereVAETime = round(HereBikeTime / 1.4, 2)
        # Retourner les durées trouvées
        return HereBikeTime,HereVAETime
    except requests.RequestException as e:
        feedback.pushWarning(f"Erreur temps vélo et vae: {e} ")
        return e,e
    except ValueError as e:
        feedback.pushWarning(f"Erreur temps vélo et vae: {e} ")
        return e,e
    except Exception as e:
        feedback.pushWarning(f"Erreur temps vélo et vae: {e} ")
        return e,e