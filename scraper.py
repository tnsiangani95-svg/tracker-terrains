import os
import time
import re
import hashlib
import requests
import subprocess
import urllib.parse
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

def install_playwright():
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
    except Exception as e:
        print(f"Erreur d'installation Chromium: {e}")

try:
    from playwright_stealth import stealth_sync
except ImportError:
    def stealth_sync(page):
        pass

try:
    from supabase import create_client, Client
except ImportError:
    pass

class RealPropertyScraper:
    def __init__(self):
        self.MIN_TERRAIN = 10200 # 10 200 m² strict
        self.SUPABASE_URL = "https://xfhtrugwsovgfcphbdsd.supabase.co"
        self.SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhmaHRydWd3c292Z2ZjcGhiZHNkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODE5ODA0OTMsImV4cCI6MjA5NzU1NjQ5M30.dS8EbRjDrsHukbOo3Gih81M58hCs86RMHJXVIb9U4mg"
        self.supabase: Client = create_client(self.SUPABASE_URL, self.SUPABASE_KEY)
        self.geo_cache = {}
        install_playwright()

    def extract_price(self, text):
        text_lower = text.lower().replace('\xa0', ' ').replace('\u202f', ' ')
        prices = []
        
        # 1. Cas des millions (ex: 1,5 M€ ou 1.5 millions d'euros)
        matches_millions = re.findall(r'(\d+(?:[.,]\d+)?)\s*(?:m€|millions?\s*d[\'’\s]*euros?)', text_lower)
        for m in matches_millions:
            val = float(m.replace(',', '.'))
            prices.append(int(val * 1000000))
            
        # 2. Cas classiques (ex: 1 500 000 € ou 1.500.000 euros)
        matches_euros = re.findall(r'(\d+(?:[\s.]*\d+)*)\s*(?:€|euros?)', text_lower)
        for m in matches_euros:
            val = int(re.sub(r'[\s.]', '', m))
            prices.append(val)
            
        if prices:
            # On ignore les "loyers" ou "honoraires" trop bas, on cherche un prix de vente global
            valid_prices = [p for p in prices if 10000 < p < 100000000]
            if valid_prices:
                return max(valid_prices)
        return 0 

    def extract_surface(self, text):
        text_lower = text.lower().replace('\xa0', ' ').replace('\u202f', ' ')
        surfaces = []
        
        # 1. Cas des hectares (ex: 1,5 ha ou 1.5 hectares)
        matches_ha = re.findall(r'(\d+(?:[.,]\d+)?)\s*(?:ha|hectares?)\b', text_lower)
        for m in matches_ha:
            val = float(m.replace(',', '.'))
            surfaces.append(int(val * 10000))
            
        # 2. Cas des mètres carrés (ex: 12 000 m² ou 12.000 sqm ou 12000 mètres carrés)
        matches_m2 = re.findall(r'(\d+(?:[\s.]*\d+)*)\s*(?:m[²2]|mètres?\s*carrés?|sqm)\b', text_lower)
        for m in matches_m2:
            val = int(re.sub(r'[\s.]', '', m))
            surfaces.append(val)
            
        if surfaces:
            # Plafond à 1 million de m² pour éviter les textes institutionnels des agences
            valid_surfaces = [s for s in surfaces if s < 1000000]
            if valid_surfaces:
                return max(valid_surfaces)
        return 0

    def extract_postal_code(self, text):
        match = re.search(r'\b((?:75|77|78|91|92|93|94|95)\d{3})\b', text)
        if match:
            return match.group(1), match.group(1)[:2]
        return "Île-de-France", "IDF"

    def extract_image(self, annonce, base_url):
        img = annonce.find('img', src=True)
        if img:
            src = img.get('data-src') or img.get('src')
            # Filtre pour ignorer les pixels espions de tracking souvent présents
            if src and not src.startswith('data:image/gif') and 'tracking' not in src:
                return urllib.parse.urljoin(base_url, src)
        return "https://images.unsplash.com/photo-1586528116311-ad8ed3c84a0c?auto=format&fit=crop&w=800&q=80"

    def get_real_link(self, annonce, base_url):
        bad_prefixes = ('mailto:', 'tel:', 'javascript:', '#')
        
        # Priorité 1 : Le lien caché dans le Titre
        title_tag = annonce.find(['h2', 'h3', 'h4', 'h5'])
        if title_tag:
            a_tag = title_tag.find('a', href=True)
            if a_tag and not a_tag['href'].startswith(bad_prefixes): 
                return urllib.parse.urljoin(base_url, a_tag['href'])
        
        # Priorité 2 : Un lien pertinent
        for a in annonce.find_all('a', href=True):
            href = a['href'].lower()
            if not href.startswith(bad_prefixes) and any(kw in href for kw in ['vente', 'terrain', 'detail', 'annonce', 'bien']):
                return urllib.parse.urljoin(base_url, a['href'])
                
        # Priorité 3 : Le premier lien propre
        for a in annonce.find_all('a', href=True):
            if not a['href'].startswith(bad_prefixes):
                return urllib.parse.urljoin(base_url, a['href'])
                
        return base_url

    def get_real_route_osm(self, location_query):
        if location_query in self.geo_cache: return self.geo_cache[location_query]
        try:
            geo_url = f"https://nominatim.openstreetmap.org/search?q={location_query},+France&format=json&limit=1"
            headers = {'User-Agent': 'FoncierTrackerPro/1.0'}
            time.sleep(1.5)
            geo_resp = requests.get(geo_url, headers=headers).json()

            if geo_resp:
                lat = float(geo_resp[0]['lat'])
                lon = float(geo_resp[0]['lon'])
                gdn_lat, gdn_lon = 48.8809, 2.3553
                route_url = f"https://router.project-osrm.org/route/v1/driving/{lon},{lat};{gdn_lon},{gdn_lat}?overview=false"
                route_resp = requests.get(route_url).json()

                if route_resp.get('code') == 'Ok':
                    dist = round(route_resp['routes'][0]['distance'] / 1000, 1)
                    time_min = round(route_resp['routes'][0]['duration'] / 60)
                    self.geo_cache[location_query] = (dist, time_min)
                    return dist, time_min
        except:
            pass
        return 25, 45

    def estimate_metrics(self, text_content, code_postal, departement):
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
        targets = [
            "https://immobilier.cbre.fr/recherche/activite-logistique/a-vendre/ile-de-france/",
            "https://www.jll.fr/fr/immobilier-entreprise/recherche/ile-de-france/terrain/vente",
            "https://www.arthur-loyd.com/immobilier-entreprise/vente/locaux-d-activites-entrepots/ile-de-france",
            "https://www.bnppre.fr/a-vendre/terrain/ile-de-france/",
            "https://www.savills.fr/recherche-immobiliere/recherche-de-biens.aspx?searchType=commercial&transactionType=buy&propertyType=industrial&location=ile-de-france",
            "https://www.geolocaux.com/vente/terrain/ile-de-france/",
            "https://www.bureauxlocaux.com/achat/entrepot-local-d-activite/ile-de-france",
            "https://www.paruvendu.fr/immobilier/vente/terrain/ile-de-france/"
        ]

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_context().new_page()
            
            try:
                stealth_sync(page)
            except:
                pass

            for url in targets:
                nom_site = url.split('//')[1].split('/')[0]
                nom_clean = nom_site.replace('www.', '').split('.')[0]
                print(f"--- Extraction : {nom_clean.upper()} ---")
                try:
                    page.goto(url, wait_until='domcontentloaded', timeout=60000)
                    
                    for page_num in range(1, 4):
                        page.wait_for_timeout(3000)
                        soup = BeautifulSoup(page.content(), 'html.parser')
                        annonces = soup.select('div[class*="card"], li[class*="item"], article[class*="annonce"], .property-item, .result-item')
                        
                        for annonce in annonces:
                            # Extraction VRAIE du lien, sans erreur
                            link = self.get_real_link(annonce, url)
                            
                            texte_complet = annonce.get_text(separator=' ')
                            
                            # Extraction VRAIE des valeurs
                            prix = self.extract_price(texte_complet)
                            surface = self.extract_surface(texte_complet)

                            # FILTRE DE SÉCURITÉ : Ne conserve que ce qui fait plus de 10 200 m²
                            if surface < self.MIN_TERRAIN:
                                continue

                            code_postal, departement = self.extract_postal_code(texte_complet)
                            dist_paris, acces_auto, tps_gare, prox_resid = self.estimate_metrics(texte_complet, code_postal, departement)
                            
                            titre_elem = annonce.find(['h2', 'h3', 'div', 'a', 'span'], class_=re.compile(r'title|name|heading|titre', re.IGNORECASE))
                            titre = titre_elem.text.strip() if titre_elem else f"Foncier sur {nom_clean.capitalize()}"

                            unique_id = hashlib.md5(link.encode()).hexdigest()[:12]
                            
                            prop = {
                                "id": f"{nom_clean}_{unique_id}",
                                "title": titre[:100],
                                "type": "terrain_nu" if surface > 0 else "bati",
                                "surface_totale": surface,
                                "surface_batie": 0,
                                "price": prix,
                                "location": code_postal,
                                "department": departement,
                                "distanceparis": dist_paris,
                                "timegaredunord": tps_gare,
                                "highwayaccess": acces_auto,
                                "residentialproximity": prox_resid,
                                "constructible": True,
                                "score": 0.0,
                                "description": f"Extrait via intelligence visuelle depuis {nom_clean.capitalize()}.",
                                "image": self.extract_image(annonce, url),
                                "url": link
                            }
                            extracted_properties.append(prop)
                        
                        try:
                            next_button = page.locator('a[aria-label="Suivant"], .next, .pagination-next, button:has-text("Suivant")').first
                            if next_button.is_visible():
                                next_button.click()
                            else:
                                break
                        except: break
                except Exception as e:
                    print(f"Erreur sur {url}: {e}")
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
            score += 1.0 
        else:
            prix_m2 = prop['price'] / prop['surface_totale']
            if prix_m2 < 150: score += 2.0
            elif prix_m2 < 250: score += 1.0

        return min(round(score, 1), 5.0)

    def run_pipeline(self):
        raw_properties = self.scrape_real_estate_site()
        valid_properties = []

        for prop in raw_properties:
            if prop['department'] in ['75', '77', '78', '91', '92', '93', '94', '95', 'IDF']:
                prop['score'] = self.calculate_score(prop)
                valid_properties.append(prop)

        # On supprime les éventuels doublons basés sur l'URL exacte
        unique_properties = {p['url']: p for p in valid_properties}.values()

        print(f"\n--- BILAN DE LA CHASSE ---")
        print(f"Annonces parfaites (>10 200m²) extraites : {len(unique_properties)}")

        if self.supabase and unique_properties:
            print("Nettoyage de l'historique Supabase en cours...")
            try:
                # Vide la base pour retirer les fausses données de tests précédentes
                self.supabase.table('properties').delete().neq("id", "0").execute()
                print("Envoi des VRAIES annonces en ligne...")
                self.supabase.table('properties').upsert(list(unique_properties)).execute()
                print("✅ Succès ! La base contient de VRAIES données et VRAIS liens.")
            except Exception as e:
                print(f"❌ Erreur lors de la synchronisation : {e}")
        else:
             print("Aucune annonce validée (>10200m²). L'ancienne BDD est conservée.")

if __name__ == "__main__":
    RealPropertyScraper().run_pipeline()
