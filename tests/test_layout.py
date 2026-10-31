"""Repo layout: maps live in maps/base/<source>/ and maps/overlays/.

Moving files must not change anything users already have: the site URL of each
map (/sources/<group>/<file>), so tak:// links and printed QR codes keep
working, and each map's slug (descriptions.yml keys, QR file names, health).
"""

from pathlib import Path

import yaml

from mapvalidator.catalog import (
    MAPS_DIR,
    PAGES_BASE,
    build_map_entry,
    is_overlay,
    iter_map_files,
    map_slug,
    site_path,
)

REPO = Path(__file__).resolve().parent.parent

TMS = """<?xml version="1.0" encoding="UTF-8"?>
<customMapSource><name>{name}</name><maxZoom>18</maxZoom><url>https://t.example/{{$z}}/{{$x}}/{{$y}}.png</url></customMapSource>
"""


class TestPaths:
    def test_overlay_is_a_file_in_the_overlays_folder(self):
        assert is_overlay(Path("maps/overlays/grg_fema_flood.xml"))
        assert not is_overlay(Path("maps/base/esri/esri_topo.xml"))

    def test_site_path_keeps_the_old_url(self):
        assert site_path(Path("maps/base/esri/esri_topo.xml")) == "esri/esri_topo.xml"
        assert (
            site_path(Path("maps/overlays/grg_fema_flood.xml"))
            == "GRG/grg_fema_flood.xml"
        )

    def test_slug_does_not_change_when_a_map_moves(self):
        assert map_slug(Path("maps/base/esri/esri_topo.xml")) == "esri-esri-topo"
        assert (
            map_slug(Path("maps/overlays/grg_fema_flood.xml")) == "grg-grg-fema-flood"
        )

    def test_entry_imports_from_the_old_url_and_links_the_new_file(self, tmp_path):
        f = tmp_path / MAPS_DIR / "base" / "esri" / "esri_topo.xml"
        f.parent.mkdir(parents=True)
        f.write_text(TMS.format(name="Esri Topo"))
        e = build_map_entry(f, tmp_path)
        assert e["slug"] == "esri-esri-topo"
        assert e["import_url"] == f"{PAGES_BASE}/sources/esri/esri_topo.xml"
        assert e["raw_url"].endswith("/maps/base/esri/esri_topo.xml")


class TestRepoLayout:
    def test_every_map_is_in_maps_base_or_maps_overlays(self):
        files = iter_map_files(REPO)
        assert files, "no maps found"
        for f in files:
            rel = f.relative_to(REPO)
            ok = rel.parts[:2] == (MAPS_DIR, "overlays") and len(rel.parts) == 3
            ok = ok or (rel.parts[:2] == (MAPS_DIR, "base") and len(rel.parts) == 4)
            assert ok, f"{rel}: maps go in maps/base/<source>/ or maps/overlays/"

    def test_overlay_files_keep_the_grg_prefix(self):
        # ATAK imports every map into one folder (atak/imagery/); the prefix
        # keeps overlay and base-map file names from colliding there.
        for f in iter_map_files(REPO):
            if is_overlay(f):
                assert f.name.startswith("grg_"), f.name

    def test_every_description_belongs_to_a_map(self):
        slugs = {map_slug(f) for f in iter_map_files(REPO)}
        described = set(
            yaml.safe_load((REPO / "maps" / "descriptions.yml").read_text())
        )
        assert described - slugs == set(), "descriptions for maps that do not exist"
