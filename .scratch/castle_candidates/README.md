# Photo review: Castle + Liathmore

Hi Andre. Below are the candidate photos pulled from TripAdvisor (The Castle Country House, exterior shots only) and Wikipedia (Two-Mile Borris article + Liathmore Churches article).

Each candidate has:
1. The photo (rendered via `file:///` so it shows in your markdown previewer)
2. My recommendation
3. A draft caption written in our usual voice
4. A **Your comments** slot for you to tell me what to do

After you fill in your comments and save the file, ping me and I'll move the approved photos into `site/docs/assets/map-data/photos/...`, write the captions, add the new Liathmore marker to `markers.json`, and rebuild the map.

> **Heads up on a duplicate I spotted:** the TripAdvisor "streetview" shot is the same photo we already use as the primary blackcastle photo (`castle-streetview-summer.jpg`). I've included it below for completeness so you can verify, but no need to add it again.

---

## Castle (Blackcastle) — candidate photos

### 1. Streetview with country house in front (TripAdvisor)

![Castle streetview with country house](file:///C:/Users/andre/OneDrive/Documents/Development/tidytowns/.scratch/castle_candidates/ta_streetview.jpg)

**My take:** This is already our primary blackcastle photo (`castle-streetview-summer.jpg`). Likely a duplicate from the same source. **Skip — already in use.**

**Your comments / instructions:**
>Skip
>

---

### 2. Castle keep close-up (Wikipedia / Geograph)

![Close-up of the castle keep](file:///C:/Users/andre/OneDrive/Documents/Development/tidytowns/.scratch/castle_candidates/wiki_castle_geograph.jpg)

**My take:** **Strong include.** This complements the streetview by showing the castle on its own — you can clearly see all four storeys of the Norman tower house, the corner detail at the top, and just how massive the stonework is. Great second photo for the popup.

**Draft caption:**
> A closer look at the keep itself. You can see all four storeys of the Norman tower house, the corner turret, and the gorgeous medieval stonework that has been standing on the western edge of the village for nearly a thousand years.

**Your comments / instructions:**
>Include
>

---

### 3. The privately-owned country house (TripAdvisor, cloudy)

![Country house with castle in background](file:///C:/Users/andre/OneDrive/Documents/Development/tidytowns/.scratch/castle_candidates/ta_country-house.jpg)

**My take:** **Flagging for you.** This shot leans more "house" than "castle" — the keep is in the background but the focus is the privately-owned country house. Honest answer is I'd skip it because the streetview (#1) does the "house with castle behind" framing better.

**Draft caption (only if you decide to keep):**
> Another angle on the privately-owned country house at the foot of the Blackcastle. Even on an overcast day the keep makes an impression rising up behind.

**Your comments / instructions:**
> Skip
>

---

### 4. View through bramble at a stone doorway (TripAdvisor)

![View through bramble at a stone doorway](file:///C:/Users/andre/OneDrive/Documents/Development/tidytowns/.scratch/castle_candidates/ta_1000-year-old-castle.jpg)

**My take:** **Flagging for you.** TripAdvisor metadata says this is exterior, but visually it reads to me as if you're peering *into* the ruins through a doorway. You said no interior shots, so my default would be to skip it. Your call.

**Draft caption (only if you decide it counts as exterior):**
> A peek through the briars at one of the original stone doorways into the keep. The greenery has grown up around the base of the castle over the centuries and now wraps the medieval stonework.

**Your comments / instructions:**
> Skip
>

---

## Liathmore Monastic Site — proposed new marker

This one is missing from the map entirely. Liathmore is genuinely TMB's most significant heritage asset and the connection to our village school is a lovely detail to highlight.

**Proposed marker entry for `markers.json`:**

```json
{
  "id": "liathmore",
  "name": "Liathmore Monastic Site",
  "category": "Village Features",
  "color": "#2196F3",
  "coords": [52.67055, -7.66861],
  "desc": "Seventh-century monastic site about 2.8km east of the village, founded by St Mochoemog, the same saint our village school Scoil Mochaomhóg Naofa NS is named after. Two ruined churches and the foundation of an ancient round tower are still visible at the site, and the larger 12th-century church has a Romanesque doorway and a sheela-na-gig carving."
}
```

A few decisions baked in that you can override:
- **Category:** I put it in `Village Features` (same blue as Blackcastle and the Forge). Alternative is `Other` (dark grey) since it's outside the village proper. Tell me if you want it switched.
- **Coordinates** are from the Wikipedia article on Liathmore Churches: 52.67055°N, 7.66861°W. About 2.8km due east.
- **Description** mentions the round tower, two churches, the Romanesque doorway, and the sheela-na-gig. Trim or expand as you like.

**Your comments / instructions on the marker:**
> yes looks good
>

### Liathmore photo

![Liathmore round tower foundation and ruined church](file:///C:/Users/andre/OneDrive/Documents/Development/tidytowns/.scratch/castle_candidates/wiki_liathmore_round_tower.jpg)

**My take:** **Include as the primary Liathmore photo.** Shows both the round tower foundation circle in the foreground and a ruined church wall behind, so you get both monuments in one frame.

**Draft caption:**
> The foundation circle of the round tower at Liathmore, with one of the two ruined churches in the background. Saint Mochoemog founded a monastery here in the 7th century and gave his name to our village school.

**Your comments / instructions on the photo:**
>
>

---

## Bonus / optional Wikipedia photos

These two extras came back from the Wikipedia article. They don't fit Castle or Liathmore but I wanted to flag them in case you'd like them used elsewhere.

### Welcome sign on the approach road

![Two-Mile-Borris welcome sign on the approach](file:///C:/Users/andre/OneDrive/Documents/Development/tidytowns/.scratch/castle_candidates/wiki_village_sign.jpg)

**My take:** Could be added to one of the approach markers. Not urgent though, you already have a welcome-sign photo on `approach_east` (`welcome-sign-may-2026.jpg`).

**Your comments:**
> skip as that was before the village road was diverted
>

---

### Main street with Corcoran's pub and the church

![Main street with Corcoran's pub and the church](file:///C:/Users/andre/OneDrive/Documents/Development/tidytowns/.scratch/castle_candidates/wiki_village_church.jpg)

**My take:** Nice atmospheric village shot but `corcorans` and `church` markers already have their own photos, so probably not needed.

**Your comments:**
> Corcoran's doesn't have a photo? add it
>

---

## Questions for you (quick summary)

If you just want to fly through the decisions, these are the ones that matter:

1. **Photo #2 (castle keep close-up):** Include and use my draft caption? Yes / no / rewrite caption?
2. **Photo #3 (country house, cloudy):** Skip, or include?
3. **Photo #4 (bramble/doorway):** Skip (likely interior), or include as exterior?
4. **Liathmore marker:** Approve as proposed? Any text changes? Category change to `Other`?
5. **Bonus photos:** Want them placed somewhere, or just delete them from `.scratch/`?

