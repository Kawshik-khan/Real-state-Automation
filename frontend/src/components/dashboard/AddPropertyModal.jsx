import React, { useState } from 'react';
import { X, Building2, MapPin, DollarSign, Bed, Sparkles, Image, FileText, CheckCircle2, Loader2 } from 'lucide-react';
import { createProject } from '../../services/api';
import { useToast } from '../ui/Toast';

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
    if (!formData.name || !formData.location || !formData.price) {
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
        description: formData.description.trim() || `${formData.name} is a premier luxury residential development located in ${formData.location}.`,
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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-fadeIn">
      <div 
        className="relative w-full max-w-2xl bg-neutral-900/95 border border-white/10 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
        style={{
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7), inset 0 1px 0 rgba(255, 255, 255, 0.1)'
        }}
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-white/[0.02]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
              <Building2 className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white tracking-wide">Add New Property Development</h2>
              <p className="text-xs text-neutral-400">Register real estate asset into Supabase database and AI search index</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-neutral-400 hover:text-white p-2 rounded-lg hover:bg-white/5 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <form onSubmit={handleSubmit} className="p-6 overflow-y-auto space-y-4 flex-1 custom-scrollbar">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Development Name */}
            <div>
              <label className="block text-xs font-semibold text-neutral-300 uppercase tracking-wider mb-1.5">
                Development Name *
              </label>
              <div className="relative">
                <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="e.g. GLG Gulshan Heights"
                  required
                  className="w-full bg-neutral-800/80 border border-white/10 rounded-xl pl-9 pr-3 py-2.5 text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/50"
                />
              </div>
            </div>

            {/* Location */}
            <div>
              <label className="block text-xs font-semibold text-neutral-300 uppercase tracking-wider mb-1.5">
                Location / Zone *
              </label>
              <div className="relative">
                <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />
                <input
                  type="text"
                  name="location"
                  value={formData.location}
                  onChange={handleChange}
                  placeholder="e.g. Road 79, Gulshan-2, Dhaka"
                  required
                  className="w-full bg-neutral-800/80 border border-white/10 rounded-xl pl-9 pr-3 py-2.5 text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/50"
                />
              </div>
            </div>

            {/* Price String */}
            <div>
              <label className="block text-xs font-semibold text-neutral-300 uppercase tracking-wider mb-1.5">
                Display Price *
              </label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />
                <input
                  type="text"
                  name="price"
                  value={formData.price}
                  onChange={handleChange}
                  placeholder="e.g. BDT 4.50 Cr - 6.20 Cr"
                  required
                  className="w-full bg-neutral-800/80 border border-white/10 rounded-xl pl-9 pr-3 py-2.5 text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/50"
                />
              </div>
            </div>

            {/* Bedrooms & Status */}
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-xs font-semibold text-neutral-300 uppercase tracking-wider mb-1.5">
                  Bedrooms
                </label>
                <div className="relative">
                  <Bed className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />
                  <select
                    name="bedrooms"
                    value={formData.bedrooms}
                    onChange={handleChange}
                    className="w-full bg-neutral-800/80 border border-white/10 rounded-xl pl-9 pr-3 py-2.5 text-sm text-white focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/50"
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
                <label className="block text-xs font-semibold text-neutral-300 uppercase tracking-wider mb-1.5">
                  Status
                </label>
                <select
                  name="status"
                  value={formData.status}
                  onChange={handleChange}
                  className="w-full bg-neutral-800/80 border border-white/10 rounded-xl px-3 py-2.5 text-sm text-white focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/50"
                >
                  <option value="Under Construction">Under Construction</option>
                  <option value="Handover Q4 2026">Handover Q4 2026</option>
                  <option value="Ready for Handover">Ready</option>
                  <option value="Upcoming Launch">Upcoming</option>
                </select>
              </div>
            </div>
          </div>

          {/* Coordinates (Latitude & Longitude) */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-neutral-300 uppercase tracking-wider mb-1.5">
                Latitude (Dhaka GPS)
              </label>
              <input
                type="text"
                name="lat"
                value={formData.lat}
                onChange={handleChange}
                placeholder="23.7925"
                className="w-full bg-neutral-800/80 border border-white/10 rounded-xl px-3 py-2 text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-amber-500/50"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-neutral-300 uppercase tracking-wider mb-1.5">
                Longitude (Dhaka GPS)
              </label>
              <input
                type="text"
                name="lng"
                value={formData.lng}
                onChange={handleChange}
                placeholder="90.4078"
                className="w-full bg-neutral-800/80 border border-white/10 rounded-xl px-3 py-2 text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-amber-500/50"
              />
            </div>
          </div>

          {/* Amenities */}
          <div>
            <label className="block text-xs font-semibold text-neutral-300 uppercase tracking-wider mb-1.5">
              Key Amenities (comma separated)
            </label>
            <div className="relative">
              <Sparkles className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />
              <input
                type="text"
                name="amenities"
                value={formData.amenities}
                onChange={handleChange}
                placeholder="Rooftop Pool, Private Gym, Acoustic Glass, 24/7 Security"
                className="w-full bg-neutral-800/80 border border-white/10 rounded-xl pl-9 pr-3 py-2 text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-amber-500/50"
              />
            </div>
          </div>

          {/* Exterior Image URL */}
          <div>
            <label className="block text-xs font-semibold text-neutral-300 uppercase tracking-wider mb-1.5">
              Feature Image URL
            </label>
            <div className="relative">
              <Image className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />
              <input
                type="url"
                name="image"
                value={formData.image}
                onChange={handleChange}
                placeholder="https://..."
                className="w-full bg-neutral-800/80 border border-white/10 rounded-xl pl-9 pr-3 py-2 text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-amber-500/50"
              />
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs font-semibold text-neutral-300 uppercase tracking-wider mb-1.5">
              Architectural Description & Overview
            </label>
            <textarea
              name="description"
              rows={3}
              value={formData.description}
              onChange={handleChange}
              placeholder="Provide key highlights, floor configurations, view orientation..."
              className="w-full bg-neutral-800/80 border border-white/10 rounded-xl p-3 text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-amber-500/50"
            />
          </div>

          {/* Submit Footer */}
          <div className="pt-4 border-t border-white/10 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-neutral-400 hover:text-white hover:bg-white/5 rounded-xl transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="flex items-center gap-2 px-5 py-2.5 text-sm font-semibold text-black bg-gradient-to-r from-amber-400 to-amber-500 hover:from-amber-300 hover:to-amber-400 rounded-xl shadow-lg shadow-amber-500/20 transition-all disabled:opacity-50"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Saving Development...
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4" />
                  Publish Development
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
