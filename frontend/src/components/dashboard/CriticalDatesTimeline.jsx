import React, { useState, useEffect } from 'react';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import Modal from '../ui/Modal';
import { Calendar, Clock, CheckCircle2, AlertCircle, ArrowRight, X } from 'lucide-react';
import { getCalendarMilestones } from '../../services/api';

const DEFAULT_CRITICAL_DATES = [
  {
    id: 'ev-1',
    day: '14',
    month: 'SEP',
    title: 'Site Visit: GLG Gulshan Heights',
    client: 'Tanvir Ahmed (High Intent)',
    time: '3:00 PM - 4:30 PM',
    type: 'Tour',
    status: 'Confirmed',
    badgeVariant: 'emerald'
  },
  {
    id: 'ev-2',
    day: '16',
    month: 'SEP',
    title: 'Contract Handover Review: Luxe Baridhara',
    client: 'Diplomatic Mission Corp',
    time: '11:00 AM',
    type: 'Handover',
    status: 'Upcoming',
    badgeVariant: 'coral'
  },
  {
    id: 'ev-3',
    day: '18',
    month: 'SEP',
    title: 'Installment Milestone 2 Payment',
    client: 'Nusrat Jahan (Apt 8B)',
    time: 'End of Day',
    type: 'Payment',
    status: 'Pending',
    badgeVariant: 'amber'
  },
  {
    id: 'ev-4',
    day: '21',
    month: 'SEP',
    title: 'HITL Booking Escalation Approval',
    client: 'Rahim Chowdhury (Site Visit)',
    time: 'Needs Sales Lead Confirmation',
    type: 'Escalation',
    status: 'Action Required',
    badgeVariant: 'rose'
  }
];

export default function CriticalDatesTimeline() {
  const [dates, setDates] = useState(DEFAULT_CRITICAL_DATES);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    let isMounted = true;
    async function loadMilestones() {
      try {
        const data = await getCalendarMilestones();
        const list = Array.isArray(data) ? data : (data?.milestones || []);
        if (list.length > 0 && isMounted) {
          const parsed = list.map((item) => {
            let d = '15', m = 'SEP';
            if (item.date && item.date.includes(' ')) {
              const parts = item.date.split(' ');
              d = parts[0];
              m = (parts[1] || 'SEP').toUpperCase();
            } else if (item.full_date) {
              const dt = new Date(item.full_date);
              d = String(dt.getDate());
              m = dt.toLocaleString('en-US', { month: 'short' }).toUpperCase();
            }
            return {
              id: item.id || `ms-${Math.random()}`,
              day: d,
              month: m,
              title: item.title,
              client: item.client || item.client_name || 'Valued Client',
              time: item.time || item.time_range || 'All Day',
              type: item.type || item.milestone_type || 'Milestone',
              status: (item.status || 'scheduled').replace('_', ' ').toUpperCase(),
              badgeVariant: item.badgeVariant || (item.status === 'confirmed' ? 'emerald' : 'amber')
            };
          });
          setDates(parsed);
        }
      } catch (e) {
        // Retain default dates
      }
    }
    loadMilestones();
    return () => { isMounted = false; };
  }, []);
  return (
    <Card
      title="Critical Dates & Milestones"
      subtitle="Scheduled site tours, contract renewals & approvals"
      action={
        <button 
          onClick={() => setIsModalOpen(true)}
          className="btn-secondary" 
          style={{ fontSize: '0.74rem', padding: '4px 8px' }}
        >
          View Calendar
        </button>
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {dates.map((item) => (
          <div
            key={item.id}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '10px 12px',
              borderRadius: '10px',
              background: 'var(--bg-card-hover)',
              border: '1px solid var(--border-glass)',
              transition: 'transform 0.15s ease'
            }}
          >
            {/* Date Box */}
            <div style={{
              width: '42px',
              height: '46px',
              borderRadius: '8px',
              background: 'var(--bg-card)',
              border: '1px solid var(--border-glass)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0
            }}>
              <span style={{ fontSize: '0.62rem', fontWeight: 800, color: 'var(--primary-coral)', textTransform: 'uppercase' }}>
                {item.month}
              </span>
              <span style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--text-main)', lineHeight: 1 }}>
                {item.day}
              </span>
            </div>

            {/* Event Details */}
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '6px' }}>
                <h5 style={{ 
                  fontSize: '0.82rem', 
                  fontWeight: 700, 
                  color: 'var(--text-main)',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis'
                }}>
                  {item.title}
                </h5>
                <Badge variant={item.badgeVariant}>
                  {item.status}
                </Badge>
              </div>
              
              <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                {item.client}
              </p>
              
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.68rem', color: 'var(--text-dim)', marginTop: '3px' }}>
                <Clock size={11} />
                <span>{item.time}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Interactive Calendar Modal */}
      {isModalOpen && (
        <Modal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          title="Executive Calendar & Critical Milestones"
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', maxHeight: '65vh', overflowY: 'auto' }}>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Comprehensive operational schedule for client site visits, deed registrations, payment tranches, and unit handovers.
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {dates.map((m) => (
                <div
                  key={`modal-${m.id}`}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '12px 14px',
                    borderRadius: '10px',
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-glass)'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{
                      padding: '8px 12px',
                      borderRadius: '8px',
                      background: 'rgba(232, 101, 74, 0.1)',
                      color: 'var(--primary-coral)',
                      fontWeight: 800,
                      textAlign: 'center'
                    }}>
                      <div style={{ fontSize: '0.7rem' }}>{m.month}</div>
                      <div style={{ fontSize: '1.1rem' }}>{m.day}</div>
                    </div>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-main)' }}>{m.title}</div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Client: {m.client}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: '4px', marginTop: '2px' }}>
                        <Clock size={12} /> {m.time} • Type: {m.type}
                      </div>
                    </div>
                  </div>
                  <Badge variant={m.badgeVariant}>{m.status}</Badge>
                </div>
              ))}
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '8px' }}>
              <button onClick={() => setIsModalOpen(false)} className="btn-primary" style={{ padding: '8px 16px' }}>
                Close Schedule
              </button>
            </div>
          </div>
        </Modal>
      )}
    </Card>
  );
}
