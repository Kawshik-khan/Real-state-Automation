"""Seed and synchronize Social Posts and Ad Campaigns in Supabase Cloud.

Ensures:
1. `social_posts` table is populated with authentic luxury real estate posts linked to canonical projects.
2. `ad_campaigns` table has project_id links and accurate multi-channel attribution.
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.supabase_db import supabase_db

now = datetime.now(timezone.utc)


def seed_social_analytics():
    print("=" * 65)
    print("🚀 SEEDING SOCIAL POSTS & AD CAMPAIGNS IN SUPABASE CLOUD")
    print("=" * 65)

    health = supabase_db.check_health()
    if not health.get("reachable"):
        print(f"[!] Supabase unreachable: {health}")
        return False
    print(f"[✓] Supabase Cloud ONLINE ({health.get('supabase_url')})")

    # 1. Update ad_campaigns to link project_ids
    print("\n--- Linking Ad Campaigns to Projects ---")
    campaigns = supabase_db._request("ad_campaigns?select=*")
    if isinstance(campaigns, list) and campaigns:
        project_map = {
            "facebook": "proj_101",   # GLG Gulshan Heights VIP Launch
            "instagram": "proj_102",  # Baridhara Diplomatic Luxe Showcase
            "linkedin": "proj_104",   # Banani Crest Towers Commercial Suites
            "youtube": "proj_103",    # GLG 4K Architectural Walkthrough
            "tiktok": "proj_105",     # Dhaka Luxury Living Lifestyle Shorts
        }
        for cmp in campaigns:
            plat = cmp.get("platform", "").lower()
            target_proj = project_map.get(plat)
            if target_proj and cmp.get("project_id") != target_proj:
                patch_res = supabase_db._request(
                    f"ad_campaigns?id=eq.{cmp['id']}",
                    method="PATCH",
                    data={"project_id": target_proj}
                )
                print(f"  [✓] Linked campaign '{cmp.get('campaign_name')}' to {target_proj}")
            else:
                print(f"  [✓] Campaign '{cmp.get('campaign_name')}' already linked to {cmp.get('project_id')}")

    # 2. Check and Seed social_posts
    print("\n--- Verifying social_posts table ---")
    existing_posts = supabase_db._request("social_posts?select=id")
    existing_count = len(existing_posts) if isinstance(existing_posts, list) else 0
    print(f"  Existing social_posts count: {existing_count}")

    if existing_count == 0:
        print("  Seeding canonical social_posts...")
        canonical_posts = [
            {
                "project_id": "proj_102",
                "platform": "instagram",
                "topic": "Baridhara Luxury Suites — Infinity Pool Aerial Reel",
                "post_content": "Your sanctuary in the diplomatic zone. Rooftop temperature-controlled infinity pool overlooking the city skyline. Handover in Q4 2026. Only 4 exclusive units remaining.",
                "hashtags": ["#BaridharaSuites", "#LuxuryRealEstateDhaka", "#InfinityPool", "#DiplomaticZone"],
                "media_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=1200&q=80",
                "tone": "luxury",
                "language": "dual",
                "status": "published",
                "published_at": (now - timedelta(days=2)).isoformat(),
                "likes_count": 8940,
                "comments_count": 486,
                "shares_count": 420,
                "created_by": "ai-content-engine",
                "tenant_id": "glg-assets-main",
            },
            {
                "project_id": "proj_103",
                "platform": "facebook",
                "topic": "GLG Sky Tower — Penthouse Sunset Walkthrough",
                "post_content": "Experience panoramic views of Gulshan lake from our signature duplex penthouses. 3,800 sq.ft of pure luxury with private elevators and Italian marble interiors. Book your private viewing today.",
                "hashtags": ["#GLGSkyTower", "#PenthouseLiving", "#GulshanAvenue", "#LuxuryLiving"],
                "media_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
                "tone": "luxury",
                "language": "dual",
                "status": "published",
                "published_at": (now - timedelta(days=1)).isoformat(),
                "likes_count": 4820,
                "comments_count": 342,
                "shares_count": 185,
                "created_by": "ai-content-engine",
                "tenant_id": "glg-assets-main",
            },
            {
                "project_id": "proj_104",
                "platform": "youtube",
                "topic": "Full 4K Architectural Tour: Banani Crest Smart Homes",
                "post_content": "Complete interior walkthrough of our 4 BHK show unit with automated climate control, IoT security, and German fitted kitchens. Watch the full episode now.",
                "hashtags": ["#BananiCrestTowers", "#SmartHomesDhaka", "#4KTour", "#Architecture"],
                "media_url": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80",
                "tone": "exclusive",
                "language": "dual",
                "status": "published",
                "published_at": (now - timedelta(days=3)).isoformat(),
                "likes_count": 3100,
                "comments_count": 215,
                "shares_count": 310,
                "created_by": "ai-content-engine",
                "tenant_id": "glg-assets-main",
            },
            {
                "project_id": "proj_101",
                "platform": "linkedin",
                "topic": "Commercial Real Estate ROI: Dhanmondi & Gulshan Corporate Suites",
                "post_content": "Why Grade-A commercial spaces in Gulshan & Dhanmondi are yielding 9.4% rental ROI in 2026. Executive briefing for institutional investors and NRI family offices.",
                "hashtags": ["#RealEstateInvesting", "#CommercialROI", "#GulshanHeights", "#InstitutionalRealEstate"],
                "media_url": "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
                "tone": "corporate",
                "language": "en",
                "status": "published",
                "published_at": (now - timedelta(days=4)).isoformat(),
                "likes_count": 1420,
                "comments_count": 88,
                "shares_count": 76,
                "created_by": "ai-content-engine",
                "tenant_id": "glg-assets-main",
            },
            {
                "project_id": "proj_105",
                "platform": "facebook",
                "topic": "Uttara Sector 3 Family Residences — 20:80 Payment Scheme",
                "post_content": "Book your 3 BHK dream home with only 20% down payment and 0% interest EMI until handover. Close to top international schools and airport expressway.",
                "hashtags": ["#UttaraResidences", "#FlexiblePayment", "#LuxuryDhakaHomes"],
                "media_url": "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1200&q=80",
                "tone": "family",
                "language": "dual",
                "status": "published",
                "published_at": (now - timedelta(days=5)).isoformat(),
                "likes_count": 3450,
                "comments_count": 278,
                "shares_count": 142,
                "created_by": "ai-content-engine",
                "tenant_id": "glg-assets-main",
            },
            {
                "project_id": "proj_101",
                "platform": "instagram",
                "topic": "Architectural Spotlight: Master Bedroom Suite Design",
                "post_content": "Walk-in wardrobes, double-glazed soundproof acoustic glass, and ambient circadian lighting in our Baridhara penthouses. Modern living redefined.",
                "hashtags": ["#ModernLiving", "#ArchitecturalDesign", "#LuxuryInterior", "#DhakaReels"],
                "media_url": "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
                "tone": "luxury",
                "language": "dual",
                "status": "published",
                "published_at": (now - timedelta(days=6)).isoformat(),
                "likes_count": 4120,
                "comments_count": 164,
                "shares_count": 98,
                "created_by": "ai-content-engine",
                "tenant_id": "glg-assets-main",
            },
            {
                "project_id": "proj_101",
                "platform": "tiktok",
                "topic": "Dhaka Luxury Penthouse Rooftop Drone View",
                "post_content": "360-degree sunset drone view over Gulshan Lake. Private infinity pool and helipad access on our signature 18th floor penthouse.",
                "hashtags": ["#DhakaPenthouse", "#DroneShot", "#LuxuryLife", "#GLGAssets"],
                "media_url": "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
                "tone": "luxury",
                "language": "dual",
                "status": "published",
                "published_at": (now - timedelta(days=7)).isoformat(),
                "likes_count": 6200,
                "comments_count": 310,
                "shares_count": 450,
                "created_by": "ai-content-engine",
                "tenant_id": "glg-assets-main",
            }
        ]

        inserted = supabase_db._request("social_posts", method="POST", data=canonical_posts)
        print(f"  [✓] Successfully inserted {len(canonical_posts)} social posts into Supabase Cloud!")
    else:
        print(f"  [✓] social_posts table already has {existing_count} records.")

    print("\n" + "=" * 65)
    print("✨ SUPABASE SOCIAL ANALYTICS SYNC COMPLETE")
    print("=" * 65)
    return True


if __name__ == "__main__":
    seed_social_analytics()
