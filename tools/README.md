# tools

Scripts that rebuild a dealer demo from the dealer's own mobile.bg listings.
They ran from a session scratchpad during the batch run (2026-08-31); copied here so a
rebuild never depends on a temp dir.

- `harvest_dealer.py <host> [--max-cars N] [--skip N] [--out DIR]` — listing pages + photos.
  Pagination is `/obiavi/avtomobili-dzhipove/p-N`.
- `refetch_details.py <dealer.json>` — re-fetches each listing for price, km, first
  registration, equipment and the description (harvest_dealer only stores the summary fields).
- `gen_config.py` — shared constants (palettes, body-type symbols, compress) used by the builders.
- `kris_car_build.py [--install]` — the bespoke Крис Кар build: merges `harvest/` and
  `harvest2/` next to `tools/`, picks an exterior cover photo per car by a brightness/sky
  heuristic, writes the config with the dealer's verified facts, builds with
  `templates/auto-dealers/atelie/build.mjs`, and with `--install` copies into `sites/kris-car`.

Template changes that came with the kris-car touch-up (2026-09-02) live in the template itself
and apply to every future rebuild: stock filters (`src/scripts/stock.js`), lead forms that
compose an email / Viber / SMS to the dealer (`src/scripts/forms.js`), Open Graph + favicon,
config-driven contact-page claims, brand row on the home page, tags on cards.
