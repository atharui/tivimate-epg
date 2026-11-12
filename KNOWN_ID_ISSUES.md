# Known incorrect provider TVG IDs

These inconsistencies were detected from the user's local Xtream metadata. Names and guide IDs are shown; **no account details or stream URLs are included**.

| IPTV display name | Provider `tvg-id` | Issue |
|---|---|---|
| BEIN SPORTS 1 HD | `beinseries1.qa` | Sports stream mapped to a Series identifier |
| BEIN SPORTS XTRA 1 SD | `beINSportsXtra2.qa` | Xtra 1 mapped to Xtra 2 |
| BEIN SPORTS XTRA 2 SD | `beINSportsXtra3.qa` | Xtra 2 mapped to Xtra 3 |
| BEIN SPORTS XTRA 4 | `beinsportsxtra3.qa` | Xtra 4 mapped to Xtra 3 |

The guide builder refuses these **clearly contradictory provider mappings** so they cannot be treated as evidence of correct EPG coverage. However, TiviMate still reads the **original provider `tvg-id`** from the subscribed playlist; an EPG-only fix cannot rewrite that playlist.

**User action:** In TiviMate, long-press the relevant channel → **Assign EPG** → select the *correct station* from the current guide, or ask the IPTV provider to fix its channel IDs. Verify the displayed programme against the live broadcast. Do not use a similarly named programme guide from a different affiliate, time-shifted feed, or country unless the channel really carries the same schedule.

Other possibly incorrect IDs (e.g., regional feeds sharing a national guide) require review and are not changed automatically.
