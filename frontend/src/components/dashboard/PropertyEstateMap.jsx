import React, { useState, useEffect } from 'react';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import { 
  MapPin, 
  Navigation, 
  Eye, 
  Search, 
  Bed, 
  Bath, 
  Maximize2, 
  Plus, 
  Minus,
  CheckCircle2
} from 'lucide-react';
import { getProjects } from '../../services/api';

const DEFAULT_PROPERTIES = [
  {
    id: 'prop-1',
    name: 'GLG Gulshan Heights',
    area: 'Gulshan 2, Dhaka',
    status: 'Available',
    type: 'Luxury Duplex',
    price: '৳3.5 কোটি',
    beds: 4,
    baths: 4,
    sqft: 3450,
    coords: { top: '35%', left: '55%' },
    color: 'var(--primary-coral)',
    image: 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=400&q=80'
  },
  {
    id: 'prop-2',
    name: 'Baridhara Diplomatic Luxe',
    area: 'Baridhara, Dhaka',
    status: 'Available',
    type: 'Exclusive Penthouse',
    price: '৳5.8 কোটি',
    beds: 5,
    baths: 5,
    sqft: 4800,
    coords: { top: '22%', left: '68%' },
    color: 'var(--primary-coral)',
    image: 'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=400&q=80'
  },
  {
    id: 'prop-3',
    name: 'Banani Crest Towers',
    area: 'Banani Block C, Dhaka',
    status: 'Leased',
    type: 'Corporate Suite',
    price: '৳2.2 কোটি',
    beds: 3,
    baths: 3,
    sqft: 2150,
    coords: { top: '48%', left: '42%' },
    color: 'var(--accent-blue)',
    image: 'https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=400&q=80'
  },
  {
    id: 'prop-4',
    name: 'Dhanmondi Lake Oasis',
    area: 'Dhanmondi 8/A, Dhaka',
    status: 'Available',
    type: 'Waterfront Flat',
    price: '৳1.9 কোটি',
    beds: 3,
    baths: 3,
    sqft: 1950,
    coords: { top: '70%', left: '32%' },
    color: 'var(--primary-coral)',
    image: 'https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=400&q=80'
  },
  {
    id: 'prop-5',
    name: 'Uttara Heights Sector 3',
    area: 'Uttara, Dhaka',
    status: 'Sold',
    type: 'Executive Residency',
    price: '৳1.4 কোটি',
    beds: 3,
    baths: 2,
    sqft: 1650,
    coords: { top: '12%', left: '38%' },
    color: 'var(--accent-blue)',
    image: 'https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=400&q=80'
  }
];

