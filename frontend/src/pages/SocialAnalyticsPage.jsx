import React, { useState, useEffect } from 'react';
import { 
  Share2, 
  TrendingUp, 
  Users, 
  DollarSign, 
  Zap, 
  Eye, 
  BarChart3, 
  Filter, 
  Sparkles, 
  RefreshCw, 
  ArrowUpRight, 
  ChevronRight, 
  X, 
  Copy, 
  Check, 
  Layers, 
  Target, 
  Compass, 
  Flame, 
  Video, 
  MessageSquare,
  ShieldCheck,
  CheckCircle2,
  ExternalLink,
  Award,
  Globe,
  Heart,
  Bookmark,
  LayoutGrid,
  List,
  Search,
  MessageCircle,
  BarChart2
} from 'lucide-react';
import { 
  AreaChart, 
  Area, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  PieChart, 
  Pie, 
  Cell 
} from 'recharts';
import { getSocialAnalyticsKPIs, simulateSocialCommentToDm } from '../services/api';
import CustomDropdown from '../components/ui/CustomDropdown';

const ChannelIcon = ({ id, color = '#FFFFFF', size = 16 }) => {
  switch (id) {
    case 'facebook':
      return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill={color}>
          <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
        </svg>
      );
    case 'instagram':
      return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <rect x="2" y="2" width="20" height="20" rx="5" ry="5"/>
          <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/>
          <line x1="17.5" y1="6.5" x2="17.51" y2="6.5"/>
        </svg>
      );
    case 'linkedin':
      return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill={color}>
          <path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.88 8.56a1.68 1.68 0 0 0 1.68-1.68c0-.93-.75-1.69-1.68-1.69a1.69 1.69 0 0 0-1.69 1.69c0 .93.76 1.68 1.69 1.68m1.39 9.94v-8.37H5.5v8.37h2.77z"/>
        </svg>
      );
    case 'youtube':
      return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill={color}>
          <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
        </svg>
      );
    case 'tiktok':
      return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill={color}>
          <path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.24 1.07-.14 1.61.24 1.64 1.82 2.89 3.5 2.77 1.81-.03 3.29-1.52 3.32-3.33.02-3.89 0-7.78.02-11.66-.02-1.92-.01-3.84-.01-5.76z"/>
        </svg>
      );
    case 'whatsapp':
      return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill={color}>
          <path d="M12.031 6.172c-3.181 0-5.767 2.586-5.768 5.766-.001 1.298.38 2.27 1.019 3.287l-.582 2.128 2.182-.573c.978.58 1.911.928 3.145.929 3.178 0 5.767-2.587 5.768-5.766 0-3.18-2.587-5.771-5.764-5.771zm3.392 8.244c-.144.405-.837.774-1.17.824-.312.045-.694.077-2.146-.525-1.724-.716-2.833-2.483-2.918-2.597-.087-.114-.687-.916-.687-1.748 0-.833.435-1.242.59-1.41.155-.168.337-.21.45-.21.112 0 .225.001.324.006.104.005.244-.04.382.292.144.348.491 1.2.534 1.288.043.088.072.19.014.304-.058.115-.087.187-.174.288-.087.102-.183.228-.261.306-.089.088-.182.185-.078.363.104.179.462.763.992 1.236.684.609 1.26.798 1.439.886.179.088.283.076.388-.045.106-.121.453-.528.574-.709.121-.181.242-.151.405-.091.164.06.993.468 1.164.553.171.085.285.128.327.2.042.072.042.418-.102.823z"/>
        </svg>
      );
    case 'telegram':
      return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill={color}>
          <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221l-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.446 1.394c-.14.18-.357.295-.6.295-.002 0-.003 0-.005 0l.213-3.054 5.56-5.022c.24-.213-.054-.334-.373-.121l-6.869 4.326-2.96-.924c-.643-.204-.657-.643.136-.953l11.57-4.458c.538-.196 1.006.128.832.943z"/>
        </svg>
      );
    default:
      return <Video size={size} color={color} />;
  }
};

const PLATFORM_BASELINES = {
  all: {
    impressions: 1420000,
    reach: 980000,
    engagements: 86400,
    leads: 642,
    ad_spend: 9180.0,
    video_views: 380000,
    cost_per_lead: 14.30,
    click_through_rate: '5.8%',
    pipeline_roas: '5.8x',
    pipeline_value_usd: '$53.2M',
    top_format: 'Instagram Reels',
    top_video: 'YouTube 4K Drone'
  },
  facebook: {
    impressions: 567000,
    reach: 420000,
    engagements: 32400,
    leads: 268,
    ad_spend: 3650.0,
    video_views: 85000,
    cost_per_lead: 13.62,
    click_through_rate: '4.6%',
    pipeline_roas: '5.4x',
    pipeline_value_usd: '$19.7M',
    top_format: 'Carousel & Instant Forms',
    top_video: 'Facebook Watch Tours'
  },
  instagram: {
    impressions: 513000,
    reach: 380000,
    engagements: 36800,
    leads: 224,
    ad_spend: 3100.0,
    video_views: 230000,
    cost_per_lead: 13.84,
    click_through_rate: '6.2%',
    pipeline_roas: '6.8x',
    pipeline_value_usd: '$21.1M',
    top_format: 'Reels Video Walkthroughs',
    top_video: 'Instagram Reels & Stories'
  },
  linkedin: {
    impressions: 128250,
    reach: 95000,
    engagements: 7800,
    leads: 78,
    ad_spend: 1450.0,
    video_views: 19200,
    cost_per_lead: 18.59,
    click_through_rate: '3.8%',
    pipeline_roas: '7.2x',
    pipeline_value_usd: '$10.4M',
    top_format: 'Sponsored InMail & Docs',
    top_video: 'Executive Briefings'
  },
  youtube: {
    impressions: 243000,
    reach: 180000,
    engagements: 12400,
    leads: 42,
    ad_spend: 980.0,
    video_views: 109350,
    cost_per_lead: 23.33,
    click_through_rate: '5.1%',
    pipeline_roas: '4.9x',
    pipeline_value_usd: '$4.8M',
    top_format: '4K Drone Walkthroughs',
    top_video: 'YouTube Virtual Tours'
  },
  tiktok: {
    impressions: 189000,
    reach: 140000,
    engagements: 18200,
    leads: 30,
    ad_spend: 0.0,
    video_views: 85050,
    cost_per_lead: 0.0,
    click_through_rate: '7.8%',
    pipeline_roas: 'N/A',
    pipeline_value_usd: '$1.5M',
    top_format: 'Architectural Shorts',
    top_video: 'TikTok & Shorts Walkthroughs'
  }
};

