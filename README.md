# Personal TiviMate EPG — USA, Europe & Arabic

A free scheduled XMLTV build deployed to GitHub Pages. No paid VPS, no local PowerShell tasks, no IPTV credentials.

## Setup

1. Create a **public** GitHub repository named `tivimate-epg` with a `main` branch.
2. Upload the files from this package while preserving `.github/workflows/publish-epg.yml`.
3. On GitHub go to **Settings → Pages → Build and deployment → Source → GitHub Actions**.
4. Under **Actions → Build and Publish EPG → Run workflow**, run the initial build. Check both jobs are green.
5. Configure TiviMate EPG source as `https://YOUR_USER.github.io/tivimate-epg/guide.xml` (replace YOUR_USER with your own login), enable it for your playlist and update EPG.

Scheduled builds: every 12 hours (06:17, 18:17 Saudi time), subject to GitHub scheduling delays. Successful builds deploy only when the generated guide has at least 1,500 channel IDs, 160,000 programme entries and a current/future sample. On build failure, the previous Pages deployment remains published.

Note: the input CSV is **public** in a free GitHub Pages repository; it contains channel names, EPG IDs and regions. It intentionally excludes provider IDs, source IDs, subscription credentials and streaming URLs. `EPG_Match_Report.csv` is *not* published. Only data obtained from independent programme sources is used. Check third-party EPG redistribution terms before public hosting.

GitHub may disable scheduled workflows in public repositories after **60 days without repository activity**. Check Actions periodically and re-enable if needed. GitHub Pages also serves an uncompressed XML version to preserve compatibility with the TiviMate source which worked on the TV.

Important: a row with missing playlist EPG ID might still require using TiviMate's Assign EPG even when a programme schedule was matched by name. The generated guide cannot change IDs already assigned by the IPTV provider.

## Coverage reporting

Open [status.json](https://atharui.github.io/tivimate-epg/status.json) for the per-region count of channels with **actual** programmes and the channel IDs represented in the XMLTV output.
The [coverage.json](https://atharui.github.io/tivimate-epg/coverage.json) file breaks it down by region. Source IDs without programme data are **not** counted as covered.

The guide builder prioritizes original matching feeds, adds publicly listed extra guides by country, and handles bilingual Arabic channel display names. US affiliate callsigns are never guessed from just a generic network name.