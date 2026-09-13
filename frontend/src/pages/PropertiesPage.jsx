import React, { useState, useEffect } from 'react';
import { 
  Building2, 
  MapPin, 
  DollarSign, 
  Bed, 
  FileText, 
  Image as ImageIcon, 
  Plus,
  Map as MapIcon,
  LayoutGrid,
  Navigation,
  Compass,
  CheckCircle2,
  SlidersHorizontal,
  X
} from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import { getProjects } from '../services/api';
import { AddPropertyModal } from '../components/dashboard/AddPropertyModal';
import { useToast } from '../components/ui/Toast';
import Pagination from '../components/ui/Pagination';

// Custom Leaflet marker icons with clean light theme styling
const createCustomIcon = (priceText) => {
  return L.divIcon({
    className: 'custom-map-marker',
    html: `
      <div style="
        background: linear-gradient(135deg, #E8654A, #F97316);
        color: #FFFFFF;
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: 800;
        font-size: 11px;
        border: 2px solid #FFFFFF;
        box-shadow: 0 4px 14px rgba(232, 101, 74, 0.45);
        white-space: nowrap;
        display: flex;
        align-items: center;
        gap: 4px;
      ">
        🏢 ${priceText}
      </div>
    `,
    iconSize: [100, 30],
    iconAnchor: [50, 15]
  });
};

const MOCK_PROJECTS = [
  {
    id: 'proj_101',
    name: 'GLG Gulshan Heights',
    location: 'Gulshan 2, Dhaka',
    lat: 23.7925,
    lng: 90.4078,
    price: '৳95 Lakhs - ৳1.8 Crore',
    price_short: '৳95L+',
    bedrooms: '3 & 4 BHK',
    status: 'Ready / Under Construction',
    image: 'https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=600&q=80',
    amenities: ['Rooftop Infinity Pool', '24/7 Generator Backup', 'Basement Parking', 'Smart Home Tech'],
    proximity: [
      { name: 'United Hospital', dist: '1.2 km' },
      { name: 'Gulshan Club', dist: '0.5 km' },
      { name: 'Diplomatic Zone', dist: '0.3 km' }
    ]
  },
  {
    id: 'proj_102',
    name: 'GLG Banani Crest',
    location: 'Banani Block F, Dhaka',
    lat: 23.7937,
    lng: 90.4046,
    price: '৳1.2 Crore - ৳2.5 Crore',
    price_short: '৳1.2Cr+',
    bedrooms: '3 & 4 BHK Luxury Duplex',
    status: 'Under Construction',
    image: 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=600&q=80',
    amenities: ['Duplex Terrace', 'Italian Marble', 'Double Height Lobby', 'Private Elevator'],
    proximity: [
      { name: 'Banani Metro Rail', dist: '0.6 km' },
      { name: 'Kemal Ataturk Ave', dist: '0.2 km' },
      { name: 'Banani Club', dist: '0.4 km' }
    ]
  },
  {
    id: 'proj_103',
    name: 'GLG Grand Residency',
    location: 'Dhanmondi 27, Dhaka',
    lat: 23.7461,
    lng: 90.3742,
    price: '৳85 Lakhs - ৳1.4 Crore',
    price_short: '৳85L+',
    bedrooms: '2 & 3 BHK',
    status: 'Handover 2026',
    image: 'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=600&q=80',
    amenities: ['Gym & Fitness Studio', 'Kids Play Zone', 'Community Hall', 'Full CCTV'],
    proximity: [
      { name: 'Dhanmondi Lake', dist: '0.4 km' },
      { name: 'Rapa Plaza', dist: '0.2 km' },
      { name: 'Square Hospital', dist: '1.5 km' }
    ]
  },
  {
    id: 'proj_104',
    name: 'GLG Uttara Sky Villas',
    location: 'Uttara Sector 3, Dhaka',
    lat: 23.8690,
    lng: 90.3980,
    price: '৳75 Lakhs - ৳1.3 Crore',
    price_short: '৳75L+',
    bedrooms: '3 BHK Modern',
    status: 'Upcoming Launch',
    image: 'https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=600&q=80',
    amenities: ['Sky Garden', 'EV Charging Station', 'Infinity Jacuzzi', 'Solar Backup'],
    proximity: [
      { name: 'Uttara Metro Station', dist: '0.5 km' },
      { name: 'Dhaka Int. Airport', dist: '2.5 km' },
      { name: 'Sector 3 Park', dist: '0.1 km' }
    ]
  }
];

