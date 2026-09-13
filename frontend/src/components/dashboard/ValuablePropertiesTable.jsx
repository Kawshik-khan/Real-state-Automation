import React, { useState, useEffect } from 'react';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import { ArrowUpRight, Building2 } from 'lucide-react';
import { getProjects } from '../../services/api';

const DEFAULT_SITES = [
  {
    id: 'ts-1',
    rank: 1,
    name: 'GLG Baridhara Diplomatic Luxe',
    location: 'Baridhara Diplomatic, Dhaka',
    valuation: '৳18.5 Cr',
    units: '8 of 12 Available',
    status: 'High Demand',
    badgeVariant: 'coral',
    image: 'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=200&q=80'
  },
  {
    id: 'ts-2',
    rank: 2,
    name: 'GLG Gulshan Heights',
    location: 'Gulshan 2, Dhaka',
    valuation: '৳14.8 Cr',
    units: '4 of 16 Available',
    status: 'Fast Moving',
    badgeVariant: 'emerald',
    image: 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=200&q=80'
  },
  {
    id: 'ts-3',
    rank: 3,
    name: 'Banani Crest Towers',
    location: 'Banani Block C, Dhaka',
    valuation: '৳9.2 Cr',
    units: '3 of 10 Available',
    status: 'Leased 70%',
    badgeVariant: 'blue',
    image: 'https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=200&q=80'
  },
  {
    id: 'ts-4',
    rank: 4,
    name: 'Dhanmondi Lake Oasis',
    location: 'Dhanmondi 8/A, Dhaka',
    valuation: '৳7.6 Cr',
    units: '6 of 14 Available',
    status: 'Under Review',
    badgeVariant: 'amber',
    image: 'https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=200&q=80'
  }
];

export default function ValuablePropertiesTable({ onNavigateProperties, searchQuery = '', selectedProperty = 'all' }) {
  const [sites, setSites] = useState(DEFAULT_SITES);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let isMounted = true;
    async function loadProperties() {
      setLoading(true);
      try {
        const data = await getProjects();
        const projectList = Array.isArray(data) ? data : (data?.projects || []);
        if (projectList.length > 0 && isMounted) {
          const mapped = projectList.map((p, index) => {
            const price = p.starting_price_bdt 
              ? `৳${(p.starting_price_bdt / 10000000).toFixed(1)} Cr`
              : (p.price_range || `৳${10 + index * 2.5} Cr`);
            const statusLabel = p.status === 'ready' 
              ? 'Ready to Move' 
              : (p.status === 'under_construction' ? 'In Progress' : 'High Demand');
            const badgeVariants = ['coral', 'emerald', 'blue', 'amber', 'purple'];
            return {
              id: p.project_id || p.id || `proj-${index}`,
              rank: index + 1,
              name: p.project_name || p.title || p.name || 'GLG Luxury Property',
              location: p.location || 'Dhaka, Bangladesh',
              valuation: price,
              units: `${p.available_units || 4} of ${p.total_units || 12} Available`,
              status: statusLabel,
              badgeVariant: badgeVariants[index % badgeVariants.length],
              image: p.hero_image || (p.images && p.images[0]) || p.image_url || DEFAULT_SITES[index % DEFAULT_SITES.length].image
            };
          });
          setSites(mapped);
        }
      } catch (err) {
        // Fallback to defaults
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadProperties();
    return () => { isMounted = false; };
  }, []);

  const filteredSites = sites.filter(site => {
    const matchesProp = selectedProperty === 'all' || site.name.toLowerCase().includes(selectedProperty.toLowerCase().replace('_', ' '));
    const matchesSearch = !searchQuery.trim() ||
      site.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      site.location.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesProp && matchesSearch;
  });

  return (
    <Card
      title="Most Valuable Properties"
      subtitle="Ranked portfolio assets by market capitalization"
      action={
        <button
          onClick={onNavigateProperties}
          className="btn-secondary"
          style={{ fontSize: '0.74rem', padding: '4px 8px' }}
        >
          View All Sites
        </button>
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {filteredSites.map((site) => (
          <div
            key={site.id}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '12px',
              padding: '8px 10px',
              borderRadius: '10px',
              background: 'var(--bg-card-hover)',
              border: '1px solid var(--border-glass)'
            }}
          >
            {/* Thumbnail + Name */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 0, flex: 1 }}>
              <img
                src={site.image}
                alt={site.name}
                style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '8px',
                  objectFit: 'cover',
                  flexShrink: 0
                }}
              />
              <div style={{ minWidth: 0 }}>
                <h5 style={{
                  fontSize: '0.82rem',
                  fontWeight: 700,
                  color: 'var(--text-main)',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis'
                }}>
                  {site.name}
                </h5>
                <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                  {site.location}
                </p>
              </div>
            </div>

            {/* Valuation & Badge */}
            <div style={{ textAlign: 'right', flexShrink: 0 }}>
              <div style={{ 
                fontSize: '0.86rem', 
                fontWeight: 800, 
                color: 'var(--primary-coral)',
                fontFamily: 'Outfit, sans-serif'
              }}>
                {site.valuation}
              </div>
              <Badge variant={site.badgeVariant} style={{ marginTop: '2px' }}>
                {site.status}
              </Badge>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
