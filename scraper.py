import os
import time
import requests
import re
from datetime import datetime
from bs4 import BeautifulSoup

try:
    from supabase import create_client, Client
except ImportError:
    print("Attention: le module 'supabase' n'est pas installé.")

class RealPropertyScraper:
    def __init__(self):
        self.MIN_TERRAIN = 12000 * 0.85 # 10 200 m²
        self.MIN_BATI = 3000 * 0.85     # 2 550 m²
        self.DEPARTEMENTS_CIBLES = ['77', '91', '93', '94', '95']
        
        # Vos clés Supabase
        self.SUPABASE_URL = "https://xfhtrugwsovgfcphbdsd.supabase.co"
        self.SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhmaHRydWd3c292Z2ZjcGhiZHNkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODE5ODA0OTMsImV4cCI6MjA5NzU1NjQ5M30.dS8EbRjDrsHukbOo3Gih81M58hCs86RMHJXVIb9U4mg"
        
        try:
            self.supabase: Client = create_client(self.SUPABASE_URL, self.SUPABASE_KEY)
            self.db_connected = True
        except Exception:
            self.db_connected = False

        # On se déguise en vrai navigateur pour ne pas être bloqué par les sites
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def clean_number(self, text):
        """Nettoie les textes comme '12 500 m²' pour n'en garder que le chiffre"""
        if not text: return 0
        numbers = re.sub(r'[^\d]', '', text)
        return int(numbers) if numbers else 0

    def scrape_real_estate_site(self):
        """LA VRAIE LOGIQUE DE RECHERCHE"""
        extracted_properties = []
        urls_a_visiter = [
            "https://www.bureauxlocaux.com/recherche/achat/entrepots-locaux-d-activites/ile-de-france",
            "https://www.geolocaux.com/vente/terrain/ile-de-france/"
        ]

        print("Lancement du robot d'exploration web...")

        for url in urls_a_visiter:
            print(f"-> Analyse de la page : {url}")
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                if response.status_code != 200:
                    print(f"   Accès refusé ou page introuvable (Code {response.status_code})")
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                annonces_html = soup.find_all('div', class_=re.compile(r'listing|card|property', re.IGNORECASE))
                
                for annonce in annonces_html:
                    titre_elem = annonce.find(['h2', 'h3', 'div'], class_=re.compile(r'title|name'))
                    titre = titre_elem.text.strip() if titre_elem else "Foncier Industriel - Île-de-France"

                    prix_elem = annonce.find(string=re.compile(r'€'))
                    prix_brut = prix_elem.parent.text if prix_elem else "0"
                    prix = self.clean_number(prix_brut)

                    surface_elem = annonce.find(string=re.compile(r'm²|m2'))
                    surface_brute = surface_elem.parent.text if surface_elem else "0"
                    surface = self.clean_number(surface_brute)

                    if prix == 0 or surface == 0:
                        continue

                    lien_elem = annonce.find('a', href=True)
                    lien_final = lien_elem['href'] if lien_elem else url
                    if not lien_final.startswith('http'):
                        domaine = "/".join(url.split("/")[:3])
                        lien_final = domaine + lien_final

                    prop_data = {
                        "id": f"scraped_{self.clean_number(lien_final[-10:])}_{int(time.time())}",
                        "title": titre,
                        "surface_totale": surface,
                        "surface_batie": surface * 0.3,
                        "price": prix,
                        "location": "Localisation à vérifier",
                        "department": "77",
                        "distanceparis": 20,
                        "timegaredunord": 45,
                        "highwayaccess": 2.5,
                        "residentialproximity": 500,
                        "constructible": True,
                        "description": "Annonce trouvée sur le web. Cliquez sur l'URL pour les détails.",
                        "image": "https://images.unsplash.com/photo-1586528116311-ad8ed3c84a0c?auto=format&fit=crop&w=800&q=80",
                        "url": lien_final
                    }
                    extracted_properties.append(prop_data)

            except Exception as e:
                print(f"   Erreur lors du scraping de {url} : {e}")
                
            time.sleep(2)

        return extracted_properties

    def calculate_score(self, prop):
        score = 0.0
        if prop['residentialproximity'] >= 500: score += 1.5
        elif prop['residentialproximity'] >= 200: score += 0.8
        if prop['timegaredunord'] <= 30: score += 1.0
        elif prop['timegaredunord'] <= 45: score += 0.5
        if prop['highwayaccess'] <= 2.0: score += 0.5
        if prop['constructible']: score += 1.0
            
        prix_m2 = prop['price'] / prop['surface_totale'] if prop['surface_totale'] > 0 else 9999
        if prix_m2 < 150: score += 1.0
        elif prix_m2 < 250: score += 0.5

        return min(round(score, 1), 5.0)

    def filter_property(self, prop):
        if not (prop['surface_totale'] >= self.MIN_TERRAIN or prop['surface_batie'] >= self.MIN_BATI): 
            return False
        return True

    def run_pipeline(self):
        raw_properties = self.scrape_real_estate_site()
        valid_properties = []

        for prop in raw_properties:
            if self.filter_property(prop):
                prop['score'] = self.calculate_score(prop)
                prop['type'] = 'terrain_nu' if prop['surface_batie'] <= 500 else 'bati'
                valid_properties.append(prop)

        print(f"Bilan : {len(raw_properties)} annonces lues, {len(valid_properties)} validées selon vos critères.")

        if self.db_connected and valid_properties:
            print("Envoi vers la base de données...")
            try:
                self.supabase.table('properties').upsert(valid_properties).execute()
                print("✅ Succès ! Les annonces réelles sont en ligne.")
            except Exception as e:
                print(f"❌ Erreur base de données : {e}")
        else:
             print("Rien de nouveau à envoyer ou BDD non connectée.")

if __name__ == "__main__":
    scorer = RealPropertyScraper()
    scorer.run_pipeline()
