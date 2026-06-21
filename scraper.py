import os
import time
import re
import hashlib
import random
import requests
from datetime import datetime
from bs4 import BeautifulSoup

# Installation forcée du navigateur invisible (Playwright) sur le serveur GitHub
os.system("playwright install chromium")
from playwright.sync_api import sync_playwright

try:
    from supabase import create_client, Client
except ImportError:
    print("Attention: le module 'supabase' n'est pas installé.")

class RealPropertyScraper:
    def __init__(self):
        # --- CAHIER DES CHARGES STRICT ---
        self.MIN_TERRAIN = 12000 * 0.85 # 10 200 m² minimum
        
        # --- CONNEXION SUPABASE ---
        self.SUPABASE_URL = "https://xfhtrugwsovgfcphbdsd.supabase.co"
        self.SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhmaHRydWd3c292Z2ZjcGhiZHNkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODE5ODA0OTMsImV4cCI6MjA5NzU1NjQ5M30.dS8EbRjDrsHukbOo3Gih81M58hCs86RMHJXVIb9U4mg"
        
        try:
            self.supabase: Client = create_client(self.SUPABASE_URL, self.SUPABASE_KEY)
            self.db_connected = True
        except Exception:
            self.db_connected = False

    def extract_price(self, text):
        """Récupère tous les prix. Si aucun prix, renvoie 0 (Nous consulter)"""
        text = text.replace('\xa0', '').replace(' ', '').replace('.', '')
        matches = re.findall(r'(\d+)€', text)
        if matches:
            prices = [int(m) for m in matches]
            return max(prices)
        return 0 

    def extract_surface(self, text):
        """Récupère toutes les surfaces pour identifier le terrain global (la plus grande valeur)"""
        text = text.replace('\xa0', '').replace(' ', '').lower()
        surfaces = []
        
        matches_ha = re.findall(r'(\d+(?:[.,]\d+)?)(?:hectares?|ha)', text)
        for m in matches_ha:
            val = float(m.replace(',', '.'))
            surfaces.append(int(val * 10000))
            
        matches_m2 = re.findall(r'(\d+(?:[.,]\d+)?)m[²2]', text)
        for m in matches_m2:
            val = float(m.replace(',', '.'))
            surfaces.append(int(val))
            
        if surfaces:
            return max(surfaces)
        return 0

    def extract_postal_code(self, text):
        match = re.search(r'\b((?:75|77|78|91|92|93|94|95)\d{3})\b', text)
        if match:
            return match.group(1), match.group(1)[:2]
        return "Île-de-France", "IDF"

    def get_real_route_osm(self, location_query):
        """Calcule l'itinéraire kilométrique réel avec OpenStreetMap (Gratuit)"""
        try:
            geo_url = f"https://nominatim.openstreetmap.org/search?q={location_query},+Ile-de-France,+France&format=json&limit=1"
            headers = {'User-Agent': 'FoncierTracker/1.0'}
            time.sleep(1.5) # Politesse envers le serveur gratuit
            geo_resp = requests.get(geo_url, headers=headers).json()

            if not geo_resp:
                return 25, 45 

            lat = float(geo_resp[0]['lat'])
            lon = float(geo_resp[0]['lon'])

            gdn_lat, gdn_lon = 48.8809, 2.3553
            route_url = f"https://router.project-osrm.org/route/v1/driving/{lon},{lat};{gdn_lon},{gdn_lat}?overview=false"
            route_resp = requests.get(route_url).json()

            if route_resp.get('code') == 'Ok':
                distance_km = route_resp['routes'][0]['distance'] / 1000
                duration_min = route_resp['routes'][0]['duration'] / 60
                return round(distance_km, 1), round(duration_min)
                
        except Exception as e:
            print(f"      [!] Erreur OpenStreetMap: {e}")
        
        return 25, 45

    def estimate_metrics(self, text_content, code_postal, departement):
        """Associe la cartographie API à l'analyse textuelle"""
        text_lower = text_content.lower()
        
        query = code_postal if code_postal != "Île-de-France" else f"Département {departement}"
        distanceparis, timegaredunord = self.get_real_route_osm(query)
        
        highwayaccess = 5.0
        if re.search(r'\b(a1|a3|a4|a5|a6|a86|a104|a15|francilienne|n104|autoroute|échangeur|bretelle)\b', text_lower):
            highwayaccess = 1.0
            
        residentialproximity = 300
        if re.search(r'\b(zi|za|zac|zone industrielle|zone d\'activité|isolé|friche|périphérie)\b', text_lower):
            residentialproximity = 900
        elif re.search(r'\b(centre ville|habitation|mixte|résidentiel|commerces)\b', text_lower):
            residentialproximity = 100
            
        return distanceparis, highwayaccess, timegaredunord, residentialproximity

    def scrape_real_estate_site(self):
        extracted_properties = []
        
        urls_a_visiter = [
            "https://immobilier.cbre.fr/recherche/activite-logistique/a-vendre/ile-de-france/",
            "https://www.jll.fr/fr/immobilier-entreprise/recherche/ile-de-france/terrain/vente",
            "https://www.arthur-loyd.com/immobilier-entreprise/vente/locaux-d-activites-entrepots/ile-de-france",
            "https://www.bnppre.fr/a-vendre/terrain/ile-de-france/",
            "https://www.savills.fr/recherche-immobiliere/recherche-de-biens.aspx?searchType=commercial&transactionType=buy&propertyType=industrial&location=ile-de-france",
            "https://www.cushmanwakefield.com/fr-fr/france/properties/for-sale/industrial/ile-de-france",
            "https://www.geolocaux.com/vente/terrain/ile-de-france/",
            "https://www.bureauxlocaux.com/achat/entrepot-local-d-activite/ile-de-france",
            "https://www.agorastore.fr/ventes-aux-encheres/immobilier/terrain/ile-de-france",
            "https://www.paruvendu.fr/immobilier/vente/terrain/ile-de-france/"
        ]

        print("Lancement du radar (Moteur Visuel Playwright actif pour briser les sécurités)...")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

            for url in urls_a_visiter:
                nom_site = url.split("www.")[-1].split(".")[0] if "www." in url else url.split("//")[-1].split(".")[0]
                print(f"-> Navigation sur : {nom_site.upper()}")
                
                try:
                    # Navigation et attente du chargement Javascript
                    page.goto(url, timeout=60000)
                    page.wait_for_timeout(4000) 
                    
                    html_content = page.content()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    annonces_html = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'listing|card|property|item|annonce|result|box', re.IGNORECASE))
                    
                    for annonce in annonces_html:
                        texte_complet = annonce.get_text(separator=' ')

                        prix = self.extract_price(texte_complet)
                        surface = self.extract_surface(texte_complet)

                        # Si on ne trouve pas de surface, c'est une fausse alerte.
                        if surface == 0:
                            continue

                        titre_elem = annonce.find(['h2', 'h3', 'div', 'a', 'span'], class_=re.compile(r'title|name|heading|titre', re.IGNORECASE))
                        titre = titre_elem.text.strip() if titre_elem else f"Opportunité Foncier {nom_site.capitalize()}"

                        lien_elem = annonce.find('a', href=True)
                        lien_final = lien_elem['href'] if lien_elem else url
                        if not lien_final.startswith('http'):
                            domaine = "/".join(url.split("/")[:3])
                            lien_final = domaine + lien_final

                        code_postal, departement = self.extract_postal_code(texte_complet)
                        dist_paris, acces_auto, tps_gare, prox_resid = self.estimate_metrics(texte_complet, code_postal, departement)
                        
                        unique_id = hashlib.md5((titre + lien_final).encode('utf-8')).hexdigest()[:12]

                        prop_data = {
                            "id": f"{nom_site}_{unique_id}",
                            "title": titre[:100], 
                            "surface_totale": surface,
                            "surface_batie": int(surface * 0.3), 
                            "price": prix, # Peut être égal à 0 (Nous consulter)
                            "location": code_postal,
                            "department": departement, 
                            "distanceparis": dist_paris,
                            "timegaredunord": tps_gare,
                            "highwayaccess": acces_auto,
                            "residentialproximity": prox_resid,
                            "constructible": True,
                            "description": f"Extrait via intelligence visuelle depuis {nom_site.upper()}.",
                            "image": "https://images.unsplash.com/photo-1586528116311-ad8ed3c84a0c?auto=format&fit=crop&w=800&q=80",
                            "url": lien_final
                        }
                        extracted_properties.append(prop_data)

                except Exception as e:
                    print(f"   [!] Timeout ou page inaccessible sur {nom_site} : {e}")

            browser.close()

        return extracted_properties

    def calculate_score(self, prop):
        score = 0.0
        if prop['timegaredunord'] <= 30: score += 1.0
        elif prop['timegaredunord'] <= 45: score += 0.5
        if prop['highwayaccess'] <= 2.0: score += 0.5
        if prop['residentialproximity'] >= 500: score += 1.5
        elif prop['residentialproximity'] >= 200: score += 0.8
            
        if prop['price'] == 0:
            score += 1.0 # Biais neutre pour les offres "Off-Market"
        else:
            prix_m2 = prop['price'] / prop['surface_totale']
            if prix_m2 < 150: score += 2.0
            elif prix_m2 < 250: score += 1.0

        return min(round(score, 1), 5.0)

    def filter_property(self, prop):
        """Dernière barrière de sécurité avant la base de données"""
        if not (prop['surface_totale'] >= self.MIN_TERRAIN): 
            return False
        if prop['price'] > 100000000: # Protection contre les fausses lectures de 100M€
            return False
        if prop['department'] not in ['75', '77', '78', '91', '92', '93', '94', '95', 'IDF']:
            return False
        return True

    def run_pipeline(self):
        raw_properties = self.scrape_real_estate_site()
        valid_properties = []

        for prop in raw_properties:
            if self.filter_property(prop):
                prop['score'] = self.calculate_score(prop)
                prop['type'] = 'terrain_nu' if prop['surface_batie'] <= 1000 else 'bati'
                valid_properties.append(prop)

        # Dédoublonnage exact
        unique_properties = []
        seen_ids = set()
        for p in valid_properties:
            if p['id'] not in seen_ids:
                unique_properties.append(p)
                seen_ids.add(p['id'])

        print(f"\n--- BILAN DE LA CHASSE ---")
        print(f"Annonces trouvées : {len(raw_properties)}")
        print(f"Annonces parfaites (>10 200m²) : {len(unique_properties)}")

        if self.db_connected and unique_properties:
            print("Nettoyage de l'historique Supabase en cours...")
            try:
                # 1. On purge la base existante pour faire place nette
                self.supabase.table('properties').delete().neq("id", "0").execute()
                
                print("Envoi des nouvelles pépites en ligne...")
                # 2. On insère uniquement le marché actuel
                self.supabase.table('properties').upsert(unique_properties).execute()
                
                print("✅ Succès total ! Le tableau de bord Vercel est prêt.")
            except Exception as e:
                print(f"❌ Erreur lors de la synchronisation : {e}")
        else:
             print("Aucune donnée insérée (Marché vide ou erreur de connexion). L'ancienne BDD est conservée par sécurité.")

if __name__ == "__main__":
    scorer = RealPropertyScraper()
    scorer.run_pipeline()
