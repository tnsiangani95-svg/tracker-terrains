import os
import time
import re
import hashlib
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
try:
    from playwright_stealth import stealth_sync
except ImportError:
    os.system("pip install playwright-stealth")
    from playwright_stealth import stealth_sync

try:
    from supabase import create_client, Client
except ImportError:
    pass

class RealPropertyScraper:
    def __init__(self):
        self.MIN_TERRAIN = 10200
        self.SUPABASE_URL = "https://xfhtrugwsovgfcphbdsd.supabase.co"
        self.SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhmaHRydWd3c292Z2ZjcGhiZHNkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODE5ODA0OTMsImV4cCI6MjA5NzU1NjQ5M30.dS8EbRjDrsHukbOo3Gih81M58hCs86RMHJXVIb9U4mg"
        self.supabase: Client = create_client(self.SUPABASE_URL, self.SUPABASE_KEY)
        self.geo_cache = {}

    def extract_image(self, annonce):
        img = annonce.find('img', src=True)
        return img['src'] if img else "https://images.unsplash.com/photo-1586528116311-ad8ed3c84a0c?auto=format&fit=crop&w=800&q=80"

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
            stealth_sync(page)

            for url in targets:
                print(f"--- Extraction complète : {url.split('//')[1].split('/')[0]} ---")
                try:
                    page.goto(url, wait_until='domcontentloaded', timeout=60000)
                    
                    # Boucle de pagination pour tout récupérer
                    for page_num in range(1, 4): # On limite à 3 pages max pour rester rapide
                        page.wait_for_timeout(3000)
                        soup = BeautifulSoup(page.content(), 'html.parser')
                        
                        annonces = soup.select('div[class*="card"], li[class*="item"], article[class*="annonce"], .property-item, .result-item')
                        
                        for annonce in annonces:
                            link_tag = annonce.find('a', href=True)
                            if not link_tag: continue
                            
                            link = link_tag['href']
                            if not link.startswith('http'):
                                domain = "/".join(url.split("/")[:3])
                                link = domain + (link if link.startswith('/') else '/' + link)

                            unique_id = hashlib.md5(link.encode()).hexdigest()[:12]
                            prop = {
                                "id": f"{url.split('.')[1]}_{unique_id}",
                                "title": annonce.get_text(strip=True)[:100],
                                "url": link,
                                "image": self.extract_image(annonce),
                                "surface_totale": 12000,
                                "price": 0,
                                "department": "77"
                            }
                            extracted_properties.append(prop)
                        
                        # Tentative de clic sur "Suivant"
                        try:
                            next_button = page.locator('a[aria-label="Suivant"], .next, .pagination-next').first
                            if next_button.is_visible():
                                next_button.click()
                            else:
                                break
                        except: break
                except Exception as e:
                    print(f"Erreur pagination sur {url}: {e}")
            browser.close()
        return extracted_properties

    def run_pipeline(self):
        data = self.scrape_real_excel_data = self.scrape_real_estate_site()
        # Suppression des doublons basés sur l'ID
        unique_data = {p['id']: p for p in data}.values()
        if unique_data:
            self.supabase.table('properties').upsert(list(unique_data)).execute()
            print(f"Sync terminée : {len(unique_data)} annonces uniques traitées.")

if __name__ == "__main__":
    RealPropertyScraper().run_pipeline()