export default function PropertiesPage({ searchQuery = '' }) {
  const { showToast } = useToast();
  const [projects, setProjects] = useState(MOCK_PROJECTS);
  const [activeView, setActiveView] = useState('grid'); // 'grid' or 'map'
  const [selectedArea, setSelectedArea] = useState('all');
  const [selectedProject, setSelectedProject] = useState(MOCK_PROJECTS[0]);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [floorPlanModalProject, setFloorPlanModalProject] = useState(null);

  useEffect(() => {
    getProjects()
      .then(res => {
        const list = Array.isArray(res) ? res : (res?.projects || []);
        if (list.length > 0) {
          const normalized = list.map((p, idx) => {
            const fallback = MOCK_PROJECTS[idx % MOCK_PROJECTS.length];
            return {
              id: p.project_id || p.id || `proj_${idx}`,
              name: p.project_name || p.title || p.name || fallback.name,
              location: p.location || fallback.location,
              lat: p.latitude || p.features?.coordinates?.[0] || fallback.lat,
              lng: p.longitude || p.features?.coordinates?.[1] || fallback.lng,
              price: p.starting_price_bdt ? `৳${(p.starting_price_bdt / 10000000).toFixed(1)} Crore` : (p.price || fallback.price),
              price_short: p.starting_price_bdt ? `৳${(p.starting_price_bdt / 10000000).toFixed(1)}Cr` : (p.price_short || fallback.price_short),
              bedrooms: `${p.bedrooms || 3} BHK`,
              status: p.status === 'ready' ? 'Ready to Move' : (p.status === 'under_construction' ? 'Under Construction' : 'Active Development'),
              image: p.hero_image || (p.images && p.images[0]) || p.image_url || fallback.image,
              amenities: p.amenities || fallback.amenities,
              proximity: p.proximity || fallback.proximity,
              brochure_url: p.brochure_url || 'https://fdjzbtkypedzlkwpzzzt.supabase.co/storage/v1/object/public/brochures/gulshan_heights_brochure.pdf'
            };
          });
          setProjects(normalized);
          setSelectedProject(normalized[0]);
        }
      })
      .catch(() => {});
  }, []);

  const handlePropertyAdded = (newProj) => {
    const formatted = {
      id: newProj.project_id || `proj_${Date.now()}`,
      name: newProj.name,
      location: newProj.location,
      lat: newProj.features?.coordinates?.[0] || 23.7925,
      lng: newProj.features?.coordinates?.[1] || 90.4078,
      price: newProj.price,
      price_short: newProj.price.split(' ')[0] || '৳80L+',
      bedrooms: `${newProj.bedrooms || 3} BHK`,
      status: newProj.status || 'Active Development',
      image: newProj.features?.image || 'https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=600&q=80',
      amenities: newProj.features?.amenities || ['Modern Lift', 'Power Backup', 'Security'],
      proximity: [{ name: 'City Center', dist: '1.2 km' }],
      brochure_url: newProj.brochure_url || 'https://fdjzbtkypedzlkwpzzzt.supabase.co/storage/v1/object/public/brochures/gulshan_heights_brochure.pdf'
    };
    setProjects(prev => [formatted, ...prev]);
    setSelectedProject(formatted);
  };

  const handleDownloadBrochure = (proj) => {
    const url = proj.brochure_url || proj.brochure || 'https://fdjzbtkypedzlkwpzzzt.supabase.co/storage/v1/object/public/brochures/gulshan_heights_brochure.pdf';
    showToast(`Opening architectural brochure for "${proj.name || proj.project_name}"...`, 'success');
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  const handleOpenFloorPlans = (proj) => {
    setFloorPlanModalProject(proj);
  };

  const filteredProjects = projects.filter(p => {
    const matchesArea = selectedArea === 'all' || p.location.toLowerCase().includes(selectedArea.toLowerCase());
    const matchesSearch = !searchQuery.trim() || 
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
      p.location.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.price.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesArea && matchesSearch;
  });

  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(6);

  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, selectedArea]);

  const paginatedProjects = filteredProjects.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  return (
    <div style={{ padding: '24px 32px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Header Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>Property Inventory &amp; Interactive Map</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Spatial Proximity Engine • CartoDB Voyager Leaflet Maps • Media &amp; Brochure Catalog
          </p>
        </div>

        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          {/* View Toggle */}
          <div style={{ background: 'var(--bg-card)', padding: '4px', borderRadius: '12px', display: 'flex', border: '1px solid var(--border-glass)', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
            <button
              onClick={() => setActiveView('grid')}
              style={{
                padding: '6px 14px',
                borderRadius: '8px',
                border: 'none',
                background: activeView === 'grid' ? 'var(--primary-coral)' : 'transparent',
                color: activeView === 'grid' ? '#FFFFFF' : 'var(--text-muted)',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: '0.8rem',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                transition: 'all 0.2s ease'
              }}
            >
              <LayoutGrid size={16} /> Grid View
            </button>

            <button
              onClick={() => setActiveView('map')}
              style={{
                padding: '6px 14px',
                borderRadius: '8px',
                border: 'none',
                background: activeView === 'map' ? 'var(--primary-coral)' : 'transparent',
                color: activeView === 'map' ? '#FFFFFF' : 'var(--text-muted)',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: '0.8rem',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                transition: 'all 0.2s ease'
              }}
            >
              <MapIcon size={16} /> Interactive Spatial Map
            </button>
          </div>

          <button 
            className="btn-gradient"
            onClick={() => setIsAddModalOpen(true)}
            id="btn-add-development"
          >
            <Plus size={16} /> Add New Development
          </button>
        </div>
      </div>

      {/* Area Location Filter Pills */}
      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
        <SlidersHorizontal size={16} color="var(--text-dim)" />
        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600, marginRight: '8px' }}>Location Filter:</span>
        {['all', 'Gulshan', 'Banani', 'Dhanmondi', 'Uttara'].map(loc => (
          <button
            key={loc}
            onClick={() => setSelectedArea(loc)}
            className={`badge ${selectedArea === loc ? 'badge-emerald' : 'badge-violet'}`}
            style={{
              cursor: 'pointer',
              padding: '6px 14px',
              textTransform: 'capitalize',
              fontSize: '0.78rem',
              border: selectedArea === loc ? '1px solid #10B981' : '1px solid transparent',
              transition: 'all 0.2s ease'
            }}
          >
            {loc === 'all' ? '🏙️ All Locations' : `📍 ${loc}`}
          </button>
        ))}
      </div>

      {/* View Mode 1: Grid View */}
      {activeView === 'grid' && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '24px' }}>
            {paginatedProjects.map((proj) => (
              <div key={proj.id} className="glass-card" style={{ overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                
                {/* Property Image Banner */}
                <div style={{ height: '180px', position: 'relative', overflow: 'hidden' }}>
                  <img
                    src={proj.image}
                    alt={proj.name}
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  />
                  <span className="badge badge-emerald" style={{ position: 'absolute', top: '12px', right: '12px', background: 'var(--bg-card)', border: '1px solid var(--border-glass)' }}>
                    {proj.status}
                  </span>
                </div>

                {/* Content */}
                <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px', flex: 1 }}>
                  <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-main)' }}>{proj.name}</h3>

                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <MapPin size={14} color="var(--primary-coral)" /> {proj.location}
                  </div>

                  <div className="text-emerald-themed" style={{ fontSize: '1.1rem', fontWeight: 800 }}>
                    {proj.price}
                  </div>

                  <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Bed size={14} /> {proj.bedrooms}
                  </div>

                  {/* Nearby Proximity Highlights */}
                  {proj.proximity && (
                    <div style={{ background: 'var(--bg-main)', padding: '10px 12px', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-main)', fontWeight: 700, marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Navigation size={12} color="#0891B2" /> Spatial Proximity Highlights
                      </div>
                      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                        {proj.proximity.map((px, idx) => (
                          <span key={idx} style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                            • {px.name} ({px.dist})
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Amenities */}
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '4px' }}>
                    {proj.amenities?.map((am, i) => (
                      <span key={i} className="badge badge-violet" style={{ fontSize: '0.65rem' }}>{am}</span>
                    ))}
                  </div>

                  {/* Actions */}
                  <div style={{ marginTop: 'auto', paddingTop: '16px', borderTop: '1px solid var(--border-glass)', display: 'flex', gap: '8px' }}>
                    <button 
                      onClick={() => handleDownloadBrochure(proj)}
                      className="badge badge-cyan" 
                      style={{ cursor: 'pointer', padding: '6px 10px', flex: 1, justifyContent: 'center' }}
                    >
                      <FileText size={12} /> Brochure PDF
                    </button>
                    <button 
                      onClick={() => handleOpenFloorPlans(proj)}
                      className="badge badge-violet" 
                      style={{ cursor: 'pointer', padding: '6px 10px', flex: 1, justifyContent: 'center' }}
                    >
                      <ImageIcon size={12} /> Floor Plans
                    </button>
                  </div>
                </div>

              </div>
            ))}
          </div>

          {filteredProjects.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '48px 0', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              No properties found matching your search criteria.
            </div>
          ) : (
            <Pagination
              currentPage={currentPage}
              totalItems={filteredProjects.length}
              pageSize={pageSize}
              onPageChange={setCurrentPage}
              onPageSizeChange={(newSize) => {
                setPageSize(newSize);
                setCurrentPage(1);
              }}
              pageSizeOptions={[6, 12, 24]}
              itemLabel="properties"
            />
          )}
        </>
      )}

      {/* View Mode 2: Interactive Spatial Map View */}
      {activeView === 'map' && (
        <div style={{ display: 'flex', gap: '24px', height: 'calc(100vh - 200px)' }}>
          
          {/* Map Container */}
          <div className="glass-card" style={{ flex: 2, borderRadius: '16px', overflow: 'hidden', position: 'relative' }}>
            <MapContainer
              center={[23.7925, 90.4078]} // Centered on Gulshan/Banani, Dhaka
              zoom={13}
              style={{ width: '100%', height: '100%' }}
            >
              {/* Voyager Tile Layer for crisp modern clarity */}
              <TileLayer
                url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
                attribution='&copy; <a href="https://carto.com/">CARTO</a>'
              />

              {/* Spatial Property Markers */}
              {filteredProjects.map((proj) => (
                <Marker
                  key={proj.id}
                  position={[proj.lat, proj.lng]}
                  icon={createCustomIcon(proj.price_short)}
                  eventHandlers={{
                    click: () => setSelectedProject(proj),
                  }}
                >
                  <Popup className="custom-leaflet-popup">
                    <div style={{ color: 'var(--text-main)', padding: '4px' }}>
                      <strong style={{ fontSize: '14px' }}>{proj.name}</strong>
                      <div style={{ fontSize: '12px', color: 'var(--text-muted)', margin: '4px 0' }}>{proj.location}</div>
                      <div style={{ color: '#059669', fontWeight: 800, fontSize: '13px' }}>{proj.price}</div>
                    </div>
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
          </div>

          {/* Sidebar Property Detail Card */}
          <div className="glass-card" style={{ flex: 1, padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto' }}>
            {selectedProject ? (
              <>
                <div style={{ height: '160px', borderRadius: '12px', overflow: 'hidden', position: 'relative' }}>
                  <img src={selectedProject.image} alt={selectedProject.name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                  <span className="badge badge-emerald" style={{ position: 'absolute', top: '12px', right: '12px', background: 'var(--bg-card)', border: '1px solid var(--border-glass)' }}>
                    {selectedProject.status}
                  </span>
                </div>

                <div>
                  <h3 style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--text-main)' }}>{selectedProject.name}</h3>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px' }}>
                    <MapPin size={14} color="var(--primary-coral)" /> {selectedProject.location}
                  </div>
                  <div className="text-emerald-themed" style={{ fontSize: '1.2rem', fontWeight: 800, marginTop: '8px' }}>
                    {selectedProject.price}
                  </div>
                </div>

                {/* Spatial Proximity Details */}
                <div style={{ background: 'var(--bg-main)', padding: '14px', borderRadius: '10px', border: '1px solid var(--border-glass)' }}>
                  <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#0891B2', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Navigation size={14} /> Neighborhood Spatial Proximity
                  </h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    {selectedProject.proximity?.map((px, i) => (
                      <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                        <span>📍 {px.name}</span>
                        <span style={{ fontWeight: 700, color: '#059669' }}>{px.dist}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Key Amenities */}
                <div>
                  <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '8px' }}>Key Amenities &amp; Specifications</h4>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {selectedProject.amenities?.map((am, i) => (
                      <span key={i} className="badge badge-violet" style={{ fontSize: '0.7rem' }}>
                        <CheckCircle2 size={10} style={{ marginRight: '4px' }} /> {am}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Quick Actions */}
                <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: '10px', paddingTop: '16px', borderTop: '1px solid var(--border-glass)' }}>
                  <button 
                    onClick={() => handleDownloadBrochure(selectedProject)}
                    className="btn-gradient" 
                    style={{ width: '100%', justifyContent: 'center' }}
                  >
                    <FileText size={16} /> Download Property Brochure PDF
                  </button>
                  <button 
                    onClick={() => handleOpenFloorPlans(selectedProject)}
                    className="badge badge-violet" 
                    style={{ width: '100%', justifyContent: 'center', padding: '10px', cursor: 'pointer' }}
                  >
                    <ImageIcon size={16} /> View Floor Plans &amp; Dimensions
                  </button>
                </div>
              </>
            ) : (
              <div style={{ textTransform: 'uppercase', color: 'var(--text-dim)', textAlign: 'center', margin: 'auto' }}>
                Select a spatial marker on the map
              </div>
            )}
          </div>

        </div>
      )}

      {/* Floor Plans Modal */}
      {floorPlanModalProject && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md">
          <div className="relative w-full max-w-2xl bg-neutral-900 border border-white/10 rounded-2xl p-6 shadow-2xl">
            <div className="flex justify-between items-center pb-4 border-b border-white/10 mb-4">
              <div>
                <h3 className="text-lg font-bold text-white">Floor Plans &amp; Specifications</h3>
                <p className="text-xs text-neutral-400">{floorPlanModalProject.name} • {floorPlanModalProject.bedrooms}</p>
              </div>
              <button 
                onClick={() => setFloorPlanModalProject(null)}
                className="text-neutral-400 hover:text-white p-1 rounded-lg hover:bg-white/10"
              >
                <X size={20} />
              </button>
            </div>
            <div className="space-y-4">
              <div className="rounded-xl overflow-hidden border border-white/10 bg-neutral-950 p-2">
                <img 
                  src="https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1000&q=80" 
                  alt="Architectural Blueprint Layout" 
                  className="w-full h-64 object-cover rounded-lg"
                />
              </div>
              <div className="grid grid-cols-3 gap-3 text-center">
                <div className="p-3 rounded-xl bg-white/[0.03] border border-white/5">
                  <div className="text-xs text-neutral-400">Total Super Built-up</div>
                  <div className="text-sm font-bold text-white mt-1">2,850 Sq.Ft</div>
                </div>
                <div className="p-3 rounded-xl bg-white/[0.03] border border-white/5">
                  <div className="text-xs text-neutral-400">Carpet Area</div>
                  <div className="text-sm font-bold text-emerald-400 mt-1">2,280 Sq.Ft</div>
                </div>
                <div className="p-3 rounded-xl bg-white/[0.03] border border-white/5">
                  <div className="text-xs text-neutral-400">Balconies</div>
                  <div className="text-sm font-bold text-amber-400 mt-1">3 Verandas</div>
                </div>
              </div>
              <button 
                onClick={() => {
                  showToast('High-resolution CAD blueprint saved to downloads.', 'success');
                  setFloorPlanModalProject(null);
                }}
                className="w-full py-2.5 rounded-xl bg-gradient-to-r from-amber-400 to-amber-500 text-black font-semibold text-sm hover:from-amber-300 hover:to-amber-400 transition-all"
              >
                Download High-Res CAD Blueprints (PDF)
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Property Development Modal */}
      <AddPropertyModal 
        isOpen={isAddModalOpen} 
        onClose={() => setIsAddModalOpen(false)} 
        onPropertyAdded={handlePropertyAdded} 
      />

    </div>
  );
}
