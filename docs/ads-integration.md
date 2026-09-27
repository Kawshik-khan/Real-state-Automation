# Ad Platform Metrics (Meta, Google Ads, TikTok)

The Social Media KPI page (`/social-analytics`), the Manager overview and the
channel donut read **only** metrics synced from the ad platforms. Nothing is
estimated or seeded: a value the platforms don't report is shown as "—".

## How it works

```
Meta Marketing API ─┐
Google Ads API ─────┼─► connectors (app/services/ads/*) ─► sync_service ─► AdsRepository ─► Supabase
TikTok Business API ┘         normalize to DailyMetric etc.    upserts       (PostgREST)
                                                                                 │
     /api/v1/analytics/social-kpis, /manager-overview ◄── analytics.py ◄─────────┘
```

| Table | Contents |
|---|---|
| `ad_accounts` | One row per connected account (currency, time zone, last sync) |
| `ad_campaigns` | Campaign names, status, objective, budget. `is_demo = true` marks seed rows |
| `ad_campaign_daily_metrics` | Per campaign × day × channel: impressions, clicks, spend (account currency), leads, chats, video views |
| `ad_campaign_period_reach` | De-duplicated reach for 7/30/90-day windows (`__account__` = whole account) |
| `ad_sync_runs` | Every sync attempt with status and error |
| `fx_rates` | Currency → BDT rates used for money totals |
| `leads` | Meta Lead Ads submissions (from the `leadgen` webhook) with campaign/ad IDs |

**Sync schedule** (background worker started with the API):
- First successful sync per account: backfill 90 days.
- Every `ADS_SYNC_INTERVAL_MINUTES` (default 60): re-pull the last 3 days.
- Once a day after `ADS_SYNC_NIGHTLY_HOUR_UTC` (default 20 = 02:00 Dhaka): re-pull 28 days, because platforms restate recent numbers.
- Managers and admins can press **Sync now** (7 days), or call `POST /api/v1/ads/sync`.

Upserts are keyed on platform IDs + date, so re-syncing a window overwrites rather than duplicates.

## 1. Apply the database migration

Run `backend/migrations/sql/0008_ads_metrics.sql` once in the Supabase SQL editor. It is idempotent, and Alembic revision `0008_ads_metrics` runs the same file.

It also **removes the `USING (true)` policies** that let anyone holding the public anon key read, change or delete `ad_campaigns`, `social_posts`, `leads`, `bookings`, `calendar_milestones`, `inventory_units` and the `ai_*` tables. The backend must therefore use `SUPABASE_SERVICE_ROLE_KEY`, not the anon key. Render already does.

## 2. Connect the platforms

Set the credentials in the backend environment (see `render.yaml`), or save them in **Developer Console → Service Integrations → Ad Platforms**, then press **Test**.

| Platform | Required | Where to get it |
|---|---|---|
| Meta | `META_ADS_ACCESS_TOKEN`, `META_AD_ACCOUNT_IDS` | Business Settings → System users → generate a token with `ads_read` (add `read_insights`, `pages_read_engagement`, `instagram_basic`, `instagram_manage_insights` for organic posts, and `leads_retrieval` for Lead Ads). Account IDs look like `act_123…`. |
| Google Ads | `GOOGLE_ADS_DEVELOPER_TOKEN`, `GOOGLE_ADS_CLIENT_ID`, `GOOGLE_ADS_CLIENT_SECRET`, `GOOGLE_ADS_REFRESH_TOKEN`, `GOOGLE_ADS_CUSTOMER_IDS` (+ `GOOGLE_ADS_LOGIN_CUSTOMER_ID` when using a manager account) | Developer token from the API Center (Basic access needs Google's review); OAuth client from Google Cloud; refresh token via the OAuth consent flow |
| TikTok | `TIKTOK_ADS_ACCESS_TOKEN`, `TIKTOK_ADVERTISER_IDS` | TikTok for Business developer app → advertiser authorization → long-term access token |

Organic Facebook/Instagram posts additionally use the existing `FACEBOOK_PAGE_ID`, `FACEBOOK_PAGE_ACCESS_TOKEN` and `INSTAGRAM_ACCOUNT_ID`.

**Lead Ads:** subscribe the Page to the `leadgen` webhook field at `/api/v1/social/facebook/webhook`. Set `FACEBOOK_APP_SECRET` so the `X-Hub-Signature-256` header is verified.

**Currency:** accounts not billed in BDT need a rate, via `PUT /api/v1/ads/fx-rates {"currency": "USD", "rate_to_bdt": 122.5}` (admin) or `FX_RATES_TO_BDT="USD=122.5"`. Spend with no rate is excluded from totals, and the page shows a warning.

## Metric definitions

- **Leads:** Meta's `lead` action (de-duplicated total); Google Ads `conversions`; TikTok `conversion` for lead-generation campaigns only.
- **Chats started:** Meta `onsite_conversion.messaging_conversation_started_7d` (click-to-WhatsApp/Messenger).
- **CTR** = clicks ÷ impressions. **CPL** = spend ÷ leads (—, not ৳0, when there are no leads).
- **Reach:** platform-de-duplicated account reach for 7/30/90-day windows. With a campaign/project filter it is the sum of campaign reach (people reached by two campaigns count twice), and it is unavailable per placement.
- **Deltas** compare against the preceding window of the same length.
- **AI reply rate:** conversations whose first customer message received an `ai` or `human_agent` reply; the median first-reply time is computed from `messages` timestamps.
- **Campaign → project:** linked automatically when the campaign name contains the project name (`PATCH /api/v1/ads/campaigns/{platform}/{id}/project` overrides it).

Campaign status is read-only here: pause or resume campaigns in the ad platform.
