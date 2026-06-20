import os
import math
from datetime import datetime

# Ce module sera installé automatiquement par GitHub Actions
try:
    from supabase import create_client, Client
except ImportError:
    print("Attention: le module 'supabase' n'est pas installé.")

class PropertyScraperAndScorer:
    """
    Moteur backend connecté à Supabase.
    Extrait les annonces, calcule le score, et les envoie dans la base de données.
    """
    def __init__(self):
        self.MIN_TERRAIN = 12000 * 0.85 # 10 200 m²
        self.MIN_BATI = 3000 * 0.85     # 2 550 m²
        self.DEPARTEMENTS_CIBLES = ['77', '91', '93', '94', '95']
        
        # --- CONNEXION SUPABASE ---
        # Clés nettoyées et corrigées
        self.SUPABASE_URL = "https://xfhtrugwsovgfcphbdsd.supabase.co"
        self.SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhmaHRydWd3c292Z2ZjcGhiZHNkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODE5ODA0OTMsImV4cCI6MjA5NzU1NjQ5M30.dS8EbRjDrsHukbOo3Gih81M58hCs86RMHJXVIb9U4mg"
        
        try:
            self.supabase: Client = create_client(self.SUPABASE_URL, self.SUPABASE_KEY)
            self.db_connected = True
        except Exception as e:
            print("Erreur de connexion Supabase. Avez-vous mis vos clés ?")
            self.db_connected = False

    def fetch_properties(self):
        """
        [MODULE D'EXTRACTION WEB]
        C'est ici que viendra le code BeautifulSoup ou Playwright 
        pour scrapper BureauxLocaux, Geolocaux, etc.
        Pour le test de la base de données, on génère une annonce fictive du jour.
        """
        return [
            {
                "id": f"ref_{datetime.now().strftime('%Y%m%d%H%M%S')}", # ID unique basé sur l'heure
                "title": "NOUVEAU - Friche industrielle à réhabiliter",
                "surface_totale": 15000,
                "surface_batie": 4000,
                "price": 3500000,
                "location": "Aulnay-sous-Bois",
                "department": "93",
                "distanceParis": 12,
                "timeGareDuNord": 15,
                "highwayAccess": 1.0,
                "residentialProximity": 450,
                "constructible": True,
                "description": "Trouvé aujourd'hui ! Belle friche isolée.",
                "image": "https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=800&q=80",
                "url": "https://www.bureauxlocaux.com/recherche/achat/entrepots-locaux-d-activites/ile-de-france"
            }
        ]

    def filter_property(self, prop):
        """Filtre strict (Département et Surface)"""
        if prop['department'] not in self.DEPARTEMENTS_CIBLES: 
            return False
        if not (prop['surface_totale'] >= self.MIN_TERRAIN or prop['surface_batie'] >= self.MIN_BATI): 
            return False
        return True

    def calculate_score(self, prop):
        """Algorithme de notation (0 à 5 étoiles)"""
        score = 0.0
        if prop['residentialProximity'] >= 500: score += 1.5
        elif prop['residentialProximity'] >= 200: score += 0.8
        
        if prop['timeGareDuNord'] <= 30: score += 1.0
        elif prop['timeGareDuNord'] <= 45: score += 0.5
            
        if prop['highwayAccess'] <= 2.0: score += 0.5
        if prop['constructible']: score += 1.0
            
        prix_m2 = prop['price'] / prop['surface_totale']
        if prix_m2 < 150: score += 1.0
        elif prix_m2 < 250: score += 0.5

        return min(round(score, 1), 5.0)

    def run_pipeline(self):
        print("1. Recherche de nouvelles annonces...")
        raw_properties = self.fetch_properties()
        valid_properties = []

        for prop in raw_properties:
            if self.filter_property(prop):
                prop['score'] = self.calculate_score(prop)
                prop['type'] = 'terrain_nu' if prop['surface_batie'] == 0 else 'bati'
                valid_properties.append(prop)

        print(f"2. {len(valid_properties)} biens qualifiés trouvés.")

        # --- ENVOI VERS SUPABASE ---
        if self.db_connected and valid_properties:
            print("3. Envoi des données vers Supabase...")
            try:
                # La commande 'upsert' ajoute le bien, ou le met à jour si l'ID existe déjà
                data, count = self.supabase.table('properties').upsert(valid_properties).execute()
                print("✅ Succès ! Les annonces sont dans la base de données.")
            except Exception as e:
                print(f"❌ Erreur lors de l'envoi : {e}")
        elif not self.db_connected:
             print("❌ Annulation de l'envoi: Base de données non connectée.")

if __name__ == "__main__":
    scorer = PropertyScraperAndScorer()
    scorer.run_pipeline()
