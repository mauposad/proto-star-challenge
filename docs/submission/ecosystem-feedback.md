# Feedback to the ProtoStar ecosystem

## What got in the way

1. **Validity is metric-specific but not machine-labeled.** The CMU annual
   table exposes `Miss Tmax`, `Miss Tmin`, and `Miss Prcp`; participants must
   infer that average temperature and CDD need both temperature completeness
   checks, while precipitation and hottest-day values use different checks.
   Applying one generic valid-year filter would silently bias some targets.
2. **Cross-repository station linkage needs a stated contract.** CMU's
   `city_info.ID` can join directly to NOAA's GHCN inventory, and our
   reproducible report matched all 210 IDs. That capability was discoverable
   only by inspecting both schemas and fixed-width NOAA documentation.
3. **Data provenance needs freeze-friendly references.** NOAA's station
   inventory is a living file. A URL alone is insufficient to reproduce the
   exact metadata integration after an update.

## What would fix it

1. Publish a `valid_<metric>` boolean for each annual index using the
   challenge's scoring completeness rule, plus a short data contract that
   identifies the applicable missing-day columns.
2. Publish a compact station crosswalk with the intended join key, metadata
   source, and any known station-thread/location caveats.
3. Include a release manifest with source URLs, retrieval date, checksum,
   cutoff date, units, and the exact evaluation-validity rule. That would make
   the dataset directly usable by both people and automated research agents.
