import { useState, useMemo } from 'react';

// --- ICÔNES SVG INTÉGRÉES (Pour éviter les erreurs d'import) ---
const Icons = {
  MapPin: () => <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>,
  Train: () => <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="16" height="16" x="4" y="3" rx="2"/><path d="M4 11h16"/><path d="M12 3v8"/><path d="m8 19-2 3"/><path d="m18 22-2-3"/><path d="M8 15h0"/><path d="M16 15h0"/></svg>,
  Car: () => <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.1-.7-1.8-.7H5c-.6 0-1.1.4-1.4.9l-1.4 2.9A3.7 3.7 0 0 0 2 12v4c0 .6.4 1 1 1h2"/><circle cx="7" cy="17" r="2"/><path d="M9 17h6"/><circle cx="17" cy="17" r="2"/></svg>,
  Ruler: () => <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21.3 15.3a2.4 2.4 0 0 1 0 3.4l-2.6 2.6a2.4 2.4 0 0 1-3.4 0L2.7 8.7a2.4 1 0 0 1 0-3.4l2.6-2.6a2.4 2.4 0 0 1 3.4 0Z"/><path d="m14.5 12.5 2-2"/><path d="m11.5 9.5 2-2"/><path d="m8.5 6.5 2-2"/><path d="m17.5 15.5 2-2"/></svg>,
  Building: () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="16" height="20" x="4" y="2" rx="2" ry="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01"/><path d="M16 6h.01"/><path d="M12 6h.01"/><path d="M12 10h.01"/><path d="M12 14h.01"/><path d="M16 10h.01"/><path d="M16 14h.01"/><path d="M8 10h.01"/><path d="M8 14h.01"/></svg>,
  Star: ({ filled }: { filled?: boolean }) => <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill={filled ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={filled ? "text-yellow-400" : "text-gray-300"}><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>,
  AlertTriangle: () => <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>,
  CheckCircle: () => <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="m9 11 3 3L22 4"/></svg>,
  Filter: () => <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>,
  ArrowUpDown: () => <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m21 16-4 4-4-4"/><path d="M17 20V4"/><path d="m3 8 4-4 4 4"/><path d="M7 4v16"/></svg>,
  Info: () => <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>,
  ExternalLink: () => <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>,
  RefreshCw: () => <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>,
  Activity: () => <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
};

// ... DONNÉES SIMULÉES ---
const MOCK_PROPERTIES = [
  {
    id: 1,
    title: "Ancien site logistique à réhabiliter - Zone d'activité",
    type: "bati",
    surface_totale: 14500,
    surface_batie: 4200,
    price: 3200000,
    location: "Mitry-Mory",
    department: "77",
    distanceParis: 25,
    timeGareDuNord: 35,
    highwayAccess: 1.2,
    residentialProximity: 600,
    constructible: true,
    score: 4.5,
    description: "Vaste entrepôt logistique des années 80. Structure métallique en bon état. PLU favorable (Zone UX) permettant l'accueil de public après travaux. Grand parking existant.",
    image: "https://images.unsplash.com/photo-1586528116311-ad8ed3c84a0c?auto=format&fit=crop&w=800&q=80",
    url: "https://www.bureauxlocaux.com/recherche/achat/entrepots-locaux-d-activites/ile-de-france"
  },
  {
    id: 2,
    title: "Terrain industriel nu - Parc d'Affaires",
    type: "terrain_nu",
    surface_totale: 11000,
    surface_batie: 0,
    price: 1800000,
    location: "Corbeil-Essonnes",
    department: "91",
    distanceParis: 35,
    timeGareDuNord: 55,
    highwayAccess: 3.5, 
    residentialProximity: 150,
    constructible: true,
    score: 3.2,
    description: "Parcelle viabilisée prête à construire. Attention: proximité immédiate avec un nouveau lotissement résidentiel à l'Est de la parcelle.",
    image: "https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=800&q=80",
    url: "https://www.geolocaux.com/vente/terrain/ile-de-france/"
  },
  {
    id: 3,
    title: "Friche industrielle majeure (Ex-usine textile)",
    type: "bati",
    surface_totale: 22000,
    surface_batie: 8500,
    price: 4500000,
    location: "Gonesse",
    department: "95",
    distanceParis: 15,
    timeGareDuNord: 25,
    highwayAccess: 0.5,
    residentialProximity: 800,
    constructible: true,
    score: 4.8,
    description: "Opportunité rare. Immense friche totalement isolée des zones d'habitation. Hauteur sous plafond de 8 mètres dans la nef principale (idéal Sanctuaire). Bâtiment annexe parfait pour la résidence.",
    image: "https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=800&q=80",
    url: "https://www.arthur-loyd.com/immobilier-entreprise/vente/locaux-d-activites-entrepots/ile-de-france"
  },
  {
    id: 4,
    title: "Ancien centre technique municipal déclassé",
    type: "bati",
    surface_totale: 12500,
    surface_batie: 3100,
    price: 2900000,
    location: "Vitry-sur-Seine",
    department: "94",
    distanceParis: 8,
    timeGareDuNord: 40,
    highwayAccess: 2.0,
    residentialProximity: 50,
    constructible: false,
    score: 2.1,
    description: "Vente par la mairie. Beaux volumes mais inséré dans un tissu urbain dense. Murs mitoyens avec des immeubles d'habitation. PLU restrictif sur les nuisances sonores.",
    image: "https://images.unsplash.com/photo-1558227691-41ea78d1f631?auto=format&fit=crop&w=800&q=80",
    url: "https://www.agorastore.fr/ventes-aux-encheres/immobilier/terrain"
  }
];

export default function App() {
  const [properties] = useState(MOCK_PROPERTIES);
  const [filterType, setFilterType] = useState('all');
  const [sortBy, setSortBy] = useState('score');
  const [selectedProperty, setSelectedProperty] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }));

  const handleRefresh = () => {
    setIsLoading(true);
    // Simulation de l'appel API vers le Scraper Python
    setTimeout(() => {
      setIsLoading(false);
      setLastUpdated(new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }));
    }, 1500);
  };

  const filteredAndSortedProperties = useMemo(() => {
    let result = [...properties];

    if (filterType !== 'all') {
      result = result.filter(p => p.type === filterType);
    }

    result.sort((a, b) => {
      if (sortBy === 'score') return b.score - a.score;
      if (sortBy === 'price_sqm') return (a.price / a.surface_totale) - (b.price / b.surface_totale);
      if (sortBy === 'surface') return b.surface_totale - a.surface_totale;
      if (sortBy === 'transport') return a.timeGareDuNord - b.timeGareDuNord;
      return 0;
    });

    return result;
  }, [properties, filterType, sortBy]);

  const StarRating = ({ score }: { score: number }) => {
    return (
      <div className="flex items-center bg-white/95 backdrop-blur px-3 py-1.5 rounded-lg shadow-sm border border-gray-100">
        {[1, 2, 3, 4, 5].map((star) => (
          <Icons.Star key={star} filled={star <= Math.round(score)} />
        ))}
        <span className="ml-2 font-black text-gray-800 text-lg">{score.toFixed(1)}</span>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-800 pb-12">
      
      {/* HEADER */}
      <nav className="bg-slate-900 text-white p-4 sticky top-0 z-10 shadow-md">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="text-blue-400"><Icons.Building /></div>
            <div>
              <h1 className="text-xl font-bold tracking-tight">Foncier Tracker ERP</h1>
              <div className="text-xs text-slate-400 font-medium">Projet Complexe Culte & Culture • IDF</div>
            </div>
          </div>
          
          <div className="flex gap-4 text-sm font-medium">
            <div className="bg-slate-800 px-3 py-1.5 rounded-full border border-slate-700 hidden md:flex items-center">
              <span className="text-slate-400 mr-2">Critère Surface:</span>
              <span className="text-emerald-400">&gt; 10 200 m²</span>
            </div>
            <button 
              onClick={handleRefresh}
              disabled={isLoading}
              className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 disabled:text-blue-300 text-white px-4 py-1.5 rounded-full transition-colors font-bold shadow-sm"
            >
              <span className={isLoading ? "animate-spin" : ""}><Icons.RefreshCw /></span>
              <span className="hidden md:inline">{isLoading ? "Recherche en cours..." : "Actualiser le marché"}</span>
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto p-4 md:p-6 mt-4">
        
        {/* KPI DASHBOARD */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-200">
            <div className="text-slate-500 text-xs font-bold uppercase tracking-wider mb-1">Biens Actifs</div>
            <div className="text-2xl font-black text-slate-900">{filteredAndSortedProperties.length}</div>
          </div>
          <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-200">
            <div className="text-slate-500 text-xs font-bold uppercase tracking-wider mb-1">Moyenne Prix/m²</div>
            <div className="text-2xl font-black text-blue-600">
              {Math.round(filteredAndSortedProperties.reduce((acc, p) => acc + (p.price / p.surface_totale), 0) / (filteredAndSortedProperties.length || 1))} €
            </div>
          </div>
          <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-200">
            <div className="text-slate-500 text-xs font-bold uppercase tracking-wider mb-1">Moyenne Trajet Paris</div>
            <div className="text-2xl font-black text-emerald-600">
              {Math.round(filteredAndSortedProperties.reduce((acc, p) => acc + p.timeGareDuNord, 0) / (filteredAndSortedProperties.length || 1))} min
            </div>
          </div>
          <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-200">
            <div className="text-slate-500 text-xs font-bold uppercase tracking-wider mb-1">Dernière extraction web</div>
            <div className="text-2xl font-black text-slate-700 flex items-center gap-2">
              <Icons.Activity /> {lastUpdated}
            </div>
          </div>
        </div>

        {/* FILTRES */}
        <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-200 mb-6 flex flex-col md:flex-row gap-4 justify-between items-center">
          <div className="flex items-center gap-2 text-slate-600 font-medium">
            <span className="bg-blue-100 text-blue-800 py-1 px-3 rounded-lg text-sm">
              {filteredAndSortedProperties.length} biens trouvés
            </span>
          </div>
          
          <div className="flex flex-wrap gap-3 w-full md:w-auto">
            <div className="flex-1 md:flex-none relative bg-slate-50 border border-slate-200 rounded-lg">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <Icons.Filter />
              </div>
              <select 
                className="w-full bg-transparent pl-10 pr-8 py-2.5 text-sm font-semibold text-slate-700 outline-none appearance-none cursor-pointer"
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
              >
                <option value="all">Tous les types de biens</option>
                <option value="terrain_nu">Terrains Nus uniquement</option>
                <option value="bati">Bâti (Entrepôts/Friches)</option>
              </select>
            </div>

            <div className="flex-1 md:flex-none relative bg-slate-50 border border-slate-200 rounded-lg">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <Icons.ArrowUpDown />
              </div>
              <select 
                className="w-full bg-transparent pl-10 pr-8 py-2.5 text-sm font-semibold text-slate-700 outline-none appearance-none cursor-pointer"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
              >
                <option value="score">Trier par Pertinence</option>
                <option value="price_sqm">Trier par Prix au m²</option>
                <option value="surface">Trier par Surface Totale</option>
                <option value="transport">Trier par Accès Gare du Nord</option>
              </select>
            </div>
          </div>
        </div>

        {/* GRILLE */}
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {filteredAndSortedProperties.map((prop) => (
            <article key={prop.id} className="bg-white rounded-2xl overflow-hidden shadow-sm hover:shadow-xl transition-all duration-300 border border-slate-200 flex flex-col">
              
              {/* IMAGE */}
              <div className="relative h-56 w-full overflow-hidden bg-slate-200">
                <img src={prop.image} alt={prop.title} className="w-full h-full object-cover" />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent"></div>
                
                <div className="absolute top-4 left-4 flex gap-2">
                  <span className={`px-3 py-1 rounded-md text-xs font-bold uppercase tracking-wider shadow-sm ${
                    prop.type === 'terrain_nu' ? 'bg-emerald-500 text-white' : 'bg-blue-600 text-white'
                  }`}>
                    {prop.type === 'terrain_nu' ? 'Terrain Nu' : 'Bâti Existant'}
                  </span>
                  <span className="bg-white/90 text-slate-800 px-2 py-1 rounded-md text-xs font-bold shadow-sm">
                    Dép. {prop.department}
                  </span>
                </div>
                
                <div className="absolute bottom-4 right-4 z-10">
                  <StarRating score={prop.score} />
                </div>

                <div className="absolute bottom-4 left-4 right-24 text-white">
                   <h3 className="font-bold text-lg leading-tight drop-shadow-md">{prop.title}</h3>
                   <div className="flex items-center text-sm mt-1 opacity-90">
                     <span className="mr-1"><Icons.MapPin /></span>
                     {prop.location} ({prop.distanceParis} km)
                   </div>
                </div>
              </div>

              {/* CONTENU */}
              <div className="p-5 flex-1 flex flex-col">
                
                <div className="grid grid-cols-2 gap-4 mb-5 p-4 bg-slate-50 rounded-xl border border-slate-100">
                  <div className="flex items-start">
                    <span className="mr-3 text-indigo-500 mt-0.5"><Icons.Ruler /></span>
                    <div>
                      <span className="font-bold text-slate-800 text-base block">{prop.surface_totale.toLocaleString()} m²</span>
                      <span className="text-xs font-medium text-slate-500">Surface Terrain</span>
                    </div>
                  </div>
                  
                  {prop.type === 'bati' ? (
                    <div className="flex items-start">
                      <span className="mr-3 text-blue-500 mt-0.5"><Icons.Building /></span>
                      <div>
                        <span className="font-bold text-slate-800 text-base block">{prop.surface_batie.toLocaleString()} m²</span>
                        <span className="text-xs font-medium text-slate-500">Surface Bâtie</span>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-start opacity-40">
                      <span className="mr-3 text-slate-500 mt-0.5"><Icons.Building /></span>
                      <div>
                        <span className="font-bold text-slate-800 text-base block">0 m²</span>
                        <span className="text-xs font-medium text-slate-500">Surface Bâtie</span>
                      </div>
                    </div>
                  )}

                  <div className="flex items-start">
                    <span className="mr-3 text-emerald-500 mt-0.5"><Icons.Train /></span>
                    <div>
                      <span className="font-bold text-slate-800 text-base block">{prop.timeGareDuNord} min</span>
                      <span className="text-xs font-medium text-slate-500">Gare du Nord</span>
                    </div>
                  </div>

                  <div className="flex items-start">
                    <span className="mr-3 text-amber-500 mt-0.5"><Icons.Car /></span>
                    <div>
                      <span className="font-bold text-slate-800 text-base block">{prop.highwayAccess} km</span>
                      <span className="text-xs font-medium text-slate-500">Accès Autoroute</span>
                    </div>
                  </div>
                </div>

                <div className="space-y-2 mb-6 flex-1">
                  <div className={`flex p-3 rounded-xl border ${
                    prop.residentialProximity < 300 
                      ? 'bg-red-50 border-red-100 text-red-800' 
                      : 'bg-emerald-50 border-emerald-100 text-emerald-800'
                  }`}>
                    <span className={`mr-3 mt-0.5 ${prop.residentialProximity < 300 ? 'text-red-500' : 'text-emerald-500'}`}>
                      {prop.residentialProximity < 300 ? <Icons.AlertTriangle /> : <Icons.CheckCircle />}
                    </span>
                    <div>
                      <div className="text-sm font-bold">Voisinage à {prop.residentialProximity} m</div>
                      <div className="text-xs mt-0.5 opacity-80">
                        {prop.residentialProximity < 300 
                          ? "Risque de nuisances sonores." 
                          : "Isolement acoustique optimal."}
                      </div>
                    </div>
                  </div>
                  
                  <div className={`flex items-center p-3 rounded-xl border text-sm font-medium ${
                    prop.constructible 
                      ? 'bg-slate-50 border-slate-200 text-slate-700' 
                      : 'bg-orange-50 border-orange-200 text-orange-800'
                  }`}>
                    <span className={`mr-2 ${prop.constructible ? 'text-slate-400' : 'text-orange-500'}`}>
                       {prop.constructible ? <Icons.Info /> : <Icons.AlertTriangle />}
                    </span>
                    {prop.constructible ? "Terrain constructible" : "Attention: Zone protégée"}
                  </div>
                </div>

                <div className="pt-4 border-t border-slate-100 flex justify-between items-end mt-auto">
                  <div>
                    <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Prix FAI</div>
                    <div className="text-2xl font-black text-slate-900 tracking-tight">
                      {(prop.price / 1000000).toFixed(2)} M€
                    </div>
                    <div className="text-sm font-medium text-slate-500 mt-0.5">
                      {Math.round(prop.price / prop.surface_totale)} €/m²
                    </div>
                  </div>
                  
                  <button 
                    onClick={() => setSelectedProperty(prop)}
                    className="flex items-center justify-center gap-2 bg-slate-900 hover:bg-blue-600 text-white px-5 py-2.5 rounded-xl text-sm font-bold transition-colors shadow-sm"
                  >
                    Détails <Icons.ExternalLink />
                  </button>
                </div>

              </div>
            </article>
          ))}
        </div>
      </main>

      {/* POPUP DE DÉTAILS */}
      {selectedProperty && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl relative">
            <button 
              onClick={() => setSelectedProperty(null)}
              className="absolute top-4 right-4 bg-white/80 hover:bg-slate-100 rounded-full w-8 h-8 flex items-center justify-center z-10 text-slate-800 font-bold"
            >
              ✕
            </button>
            
            <img 
              src={selectedProperty.image} 
              alt={selectedProperty.title} 
              className="w-full h-64 object-cover"
            />
            
            <div className="p-6 md:p-8">
              <div className="flex items-center gap-3 mb-2">
                 <span className="bg-slate-100 text-slate-700 px-3 py-1 rounded-lg text-sm font-bold">Réf: #{selectedProperty.id}</span>
                 <StarRating score={selectedProperty.score} />
              </div>
              
              <h2 className="text-2xl font-black text-slate-900 mb-2">{selectedProperty.title}</h2>
              <div className="text-slate-500 font-medium mb-6 flex items-center">
                <span className="mr-1"><Icons.MapPin /></span> {selectedProperty.location} ({selectedProperty.department})
              </div>

              <div className="bg-blue-50 border border-blue-100 rounded-xl p-5 mb-8">
                <h4 className="font-bold text-blue-900 mb-2">Analyse du site</h4>
                <p className="text-blue-800 text-sm leading-relaxed">
                  {selectedProperty.description}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-8">
                <div>
                  <div className="text-sm text-slate-500 mb-1">Prix de présentation</div>
                  <div className="text-xl font-bold text-slate-900">{(selectedProperty.price / 1000000).toFixed(2)} M€</div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">Surface Terrain</div>
                  <div className="text-xl font-bold text-slate-900">{selectedProperty.surface_totale.toLocaleString()} m²</div>
                </div>
              </div>

              <a 
                href={selectedProperty.url}
                target="_blank"
                rel="noopener noreferrer"
                className="w-full bg-blue-600 hover:bg-blue-700 text-white py-4 rounded-xl font-bold text-lg transition-colors flex justify-center items-center gap-2"
              >
                Aller sur l'annonce originale <Icons.ExternalLink />
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
