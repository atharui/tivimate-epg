# NFL Teams FOX Rams / Redskins — EPG audit

**Problem:** The IPTV subscription lists these streams as NFL Teams FOX, not explicitly as full-time local FOX stations. Their playlist `EPGChannelID` is empty. Automatically matching the station callsign linked them to **ordinary local-channel programmes**, causing mismatches if the provider uses them as NFL-only/event feeds.

| Playlist channel | Previous automatic mapping | Status |
|---|---|---|
| USA: NFL Teams: FOX Rams (KTXL) Sacramento CA | `KTXL-DT.us_locals1` | Team-feed auto-mapping suspended pending stream verification |
| USA: NFL Teams: FOX Redskins (WBFF) Baltimore MD | `WBFF-DT.us_locals1` | Team-feed auto-mapping suspended pending stream verification |
| USA: NFL Teams: FOX Redskins (WTTG) Washington DC | `WTTG-DT.us_locals1` | Team-feed auto-mapping suspended pending stream verification |

These call signs belong to genuine FOX affiliates, **but that does not establish** whether the IPTV provider's special team-labelled stream carries the affiliate 24/7 or only changes to NFL coverage for games.

**Fix:** The guide builder no longer associates the three NFL team-labelled stream display names with ordinary local-station schedules. It still exposes dedicated *complete local station* choices as `FOX 40 KTXL Sacramento — complete local station`, `FOX 45 WBFF Baltimore — complete local station`, and `FOX 5 WTTG Washington — complete local station`. These should only be selected using TiviMate **Assign EPG** after checking that the live stream is truly the full local channel.

The NFL team formerly called *Redskins* is currently **Washington Commanders**. Outdated provider naming is another reason not to infer sports scheduling from the channel label alone.

**Not provided yet:** A confirmed game-only stream schedule. For this we must know whether these feeds are event-only and verify exactly which NFL matchups they actually broadcast. We should not fabricate programme entries or assign a national FOX schedule to a specific local market without proof.

TiviMate may cache a prior manual per-channel assignment. If wrong programmes continue after refreshing EPG, inspect/reassign that channel individually; removing an EPG name does not necessarily clear a saved manual mapping.
