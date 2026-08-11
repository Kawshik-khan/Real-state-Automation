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
  SlidersHorizontal
} from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import { getProjects } from '../services/api';

// Custom Leaflet marker icons with CSS glow
const createCustomIcon = (priceText) => {
  return L.divIcon({
    className: 'custom-map-marker',
    html: `
      <div style="
        background: linear-gradient(135deg, #8B5CF6, #6366F1);
        color: #FFFFFF;
        padding: 6px 10px;
        border-radius: 20px;
        font-weight: 800;
        font-size: 11px;
        border: 2px solid #34D399;
        box-shadow: 0 4px 15px rgba(139, 92, 246, 0.6);
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

export default function PropertiesPage() {
  const [projects, setProjects] = useState(MOCK_PROJECTS);
  const [activeView, setActiveView] = useState('grid'); // 'grid' or 'map'
  const [selectedArea, setSelectedArea] = useState('all');
  const [selectedProject, setSelectedProject] = useState(MOCK_PROJECTS[0]);

  useEffect(() => {
    getProjects()
      .then(res => {
        if (res.projects && res.projects.length > 0) {
          // Merge coordinates onto API response if missing
          const merged = res.projects.map((p, idx) => ({
            ...MOCK_PROJECTS[idx % MOCK_PROJECTS.length],
            ...p,
          }));
          setProjects(merged);
        }
      })
      .catch(() => {});
  }, []);

  const filteredProjects = projects.filter(p => {
    if (selectedArea === 'all') return true;
    return p.location.toLowerCase().includes(selectedArea.toLowerCase());
  });

  return (
    <div style={{ padding: '24px 32px', display: 'flex', flexDirection: 'column', gap: '24px', height: 'calc(100vh - 70px)', overflowY: 'auto' }}>
      
      {/* Header Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 800 }}>Property Inventory & Interactive Map</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Spatial Proximity Engine • CartoDB Dark Leaflet Maps • Media & Brochure Catalog
          </p>
        </div>

        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          {/* View Toggle */}
          <div style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '4px', borderRadius: '10px', display: 'flex', border: '1px solid var(--border-glass)' }}>
            <button
              onClick={() => setActiveView('grid')}
              style={{
                padding: '6px 14px',
                borderRadius: '8px',
                border: 'none',
                background: activeView === 'grid' ? 'var(--primary)' : 'transparent',
                color: activeView === 'grid' ? '#FFF' : 'var(--text-muted)',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: '0.8rem',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
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
                background: activeView === 'map' ? 'var(--primary)' : 'transparent',
                color: activeView === 'map' ? '#FFF' : 'var(--text-muted)',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: '0.8rem',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <MapIcon size={16} /> Interactive Spatial Map
            </button>
          </div>

          <button className="btn-gradient">
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
              padding: '6px 12px',
              textTransform: 'capitalize',
              fontSize: '0.78rem',
              border: selectedArea === loc ? '1px solid #34D399' : '1px solid transparent'
            }}
          >
            {loc === 'all' ? '🏙️ All Locations' : `📍 ${loc}`}
          </button>
        ))}
      </div>

      {/* View Mode 1: Grid View */}
      {activeView === 'grid' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '24px' }}>
          {filteredProjects.map((proj) => (
            <div key={proj.id} className="glass-card" style={{ overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
              
              {/* Property Image Banner */}
              <div style={{ height: '180px', position: 'relative', overflow: 'hidden' }}>
                <img
                  src={proj.image}
                  alt={proj.name}
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
                <span className="badge badge-emerald" style={{ position: 'absolute', top: '12px', right: '12px' }}>
                  {proj.status}
                </span>
              </div>

              {/* Content */}
              <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px', flex: 1 }}>
                <h3 style={{ fontSize: '1.2rem', fontWeight: 700 }}>{proj.name}</h3>

                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <MapPin size={14} color="#8B5CF6" /> {proj.location}
                </div>

                <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#34D399' }}>
                  {proj.price}
                </div>

                <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Bed size={14} /> {proj.bedrooms}
                </div>

                {/* Nearby Proximity Highlights */}
                {proj.proximity && (
                  <div style={{ background: 'rgba(0,0,0,0.2)', padding: '10px', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 700, marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Navigation size={12} color="#06B6D4" /> Spatial Proximity Highlights
                    </div>
                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                      {proj.proximity.map((px, idx) => (
                        <span key={idx} style={{ fontSize: '0.68rem', color: '#9CA3AF' }}>
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
                  <button className="badge badge-cyan" style={{ cursor: 'pointer', padding: '6px 10px', flex: 1, justifyContent: 'center' }}>
                    <FileText size={12} /> Brochure PDF
                  </button>
                  <button className="badge badge-violet" style={{ cursor: 'pointer', padding: '6px 10px', flex: 1, justifyContent: 'center' }}>
                    <ImageIcon size={12} /> Floor Plans
                  </button>
                </div>
              </div>

            </div>
          ))}
        </div>
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
              {/* Dark Mode CartoDB Tile Layer */}
              <TileLayer
                url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
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
                    <div style={{ color: '#000', padding: '4px' }}>
                      <strong style={{ fontSize: '14px' }}>{proj.name}</strong>
                      <div style={{ fontSize: '12px', color: '#4B5563', margin: '4px 0' }}>{proj.location}</div>
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
                  <span className="badge badge-emerald" style={{ position: 'absolute', top: '12px', right: '12px' }}>
                    {selectedProject.status}
                  </span>
                </div>

                <div>
                  <h3 style={{ fontSize: '1.3rem', fontWeight: 800 }}>{selectedProject.name}</h3>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px' }}>
                    <MapPin size={14} color="#8B5CF6" /> {selectedProject.location}
                  </div>
                  <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#34D399', marginTop: '8px' }}>
                    {selectedProject.price}
                  </div>
                </div>

                {/* Spatial Proximity Details */}
                <div style={{ background: 'rgba(0, 0, 0, 0.3)', padding: '14px', borderRadius: '10px', border: '1px solid var(--border-glass)' }}>
                  <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#06B6D4', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Navigation size={14} /> Neighborhood Spatial Proximity
                  </h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    {selectedProject.proximity?.map((px, i) => (
                      <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                        <span>📍 {px.name}</span>
                        <span style={{ fontWeight: 700, color: '#34D399' }}>{px.dist}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Key Amenities */}
                <div>
                  <h4 style={{ fontSize: '0.85rem', fontWeight: 700, marginBottom: '8px' }}>Key Amenities & Specifications</h4>
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
                  <button className="btn-gradient" style={{ width: '100%', justifyContent: 'center' }}>
                    <FileText size={16} /> Request AI Brochure Mapping
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

    </div>
  );
}
