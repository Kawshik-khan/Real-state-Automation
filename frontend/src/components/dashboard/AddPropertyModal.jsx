import React, { useState } from 'react';
import { 
  Building2, 
  MapPin, 
  DollarSign, 
  Bed, 
  Sparkles, 
  Image as ImageIcon, 
  CheckCircle2, 
  Loader2, 
  Compass,
  Layers
} from 'lucide-react';
import { createProject } from '../../services/api';
import { useToast } from '../ui/Toast';
import Modal from '../ui/Modal';
import Button from '../ui/Button';

export const AddPropertyModal = ({ isOpen, onClose, onPropertyAdded }) => {
  const { showToast } = useToast();
  const [submitting, setSubmitting] = useState(false);

  const [formData, setFormData] = useState({
    name: '',
    location: '',
    price: '',
    price_val: '',
    bedrooms: '3',
    status: 'Under Construction',
    lat: '23.7925',
    lng: '90.4078',
    amenities: 'Infinity Pool, Private Elevator, Smart Home Automation, Italian Marble',
    description: '',
    image: 'https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80',
    brochure: '/GLG_Gulshan_Heights_Property_Details.pdf'
  });

  if (!isOpen) return null;

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim() || !formData.location.trim() || !formData.price.trim()) {
      showToast('Please fill in Development Name, Location, and Price.', 'warning');
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        name: formData.name.trim(),
        location: formData.location.trim(),
        price: formData.price.trim(),
        price_val: formData.price_val ? parseInt(formData.price_val, 10) : undefined,
        bedrooms: parseInt(formData.bedrooms, 10) || 3,
        status: formData.status,
        description: formData.description.trim() || `${formData.name.trim()} is a premier luxury residential development located in ${formData.location.trim()}.`,
        features: {
          amenities: formData.amenities.split(',').map((s) => s.trim()).filter(Boolean),
          coordinates: [parseFloat(formData.lat) || 23.7925, parseFloat(formData.lng) || 90.4078],
          image: formData.image.trim(),
          brochure: formData.brochure.trim(),
          floors: 18,
          total_units: 32,
          handover: 'Q4 2026'
        }
      };

      const res = await createProject(payload);
      if (res && res.success) {
        showToast(`🎉 "${formData.name}" added successfully to real estate catalog!`, 'success');
        if (onPropertyAdded) {
          onPropertyAdded(res.project || payload);
        }
        onClose();
      } else {
        showToast(res?.message || 'Failed to create development. Please try again.', 'error');
      }
    } catch (err) {
      console.error('Error creating property development:', err);
      showToast('Error saving development to database.', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Add New Property Development"
      subtitle="Register real estate asset into Supabase database and AI search index"
      icon={<Building2 size={20} color="var(--primary-coral)" />}
      maxWidth="720px"
    >
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {/* Responsive Grid Fields */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '16px'
        }}>
          {/* Development Name */}
          <div>
            <label style={{
              display: 'block',
              fontSize: '0.72rem',
              fontWeight: 700,
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
              color: 'var(--text-muted)',
              marginBottom: '6px'
            }}>
              Development Name *
            </label>
            <div style={{ position: 'relative' }}>
              <Building2 
                size={16} 
                style={{
                  position: 'absolute',
                  left: '12px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'var(--text-dim)',
                  pointerEvents: 'none'
                }} 
              />
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                placeholder="e.g. GLG Gulshan Heights"
                required
                className="glass-input"
                style={{ width: '100%', paddingLeft: '38px', height: '42px' }}
              />
            </div>
          </div>

          {/* Location / Zone */}
          <div>
            <label style={{
              display: 'block',
              fontSize: '0.72rem',
              fontWeight: 700,
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
              color: 'var(--text-muted)',
              marginBottom: '6px'
            }}>
              Location / Zone *
            </label>
            <div style={{ position: 'relative' }}>
              <MapPin 
                size={16} 
                style={{
                  position: 'absolute',
                  left: '12px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'var(--text-dim)',
                  pointerEvents: 'none'
                }} 
              />
              <input
                type="text"
                name="location"
                value={formData.location}
                onChange={handleChange}
                placeholder="e.g. Road 79, Gulshan-2, Dhaka"
                required
                className="glass-input"
                style={{ width: '100%', paddingLeft: '38px', height: '42px' }}
              />
            </div>
          </div>

          {/* Display Price */}
          <div>
            <label style={{
              display: 'block',
              fontSize: '0.72rem',
              fontWeight: 700,
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
              color: 'var(--text-muted)',
              marginBottom: '6px'
            }}>
              Display Price *
            </label>
            <div style={{ position: 'relative' }}>
              <DollarSign 
                size={16} 
                style={{
                  position: 'absolute',
                  left: '12px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'var(--text-dim)',
                  pointerEvents: 'none'
                }} 
              />
              <input
                type="text"
                name="price"
                value={formData.price}
                onChange={handleChange}
                placeholder="e.g. BDT 4.50 Cr - 6.20 Cr"
                required
                className="glass-input"
                style={{ width: '100%', paddingLeft: '38px', height: '42px' }}
              />
            </div>
          </div>

          {/* Bedrooms & Status Dual Dropdowns */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            <div>
              <label style={{
                display: 'block',
                fontSize: '0.72rem',
                fontWeight: 700,
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
                color: 'var(--text-muted)',
                marginBottom: '6px'
              }}>
                Bedrooms
              </label>
              <div style={{ position: 'relative' }}>
                <Bed 
                  size={16} 
                  style={{
                    position: 'absolute',
                    left: '10px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    color: 'var(--text-dim)',
                    pointerEvents: 'none'
                  }} 
                />
                <select
                  name="bedrooms"
                  value={formData.bedrooms}
                  onChange={handleChange}
                  className="glass-input"
                  style={{ width: '100%', paddingLeft: '34px', height: '42px', cursor: 'pointer' }}
                >
                  <option value="1">1 BHK</option>
                  <option value="2">2 BHK</option>
                  <option value="3">3 BHK</option>
                  <option value="4">4 BHK</option>
                  <option value="5">5+ Penthouse</option>
                </select>
              </div>
            </div>

            <div>
              <label style={{
                display: 'block',
                fontSize: '0.72rem',
                fontWeight: 700,
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
                color: 'var(--text-muted)',
                marginBottom: '6px'
              }}>
                Status
              </label>
              <div style={{ position: 'relative' }}>
                <Layers 
                  size={16} 
                  style={{
                    position: 'absolute',
                    left: '10px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    color: 'var(--text-dim)',
                    pointerEvents: 'none'
                  }} 
                />
                <select
                  name="status"
                  value={formData.status}
                  onChange={handleChange}
                  className="glass-input"
                  style={{ width: '100%', paddingLeft: '34px', height: '42px', cursor: 'pointer' }}
                >
                  <option value="Under Construction">Under Construction</option>
                  <option value="Handover Q4 2026">Handover Q4 2026</option>
                  <option value="Ready for Handover">Ready for Handover</option>
                  <option value="Upcoming Launch">Upcoming Launch</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Coordinates (Latitude & Longitude) */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div>
            <label style={{
              display: 'block',
              fontSize: '0.72rem',
              fontWeight: 700,
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
              color: 'var(--text-muted)',
              marginBottom: '6px'
            }}>
              Latitude (Dhaka GPS)
            </label>
            <div style={{ position: 'relative' }}>
              <Compass 
                size={16} 
                style={{
                  position: 'absolute',
                  left: '12px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'var(--text-dim)',
                  pointerEvents: 'none'
                }} 
              />
              <input
                type="text"
                name="lat"
                value={formData.lat}
                onChange={handleChange}
                placeholder="23.7925"
                className="glass-input"
                style={{ width: '100%', paddingLeft: '38px', height: '42px' }}
              />
            </div>
          </div>
          <div>
            <label style={{
              display: 'block',
              fontSize: '0.72rem',
              fontWeight: 700,
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
              color: 'var(--text-muted)',
              marginBottom: '6px'
            }}>
              Longitude (Dhaka GPS)
            </label>
            <div style={{ position: 'relative' }}>
              <Compass 
                size={16} 
                style={{
                  position: 'absolute',
                  left: '12px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'var(--text-dim)',
                  pointerEvents: 'none'
                }} 
              />
              <input
                type="text"
                name="lng"
                value={formData.lng}
                onChange={handleChange}
                placeholder="90.4078"
                className="glass-input"
                style={{ width: '100%', paddingLeft: '38px', height: '42px' }}
              />
            </div>
          </div>
        </div>

        {/* Key Amenities */}
        <div>
          <label style={{
            display: 'block',
            fontSize: '0.72rem',
            fontWeight: 700,
            letterSpacing: '0.04em',
            textTransform: 'uppercase',
            color: 'var(--text-muted)',
            marginBottom: '6px'
          }}>
            Key Amenities (comma separated)
          </label>
          <div style={{ position: 'relative' }}>
            <Sparkles 
              size={16} 
              style={{
                position: 'absolute',
                left: '12px',
                top: '50%',
                transform: 'translateY(-50%)',
                color: 'var(--text-dim)',
                pointerEvents: 'none'
              }} 
            />
            <input
              type="text"
              name="amenities"
              value={formData.amenities}
              onChange={handleChange}
              placeholder="Rooftop Infinity Pool, Private Elevator, Smart Home Automation, Italian Marble"
              className="glass-input"
              style={{ width: '100%', paddingLeft: '38px', height: '42px' }}
            />
          </div>
        </div>

        {/* Feature Image URL */}
        <div>
          <label style={{
            display: 'block',
            fontSize: '0.72rem',
            fontWeight: 700,
            letterSpacing: '0.04em',
            textTransform: 'uppercase',
            color: 'var(--text-muted)',
            marginBottom: '6px'
          }}>
            Feature Image URL
          </label>
          <div style={{ position: 'relative' }}>
            <ImageIcon 
              size={16} 
              style={{
                position: 'absolute',
                left: '12px',
                top: '50%',
                transform: 'translateY(-50%)',
                color: 'var(--text-dim)',
                pointerEvents: 'none'
              }} 
            />
            <input
              type="url"
              name="image"
              value={formData.image}
              onChange={handleChange}
              placeholder="https://images.unsplash.com/..."
              className="glass-input"
              style={{ width: '100%', paddingLeft: '38px', height: '42px' }}
            />
          </div>
        </div>

        {/* Architectural Description & Overview */}
        <div>
          <label style={{
            display: 'block',
            fontSize: '0.72rem',
            fontWeight: 700,
            letterSpacing: '0.04em',
            textTransform: 'uppercase',
            color: 'var(--text-muted)',
            marginBottom: '6px'
          }}>
            Architectural Description &amp; Overview
          </label>
          <textarea
            name="description"
            rows={3}
            value={formData.description}
            onChange={handleChange}
            placeholder="Provide key highlights, floor configurations, view orientation..."
            className="glass-input"
            style={{ width: '100%', padding: '10px 14px', resize: 'vertical', minHeight: '80px' }}
          />
        </div>

        {/* Modal Actions Footer */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'flex-end',
          gap: '12px',
          paddingTop: '16px',
          borderTop: '1px solid var(--border-glass)',
          marginTop: '6px'
        }}>
          <Button
            variant="secondary"
            onClick={onClose}
            disabled={submitting}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="coral"
            disabled={submitting}
            icon={submitting ? <Loader2 size={16} className="spin-anim" /> : <CheckCircle2 size={16} />}
          >
            {submitting ? 'Saving Development...' : 'Publish Development'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};

export default AddPropertyModal;
