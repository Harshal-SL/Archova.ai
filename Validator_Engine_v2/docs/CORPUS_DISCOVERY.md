# Real-World Corpus Discovery

## 1. Corpus Path and Overview
- **Environment Variable**: `REAL_WORLD_CORPUS_PATH`
- **Default Path**: `d:/Archova.ai/ai_engine/data/RAG` (or relative `../ai_engine/data/RAG`)
- **Total Folders in RAG Root**: 22 subdirectories
- **Configured Target Folders**:
  1. `category_10_real_world_systems`: 25 files
  2. `domain_architectures`: 14 files
  3. `category_11_failure_modes`: 28 files
  - **Total Configured Files**: 67 markdown files

## 2. Folder Tree & File Counts
```text
ai_engine/data/RAG/
├── category_10_real_world_systems/   (25 markdown files, avg 2.1 KB)
├── domain_architectures/             (14 markdown files, avg 8.5 KB)
├── category_11_failure_modes/        (28 markdown files, avg 2.1 KB)
├── category_1_architecture_patterns/ (42 markdown files)
├── category_2_architecture_decisions/(20 markdown files)
├── category_3_scaling_techniques/    (20 markdown files)
├── category_4_caching_strategies/    (20 markdown files)
├── category_5_database_design/       (25 markdown files)
├── category_6_messaging_systems/     (20 markdown files)
├── category_7_infrastructure_components/ (20 markdown files)
├── category_8_deployment_strategies/ (18 markdown files)
├── category_9_security_architecture/ (22 markdown files)
└── ... (archetypes, ai_systems, cloud_architecture, lld/hld_templates)
```

## 3. Systems Covered in `category_10_real_world_systems`
All 25 systems:
1. `10.10_cloudflare_edge_network.md`: Cloudflare Edge Network
2. `10.11_tiktok_short_video_feed.md`: TikTok Short Video Feed
3. `10.12_instagram_photo_sharing.md`: Instagram Photo Sharing
4. `10.13_twitter_realtime_feed.md`: Twitter Realtime Feed
5. `10.14_linkedin_social_graph.md`: LinkedIn Social Graph
6. `10.15_reddit_forum_platform.md`: Reddit Forum Platform
7. `10.16_robinhood_trading_platform.md`: Robinhood Trading Platform
8. `10.17_shopify_commerce_platform.md`: Shopify Commerce Platform
9. `10.18_salesforce_crm_platform.md`: Salesforce CRM Platform
10. `10.19_dropbox_file_storage_system.md`: Dropbox File Storage System
11. `10.1_netflix_streaming_platform.md`: Netflix Streaming Platform
12. `10.20_youtube_video_platform.md`: YouTube Video Platform
13. `10.21_wikipedia_content_platform.md`: Wikipedia Content Platform
14. `10.22_paypal_payments_system.md`: PayPal Payments System
15. `10.23_uber_dynamic_pricing_architecture.md`: Uber Dynamic Pricing Architecture
16. `10.24_doordash_order_assignment_algorithm.md`: DoorDash Order Assignment Algorithm
17. `10.25_spotify_recommendation_engine.md`: Spotify Recommendation Engine
18. `10.2_whatsapp_messaging_system.md`: WhatsApp Messaging System
19. `10.3_amazon_E-commerce_system.md`: Amazon E-commerce System
20. `10.4_google_search_system.md`: Google Search System
21. `10.5_airbnb_marketplace_platform.md`: Airbnb Marketplace Platform
22. `10.6_stripe_payments_platform.md`: Stripe Payments Platform
23. `10.7_slack_collaboration_platform.md`: Slack Collaboration Platform
24. `10.8_zoom_video_conferencing_system.md`: Zoom Video Conferencing System
25. `10.9_github_code_hosting_platform.md`: GitHub Code Hosting Platform

## 4. Heading Structure of Case-Study Markdown
Each file in `category_10_real_world_systems` adheres to a strict canonical structure:
- `# <System Name>` (H1 Title)
- `## chunk_id`
- `## category`
- `## type`
- `## definition`
- `## when_to_use`
- `## when_not_to_use`
- `## decision_signals` (includes scale hints e.g. latency targets, request volume, offload ratios)
- `## advantages`
- `## disadvantages`
- `## anti_patterns`
- `## real_world_examples`
- `## related_patterns` (relative markdown links to architectural patterns)
- `## keywords`
- `## llm_hint`

### Sample Headings from 3 Case Studies
1. **`10.10_cloudflare_edge_network.md`**:
   - `# Cloudflare Edge Network`
   - `## decision_signals`
   - `## anti_patterns`
2. **`10.1_netflix_streaming_platform.md`**:
   - `# Netflix Streaming Platform`
   - `## when_to_use`
   - `## advantages`
3. **`10.6_stripe_payments_platform.md`**:
   - `# Stripe Payments Platform`
   - `## real_world_examples`
   - `## decision_signals`

## 5. Citations and URLs
- **External URLs (`http://`, `https://`)**: 0 occurrences across all files. No web URLs are cited.
- **Internal Cross-References**: Rich relative markdown links to related patterns under other categories (e.g., `[Rate Limiter Pattern](../category_1_architecture_patterns/1.38_rate_limiter_pattern.md)`).
- **UI Treatment**: When displaying references used, cite the internal pattern document and mark external source links as `"no source cited"`.

## 6. Stop Condition Check
- `category_10_real_world_systems` contains **25 usable files** (far exceeding the minimum threshold of 3).
- Headings are highly consistent across all 25 files, allowing clean structural section parsing (no fallback to paragraph-based parsing required).
