<!-- markdownlint-disable MD041 -- a PR body has no title heading -->
## What this changes

<!-- One or two sentences. Link the issue: "Closes #123". -->

## Adding or changing a map

- [ ] File is in `maps/base/<source>/` or `maps/overlays/` (`grg_` file prefix; the map name starts with "+")
- [ ] `minZoom` and `maxZoom` match where the server has real tiles
- [ ] Entry in `maps/descriptions.yml` (category, text, `test_point` for regional maps)
- [ ] Tested the way ATAK loads it:
      `uv run python -m mapvalidator --harness . --only <your map file>`
- [ ] The tile server allows this use (licence or terms linked below)

Guide: [Add a map](https://joshuafuller.github.io/ATAK-Maps/creating-custom-maps/)

## Other changes

- [ ] `uv run --extra dev pytest` passes
