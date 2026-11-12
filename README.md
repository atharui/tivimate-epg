# TiviMate EPG — US, European & Arabic channels

An automatically refreshed XMLTV programme guide generated from public EPG source data and a sanitized channel-name/EPG-ID list.

**Active TiviMate EPG URL:**  
https://github.com/atharui/tivimate-epg/releases/download/epg-current/guide.xml.gz

The guide is released via **GitHub Releases**, not GitHub Pages. GitHub Actions runs at about 06:17 and 18:17 Saudi time; actual start times may vary. No local PowerShell tasks, VPS, or IPTV credentials are required.

## Reliability and correctness

1. The Python builder gathers programme data from external sources and matches channels by ID, bilingual display-name and US affiliate callsign.
2. Known provider-ID mistakes are refused. If a single EPG ID points to **different source schedules**, all conflicting mappings are quarantined rather than arbitrarily selecting the first.
3. `epg_quality.py` checks the XMLTV data, removes duplicate events and invalid durations, and quarantines **contradictory titles occupying the same time slot**. Expired listings beyond the useful window are removed.
4. `publish_guide.py` validates the **sanitized** XMLTV, checks current/future listings, and calculates coverage from the programme records actually included.
5. The Release asset `guide.xml.gz` is updated only after all tests and quality gates pass. Follow the workflow status at [Actions](https://github.com/atharui/tivimate-epg/actions).

**Important limitations:** A validated XMLTV file still cannot prove a broadcast's real schedule matches the channel. Some source schedules may be wrong without containing invalid times or contradictory records. Channels with missing or incorrect playlist `tvg-id` may require using **Assign EPG** in TiviMate or corrections by the IPTV provider. Never invent programmes simply to raise the coverage percentage.

### Known provider-side mistakes

See [KNOWN_ID_ISSUES.md](KNOWN_ID_ISSUES.md). The publicly shared playlist metadata contained at least four clearly mismatched beIN channel IDs. These cannot be fixed for the live IPTV account merely by editing our XMLTV builder.

## Privacy

The public `channels.csv` contains channel names and guide identifiers but **no subscription passwords, stream addresses, IPTV server access URLs, or provider stream IDs**. Never upload TiviMate backups or raw account exports. External EPG providers may have distribution terms that need to be respected.

## Debugging

- [Latest guide asset](https://github.com/atharui/tivimate-epg/releases/download/epg-current/guide.xml.gz)
- [Workflow history and audit logs](https://github.com/atharui/tivimate-epg/actions)
- [Latest Release](https://github.com/atharui/tivimate-epg/releases/tag/epg-current)

If GitHub's workflow fails, investigate the test, source-download, quality-check, or release step before triggering another run. Do not clear your working TiviMate guide until a replacement has been verified.