export default function PropertyEstateMap() {
  const [properties, setProperties] = useState(DEFAULT_PROPERTIES);
  const [selectedProp, setSelectedProp] = useState(DEFAULT_PROPERTIES[0]);
  const [filterType, setFilterType] = useState('all');
  const [zoomLevel, setZoomLevel] = useState(1);

  useEffect(() => {
    let isMounted = true;
    async function loadMapProjects() {
      try {
        const res = await getProjects();
        const list = Array.isArray(res) ? res : (res?.projects || []);
        if (list.length > 0 && isMounted) {
          const coordsPool = [
            { top: '35%', left: '55%' },
            { top: '22%', left: '68%' },
            { top: '48%', left: '42%' },
            { top: '70%', left: '32%' },
            { top: '12%', left: '38%' },
            { top: '26%', left: '78%' },
            { top: '42%', left: '26%' }
          ];
          const mapped = list.map((p, idx) => {
            const isAvail = p.status !== 'sold' && p.status !== 'leased';
            return {
              id: p.project_id || p.id || `prop-${idx}`,
              name: p.project_name || p.title || p.name || 'GLG Residence',
              area: p.location || 'Dhaka, Bangladesh',
              status: isAvail ? 'Available' : 'Sold/Leased',
              type: p.property_type || 'Luxury Residence',
              price: p.starting_price_bdt ? `৳${(p.starting_price_bdt / 10000000).toFixed(1)} কোটি` : (p.price_range || '৳2.5 কোটি'),
              beds: p.bedrooms || 4,
              baths: p.bathrooms || 3,
              sqft: p.unit_size_sqft || 2800,
              coords: coordsPool[idx % coordsPool.length],
              color: isAvail ? 'var(--primary-coral)' : 'var(--accent-blue)',
              image: p.hero_image || (p.images && p.images[0]) || p.image_url || DEFAULT_PROPERTIES[idx % DEFAULT_PROPERTIES.length].image
            };
          });
          setProperties(mapped);
          setSelectedProp(mapped[0]);
        }
      } catch (e) {
        // Retain default properties
      }
    }
    loadMapProjects();
    return () => { isMounted = false; };
  }, []);

  const filteredProps = properties.filter(p => {
    if (filterType === 'available') return p.status === 'Available';
    if (filterType === 'leased') return p.status !== 'Available';
    return true;
  });

  return (
    <Card
      title="Estate Property Map"
      subtitle="Geographic real-estate inventory distribution in Dhaka"
      action={
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.72rem', fontWeight: 600 }}>
            <span style={{ display: 'inline-block', width: '8px', height: '8px', borderRadius: '50%', background: 'var(--primary-coral)' }} />
            <span style={{ color: 'var(--text-muted)' }}>Available</span>
            <span style={{ display: 'inline-block', width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-blue)', marginLeft: '6px' }} />
            <span style={{ color: 'var(--text-muted)' }}>Leased/Sold</span>
          </div>
        </div>
      }
      style={{ minHeight: '380px' }}
      noPadding
    >
      <div style={{ position: 'relative', width: '100%', height: '315px', overflow: 'hidden', borderRadius: '0 0 16px 16px' }}>
        {/* Map Canvas with Stylized Dhaka Cartography Pattern */}
        <div style={{
          position: 'absolute',
          inset: 0,
          background: 'linear-gradient(135deg, #E2E8F0 0%, #CBD5E1 100%)',
          backgroundImage: `
            radial-gradient(ellipse at 50% 50%, rgba(255,255,255,0.7) 0%, transparent 80%),
            linear-gradient(to right, rgba(203,213,225,0.4) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(203,213,225,0.4) 1px, transparent 1px)
          `,
          backgroundSize: '100% 100%, 28px 28px, 28px 28px',
          transform: `scale(${zoomLevel})`,
          transition: 'transform 0.3s ease'
        }}>
          {/* Stylized River (Hatirjheel / Gulshan Lake) SVG Curve */}
          <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
            <path 
              d="M 50 20 Q 220 80, 260 170 T 380 320" 
              fill="none" 
              stroke="#93C5FD" 
              strokeWidth="24" 
              strokeLinecap="round"
              opacity="0.5"
            />
            <path 
              d="M 180 20 Q 210 120, 160 220 T 200 320" 
              fill="none" 
              stroke="#BFDBFE" 
              strokeWidth="12" 
              strokeLinecap="round"
              opacity="0.6"
            />
          </svg>

          {/* Property Pins */}
          {filteredProps.map((prop) => {
            const isSelected = selectedProp?.id === prop.id;
            return (
              <div
                key={prop.id}
                onClick={() => setSelectedProp(prop)}
                style={{
                  position: 'absolute',
                  top: prop.coords.top,
                  left: prop.coords.left,
                  transform: 'translate(-50%, -50%)',
                  cursor: 'pointer',
                  zIndex: isSelected ? 10 : 5,
                  transition: 'all 0.2s ease'
                }}
              >
                {/* Pin Head */}
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  padding: isSelected ? '5px 10px' : '4px 8px',
                  borderRadius: '20px',
                  background: prop.color,
                  color: '#FFFFFF',
                  boxShadow: isSelected ? '0 0 0 4px rgba(232,101,74,0.3), 0 4px 12px rgba(0,0,0,0.3)' : '0 2px 8px rgba(0,0,0,0.2)',
                  fontSize: '0.72rem',
                  fontWeight: 700,
                  whiteSpace: 'nowrap'
                }}>
                  <MapPin size={12} />
                  <span>{prop.name.split(' ')[1] || prop.name}</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Floating Zoom & Filter Controls */}
        <div style={{
          position: 'absolute',
          top: '12px',
          right: '12px',
          display: 'flex',
          flexDirection: 'column',
          gap: '4px',
          zIndex: 15
        }}>
          <button
            onClick={() => setZoomLevel(prev => Math.min(prev + 0.15, 1.4))}
            className="btn-secondary"
            style={{ width: '28px', height: '28px', padding: 0, justifyContent: 'center' }}
            title="Zoom In"
          >
            <Plus size={14} />
          </button>
          <button
            onClick={() => setZoomLevel(prev => Math.max(prev - 0.15, 0.85))}
            className="btn-secondary"
            style={{ width: '28px', height: '28px', padding: 0, justifyContent: 'center' }}
            title="Zoom Out"
          >
            <Minus size={14} />
          </button>
        </div>

        {/* Floating Selected Property Card Overlay */}
        {selectedProp && (
          <div style={{
            position: 'absolute',
            bottom: '12px',
            left: '12px',
            right: '12px',
            background: 'var(--bg-card)',
            border: '1px solid var(--border-glass)',
            boxShadow: 'var(--shadow-dropdown)',
            borderRadius: '12px',
            padding: '12px',
            display: 'flex',
            alignItems: 'center',
            gap: '14px',
            zIndex: 20
          }}>
            <img 
              src={selectedProp.image} 
              alt={selectedProp.name}
              style={{
                width: '64px',
                height: '64px',
                borderRadius: '8px',
                objectFit: 'cover',
                flexShrink: 0
              }}
            />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h4 style={{ 
                  fontSize: '0.92rem', 
                  fontWeight: 700, 
                  color: 'var(--text-main)', 
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis' 
                }}>
                  {selectedProp.name}
                </h4>
                <Badge variant={selectedProp.status === 'Available' ? 'coral' : 'blue'}>
                  {selectedProp.status}
                </Badge>
              </div>
              <p style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                {selectedProp.area}
              </p>
              
              {/* Specs & Pricing */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginTop: '6px', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                <span style={{ fontWeight: 800, color: 'var(--primary-coral)', fontSize: '0.85rem' }}>
                  {selectedProp.price}
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
                  <Bed size={12} /> {selectedProp.beds} Bed
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
                  <Bath size={12} /> {selectedProp.baths} Bath
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
                  <Maximize2 size={12} /> {selectedProp.sqft} sqft
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}