export default function SocialAnalyticsPage() {
  // Filter States
  const [period, setPeriod] = useState('30d');
  const [platform, setPlatform] = useState('all');
  const [campaignType, setCampaignType] = useState('all');
  const [projectId, setProjectId] = useState('all');
  
  // Data State
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  // Right-Side Drawer State
  const [selectedItem, setSelectedItem] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  // Per-Post Filters & Controls
  const [postSearch, setPostSearch] = useState('');
  const [postPlatformFilter, setPostPlatformFilter] = useState('all');
  const [postFormatFilter, setPostFormatFilter] = useState('all');
  const [postSortBy, setPostSortBy] = useState('views');
  const [postViewMode, setPostViewMode] = useState('grid'); // 'grid' | 'table'

  // Comment-to-DM Lead Bridge Simulator State
  const [simPlatform, setSimPlatform] = useState('facebook');
  const [simAuthor, setSimAuthor] = useState('Mahmudur Rahman');
  const [simComment, setSimComment] = useState('Banani 3 BHK flat price koto? Details inbox korun');
  const [simLoading, setSimLoading] = useState(false);
  const [simResult, setSimResult] = useState(null);

  const handleRunSimulator = async () => {
    if (!simComment.trim()) return;
    setSimLoading(true);
    try {
      const res = await simulateSocialCommentToDm({
        platform: simPlatform,
        author_name: simAuthor,
        comment_text: simComment,
      });
      if (res.success) {
        setSimResult(res);
      }
    } catch (err) {
      console.error('Simulation failed:', err);
    } finally {
      setSimLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [period, platform, campaignType, projectId]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await getSocialAnalyticsKPIs({
        period,
        platform,
        campaign_type: campaignType,
        project_id: projectId
      });
      if (res.success) {
        setData(res);
      }
    } catch (err) {
      console.warn('Failed to load social KPIs, using fallback data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDrawer = (item, type = 'metric') => {
    setSelectedItem({ ...item, drawerType: type });
    setDrawerOpen(true);
  };

  const handleCloseDrawer = () => {
    setDrawerOpen(false);
  };

  const handleCopySummary = () => {
    if (!data) return;
    const text = `📊 GLG Assets — Executive Social Media KPI Summary (${period.toUpperCase()})
- Total Impressions: ${data.kpis?.total_impressions?.toLocaleString() || '1,420,000'}
- Social Inquiries / Leads: ${data.kpis?.total_leads_generated || 642} leads (CPL: $${data.kpis?.cost_per_lead || '14.30'})
- Paid Ad Spend & ROAS: $${data.kpis?.total_ad_spend?.toLocaleString() || '9,180'} (${data.kpis?.pipeline_roas || '5.8x'} ROAS)
- Pipeline Value Generated: ${data.kpis?.pipeline_value_usd || '$53.2M'}
- AI Fast Reply Rate: ${data.kpis?.ai_response_rate || '98.4%'} (Avg Response: ${data.kpis?.ai_avg_reply_latency || '2.4s'})
- Video Walkthrough Views: ${data.kpis?.video_views?.toLocaleString() || '380,000'}`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Dynamic Period Multiplier
  const periodMultiplier = {
    '24h': 0.08,
    '7d': 0.3,
    '30d': 1.0,
    '90d': 2.8
  }[period] || 1.0;

  // Selected Platform Baseline
  const baseMetrics = PLATFORM_BASELINES[platform] || PLATFORM_BASELINES.all;

  // Safe dynamic fallback KPI data
  const fallbackKpis = {
    total_impressions: Math.round(baseMetrics.impressions * periodMultiplier),
    total_reach: Math.round(baseMetrics.reach * periodMultiplier),
    total_engagements: Math.round(baseMetrics.engagements * periodMultiplier),
    total_leads_generated: Math.max(1, Math.round(baseMetrics.leads * periodMultiplier)),
    total_ad_spend: Math.round(baseMetrics.ad_spend * periodMultiplier * 100) / 100,
    video_views: Math.round(baseMetrics.video_views * periodMultiplier),
    cost_per_lead: baseMetrics.cost_per_lead,
    click_through_rate: baseMetrics.click_through_rate,
    pipeline_roas: baseMetrics.pipeline_roas,
    pipeline_value_usd: baseMetrics.pipeline_value_usd,
    ai_response_rate: '98.4%',
    ai_avg_reply_latency: '2.4s'
  };

  const kpis = data?.kpis || fallbackKpis;

  const activeTopFormat = baseMetrics.top_format;
  const activeTopVideo = baseMetrics.top_video;
  const highIntentLeads = Math.max(1, Math.round((kpis.total_leads_generated || 10) * 0.08));

  // Fallback Multi-Channel Platform Breakdown
  const FALLBACK_PLATFORMS = [
    {
      id: "facebook",
      name: "Facebook & Meta Ads",
      icon: "facebook",
      color: "#1877F2",
      reach: Math.round(420000 * periodMultiplier),
      engagements: Math.round(32400 * periodMultiplier),
      leads: Math.round(268 * periodMultiplier),
      ad_spend: Math.round(3650 * periodMultiplier),
      cpl: 13.62,
      ctr: "4.6%",
      roas: "5.4x",
      trend: "+18.2%",
      top_ad_format: "Carousel & Instant Forms"
    },
    {
      id: "instagram",
      name: "Instagram & Reels",
      icon: "instagram",
      color: "#E1306C",
      reach: Math.round(380000 * periodMultiplier),
      engagements: Math.round(36800 * periodMultiplier),
      leads: Math.round(224 * periodMultiplier),
      ad_spend: Math.round(3100 * periodMultiplier),
      cpl: 13.84,
      ctr: "6.2%",
      roas: "6.8x",
      trend: "+26.5%",
      top_ad_format: "Reels Video Walkthroughs"
    },
    {
      id: "linkedin",
      name: "LinkedIn B2B & HNIs",
      icon: "linkedin",
      color: "#0A66C2",
      reach: Math.round(95000 * periodMultiplier),
      engagements: Math.round(7800 * periodMultiplier),
      leads: Math.round(78 * periodMultiplier),
      ad_spend: Math.round(1450 * periodMultiplier),
      cpl: 18.59,
      ctr: "3.8%",
      roas: "7.2x",
      trend: "+14.0%",
      top_ad_format: "Sponsored InMail & Document Ads"
    },
    {
      id: "youtube",
      name: "YouTube Virtual Tours",
      icon: "youtube",
      color: "#FF0000",
      reach: Math.round(180000 * periodMultiplier),
      engagements: Math.round(12400 * periodMultiplier),
      leads: Math.round(42 * periodMultiplier),
      ad_spend: Math.round(980 * periodMultiplier),
      cpl: 23.33,
      ctr: "5.1%",
      roas: "4.9x",
      trend: "+31.8%",
      top_ad_format: "4K Drone Walkthroughs"
    },
    {
      id: "tiktok",
      name: "TikTok & Shorts",
      icon: "tiktok",
      color: "#00F2FE",
      reach: Math.round(140000 * periodMultiplier),
      engagements: Math.round(18200 * periodMultiplier),
      leads: Math.round(30 * periodMultiplier),
      ad_spend: 0.0,
      cpl: 0.0,
      ctr: "7.8%",
      roas: "N/A",
      trend: "+45.2%",
      top_ad_format: "Architectural Highlights"
    }
  ];

  // Fallback Live Campaigns
  const FALLBACK_CAMPAIGNS = [
    {
      id: "cmp-gulshan-01",
      name: "GLG Gulshan Heights — Exclusive Launch",
      project: "GLG Gulshan Heights",
      platform: "Instagram & Meta Ads",
      type: "Lead Generation",
      status: "ACTIVE",
      spend: Math.round(3850 * periodMultiplier),
      leads: Math.round(278 * periodMultiplier),
      cpl: "$13.85",
      conv_rate: "21.4%",
      ctr: "5.9%",
      creative: "Penthouse Sky Lounge 3D Tour",
      target_audience: "HNIs, Gulshan Business Owners, Expats (Age 32-55)"
    },
    {
      id: "cmp-baridhara-02",
      name: "Baridhara Luxury Suites — Lake-Facing Reveal",
      project: "Baridhara Luxury Suites",
      platform: "Meta & LinkedIn",
      type: "Virtual Tour / Brand",
      status: "ACTIVE",
      spend: Math.round(2940 * periodMultiplier),
      leads: Math.round(196 * periodMultiplier),
      cpl: "$15.00",
      conv_rate: "18.8%",
      ctr: "4.8%",
      creative: "Sunset Infinity Pool Walkthrough",
      target_audience: "Tech Executives, Corporate Leaders & NRBs"
    },
    {
      id: "cmp-sky-03",
      name: "GLG Sky Tower — 20:80 Payment Scheme",
      project: "GLG Sky Tower",
      platform: "Facebook & WhatsApp",
      type: "Lead Ads",
      status: "OPTIMIZING",
      spend: Math.round(1650 * periodMultiplier),
      leads: Math.round(124 * periodMultiplier),
      cpl: "$13.30",
      conv_rate: "24.2%",
      ctr: "5.4%",
      creative: "Subvention ROI Calculator Video",
      target_audience: "First-time Luxury Buyers, Investors"
    },
    {
      id: "cmp-goa-04",
      name: "Goa Coastal Villas — Vacation Retreat",
      project: "Goa Coastal Villas",
      platform: "YouTube & Instagram",
      type: "Video Walkthrough",
      status: "SCHEDULED",
      spend: Math.round(740 * periodMultiplier),
      leads: Math.round(44 * periodMultiplier),
      cpl: "$16.80",
      conv_rate: "15.6%",
      ctr: "6.1%",
      creative: "Private Beachfront Villa Drone Reel",
      target_audience: "NRI Diaspora, Holiday Home Seekers"
    }
  ];

  const rawPlatforms = data?.platforms?.length ? data.platforms : FALLBACK_PLATFORMS;
  const platforms = platform === 'all' 
    ? rawPlatforms 
    : rawPlatforms.filter(p => p.id?.toLowerCase() === platform.toLowerCase());

  const rawCampaigns = data?.campaigns?.length ? data.campaigns : FALLBACK_CAMPAIGNS;
  const campaigns = rawCampaigns.filter(c => {
    if (projectId !== 'all' && !c.project?.toLowerCase().includes(projectId.toLowerCase()) && !c.id?.toLowerCase().includes(projectId.toLowerCase())) return false;
    if (campaignType !== 'all' && !c.type?.toLowerCase().includes(campaignType.toLowerCase())) return false;
    if (platform !== 'all') {
      const platStr = (c.platform || '').toLowerCase();
      if (platform === 'facebook') return platStr.includes('facebook') || platStr.includes('meta');
      if (platform === 'instagram') return platStr.includes('instagram') || platStr.includes('meta');
      return platStr.includes(platform.toLowerCase());
    }
    return true;
  });

  const timeSeries = data?.time_series || [
    { name: 'Day 1', impressions: Math.round(38000 * periodMultiplier), leads: Math.round(18 * periodMultiplier), spend: Math.round(290 * periodMultiplier) },
    { name: 'Day 2', impressions: Math.round(42000 * periodMultiplier), leads: Math.round(22 * periodMultiplier), spend: Math.round(310 * periodMultiplier) },
    { name: 'Day 3', impressions: Math.round(49000 * periodMultiplier), leads: Math.round(26 * periodMultiplier), spend: Math.round(340 * periodMultiplier) },
    { name: 'Day 4', impressions: Math.round(58000 * periodMultiplier), leads: Math.round(31 * periodMultiplier), spend: Math.round(390 * periodMultiplier) },
    { name: 'Day 5', impressions: Math.round(65000 * periodMultiplier), leads: Math.round(38 * periodMultiplier), spend: Math.round(420 * periodMultiplier) },
    { name: 'Day 6', impressions: Math.round(72000 * periodMultiplier), leads: Math.round(44 * periodMultiplier), spend: Math.round(480 * periodMultiplier) },
    { name: 'Day 7', impressions: Math.round(81000 * periodMultiplier), leads: Math.round(49 * periodMultiplier), spend: Math.round(510 * periodMultiplier) }
  ];

  const aiRecommendations = data?.ai_recommendations || [
    {
      priority: "HIGH",
      title: "Shift 15% Budget to Instagram Reels",
      detail: "Instagram Reels for GLG Gulshan Heights is delivering 6.2% CTR and $13.85 CPL (22% lower than Facebook standard feed ads).",
      impact: "+38 Projected Leads / mo"
    },
    {
      priority: "MEDIUM",
      title: "Scale YouTube 4K Drone Walkthroughs",
      detail: "YouTube viewers watching >60s have an 18.8% site visit booking conversion rate upon contacting via WhatsApp.",
      impact: "+4.9x High-Intent Tour Bookings"
    },
    {
      priority: "HIGH",
      title: "Enable Instant WhatsApp Lead Retargeting",
      detail: "Leads clicking Instagram ads and receiving an immediate AI WhatsApp outreach within 60 seconds show 94% response engagement.",
      impact: "Sub-2.4s AI First Contact"
    }
  ];

  const fallbackPosts = [
    {
      id: "post-fb-01",
      title: "GLG Sky Tower — Penthouse Sunset Walkthrough",
      caption: "Experience panoramic views of Gulshan lake from our signature duplex penthouses. 3,800 sq.ft of pure luxury with private elevators and Italian marble interiors. Book your private viewing today.",
      platform: "facebook",
      format: "Reel / Video",
      project: "GLG Sky Tower",
      published_at: "Yesterday at 6:30 PM",
      views: 84200,
      reach: 68500,
      likes: 4820,
      comments: 342,
      shares: 185,
      saves: 512,
      engagement_rate: "7.4%",
      leads_generated: 28,
      ad_boosted: true,
      ad_spend: 120.0,
      cpl: "$4.28"
    },
    {
      id: "post-ig-02",
      title: "Baridhara Luxury Suites — Infinity Pool Aerial Reel",
      caption: "Your sanctuary in the diplomatic zone. Rooftop temperature-controlled infinity pool overlooking the city skyline. Handover in Q4 2026. Only 4 exclusive units remaining.",
      platform: "instagram",
      format: "Instagram Reel",
      project: "Baridhara Luxury Suites",
      published_at: "2 days ago",
      views: 112400,
      reach: 94200,
      likes: 8940,
      comments: 486,
      shares: 420,
      saves: 1240,
      engagement_rate: "9.8%",
      leads_generated: 42,
      ad_boosted: true,
      ad_spend: 180.0,
      cpl: "$4.28"
    },
    {
      id: "post-yt-03",
      title: "Full 4K Architectural Tour: Banani Crest Smart Homes",
      caption: "Complete interior walkthrough of our 4 BHK show unit with automated climate control, IoT security, and German fitted kitchens. Watch the full episode now.",
      platform: "youtube",
      format: "4K Video Tour",
      project: "Banani Crest Towers",
      published_at: "3 days ago",
      views: 46500,
      reach: 41000,
      likes: 3100,
      comments: 215,
      shares: 310,
      saves: 890,
      engagement_rate: "8.5%",
      leads_generated: 36,
      ad_boosted: false,
      ad_spend: 0.0,
      cpl: "$0.00"
    },
    {
      id: "post-li-04",
      title: "Commercial Real Estate ROI: Dhanmondi Heights Corporate Floor",
      caption: "Why Grade-A commercial spaces in Dhanmondi are yielding 9.4% rental ROI in 2026. Executive briefing for institutional investors and NRI family offices.",
      platform: "linkedin",
      format: "Document / Carousel",
      project: "Dhanmondi Heights",
      published_at: "4 days ago",
      views: 28400,
      reach: 24000,
      likes: 1420,
      comments: 88,
      shares: 76,
      saves: 340,
      engagement_rate: "6.2%",
      leads_generated: 19,
      ad_boosted: true,
      ad_spend: 95.0,
      cpl: "$5.00"
    },
    {
      id: "post-fb-05",
      title: "Uttara Sector 3 Family Residences — 20:80 Payment Scheme",
      caption: "Book your 3 BHK dream home with only 20% down payment and 0% interest EMI until handover. Close to top international schools and airport expressway.",
      platform: "facebook",
      format: "Carousel Post",
      project: "Uttara Sector 3 Heights",
      published_at: "5 days ago",
      views: 62000,
      reach: 51200,
      likes: 3450,
      comments: 278,
      shares: 142,
      saves: 410,
      engagement_rate: "7.1%",
      leads_generated: 31,
      ad_boosted: true,
      ad_spend: 110.0,
      cpl: "$3.54"
    },
    {
      id: "post-ig-06",
      title: "Architectural Spotlight: Master Bedroom Suite Design",
      caption: "Walk-in wardrobes, double-glazed soundproof acoustic glass, and ambient circadian lighting in our Baridhara penthouses. Modern living redefined.",
      platform: "instagram",
      format: "Photo Gallery",
      project: "Baridhara Luxury Suites",
      published_at: "6 days ago",
      views: 48900,
      reach: 39800,
      likes: 4120,
      comments: 164,
      shares: 98,
      saves: 680,
      engagement_rate: "8.8%",
      leads_generated: 14,
      ad_boosted: false,
      ad_spend: 0.0,
      cpl: "$0.00"
    }
  ];

  const posts = (data?.posts || fallbackPosts).map(p => ({
    ...p,
    views: Math.round((p.views || 0) * (data?.posts ? 1 : periodMultiplier)),
    reach: Math.round((p.reach || 0) * (data?.posts ? 1 : periodMultiplier)),
    likes: Math.round((p.likes || 0) * (data?.posts ? 1 : periodMultiplier)),
    comments: Math.round((p.comments || 0) * (data?.posts ? 1 : periodMultiplier)),
    shares: Math.round((p.shares || 0) * (data?.posts ? 1 : periodMultiplier)),
    saves: Math.round((p.saves || 0) * (data?.posts ? 1 : periodMultiplier)),
    leads_generated: Math.max(1, Math.round((p.leads_generated || 0) * (data?.posts ? 1 : periodMultiplier))),
    ad_spend: Math.round((p.ad_spend || 0) * (data?.posts ? 1 : periodMultiplier) * 100) / 100
  })).filter(p => {
    if (platform !== 'all' && !data?.posts) {
      if (platform === 'facebook' && p.platform !== 'facebook') return false;
      if (platform === 'instagram' && p.platform !== 'instagram') return false;
      if (platform === 'linkedin' && p.platform !== 'linkedin') return false;
      if (platform === 'youtube' && p.platform !== 'youtube') return false;
      if (platform === 'tiktok' && p.platform !== 'tiktok') return false;
    }
    return true;
  });

  const filteredPosts = posts
    .filter(p => {
      if (postPlatformFilter !== 'all' && p.platform !== postPlatformFilter) return false;
      if (postFormatFilter !== 'all') {
        const fmt = p.format.toLowerCase();
        if (postFormatFilter === 'video' && !fmt.includes('reel') && !fmt.includes('video') && !fmt.includes('tour')) return false;
        if (postFormatFilter === 'carousel' && !fmt.includes('carousel') && !fmt.includes('document')) return false;
        if (postFormatFilter === 'image' && !fmt.includes('photo') && !fmt.includes('image') && !fmt.includes('gallery')) return false;
      }
      if (postSearch.trim()) {
        const q = postSearch.toLowerCase();
        const matchTitle = p.title?.toLowerCase().includes(q);
        const matchCaption = p.caption?.toLowerCase().includes(q);
        const matchProject = p.project?.toLowerCase().includes(q);
        if (!matchTitle && !matchCaption && !matchProject) return false;
      }
      return true;
    })
    .sort((a, b) => {
      if (postSortBy === 'views') return (b.views || 0) - (a.views || 0);
      if (postSortBy === 'er') return parseFloat(b.engagement_rate) - parseFloat(a.engagement_rate);
      if (postSortBy === 'likes') return (b.likes || 0) - (a.likes || 0);
      if (postSortBy === 'comments') return (b.comments || 0) - (a.comments || 0);
      if (postSortBy === 'shares') return (b.shares || 0) - (a.shares || 0);
      if (postSortBy === 'leads') return (b.leads_generated || 0) - (a.leads_generated || 0);
      return 0;
    });

  const platformOptions = [
    { value: 'all', label: 'All Channels', icon: <Globe size={13} color="var(--text-muted)" /> },
    { value: 'facebook', label: 'Facebook & Meta Ads', icon: <ChannelIcon id="facebook" color="#1877F2" size={13} /> },
    { value: 'instagram', label: 'Instagram & Reels', icon: <ChannelIcon id="instagram" color="#E1306C" size={13} /> },
    { value: 'linkedin', label: 'LinkedIn B2B', icon: <ChannelIcon id="linkedin" color="#0A66C2" size={13} /> },
    { value: 'youtube', label: 'YouTube Walkthroughs', icon: <ChannelIcon id="youtube" color="#FF0000" size={13} /> },
    { value: 'tiktok', label: 'TikTok & Shorts', icon: <ChannelIcon id="tiktok" color="#00F2FE" size={13} /> },
  ];

  const campaignTypeOptions = [
    { value: 'all', label: 'All Campaign Types', icon: <Target size={13} color="var(--accent-coral)" /> },
    { value: 'lead_gen', label: 'Direct Lead Generation', icon: <Zap size={13} color="#059669" /> },
    { value: 'brand', label: 'Brand Awareness & Launch', icon: <Sparkles size={13} color="#8B5CF6" /> },
    { value: 'video_walkthrough', label: 'Virtual Video Walkthroughs', icon: <Video size={13} color="#9333EA" /> },
    { value: 'payment_scheme', label: 'Subvention & Pricing Ads', icon: <DollarSign size={13} color="#D97706" /> },
  ];

  const projectFilterOptions = [
    { value: 'all', label: 'All Projects', icon: <Layers size={13} color="var(--accent-coral)" /> },
    { value: 'gulshan_heights', label: 'GLG Gulshan Heights', icon: <Award size={13} color="#3B82F6" /> },
    { value: 'bandra_luxury', label: 'Bandra Luxury Suites', icon: <Award size={13} color="#E11D48" /> },
    { value: 'sky_tower', label: 'GLG Sky Tower', icon: <Award size={13} color="#7C3AED" /> },
    { value: 'goa_villas', label: 'Goa Coastal Villas', icon: <Award size={13} color="#10B981" /> },
  ];

  const postFormatOptions = [
    { value: 'all', label: 'All Formats' },
    { value: 'video', label: 'Videos & Reels' },
    { value: 'carousel', label: 'Carousels & Docs' },
    { value: 'image', label: 'Images & Photos' }
  ];

  const postSortOptions = [
    { value: 'views', label: 'Sort: Most Views' },
    { value: 'er', label: 'Sort: Highest ER %' },
    { value: 'likes', label: 'Sort: Most Likes' },
    { value: 'comments', label: 'Sort: Most Comments' },
    { value: 'shares', label: 'Sort: Most Shares' },
    { value: 'leads', label: 'Sort: Most Inbound Leads' }
  ];

  const simPlatformOptions = [
    { value: 'facebook', label: 'Facebook Page Post / Ad', icon: <ChannelIcon id="facebook" color="#1877F2" size={13} /> },
    { value: 'instagram', label: 'Instagram Business Post / Reel', icon: <ChannelIcon id="instagram" color="#E1306C" size={13} /> }
  ];

  // Dynamic Granular Channel Breakdown Calculator for every specific metric
  const getMetricBreakdown = (metricKey) => {
    switch (metricKey) {
      case 'impressions':
        return [
          { id: 'facebook', name: 'Facebook & Meta Ads', color: '#1877F2', value: '540,000', raw: 540000, pct: '38.0%', sub: 'Feed Ads, Carousel & Sponsored Posts', barPct: 38 },
          { id: 'instagram', name: 'Instagram & Reels', color: '#E1306C', value: '480,000', raw: 480000, pct: '33.8%', sub: 'Reels Video & Luxury Showcase Stories', barPct: 34 },
          { id: 'youtube', name: 'YouTube Virtual Tours', color: '#FF0000', value: '210,000', raw: 210000, pct: '14.8%', sub: '4K Drone Architecture Walkthroughs', barPct: 15 },
          { id: 'tiktok', name: 'TikTok & Shorts', color: '#00F2FE', value: '120,000', raw: 120000, pct: '8.5%', sub: 'Architectural Shorts & Lifestyle Reels', barPct: 9 },
          { id: 'linkedin', name: 'LinkedIn B2B', color: '#0A66C2', value: '70,000', raw: 70000, pct: '4.9%', sub: 'Executive InMail & NRI Investor Feeds', barPct: 5 },
        ];
      case 'engagement':
        return [
          { id: 'instagram', name: 'Instagram & Reels', color: '#E1306C', value: '36,800', raw: 36800, pct: '42.6%', sub: '6.2% CTR (Highest Engagement Channel)', barPct: 43 },
          { id: 'facebook', name: 'Facebook & Meta Ads', color: '#1877F2', value: '32,400', raw: 32400, pct: '37.5%', sub: '4.6% CTR (Lead Form Clicks & Shares)', barPct: 38 },
          { id: 'tiktok', name: 'TikTok & Shorts', color: '#00F2FE', value: '18,200', raw: 18200, pct: '7.8%', sub: '7.8% Organic Engagement & Comments', barPct: 21 },
          { id: 'youtube', name: 'YouTube Virtual Tours', color: '#FF0000', value: '12,400', raw: 12400, pct: '5.1%', sub: '5.1% CTR & Extended Watch Time', barPct: 14 },
          { id: 'linkedin', name: 'LinkedIn B2B', color: '#0A66C2', value: '7,800', raw: 7800, pct: '3.8%', sub: '3.8% CTR (High-Net-Worth Inquiries)', barPct: 9 },
        ];
      case 'leads':
        return [
          { id: 'facebook', name: 'Facebook & Meta Ads', color: '#1877F2', value: '268 Leads', raw: 268, pct: '41.7%', sub: '$13.62 CPL (Instant Lead Forms & Sync)', barPct: 42 },
          { id: 'instagram', name: 'Instagram & Reels', color: '#E1306C', value: '224 Leads', raw: 224, pct: '34.9%', sub: '$13.84 CPL (Direct WhatsApp Chat Ads)', barPct: 35 },
          { id: 'linkedin', name: 'LinkedIn B2B', color: '#0A66C2', value: '78 Leads', raw: 78, pct: '12.1%', sub: '$18.59 CPL (High Ticket Investors)', barPct: 12 },
          { id: 'youtube', name: 'YouTube Virtual Tours', color: '#FF0000', value: '42 Leads', raw: 42, pct: '6.5%', sub: '$23.33 CPL (VIP Site Visit Bookings)', barPct: 7 },
          { id: 'tiktok', name: 'TikTok & Shorts', color: '#00F2FE', value: '30 Leads', raw: 30, pct: '4.7%', sub: '$0.00 CPL (100% Organic Direct Leads)', barPct: 5 },
        ];
      case 'spend':
        return [
          { id: 'facebook', name: 'Facebook & Meta Ads', color: '#1877F2', value: '$3,650', raw: 3650, pct: '39.8%', sub: '5.4x Pipeline ROAS ($21.2M Generated)', barPct: 40 },
          { id: 'instagram', name: 'Instagram & Reels', color: '#E1306C', value: '$3,100', raw: 3100, pct: '33.8%', sub: '6.8x Pipeline ROAS (Top Efficiency)', barPct: 34 },
          { id: 'linkedin', name: 'LinkedIn B2B', color: '#0A66C2', value: '$1,450', raw: 1450, pct: '15.8%', sub: '7.2x HNI Deal Size ROAS ($14.5M)', barPct: 16 },
          { id: 'youtube', name: 'YouTube Virtual Tours', color: '#FF0000', value: '$980', raw: 980, pct: '10.7%', sub: '4.9x ROAS ($4.8M Direct Pipeline)', barPct: 11 },
          { id: 'tiktok', name: 'TikTok & Shorts', color: '#00F2FE', value: '$0', raw: 0, pct: '0.0%', sub: 'Free Organic Channel Distribution', barPct: 0 },
        ];
      case 'ai_sla':
        return [
          { id: 'whatsapp', name: 'WhatsApp Lead Gateway', color: '#25D366', value: '99.2% Auto-Reply', raw: 99.2, pct: '1.8s', sub: '1.8s Avg Latency (340 Inquiries Handled)', barPct: 99 },
          { id: 'facebook', name: 'Facebook Messenger AI', color: '#1877F2', value: '98.1% Auto-Reply', raw: 98.1, pct: '2.4s', sub: '2.4s Avg Latency (186 Inquiries Handled)', barPct: 98 },
          { id: 'instagram', name: 'Instagram Direct AI', color: '#E1306C', value: '97.8% Auto-Reply', raw: 97.8, pct: '2.6s', sub: '2.6s Avg Latency (142 Inquiries Handled)', barPct: 98 },
          { id: 'telegram', name: 'Telegram Bot Assistant', color: '#229ED9', value: '99.6% Auto-Reply', raw: 99.6, pct: '1.2s', sub: '1.2s Avg Latency (98 Inquiries Handled)', barPct: 100 },
        ];
      case 'video_views':
        return [
          { id: 'youtube', name: 'YouTube 4K Virtual Tours', color: '#FF0000', value: '180,000 Views', raw: 180000, pct: '47.4%', sub: '72% Avg Watch Completion Rate', barPct: 47 },
          { id: 'instagram', name: 'Instagram Reels & Stories', color: '#E1306C', value: '120,000 Views', raw: 120000, pct: '31.6%', sub: '64% Watch Completion Rate', barPct: 32 },
          { id: 'tiktok', name: 'TikTok & Shorts Walkthroughs', color: '#00F2FE', value: '65,000 Views', raw: 65000, pct: '17.1%', sub: '58% Watch Completion Rate', barPct: 17 },
          { id: 'facebook', name: 'Facebook Watch & Video Ads', color: '#1877F2', value: '15,000 Views', raw: 15000, pct: '3.9%', sub: '48% Watch Completion Rate', barPct: 4 },
        ];
      default:
        return [];
    }
  };

  return (
    <div style={{ padding: '24px 32px', display: 'flex', flexDirection: 'column', gap: '24px', position: 'relative' }}>
      
      {/* ── Top Header & Multi-Dimensional Filter Bar ── */}
      <div className="glass-card" style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: '16px', position: 'relative', zIndex: 30 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: 'linear-gradient(135deg, var(--accent-coral), #8B5CF6)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 4px 12px rgba(232, 101, 74, 0.25)' }}>
                <Share2 size={20} color="#FFFFFF" />
              </div>
              <div>
                <h1 style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em', margin: 0 }}>
                  Social Media KPI & Campaign Command Center
                </h1>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: 0 }}>
                  Admin Executive Multi-Channel Attribution, Ad Spend, ROAS & Lead Funnels
                </p>
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <button
              onClick={fetchData}
              disabled={loading}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 14px',
                borderRadius: '8px',
                background: 'var(--bg-glass)',
                border: '1px solid var(--border-glass)',
                color: 'var(--text-main)',
                fontSize: '0.8rem',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
              <span>Refresh</span>
            </button>

            <button
              onClick={handleCopySummary}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 16px',
                borderRadius: '8px',
                background: 'linear-gradient(135deg, var(--accent-coral), #D95338)',
                border: 'none',
                color: '#FFFFFF',
                fontSize: '0.8rem',
                fontWeight: 700,
                cursor: 'pointer',
                boxShadow: '0 4px 14px rgba(232, 101, 74, 0.35)'
              }}
            >
              {copied ? <Check size={14} /> : <Copy size={14} />}
              <span>{copied ? 'Copied Summary!' : 'Export KPI Summary'}</span>
            </button>
          </div>
        </div>

        {/* ── Multi-Filter Control Strip ── */}
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between', 
          flexWrap: 'wrap', 
          gap: '12px', 
          paddingTop: '12px', 
          borderTop: '1px solid var(--border-glass)',
          position: 'relative',
          zIndex: 35
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-muted)', fontSize: '0.78rem', fontWeight: 600 }}>
              <Filter size={14} color="var(--accent-coral)" />
              <span>Filters:</span>
            </div>

            {/* Period Filter */}
            <div style={{ display: 'flex', background: 'var(--bg-main)', padding: '2px', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
              {[
                { id: '24h', label: '24h' },
                { id: '7d', label: '7 Days' },
                { id: '30d', label: '30 Days' },
                { id: '90d', label: 'Quarterly' }
              ].map(p => (
                <button
                  key={p.id}
                  onClick={() => setPeriod(p.id)}
                  style={{
                    padding: '4px 10px',
                    borderRadius: '6px',
                    border: 'none',
                    background: period === p.id ? 'var(--accent-coral)' : 'transparent',
                    color: period === p.id ? '#FFFFFF' : 'var(--text-muted)',
                    fontSize: '0.74rem',
                    fontWeight: 700,
                    cursor: 'pointer'
                  }}
                >
                  {p.label}
                </button>
              ))}
            </div>

            {/* Platform Filter */}
            <CustomDropdown
              value={platform}
              onChange={setPlatform}
              options={platformOptions}
              minWidth="180px"
              ariaLabel="Filter by Platform"
            />

            {/* Campaign Type Filter */}
            <CustomDropdown
              value={campaignType}
              onChange={setCampaignType}
              options={campaignTypeOptions}
              minWidth="190px"
              ariaLabel="Filter by Campaign Type"
            />

            {/* Project Filter */}
            <CustomDropdown
              value={projectId}
              onChange={setProjectId}
              options={projectFilterOptions}
              minWidth="180px"
              ariaLabel="Filter by Project"
            />
          </div>

          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
            <span>Auto-synced with Meta Graph API & Ad Accounts</span>
          </div>
        </div>
      </div>

      {/* ── 6 Top Executive KPI Ribbon ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px' }}>
        
        {/* Card 1: Total Reach */}
        <div 
          onClick={() => handleOpenDrawer({
            title: 'Social Reach & Impressions',
            primaryValue: (kpis.total_impressions ?? 1420000).toLocaleString(),
            subValue: `${(kpis.total_reach ?? 980000).toLocaleString()} Unique Reach`,
            growth: '+22.4%',
            category: 'Reach & Visibility',
            metricKey: 'impressions',
            metricLabel: 'Total Social Impressions',
            description: 'Cumulative impressions across Meta Ads, Instagram Reels, LinkedIn and YouTube video campaigns.',
            timeSeries: timeSeries
          }, 'metric')}
          className="glass-card clickable-card"
          style={{ padding: '18px 20px', display: 'flex', flexDirection: 'column', gap: '10px', cursor: 'pointer', transition: 'all 0.2s ease', position: 'relative', overflow: 'hidden' }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600 }}>Total Social Impressions</span>
            <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'rgba(56, 189, 248, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Eye size={16} color="#0284C7" />
            </div>
          </div>
          <div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>
              {(kpis.total_impressions ?? 1420000).toLocaleString()}
            </div>
            <div style={{ fontSize: '0.75rem', color: '#059669', display: 'flex', alignItems: 'center', gap: '4px', marginTop: '2px', fontWeight: 600 }}>
              <TrendingUp size={12} />
              <span>+22.4% vs previous period</span>
            </div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '8px', borderTop: '1px solid var(--border-glass)' }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Reach: {(kpis.total_reach ?? 980000).toLocaleString()}</span>
            <span style={{ fontSize: '0.72rem', color: '#0284C7', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '2px' }}>
              Inspect <ChevronRight size={12} />
            </span>
          </div>
        </div>

        {/* Card 2: Engagement Rate */}
        <div 
          onClick={() => handleOpenDrawer({
            title: 'Social Engagement & CTR',
            primaryValue: (kpis.total_engagements ?? 86400).toLocaleString(),
            subValue: `${kpis.click_through_rate || '5.8%'} Click-Through Rate`,
            growth: '+18.6%',
            category: 'Engagement & Clicks',
            metricKey: 'engagement',
            metricLabel: 'Total Social Engagements',
            description: 'Combined post likes, shares, direct message inquiries, and ad click interactions.',
            timeSeries: timeSeries
          }, 'metric')}
          className="glass-card clickable-card"
          style={{ padding: '18px 20px', display: 'flex', flexDirection: 'column', gap: '10px', cursor: 'pointer', transition: 'all 0.2s ease' }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600 }}>Engagement & CTR</span>
            <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'rgba(236, 72, 153, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Flame size={16} color="#DB2777" />
            </div>
          </div>
          <div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>
              {(kpis.total_engagements ?? 86400).toLocaleString()}
            </div>
            <div style={{ fontSize: '0.75rem', color: '#059669', display: 'flex', alignItems: 'center', gap: '4px', marginTop: '2px', fontWeight: 600 }}>
              <TrendingUp size={12} />
              <span>{kpis.click_through_rate || '5.8%'} Avg CTR across channels</span>
            </div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '8px', borderTop: '1px solid var(--border-glass)' }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Top: {activeTopFormat}</span>
            <span style={{ fontSize: '0.72rem', color: '#DB2777', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '2px' }}>
              Inspect <ChevronRight size={12} />
            </span>
          </div>
        </div>

        {/* Card 3: Social Leads */}
        <div 
          onClick={() => handleOpenDrawer({
            title: 'Social Lead Inquiries Generated',
            primaryValue: `${kpis.total_leads_generated ?? 642} Verified Leads`,
            subValue: `$${kpis.cost_per_lead ?? '14.30'} Cost Per Lead (CPL)`,
            growth: '+34.2%',
            category: 'Lead Attribution',
            metricKey: 'leads',
            metricLabel: 'Total Leads Generated',
            description: 'Direct instant form submissions, WhatsApp click-to-chat triggers, and brochure download captures.',
            timeSeries: timeSeries
          }, 'metric')}
          className="glass-card clickable-card"
          style={{ padding: '18px 20px', display: 'flex', flexDirection: 'column', gap: '10px', cursor: 'pointer', transition: 'all 0.2s ease', border: '1px solid rgba(139, 92, 246, 0.35)' }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.78rem', color: '#7C3AED', fontWeight: 700 }}>Social Inquiries & Leads</span>
            <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'rgba(139, 92, 246, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Target size={16} color="#7C3AED" />
            </div>
          </div>
          <div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>
              {kpis.total_leads_generated ?? 642}
            </div>
            <div style={{ fontSize: '0.75rem', color: '#059669', display: 'flex', alignItems: 'center', gap: '4px', marginTop: '2px', fontWeight: 600 }}>
              <TrendingUp size={12} />
              <span>Avg CPL: ${kpis.cost_per_lead ?? '14.30'} (-18% lower)</span>
            </div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '8px', borderTop: '1px solid var(--border-glass)' }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{highIntentLeads} High-Intent Leads</span>
            <span style={{ fontSize: '0.72rem', color: '#7C3AED', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '2px' }}>
              Inspect <ChevronRight size={12} />
            </span>
          </div>
        </div>

        {/* Card 4: Ad Spend & ROAS */}
        <div 
          onClick={() => handleOpenDrawer({
            title: 'Ad Spend, Pipeline & ROAS',
            primaryValue: `$${(kpis.total_ad_spend ?? 9180).toLocaleString()}`,
            subValue: `${kpis.pipeline_roas || '5.8x'} ROAS (${kpis.pipeline_value_usd || '$53.2M'} Pipeline)`,
            growth: '5.8x ROAS',
            category: 'Ad Spend & Revenue',
            metricKey: 'spend',
            metricLabel: 'Total Ad Spend & Pipeline ROAS',
            description: 'Paid campaign ad budget allocation across Meta Ads Manager, LinkedIn Campaign Manager, and YouTube.',
            timeSeries: timeSeries
          }, 'metric')}
          className="glass-card clickable-card"
          style={{ padding: '18px 20px', display: 'flex', flexDirection: 'column', gap: '10px', cursor: 'pointer', transition: 'all 0.2s ease' }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600 }}>Ad Spend & Pipeline Value</span>
            <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <DollarSign size={16} color="#059669" />
            </div>
          </div>
          <div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>
              ${(kpis.total_ad_spend ?? 9180).toLocaleString()}
            </div>
            <div style={{ fontSize: '0.75rem', color: '#059669', display: 'flex', alignItems: 'center', gap: '4px', marginTop: '2px', fontWeight: 600 }}>
              <Award size={12} />
              <span>{kpis.pipeline_roas || '5.8x'} Pipeline ROAS ({kpis.pipeline_value_usd || '$53.2M'})</span>
            </div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '8px', borderTop: '1px solid var(--border-glass)' }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Target ROAS: 4.5x</span>
            <span style={{ fontSize: '0.72rem', color: '#059669', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '2px' }}>
              Inspect <ChevronRight size={12} />
            </span>
          </div>
        </div>

        {/* Card 5: AI Social Reply SLA */}
        <div 
          onClick={() => handleOpenDrawer({
            title: 'AI Fast Social Response SLA',
            primaryValue: kpis.ai_response_rate || '98.4%',
            subValue: `Avg Response Time: ${kpis.ai_avg_reply_latency || '2.4s'}`,
            growth: '98.4% Auto-Replied',
            category: 'AI Operational Speed',
            metricKey: 'ai_sla',
            metricLabel: 'AI Automated Fast Reply SLA',
            description: 'Real-time AI lead qualification, instant property brochure dispatch, and tour scheduling via multi-channel bots.',
            timeSeries: timeSeries
          }, 'metric')}
          className="glass-card clickable-card"
          style={{ padding: '18px 20px', display: 'flex', flexDirection: 'column', gap: '10px', cursor: 'pointer', transition: 'all 0.2s ease' }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600 }}>AI Fast Reply SLA</span>
            <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'rgba(245, 158, 11, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Zap size={16} color="#D97706" />
            </div>
          </div>
          <div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>
              {kpis.ai_response_rate || '98.4%'}
            </div>
            <div style={{ fontSize: '0.75rem', color: '#0284C7', display: 'flex', alignItems: 'center', gap: '4px', marginTop: '2px', fontWeight: 600 }}>
              <Sparkles size={12} />
              <span>Avg Latency: {kpis.ai_avg_reply_latency || '2.4s'}</span>
            </div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '8px', borderTop: '1px solid var(--border-glass)' }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>0 Missed Inquiries</span>
            <span style={{ fontSize: '0.72rem', color: '#D97706', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '2px' }}>
              Inspect <ChevronRight size={12} />
            </span>
          </div>
        </div>

        {/* Card 6: Video Walkthrough Views */}
        <div 
          onClick={() => handleOpenDrawer({
            title: 'Virtual Tours & Video Walkthroughs',
            primaryValue: (kpis.video_views ?? 380000).toLocaleString(),
            subValue: '68% Avg Watch Completion Rate',
            growth: '+38.4%',
            category: 'Video Intelligence',
            metricKey: 'video_views',
            metricLabel: 'Total Video Walkthrough Views',
            description: '4K drone architectural reels, penthouse walkthroughs, and 3D floorplan exploration video views.',
            timeSeries: timeSeries
          }, 'metric')}
          className="glass-card clickable-card"
          style={{ padding: '18px 20px', display: 'flex', flexDirection: 'column', gap: '10px', cursor: 'pointer', transition: 'all 0.2s ease' }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600 }}>Virtual Tour Views</span>
            <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'rgba(168, 85, 247, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Video size={16} color="#9333EA" />
            </div>
          </div>
          <div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>
              {(kpis.video_views ?? 380000).toLocaleString()}
            </div>
            <div style={{ fontSize: '0.75rem', color: '#059669', display: 'flex', alignItems: 'center', gap: '4px', marginTop: '2px', fontWeight: 600 }}>
              <TrendingUp size={12} />
              <span>+38% Watch completion rate</span>
            </div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '8px', borderTop: '1px solid var(--border-glass)' }}>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Top: {activeTopVideo}</span>
            <span style={{ fontSize: '0.72rem', color: '#9333EA', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '2px' }}>
              Inspect <ChevronRight size={12} />
            </span>
          </div>
        </div>

      </div>

      {/* ── Multi-Channel Platform Performance Grid ── */}
      <div className="glass-card" style={{ padding: '22px 24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-main)', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Layers size={18} color="var(--accent-coral)" /> Platform Breakdown & Channel Attribution
            </h2>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', margin: '2px 0 0 0' }}>
              Click any channel card to inspect granular ad formats, creative assets, and lead conversion velocity
            </p>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px' }}>
          {platforms.map((p) => (
            <div
              key={p.id}
              onClick={() => handleOpenDrawer(p, 'platform')}
              style={{
                padding: '16px',
                borderRadius: '10px',
                background: 'var(--bg-glass)',
                border: '1px solid var(--border-glass)',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
              className="clickable-card"
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div style={{ width: '28px', height: '28px', borderRadius: '6px', background: `${p.color}22`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <ChannelIcon id={p.id} color={p.color} size={16} />
                  </div>
                  <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-main)' }}>{p.name}</span>
                </div>
                <span style={{ fontSize: '0.72rem', color: '#059669', fontWeight: 700 }}>{p.trend}</span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                <div style={{ padding: '8px', borderRadius: '6px', background: 'var(--bg-main)' }}>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Leads</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-main)' }}>{p.leads}</div>
                </div>
                <div style={{ padding: '8px', borderRadius: '6px', background: 'var(--bg-main)' }}>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>CPL</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#0284C7' }}>${p.cpl}</div>
                </div>
              </div>

              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between', borderTop: '1px solid var(--border-glass)', paddingTop: '8px' }}>
                <span>ROAS: <strong style={{ color: '#059669' }}>{p.roas}</strong></span>
                <span>CTR: <strong style={{ color: 'var(--text-main)' }}>{p.ctr}</strong></span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Per-Post Social Engagement & Views Performance ── */}
      <div className="glass-card" style={{ padding: '22px 24px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <BarChart2 size={20} color="var(--accent-coral)" />
              <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-main)', margin: 0 }}>
                Per-Post Social Engagement & Views Performance
              </h2>
              <span style={{ fontSize: '0.7rem', padding: '2px 8px', borderRadius: '12px', background: 'rgba(232, 101, 74, 0.12)', color: 'var(--accent-coral)', fontWeight: 700 }}>
                {filteredPosts.length} {filteredPosts.length === 1 ? 'Post' : 'Posts'} Tracked
              </span>
            </div>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', margin: '4px 0 0 0' }}>
              Granular post-level analytics across Facebook, Instagram, YouTube & LinkedIn. Track individual post views, likes, shares, comments, saves, engagement rates (ER), and direct buyer lead generation.
            </p>
          </div>

          {/* View Mode Toggle */}
          <div style={{ display: 'flex', background: 'var(--bg-main)', padding: '3px', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
            <button
              onClick={() => setPostViewMode('cards')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '5px 12px',
                borderRadius: '6px',
                border: 'none',
                background: postViewMode === 'cards' ? 'var(--accent-coral)' : 'transparent',
                color: postViewMode === 'cards' ? '#FFFFFF' : 'var(--text-muted)',
                fontSize: '0.74rem',
                fontWeight: 700,
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              <LayoutGrid size={13} />
              <span>Cards</span>
            </button>
            <button
              onClick={() => setPostViewMode('table')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '5px 12px',
                borderRadius: '6px',
                border: 'none',
                background: postViewMode === 'table' ? 'var(--accent-coral)' : 'transparent',
                color: postViewMode === 'table' ? '#FFFFFF' : 'var(--text-muted)',
                fontSize: '0.74rem',
                fontWeight: 700,
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              <List size={13} />
              <span>Table</span>
            </button>
          </div>
        </div>

        {/* ── Filter & Search Toolbar ── */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px', padding: '12px 14px', borderRadius: '10px', background: 'var(--bg-main)', border: '1px solid var(--border-glass)', position: 'relative', zIndex: 15 }}>
          {/* Search Box */}
          <div style={{ position: 'relative', flex: '1', minWidth: '240px', maxWidth: '380px' }}>
            <Search size={14} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              type="text"
              value={postSearch}
              onChange={(e) => setPostSearch(e.target.value)}
              placeholder="Search post titles, captions, projects..."
              style={{
                width: '100%',
                padding: '7px 12px 7px 32px',
                borderRadius: '6px',
                background: 'var(--bg-card)',
                border: '1px solid var(--border-glass)',
                color: 'var(--text-main)',
                fontSize: '0.78rem',
                outline: 'none'
              }}
            />
            {postSearch && (
              <button
                onClick={() => setPostSearch('')}
                style={{
                  position: 'absolute',
                  right: '8px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  padding: 0
                }}
              >
                <X size={12} />
              </button>
            )}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
            {/* Platform Filter Pills */}
            <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
              {[
                { id: 'all', label: 'All Channels' },
                { id: 'facebook', label: 'Facebook', color: '#1877F2' },
                { id: 'instagram', label: 'Instagram', color: '#E1306C' },
                { id: 'youtube', label: 'YouTube', color: '#FF0000' },
                { id: 'linkedin', label: 'LinkedIn', color: '#0A66C2' }
              ].map((pl) => (
                <button
                  key={pl.id}
                  onClick={() => setPostPlatformFilter(pl.id)}
                  style={{
                    padding: '4px 9px',
                    borderRadius: '6px',
                    border: '1px solid',
                    borderColor: postPlatformFilter === pl.id ? (pl.color || 'var(--accent-coral)') : 'var(--border-glass)',
                    background: postPlatformFilter === pl.id 
                      ? (pl.color ? `${pl.color}20` : 'rgba(232, 101, 74, 0.15)') 
                      : 'var(--bg-card)',
                    color: postPlatformFilter === pl.id 
                      ? (pl.color || 'var(--accent-coral)') 
                      : 'var(--text-muted)',
                    fontSize: '0.72rem',
                    fontWeight: 700,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    transition: 'all 0.15s ease'
                  }}
                >
                  {pl.id !== 'all' && <ChannelIcon id={pl.id} color={pl.color} size={11} />}
                  <span>{pl.label}</span>
                </button>
              ))}
            </div>

            {/* Format Filter */}
            <CustomDropdown
              value={postFormatFilter}
              onChange={setPostFormatFilter}
              options={postFormatOptions}
              minWidth="140px"
              ariaLabel="Filter by Content Format"
            />

            {/* Sort Select */}
            <CustomDropdown
              value={postSortBy}
              onChange={setPostSortBy}
              options={postSortOptions}
              minWidth="175px"
              ariaLabel="Sort Posts"
            />
          </div>
        </div>

        {/* ── Empty State ── */}
        {filteredPosts.length === 0 ? (
          <div style={{ padding: '36px', textAlign: 'center', borderRadius: '10px', background: 'var(--bg-main)', border: '1px dashed var(--border-glass)' }}>
            <BarChart2 size={32} color="var(--text-muted)" style={{ margin: '0 auto 8px auto', opacity: 0.5 }} />
            <div style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-main)' }}>No matching social media posts found</div>
            <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', marginTop: '4px' }}>
              Try adjusting your search query, platform selection, or format filters.
            </div>
            <button
              onClick={() => {
                setPostSearch('');
                setPostPlatformFilter('all');
                setPostFormatFilter('all');
              }}
              style={{
                marginTop: '12px',
                padding: '6px 14px',
                borderRadius: '6px',
                background: 'var(--accent-coral)',
                border: 'none',
                color: '#FFFFFF',
                fontSize: '0.75rem',
                fontWeight: 700,
                cursor: 'pointer'
              }}
            >
              Reset Post Filters
            </button>
          </div>
        ) : postViewMode === 'cards' ? (
          /* ── Post Cards Grid View ── */
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '16px' }}>
            {filteredPosts.map((p) => {
              const platformColors = {
                facebook: '#1877F2',
                instagram: '#E1306C',
                youtube: '#FF0000',
                linkedin: '#0A66C2'
              };
              const pColor = platformColors[p.platform] || 'var(--accent-coral)';

              return (
                <div
                  key={p.id}
                  onClick={() => handleOpenDrawer(p, 'post')}
                  style={{
                    padding: '16px',
                    borderRadius: '12px',
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-glass)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '12px',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    boxShadow: 'var(--shadow-card)',
                    position: 'relative'
                  }}
                  className="clickable-card"
                >
                  {/* Card Header: Platform badge, format, boost indicator, date */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <div style={{ width: '24px', height: '24px', borderRadius: '6px', background: `${pColor}20`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <ChannelIcon id={p.platform} color={pColor} size={13} />
                      </div>
                      <span style={{ fontSize: '0.74rem', fontWeight: 700, color: pColor, textTransform: 'capitalize' }}>
                        {p.platform}
                      </span>
                      <span style={{ fontSize: '0.68rem', padding: '2px 6px', borderRadius: '4px', background: 'var(--bg-main)', color: 'var(--text-muted)', fontWeight: 600 }}>
                        {p.format}
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      {p.ad_boosted ? (
                        <span style={{ fontSize: '0.65rem', padding: '2px 6px', borderRadius: '4px', background: 'rgba(99, 102, 241, 0.15)', color: '#6366F1', fontWeight: 700, border: '1px solid rgba(99, 102, 241, 0.3)' }}>
                          🚀 Boosted (${p.ad_spend})
                        </span>
                      ) : (
                        <span style={{ fontSize: '0.65rem', padding: '2px 6px', borderRadius: '4px', background: 'rgba(16, 185, 129, 0.15)', color: '#059669', fontWeight: 700 }}>
                          🌱 Organic
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Title and Project */}
                  <div>
                    <h3 style={{ fontSize: '0.9rem', fontWeight: 800, color: 'var(--text-main)', margin: '0 0 4px 0', lineHeight: 1.3 }}>
                      {p.title}
                    </h3>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
                      <span style={{ fontSize: '0.68rem', padding: '1px 6px', borderRadius: '4px', background: 'rgba(232, 101, 74, 0.12)', color: 'var(--accent-coral)', fontWeight: 700 }}>
                        🏢 {p.project}
                      </span>
                      <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                        {p.published_at}
                      </span>
                    </div>
                    <p style={{
                      fontSize: '0.74rem',
                      color: 'var(--text-muted)',
                      margin: 0,
                      lineHeight: 1.45,
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                      overflow: 'hidden'
                    }}>
                      {p.caption}
                    </p>
                  </div>

                  {/* 6-Metric Interaction Grid */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px', padding: '10px 8px', borderRadius: '8px', background: 'var(--bg-main)', border: '1px solid var(--border-glass)' }}>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '0.64rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '3px' }}>
                        <Eye size={10} color="#7C3AED" /> Views
                      </div>
                      <div style={{ fontSize: '0.85rem', fontWeight: 800, color: 'var(--text-main)', marginTop: '2px' }}>
                        {(p.views || 0).toLocaleString()}
                      </div>
                    </div>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '0.64rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '3px' }}>
                        <Heart size={10} color="#E11D48" /> Likes
                      </div>
                      <div style={{ fontSize: '0.85rem', fontWeight: 800, color: '#E11D48', marginTop: '2px' }}>
                        {(p.likes || 0).toLocaleString()}
                      </div>
                    </div>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '0.64rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '3px' }}>
                        <MessageCircle size={10} color="#2563EB" /> Comments
                      </div>
                      <div style={{ fontSize: '0.85rem', fontWeight: 800, color: '#2563EB', marginTop: '2px' }}>
                        {(p.comments || 0).toLocaleString()}
                      </div>
                    </div>
                    <div style={{ textAlign: 'center', paddingTop: '4px', borderTop: '1px solid var(--border-glass)' }}>
                      <div style={{ fontSize: '0.64rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '3px' }}>
                        <Share2 size={10} color="#059669" /> Shares
                      </div>
                      <div style={{ fontSize: '0.85rem', fontWeight: 800, color: '#059669', marginTop: '2px' }}>
                        {(p.shares || 0).toLocaleString()}
                      </div>
                    </div>
                    <div style={{ textAlign: 'center', paddingTop: '4px', borderTop: '1px solid var(--border-glass)' }}>
                      <div style={{ fontSize: '0.64rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '3px' }}>
                        <Bookmark size={10} color="#D97706" /> Saves
                      </div>
                      <div style={{ fontSize: '0.85rem', fontWeight: 800, color: '#D97706', marginTop: '2px' }}>
                        {(p.saves || 0).toLocaleString()}
                      </div>
                    </div>
                    <div style={{ textAlign: 'center', paddingTop: '4px', borderTop: '1px solid var(--border-glass)' }}>
                      <div style={{ fontSize: '0.64rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '3px' }}>
                        <Zap size={10} color="var(--accent-coral)" /> ER %
                      </div>
                      <div style={{ fontSize: '0.85rem', fontWeight: 800, color: 'var(--accent-coral)', marginTop: '2px' }}>
                        {p.engagement_rate}
                      </div>
                    </div>
                  </div>

                  {/* Card Bottom: Inbound Lead Count & Inspect Button */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '6px', borderTop: '1px solid var(--border-glass)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                      <Target size={12} color="#059669" />
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-main)', fontWeight: 700 }}>
                        <strong style={{ color: '#059669' }}>{p.leads_generated || 0}</strong> Qualified Leads
                      </span>
                    </div>

                    <span style={{ fontSize: '0.72rem', color: 'var(--accent-coral)', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '2px' }}>
                      Inspect Post <ChevronRight size={12} />
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          /* ── Post Table View ── */
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.78rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-glass)', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '10px 12px', fontWeight: 700 }}>Post Title & Project</th>
                  <th style={{ padding: '10px 12px', fontWeight: 700 }}>Channel</th>
                  <th style={{ padding: '10px 12px', fontWeight: 700 }}>Format</th>
                  <th style={{ padding: '10px 12px', fontWeight: 700 }}>Views</th>
                  <th style={{ padding: '10px 12px', fontWeight: 700 }}>Likes</th>
                  <th style={{ padding: '10px 12px', fontWeight: 700 }}>Comments</th>
                  <th style={{ padding: '10px 12px', fontWeight: 700 }}>Shares</th>
                  <th style={{ padding: '10px 12px', fontWeight: 700 }}>Saves</th>
                  <th style={{ padding: '10px 12px', fontWeight: 700 }}>ER %</th>
                  <th style={{ padding: '10px 12px', fontWeight: 700 }}>Leads</th>
                  <th style={{ padding: '10px 12px', fontWeight: 700 }}>Status</th>
                  <th style={{ padding: '10px 12px', fontWeight: 700 }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredPosts.map((p) => {
                  const platformColors = {
                    facebook: '#1877F2',
                    instagram: '#E1306C',
                    youtube: '#FF0000',
                    linkedin: '#0A66C2'
                  };
                  const pColor = platformColors[p.platform] || 'var(--accent-coral)';

                  return (
                    <tr
                      key={p.id}
                      onClick={() => handleOpenDrawer(p, 'post')}
                      style={{
                        borderBottom: '1px solid var(--border-glass)',
                        cursor: 'pointer',
                        transition: 'background 0.15s ease'
                      }}
                      className="table-row-hover"
                    >
                      <td style={{ padding: '12px' }}>
                        <div style={{ fontWeight: 700, color: 'var(--text-main)' }}>{p.title}</div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--accent-coral)', fontWeight: 600 }}>🏢 {p.project}</div>
                      </td>
                      <td style={{ padding: '12px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: pColor, fontWeight: 700, textTransform: 'capitalize' }}>
                          <ChannelIcon id={p.platform} color={pColor} size={12} />
                          <span>{p.platform}</span>
                        </div>
                      </td>
                      <td style={{ padding: '12px', color: 'var(--text-muted)' }}>{p.format}</td>
                      <td style={{ padding: '12px', fontWeight: 800, color: 'var(--text-main)' }}>
                        {(p.views || 0).toLocaleString()}
                      </td>
                      <td style={{ padding: '12px', color: '#E11D48', fontWeight: 700 }}>
                        {(p.likes || 0).toLocaleString()}
                      </td>
                      <td style={{ padding: '12px', color: '#2563EB', fontWeight: 700 }}>
                        {(p.comments || 0).toLocaleString()}
                      </td>
                      <td style={{ padding: '12px', color: '#059669', fontWeight: 700 }}>
                        {(p.shares || 0).toLocaleString()}
                      </td>
                      <td style={{ padding: '12px', color: '#D97706', fontWeight: 700 }}>
                        {(p.saves || 0).toLocaleString()}
                      </td>
                      <td style={{ padding: '12px', fontWeight: 800, color: 'var(--accent-coral)' }}>
                        {p.engagement_rate}
                      </td>
                      <td style={{ padding: '12px', fontWeight: 800, color: '#059669' }}>
                        {p.leads_generated || 0}
                      </td>
                      <td style={{ padding: '12px' }}>
                        {p.ad_boosted ? (
                          <span style={{ fontSize: '0.65rem', padding: '2px 6px', borderRadius: '4px', background: 'rgba(99, 102, 241, 0.15)', color: '#6366F1', fontWeight: 700 }}>
                            🚀 Boosted
                          </span>
                        ) : (
                          <span style={{ fontSize: '0.65rem', padding: '2px 6px', borderRadius: '4px', background: 'rgba(16, 185, 129, 0.15)', color: '#059669', fontWeight: 700 }}>
                            🌱 Organic
                          </span>
                        )}
                      </td>
                      <td style={{ padding: '12px' }}>
                        <span style={{ fontSize: '0.72rem', color: 'var(--accent-coral)', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '2px' }}>
                          Inspect <ChevronRight size={12} />
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ── Active Live Campaigns Table ── */}
      <div className="glass-card" style={{ padding: '22px 24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-main)', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Compass size={18} color="var(--accent-coral)" /> Live Campaigns & Creative Performance
            </h2>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', margin: '2px 0 0 0' }}>
              Direct lead ad sets with real-time spend, cost per qualified lead, and creative CTR
            </p>
          </div>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.8rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-glass)', color: 'var(--text-muted)' }}>
                <th style={{ padding: '10px 12px', fontWeight: 700 }}>Campaign Name</th>
                <th style={{ padding: '10px 12px', fontWeight: 700 }}>Project</th>
                <th style={{ padding: '10px 12px', fontWeight: 700 }}>Platform</th>
                <th style={{ padding: '10px 12px', fontWeight: 700 }}>Status</th>
                <th style={{ padding: '10px 12px', fontWeight: 700 }}>Spend</th>
                <th style={{ padding: '10px 12px', fontWeight: 700 }}>Leads</th>
                <th style={{ padding: '10px 12px', fontWeight: 700 }}>CPL</th>
                <th style={{ padding: '10px 12px', fontWeight: 700 }}>Conv Rate</th>
                <th style={{ padding: '10px 12px', fontWeight: 700 }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {campaigns.map((c) => (
                <tr 
                  key={c.id}
                  onClick={() => handleOpenDrawer(c, 'campaign')}
                  style={{ 
                    borderBottom: '1px solid var(--border-glass)', 
                    cursor: 'pointer',
                    transition: 'background 0.15s ease'
                  }}
                  className="table-row-hover"
                >
                  <td style={{ padding: '12px', color: 'var(--text-main)', fontWeight: 700 }}>
                    <div>{c.name}</div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{c.creative}</div>
                  </td>
                  <td style={{ padding: '12px', color: 'var(--text-main)' }}>{c.project}</td>
                  <td style={{ padding: '12px', color: '#7C3AED', fontWeight: 600 }}>{c.platform}</td>
                  <td style={{ padding: '12px' }}>
                    <span style={{
                      padding: '3px 8px',
                      borderRadius: '12px',
                      fontSize: '0.7rem',
                      fontWeight: 700,
                      background: c.status === 'ACTIVE' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                      color: c.status === 'ACTIVE' ? '#059669' : '#D97706',
                      border: c.status === 'ACTIVE' ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(245, 158, 11, 0.3)'
                    }}>
                      {c.status}
                    </span>
                  </td>
                  <td style={{ padding: '12px', color: 'var(--text-main)', fontWeight: 600 }}>${c.spend}</td>
                  <td style={{ padding: '12px', color: 'var(--text-main)', fontWeight: 700 }}>{c.leads}</td>
                  <td style={{ padding: '12px', color: '#0284C7', fontWeight: 700 }}>{c.cpl}</td>
                  <td style={{ padding: '12px', color: '#059669', fontWeight: 700 }}>{c.conv_rate}</td>
                  <td style={{ padding: '12px' }}>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleOpenDrawer(c, 'campaign');
                      }}
                      style={{
                        padding: '4px 10px',
                        borderRadius: '6px',
                        background: 'rgba(232, 101, 74, 0.1)',
                        border: '1px solid rgba(232, 101, 74, 0.3)',
                        color: 'var(--accent-coral)',
                        fontSize: '0.72rem',
                        fontWeight: 700,
                        cursor: 'pointer'
                      }}
                    >
                      Inspect
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── FACEBOOK & INSTAGRAM COMMENT-TO-DM LEAD BRIDGE STUDIO ── */}
      <div 
        className="glass-card" 
        style={{ 
          padding: '24px 26px', 
          display: 'flex', 
          flexDirection: 'column', 
          gap: '18px', 
          background: 'linear-gradient(135deg, rgba(24, 119, 242, 0.04), rgba(225, 48, 108, 0.04), var(--bg-card))',
          border: '1px solid var(--border-glass)',
          borderRadius: '16px',
          boxShadow: 'var(--shadow-card)'
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ padding: '8px', borderRadius: '10px', background: 'linear-gradient(135deg, #1877F2, #E1306C)', boxShadow: '0 4px 12px rgba(24, 119, 242, 0.25)' }}>
              <MessageSquare size={20} color="#FFFFFF" />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-main)', margin: 0 }}>
                  Facebook & Instagram Auto-Comment to Private DM Lead Bridge
                </h2>
                <span style={{ fontSize: '0.68rem', padding: '2px 8px', borderRadius: '6px', background: 'rgba(16, 185, 129, 0.15)', color: '#059669', fontWeight: 700, border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                  ⚡ LIVE AI BRIDGE
                </span>
              </div>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', margin: '2px 0 0 0' }}>
                Converts post comments directly into qualified Messenger & Instagram DM leads with automated public replies and private property brochures.
              </p>
            </div>
          </div>

          {/* Quick Pre-fill Pills */}
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {[
              { label: '🇧🇩 Banani 3 BHK Price?', text: 'Banani 3 BHK flat price koto? Details inbox korun' },
              { label: '🏢 Gulshan Brochure', text: 'Gulshan luxury project er brochure & payment plan pathan' },
              { label: '🇬🇧 English Inquiry', text: 'What is the price of 3BHK flat in Banani? Please send floor plans.' }
            ].map((pill, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setSimComment(pill.text);
                  setSimResult(null);
                }}
                style={{
                  padding: '4px 10px',
                  borderRadius: '20px',
                  background: 'var(--bg-main)',
                  border: '1px solid var(--border-glass)',
                  color: 'var(--text-main)',
                  fontSize: '0.72rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
              >
                {pill.label}
              </button>
            ))}
          </div>
        </div>

        {/* Simulator Input Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px', alignItems: 'end' }}>
          <div>
            <label style={{ fontSize: '0.74rem', color: 'var(--text-muted)', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
              Target Social Platform
            </label>
            <CustomDropdown
              value={simPlatform}
              onChange={setSimPlatform}
              options={simPlatformOptions}
              minWidth="100%"
              buttonStyle={{ padding: '8px 12px', fontSize: '0.8rem' }}
              ariaLabel="Select Simulator Platform"
            />
          </div>

          <div>
            <label style={{ fontSize: '0.74rem', color: 'var(--text-muted)', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
              Commenter Name
            </label>
            <input
              type="text"
              value={simAuthor}
              onChange={(e) => setSimAuthor(e.target.value)}
              placeholder="e.g. Mahmudur Rahman"
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '8px',
                background: 'var(--bg-card)',
                border: '1px solid var(--border-glass)',
                color: 'var(--text-main)',
                fontSize: '0.8rem',
                outline: 'none'
              }}
            />
          </div>

          <div style={{ gridColumn: 'span 2' }}>
            <label style={{ fontSize: '0.74rem', color: 'var(--text-muted)', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
              User's Public Comment (Bangla / Banglish / English)
            </label>
            <div style={{ display: 'flex', gap: '8px' }}>
              <input
                type="text"
                value={simComment}
                onChange={(e) => setSimComment(e.target.value)}
                placeholder="Type any inquiry e.g. Price koto? Banani flat details inbox korun"
                style={{
                  flex: 1,
                  padding: '9px 14px',
                  borderRadius: '8px',
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-glass)',
                  color: 'var(--text-main)',
                  fontSize: '0.82rem',
                  outline: 'none'
                }}
              />
              <button
                onClick={handleRunSimulator}
                disabled={simLoading}
                style={{
                  padding: '9px 20px',
                  borderRadius: '8px',
                  background: simPlatform === 'facebook' ? 'linear-gradient(135deg, #1877F2, #0A58CA)' : 'linear-gradient(135deg, #E1306C, #C13584)',
                  border: 'none',
                  color: '#FFFFFF',
                  fontSize: '0.82rem',
                  fontWeight: 700,
                  cursor: simLoading ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  boxShadow: '0 4px 14px rgba(24, 119, 242, 0.4)',
                  whiteSpace: 'nowrap'
                }}
              >
                {simLoading ? <RefreshCw size={15} className="spin" /> : <Zap size={15} />}
                {simLoading ? 'Bridging...' : 'Execute Comment Bridge'}
              </button>
            </div>
          </div>
        </div>

        {/* Live Simulation Output Panel */}
        {simResult && (
          <div 
            style={{ 
              marginTop: '8px', 
              padding: '18px 20px', 
              borderRadius: '12px', 
              background: 'var(--bg-card)', 
              border: '1px solid var(--border-glass)',
              display: 'flex',
              flexDirection: 'column',
              gap: '14px',
              animation: 'fadeIn 0.3s ease'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-glass)', paddingBottom: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <CheckCircle2 size={18} color="#059669" />
                <span style={{ fontSize: '0.88rem', fontWeight: 800, color: 'var(--text-main)' }}>
                  Comment-to-DM Bridge Executed Successfully
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '0.72rem', padding: '3px 8px', borderRadius: '4px', background: 'rgba(139, 92, 246, 0.15)', color: '#7C3AED', fontWeight: 700 }}>
                  Lead Intent Score: {simResult.lead_score}/100
                </span>
                {simResult.is_hot_lead && (
                  <span style={{ fontSize: '0.72rem', padding: '3px 8px', borderRadius: '4px', background: 'rgba(239, 68, 68, 0.15)', color: '#DC2626', fontWeight: 800, border: '1px solid rgba(239, 68, 68, 0.3)' }}>
                    🔥 HOT LEAD DETECTED
                  </span>
                )}
              </div>
            </div>

            {/* Dual Previews: Step 1 Public Reply & Step 2 Private DM */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
              
              {/* Step 1: Public Auto-Reply Card */}
              <div style={{ padding: '14px 16px', borderRadius: '10px', background: 'var(--bg-main)', border: '1px solid var(--border-glass)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#2563EB', textTransform: 'uppercase' }}>
                    1. Public Comment Auto-Reply
                  </span>
                  <span style={{ fontSize: '0.65rem', padding: '2px 6px', borderRadius: '4px', background: 'rgba(16, 185, 129, 0.15)', color: '#059669', fontWeight: 700 }}>
                    POSTED (0.4s)
                  </span>
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-main)', lineHeight: 1.5, background: 'var(--bg-card)', padding: '10px 12px', borderRadius: '8px', borderLeft: '3px solid #1877F2', border: '1px solid var(--border-glass)' }}>
                  {simResult.public_reply}
                </div>
              </div>

              {/* Step 2: Private DM Lead Hook Card */}
              <div style={{ padding: '14px 16px', borderRadius: '10px', background: 'var(--bg-main)', border: '1px solid var(--border-glass)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#7C3AED', textTransform: 'uppercase' }}>
                    2. Private Messenger / IG Direct Message
                  </span>
                  <span style={{ fontSize: '0.65rem', padding: '2px 6px', borderRadius: '4px', background: 'rgba(139, 92, 246, 0.15)', color: '#7C3AED', fontWeight: 700 }}>
                    DELIVERED (0.8s)
                  </span>
                </div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-main)', lineHeight: 1.5, background: 'var(--bg-card)', padding: '10px 12px', borderRadius: '8px', borderLeft: '3px solid #E1306C', border: '1px solid var(--border-glass)', whiteSpace: 'pre-wrap' }}>
                  {simResult.private_dm}
                </div>

                {/* Quick Reply Buttons */}
                <div style={{ display: 'flex', gap: '6px', marginTop: '10px', flexWrap: 'wrap' }}>
                  {['📅 Book Site Tour', '📥 Download Brochure', '💬 Talk to Consultant'].map((btn, bidx) => (
                    <button
                      key={bidx}
                      style={{
                        padding: '4px 8px',
                        borderRadius: '6px',
                        background: 'var(--bg-card)',
                        border: '1px solid var(--border-glass)',
                        color: 'var(--text-main)',
                        fontSize: '0.68rem',
                        fontWeight: 600,
                        cursor: 'default'
                      }}
                    >
                      {btn}
                    </button>
                  ))}
                </div>
              </div>

            </div>
          </div>
        )}
      </div>

      {/* ── AI Campaign Optimization Recommendations Banner ── */}
      <div className="glass-card" style={{ padding: '22px 24px', display: 'flex', flexDirection: 'column', gap: '14px', background: 'linear-gradient(135deg, rgba(232, 101, 74, 0.06), rgba(139, 92, 246, 0.06))' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Sparkles size={18} color="var(--accent-coral)" />
          <h2 style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--text-main)', margin: 0 }}>
            Executive AI Campaign Optimization Recommendations
          </h2>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '14px' }}>
          {aiRecommendations.map((rec, i) => (
            <div key={i} style={{ padding: '14px', borderRadius: '8px', background: 'var(--bg-card)', border: '1px solid var(--border-glass)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-main)' }}>{rec.title}</span>
                <span style={{ fontSize: '0.68rem', padding: '2px 6px', borderRadius: '4px', background: 'rgba(232, 101, 74, 0.12)', color: 'var(--accent-coral)', fontWeight: 700 }}>
                  {rec.priority} PRIORITY
                </span>
              </div>
              <p style={{ fontSize: '0.76rem', color: 'var(--text-muted)', margin: 0, lineHeight: 1.4 }}>{rec.detail}</p>
              <div style={{ fontSize: '0.72rem', color: '#059669', fontWeight: 700, marginTop: '4px' }}>
                Expected Impact: {rec.impact}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── INTERACTIVE RIGHT-SIDE SLIDE-OUT DETAIL DRAWER ── */}
      {drawerOpen && (
        <div 
          onClick={handleCloseDrawer}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.65)',
            backdropFilter: 'blur(4px)',
            zIndex: 9998,
            transition: 'opacity 0.2s ease'
          }}
        >
          <div 
            onClick={(e) => e.stopPropagation()}
            style={{
              position: 'fixed',
              top: 0,
              right: 0,
              width: '540px',
              maxWidth: '92vw',
              height: '100vh',
              background: 'var(--bg-card)',
              borderLeft: '1px solid var(--border-glass)',
              boxShadow: '-10px 0 35px rgba(0, 0, 0, 0.12)',
              zIndex: 9999,
              display: 'flex',
              flexDirection: 'column',
              padding: '26px 24px',
              gap: '18px',
              overflowY: 'auto',
              animation: 'slideInRight 0.25s ease-out'
            }}
          >
            {/* Drawer Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--border-glass)', paddingBottom: '14px' }}>
              <div>
                <span style={{ fontSize: '0.72rem', padding: '3px 8px', borderRadius: '6px', background: 'rgba(232, 101, 74, 0.12)', color: 'var(--accent-coral)', fontWeight: 700, display: 'inline-block', marginBottom: '6px' }}>
                  {selectedItem?.drawerType === 'post' 
                    ? `${selectedItem?.platform?.toUpperCase()} POST • ${selectedItem?.format}`
                    : selectedItem?.category || selectedItem?.project || 'Drilldown Details'}
                </span>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-main)', margin: '0 0 4px 0' }}>
                  {selectedItem?.title || selectedItem?.name || 'Inspection Details'}
                </h2>
                <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>
                  {selectedItem?.description || selectedItem?.creative || selectedItem?.caption || 'Deep multi-channel analytics and performance breakdown.'}
                </div>
              </div>

              <button
                onClick={handleCloseDrawer}
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  background: 'var(--bg-main)',
                  border: '1px solid var(--border-glass)',
                  color: 'var(--text-main)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                  flexShrink: 0
                }}
              >
                <X size={18} />
              </button>
            </div>

            {/* ── 1. Top Total Metric Card ── */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div style={{ padding: '14px 16px', borderRadius: '10px', background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.08), var(--bg-card))', border: '1px solid rgba(139, 92, 246, 0.2)' }}>
                <div style={{ fontSize: '0.72rem', color: '#7C3AED', fontWeight: 600 }}>
                  {selectedItem?.drawerType === 'post' ? 'Total Post Views' : selectedItem?.metricLabel || 'Total Metric Value'}
                </div>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em', marginTop: '2px' }}>
                  {selectedItem?.drawerType === 'post' 
                    ? (selectedItem?.views || 0).toLocaleString() 
                    : selectedItem?.primaryValue || selectedItem?.leads || `$${selectedItem?.spend || 0}`}
                </div>
              </div>
              <div style={{ padding: '14px 16px', borderRadius: '10px', background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.08), var(--bg-card))', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
                <div style={{ fontSize: '0.72rem', color: '#059669', fontWeight: 600 }}>
                  {selectedItem?.drawerType === 'post' ? 'Engagement Rate (ER)' : 'Rate / Sub-Metric'}
                </div>
                <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#059669', marginTop: '4px' }}>
                  {selectedItem?.drawerType === 'post' 
                    ? selectedItem?.engagement_rate 
                    : selectedItem?.subValue || selectedItem?.conv_rate || selectedItem?.cpl || '+18.4% Growth'}
                </div>
              </div>
            </div>

            {/* ── 2. DEDICATED SOCIAL MEDIA CHANNEL BREAKDOWN (Directly Below Total Card) ── */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Layers size={15} color="var(--accent-coral)" /> 
                  {selectedItem?.drawerType === 'platform' 
                    ? `${selectedItem?.name} Performance Breakdown` 
                    : selectedItem?.drawerType === 'campaign'
                    ? 'Campaign Metrics Breakdown'
                    : selectedItem?.drawerType === 'post'
                    ? 'Post Engagement & Lead Intelligence'
                    : 'Social Media Channel Breakdown'}
                </span>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                  {selectedItem?.drawerType === 'platform' ? 'Channel Metrics' : selectedItem?.drawerType === 'post' ? 'Post Drilldown' : 'Contribution by Network'}
                </span>
              </div>

              {/* Breakdown Rows */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {selectedItem?.drawerType === 'metric' && (
                  getMetricBreakdown(selectedItem?.metricKey).map((item) => (
                    <div 
                      key={item.id}
                      style={{
                        padding: '12px 14px',
                        borderRadius: '8px',
                        background: 'var(--bg-main)',
                        border: '1px solid var(--border-glass)',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '6px'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <div style={{ width: '26px', height: '26px', borderRadius: '6px', background: `${item.color}20`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <ChannelIcon id={item.id} color={item.color} size={14} />
                          </div>
                          <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-main)' }}>{item.name}</span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{ fontSize: '0.9rem', fontWeight: 800, color: 'var(--text-main)' }}>{item.value}</span>
                          <span style={{ 
                            fontSize: '0.7rem', 
                            fontWeight: 700, 
                            padding: '2px 6px', 
                            borderRadius: '4px', 
                            background: `${item.color}15`, 
                            color: item.color,
                            border: `1px solid ${item.color}30`
                          }}>
                            {item.pct}
                          </span>
                        </div>
                      </div>

                      {/* Subtitle / format info */}
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                        <span>{item.sub}</span>
                        <span>{item.barPct > 0 ? `${item.barPct}% share` : 'Organic'}</span>
                      </div>

                      {/* Visual colored progress bar */}
                      <div style={{ width: '100%', height: '4px', background: 'rgba(0, 0, 0, 0.06)', borderRadius: '2px', overflow: 'hidden' }}>
                        <div 
                          style={{ 
                            width: `${Math.max(item.barPct, 4)}%`, 
                            height: '100%', 
                            background: item.color, 
                            borderRadius: '2px',
                            transition: 'width 0.4s ease'
                          }} 
                        />
                      </div>
                    </div>
                  ))
                )}

                {/* If a Platform Card was clicked */}
                {selectedItem?.drawerType === 'platform' && (
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                    <div style={{ padding: '10px', borderRadius: '8px', background: 'var(--bg-main)', border: '1px solid var(--border-glass)' }}>
                      <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Total Impressions</div>
                      <div style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--text-main)' }}>{selectedItem?.impressions || '480,000'}</div>
                    </div>
                    <div style={{ padding: '10px', borderRadius: '8px', background: 'var(--bg-main)', border: '1px solid var(--border-glass)' }}>
                      <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Click-Through Rate (CTR)</div>
                      <div style={{ fontSize: '1rem', fontWeight: 800, color: '#0284C7' }}>{selectedItem?.ctr || '5.4%'}</div>
                    </div>
                    <div style={{ padding: '10px', borderRadius: '8px', background: 'var(--bg-main)', border: '1px solid var(--border-glass)' }}>
                      <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Verified Leads</div>
                      <div style={{ fontSize: '1rem', fontWeight: 800, color: '#059669' }}>{selectedItem?.leads || '224'}</div>
                    </div>
                    <div style={{ padding: '10px', borderRadius: '8px', background: 'var(--bg-main)', border: '1px solid var(--border-glass)' }}>
                      <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Cost Per Lead (CPL)</div>
                      <div style={{ fontSize: '1rem', fontWeight: 800, color: '#D97706' }}>${selectedItem?.cpl || '13.84'}</div>
                    </div>
                  </div>
                )}

                {/* If a Campaign Row was clicked */}
                {selectedItem?.drawerType === 'campaign' && (
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                    <div style={{ padding: '10px', borderRadius: '8px', background: 'var(--bg-main)', border: '1px solid var(--border-glass)' }}>
                      <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Target Project</div>
                      <div style={{ fontSize: '0.85rem', fontWeight: 800, color: 'var(--text-main)' }}>{selectedItem?.project}</div>
                    </div>
                    <div style={{ padding: '10px', borderRadius: '8px', background: 'var(--bg-main)', border: '1px solid var(--border-glass)' }}>
                      <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Platform</div>
                      <div style={{ fontSize: '0.85rem', fontWeight: 800, color: '#7C3AED' }}>{selectedItem?.platform}</div>
                    </div>
                    <div style={{ padding: '10px', borderRadius: '8px', background: 'var(--bg-main)', border: '1px solid var(--border-glass)' }}>
                      <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Spend & CPL</div>
                      <div style={{ fontSize: '0.9rem', fontWeight: 800, color: '#0284C7' }}>${selectedItem?.spend} (CPL: {selectedItem?.cpl})</div>
                    </div>
                    <div style={{ padding: '10px', borderRadius: '8px', background: 'var(--bg-main)', border: '1px solid var(--border-glass)' }}>
                      <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Conversion Rate</div>
                      <div style={{ fontSize: '0.9rem', fontWeight: 800, color: '#059669' }}>{selectedItem?.conv_rate}</div>
                    </div>
                  </div>
                )}

                {/* If a Post was clicked */}
                {selectedItem?.drawerType === 'post' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {/* Caption Preview Box */}
                    <div style={{ padding: '12px', borderRadius: '8px', background: 'var(--bg-main)', border: '1px solid var(--border-glass)' }}>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 600, marginBottom: '4px' }}>
                        Post Caption & Copy
                      </div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-main)', lineHeight: 1.45, fontStyle: 'italic' }}>
                        "{selectedItem?.caption}"
                      </div>
                      <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: '8px' }}>
                        <span style={{ fontSize: '0.68rem', padding: '2px 6px', borderRadius: '4px', background: 'var(--bg-card)', color: 'var(--text-main)', fontWeight: 600 }}>
                          🏢 {selectedItem?.project}
                        </span>
                        <span style={{ fontSize: '0.68rem', padding: '2px 6px', borderRadius: '4px', background: 'var(--bg-card)', color: 'var(--text-muted)' }}>
                          🕒 {selectedItem?.published_at}
                        </span>
                        <span style={{ fontSize: '0.68rem', padding: '2px 6px', borderRadius: '4px', background: selectedItem?.ad_boosted ? 'rgba(99, 102, 241, 0.15)' : 'rgba(16, 185, 129, 0.15)', color: selectedItem?.ad_boosted ? '#6366F1' : '#059669', fontWeight: 700 }}>
                          {selectedItem?.ad_boosted ? `🚀 Boosted ($${selectedItem?.ad_spend})` : '🌱 Organic'}
                        </span>
                      </div>
                    </div>

                    {/* 6 Grid Metrics */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
                      <div style={{ padding: '10px', borderRadius: '8px', background: 'var(--bg-main)', border: '1px solid var(--border-glass)', textAlign: 'center' }}>
                        <div style={{ fontSize: '0.66rem', color: 'var(--text-muted)' }}>Likes / Reacts</div>
                        <div style={{ fontSize: '1rem', fontWeight: 800, color: '#E11D48' }}>{(selectedItem?.likes || 0).toLocaleString()}</div>
                      </div>
                      <div style={{ padding: '10px', borderRadius: '8px', background: 'var(--bg-main)', border: '1px solid var(--border-glass)', textAlign: 'center' }}>
                        <div style={{ fontSize: '0.66rem', color: 'var(--text-muted)' }}>Comments</div>
                        <div style={{ fontSize: '1rem', fontWeight: 800, color: '#2563EB' }}>{(selectedItem?.comments || 0).toLocaleString()}</div>
                      </div>
                      <div style={{ padding: '10px', borderRadius: '8px', background: 'var(--bg-main)', border: '1px solid var(--border-glass)', textAlign: 'center' }}>
                        <div style={{ fontSize: '0.66rem', color: 'var(--text-muted)' }}>Shares</div>
                        <div style={{ fontSize: '1rem', fontWeight: 800, color: '#059669' }}>{(selectedItem?.shares || 0).toLocaleString()}</div>
                      </div>
                      <div style={{ padding: '10px', borderRadius: '8px', background: 'var(--bg-main)', border: '1px solid var(--border-glass)', textAlign: 'center' }}>
                        <div style={{ fontSize: '0.66rem', color: 'var(--text-muted)' }}>Saves</div>
                        <div style={{ fontSize: '1rem', fontWeight: 800, color: '#D97706' }}>{(selectedItem?.saves || 0).toLocaleString()}</div>
                      </div>
                      <div style={{ padding: '10px', borderRadius: '8px', background: 'var(--bg-main)', border: '1px solid var(--border-glass)', textAlign: 'center' }}>
                        <div style={{ fontSize: '0.66rem', color: 'var(--text-muted)' }}>Leads</div>
                        <div style={{ fontSize: '1rem', fontWeight: 800, color: '#7C3AED' }}>{selectedItem?.leads_generated || 0}</div>
                      </div>
                      <div style={{ padding: '10px', borderRadius: '8px', background: 'var(--bg-main)', border: '1px solid var(--border-glass)', textAlign: 'center' }}>
                        <div style={{ fontSize: '0.66rem', color: 'var(--text-muted)' }}>CPL</div>
                        <div style={{ fontSize: '1rem', fontWeight: 800, color: '#0284C7' }}>{selectedItem?.cpl || '$0.00'}</div>
                      </div>
                    </div>

                    {/* Pipeline Info */}
                    <div style={{ padding: '10px 12px', borderRadius: '8px', background: 'rgba(99, 102, 241, 0.08)', border: '1px solid rgba(99, 102, 241, 0.2)', fontSize: '0.74rem', color: 'var(--text-main)', lineHeight: 1.4 }}>
                      🎯 <strong>Lead Dispatch:</strong> This post has delivered <strong>{selectedItem?.leads_generated || 0} direct inquiries</strong> into the CRM with automated WhatsApp follow-up.
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* ── 3. Mini 7-Day Performance Trend Chart ── */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <TrendingUp size={14} color="#0284C7" /> 7-Day Performance Trend
              </span>
              <div style={{ height: '130px', width: '100%', background: 'var(--bg-main)', borderRadius: '8px', padding: '8px', border: '1px solid var(--border-glass)' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={timeSeries}>
                    <defs>
                      <linearGradient id="drawerGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.35}/>
                        <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="name" stroke="#64748B" fontSize={10} />
                    <YAxis stroke="#64748B" fontSize={10} />
                    <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border-glass)', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.08)', fontSize: '11px', color: 'var(--text-main)' }} />
                    <Area type="monotone" dataKey="leads" stroke="#8B5CF6" fillOpacity={1} fill="url(#drawerGrad)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* ── 4. Audience & Demographic Targeting Profile ── */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Users size={14} color="var(--accent-coral)" /> Audience & Geography Targeting
              </span>
              <div style={{ padding: '12px', borderRadius: '8px', background: 'var(--bg-main)', border: '1px solid var(--border-glass)', display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.78rem' }}>
                <div style={{ color: 'var(--text-main)' }}>
                  Target: <strong>{selectedItem?.target_audience || 'High Net Worth Individuals (HNIs), Expats, Business Owners'}</strong>
                </div>
                <div style={{ color: 'var(--text-muted)' }}>
                  Top Hubs: <span style={{ color: '#7C3AED', fontWeight: 600 }}>Dhaka (Gulshan, Banani), Mumbai, London, Dubai</span>
                </div>
                <div style={{ color: 'var(--text-muted)' }}>
                  Primary Inflow: <span style={{ color: '#0284C7', fontWeight: 600 }}>WhatsApp Direct Lead Sync & n8n RAG</span>
                </div>
              </div>
            </div>

            {/* ── 5. AI Optimization Takeaway ── */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Sparkles size={14} color="#D97706" /> AI Executive Optimization Takeaway
              </span>
              <div style={{ padding: '12px', borderRadius: '8px', background: 'rgba(245, 158, 11, 0.08)', border: '1px solid rgba(245, 158, 11, 0.25)', fontSize: '0.76rem', color: 'var(--text-main)', lineHeight: 1.4 }}>
                💡 Recommendation: Increase daily budget by 15% on Meta & Instagram Reels during 7 PM – 11 PM peak browsing hours to capture up to 2.4x higher verified lead conversions.
              </div>
            </div>

            {/* ── 6. Drawer Action Buttons ── */}
            <div style={{ display: 'flex', gap: '10px', marginTop: 'auto', paddingTop: '14px', borderTop: '1px solid var(--border-glass)' }}>
              <button
                onClick={handleCloseDrawer}
                style={{
                  flex: 1,
                  padding: '10px',
                  borderRadius: '8px',
                  background: 'var(--bg-main)',
                  border: '1px solid var(--border-glass)',
                  color: 'var(--text-main)',
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                Close Drawer
              </button>
              <button
                onClick={handleCopySummary}
                style={{
                  flex: 1,
                  padding: '10px',
                  borderRadius: '8px',
                  background: 'linear-gradient(135deg, var(--accent-coral), #D95338)',
                  border: 'none',
                  color: '#FFFFFF',
                  fontSize: '0.8rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                  boxShadow: '0 4px 14px rgba(232, 101, 74, 0.35)'
                }}
              >
                Export Metric
              </button>
            </div>

          </div>
        </div>
      )}

    </div>
  );
}
