# TiviMate EPG — USA, Europe & Arabic

Free automatic TV guide updates on GitHub Actions and GitHub Pages for Sony BRAVIA / TiviMate.

## Status

- 11,042 channel names for EPG matching (United States, Europe and Arabic channels).
- No IPTV account login, passwords, provider IDs or streaming URLs are included.
- A successful build publishes `guide.xml`, `guide.xml.gz` and `status.json` to GitHub Pages.
- The XMLTV guide only contains real retrieved programmes. Missing playlist IDs may still require manually using **Assign EPG** in TiviMate.
- The last working guide is kept on build failure.

## One-time setup

1. Open repository **Settings → Pages → Build and deployment → Source → GitHub Actions**.
2. Open **Actions → Build and Publish EPG → Run workflow** and run it on `main`.
3. Wait until both `build` and `deploy` succeed.
4. Open https://atharui.github.io/tivimate-epg/status.json to check the latest published counts.
5. In TiviMate add `https://atharui.github.io/tivimate-epg/guide.xml` under EPG Sources, enable it for the playlist and refresh.

The build is scheduled at 06:17 and 18:17 Asia/Riyadh (03:17 and 15:17 UTC). GitHub can delay scheduled tasks or disable them after 60 days without activity in a public repository.

## Privacy and limitations

This repository is **public**. `channels.csv` contains the channel display names, EPG IDs and regions, but no IPTV credentials or streaming links. The private TiviMate backup and original full channel exports must **never** be committed.

Some third-party EPG listings may have redistribution restrictions; assess source licenses before continuing public hosting. Sources may be blocked or change format, in which case the pipeline refuses to publish an insufficient guide.
