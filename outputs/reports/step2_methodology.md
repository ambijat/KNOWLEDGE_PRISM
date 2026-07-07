# Step 2 — Literature pull via the looping knowledge logic

## From eigenspace to seeds
The publication eigenspace (47 works, weighted by citation × recency) resolved into
**five latent axes**, each already an A×B fusion of an empirical object with a method lens:

1. Af-Pak regional security × realism / RSCT
2. Afghan state & ethnicity × critical geopolitics / ethnogeopolitics
3. India energy corridors × classical geopolitics / subaltern
4. BRI connectivity × geoeconomic simulacrum / semiotics
5. China–Central Asia–Eurasia × classical geopolitics / RSCT

The top **intersectionables** (empirical × method seams, weighted) seeded Step 2. Per the
chosen strategy ("bridge the gap"), each seed query paired an empirical anchor with the
**computational / formal modelling lens** the stated research goal needs but the published
output under-samples.

## The loop (three passes)
- **Wave 1 — seed.** 12 bridge queries on OpenAlex + 8 on arXiv → 314 unique OpenAlex hits.
  LLM relevance screen (IR/geopolitics × modelling) kept **47**.
- **Wave 2 — citation loop.** Expanded the 8 IR-that-models hubs along the citation graph
  (who-cites + references) → 452 neighbours, screened → **27** kept. This vein drifted toward
  the BRI / economic-geography cluster (axis 4), so a correction pass followed.
- **Wave 2 — method frontier.** Re-expanded the 5 method-anchored hubs (systems theory,
  semiotics, ontology, taxonomy) → 172 neighbours → **12** foundational modelling works
  (Wasserman & Faust; Axelrod; Epstein; formal ontology; semantic network analysis; Pajek/UCINET).

## Result
**86 unique papers**, 1994–2025, median 82 citations, 80 with DOIs (full-text retrievable).
See `step2_corpus.csv` (columns: id, doi, title, year, cites, type, venue, wave, reason).

## What the loop revealed about the boundary
The empirical layer (A) is well-served by IR literature; the method layer (B) splits into
(i) modelling apparatus that exists but is rarely applied to your region, and (ii) a thin
but real IR-that-models tradition (Cyberpolitics; Territorial Conflicts in World Society;
semiotic geopolitics). The intersection the goal targets — *formal/computational models of
regional security-complex knowledge structures* — is genuinely sparse. That sparseness is
the opportunity, not a gap in the search.

## Next iterations of the loop (optional)
- Round 2 snowball from the 12 frontier works, filtered to IR/geopolitics applications only.
- Cross-reference the 86 against your `bridge_concepts.csv` and Zotero to mark own-vs-need.
- Targeted refresh: post-2021 Taliban/Afghanistan + BRI energy empirics to update axes 1 & 5.
