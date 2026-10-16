# this_file: tools/tests/test_build_getgo.py
"""Exercise the real catalogue pipeline with two small, public GetGo fonts."""

import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from unittest.mock import patch

from fontTools.ttLib import TTFont
from PIL import Image
from yaplon import oyaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_getgo

ROOT = Path(__file__).resolve().parents[2]


class BuildGetGoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for family in ("baar", "star"):
            src = ROOT / "getgo-fonts/cc0" / family
            dst = self.root / "getgo-fonts/cc0" / family
            dst.mkdir(parents=True)
            stem = family
            for ext in ("ttf", "vfj", "md", "yaml"):
                shutil.copyfile(src / f"{stem}.{ext}", dst / f"{stem}.{ext}")
        prolog = self.root / "srcdocs/prolog.md"
        prolog.parent.mkdir()
        shutil.copyfile(ROOT / "srcdocs/prolog.md", prolog)
        illustrations = self.root / "src_docs/md/illustrations"
        illustrations.mkdir(parents=True)
        shutil.copyfile(
            ROOT / "src_docs/md/illustrations/baar.png", illustrations / "baar.png"
        )
        # The complete pipeline must work without the optional Rust executable.
        optimizer = patch.object(build_getgo, "is_usvg", False)
        optimizer.start()
        self.addCleanup(optimizer.stop)

    def build(self) -> build_getgo.GetGoDocs:
        builder = build_getgo.GetGoDocs(self.root)
        builder.make()
        return builder

    def snapshot(self) -> dict[str, tuple[str, int]]:
        return {
            p.relative_to(self.root).as_posix(): (
                hashlib.sha256(p.read_bytes()).hexdigest(),
                p.stat().st_mtime_ns,
            )
            for p in self.root.rglob("*")
            if p.is_file()
        }

    def test_build_twice_has_identical_bytes_and_mtimes(self) -> None:
        self.build()
        first = self.snapshot()
        with patch.object(
            build_getgo.vharfbuzz,
            "Vharfbuzz",
            side_effect=AssertionError("unchanged specimen rendered"),
        ):
            self.build()
        self.assertEqual(
            first, self.snapshot(), "second build must not rewrite any output"
        )

    def test_headers_and_properdocs_paths(self) -> None:
        self.build()
        md = self.root / "src_docs/md"
        for stem in ("index", "baar", "star"):
            text = (md / f"{stem}.md").read_text()
            self.assertTrue(
                text.startswith(f"---\nthis_file: src_docs/md/{stem}.md\n"), stem
            )
            self.assertNotIn("../illustrations/", text, stem)
        self.assertTrue(
            (md / "css/fonts.css")
            .read_text()
            .startswith("/* this_file: src_docs/md/css/fonts.css */\n")
        )
        self.assertIn(
            "[![GG Baar](illustrations/baar.png)](illustrations/baar.png)",
            (md / "baar.md").read_text(),
            "illustration must use migrated source layout",
        )
        self.assertIn(
            "src: url(../fonts/baar.woff2)",
            (md / "css/fonts.css").read_text(),
            "CSS must resolve its sibling font directory",
        )
        data = json.loads((self.root / "fonts.json").read_text())
        for family in data.values():
            for kind in ("svg", "png"):
                url = family["url"][kind]
                self.assertIn("/main/docs/images/", url, url)
                self.assertNotIn("src_docs", url, url)
                self.assertTrue((md / "images" / url.rsplit("/", 1)[-1]).is_file(), url)

    def test_authored_script_order_is_stable(self) -> None:
        path = self.root / "getgo-fonts/cc0/star/star.yaml"
        metadata = oyaml.read_yaml(path.read_text())
        order = list(reversed(metadata["scripts"]))
        self.assertGreater(len(order), 1, "fixture must exercise script ordering")
        metadata["scripts"] = order
        path.write_text(oyaml.yaml_dump(metadata))
        self.build()
        self.build()
        self.assertEqual(
            order,
            oyaml.read_yaml(path.read_text())["scripts"],
            "authored script order was lost",
        )
        self.assertIn(
            "scripts: " + ", ".join(order),
            (self.root / "src_docs/md/star.md").read_text(),
        )

    def test_changed_font_with_same_mtime_only_updates_its_outputs(self) -> None:
        self.build()
        first = self.snapshot()
        path = self.root / "getgo-fonts/cc0/baar/baar.ttf"
        stat = path.stat()
        with TTFont(path, recalcTimestamp=False) as font:
            font["name"].setName("GG BaaR", 4, 3, 1, 0x409)
            glyph = font.getBestCmap()[ord("D")]
            width, lsb = font["hmtx"][glyph]
            font["hmtx"][glyph] = width + 111, lsb
            font.save(path)
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        self.build()
        second = self.snapshot()
        for path, value in first.items():
            if "star" in path:
                self.assertEqual(
                    value, second[path], f"unrelated font output rewritten: {path}"
                )
        for path in (
            "src_docs/md/fonts/baar.woff2",
            "src_docs/md/images/baar.svg",
            "src_docs/md/baar.md",
        ):
            self.assertNotEqual(
                first[path][0], second[path][0], f"changed font output is stale: {path}"
            )

    def test_markdown_edit_and_source_touch_do_not_render_specimens(self) -> None:
        self.build()
        first = self.snapshot()
        article = self.root / "getgo-fonts/cc0/baar/baar.md"
        article.write_text(article.read_text() + "\nNew author note.\n")
        (self.root / "getgo-fonts/cc0/star/star.ttf").touch()
        with patch.object(
            build_getgo.vharfbuzz,
            "Vharfbuzz",
            side_effect=AssertionError("text edit rendered specimen"),
        ):
            self.build()
        second = self.snapshot()
        self.assertIn(
            "New author note.", (self.root / "src_docs/md/baar.md").read_text()
        )
        for path, value in first.items():
            if path.startswith("src_docs/md/") and not path.endswith("/baar.md"):
                self.assertEqual(
                    value, second[path], f"unrelated output rewritten: {path}"
                )

    def test_sample_edit_and_missing_output_are_rebuilt(self) -> None:
        self.build()
        path = self.root / "getgo-fonts/cc0/baar/baar.yaml"
        metadata = oyaml.read_yaml(path.read_text())
        metadata["sample_text"] = "DECODE"
        path.write_text(oyaml.yaml_dump(metadata))
        first = self.snapshot()
        (self.root / "src_docs/md/fonts/star.woff2").unlink()
        self.build()
        second = self.snapshot()
        self.assertNotEqual(
            first["src_docs/md/images/baar.svg"][0],
            second["src_docs/md/images/baar.svg"][0],
            "new sample did not render",
        )
        self.assertEqual(
            first["src_docs/md/fonts/baar.woff2"],
            second["src_docs/md/fonts/baar.woff2"],
            "sample edit rewrote webfont",
        )
        self.assertEqual(
            first["src_docs/md/fonts/star.woff2"][0],
            second["src_docs/md/fonts/star.woff2"][0],
            "missing webfont was not reproduced",
        )

    def test_zip_contains_current_sources_and_is_not_rewritten_on_touch(self) -> None:
        self.build()
        archive = self.root / "getgo-fonts-for-fontlab.zip"
        before = archive.stat().st_mtime_ns
        with zipfile.ZipFile(archive) as z:
            files = {
                p.relative_to(self.root / "getgo-fonts").as_posix(): p
                for p in (self.root / "getgo-fonts").rglob("*")
                if p.is_file()
            }
            self.assertEqual(
                set(files), set(z.namelist()), "ZIP payload differs from font sources"
            )
            for name, path in files.items():
                self.assertEqual(
                    z.getinfo(name).external_attr >> 16,
                    0o644,
                    f"ZIP member must extract as 0644: {name}",
                )
                self.assertEqual(
                    path.read_bytes(), z.read(name), f"stale ZIP member: {name}"
                )
        for p in (self.root / "getgo-fonts").rglob("*"):
            if p.is_file():
                p.touch()
        self.build()
        self.assertEqual(
            before, archive.stat().st_mtime_ns, "mtime-only changes rewrote the ZIP"
        )

    def test_render_has_committed_structure_and_ink_across_specimen(self) -> None:
        self.build()
        ns = {"svg": "http://www.w3.org/2000/svg"}
        svg = ET.parse(self.root / "src_docs/md/images/baar.svg").getroot()
        reference = ET.parse(ROOT / "src_docs/md/images/baar.svg").getroot()
        x, y, width, height = map(float, svg.attrib["viewBox"].split())
        self.assertEqual((x, y), (0, 0), "specimen viewport must start at the origin")
        ref_width, ref_height = map(float, reference.attrib["viewBox"].split()[2:])
        self.assertAlmostEqual(
            width / ref_width,
            1,
            delta=0.05,
            msg="specimen's horizontal font metrics changed unexpectedly",
        )
        self.assertTrue(
            0.5 < height / ref_height < 2, "specimen lost its font-scale viewBox"
        )
        self.assertTrue(
            svg.findall("svg:g", ns), "font-space Y-flip must be on a group"
        )
        self.assertIn(
            "-1", svg.find("svg:g", ns).attrib["transform"], "Y-flip is missing"
        )
        uses = svg.findall(".//svg:use", ns)
        paths = {
            path.get("id"): path.get("d") for path in svg.findall(".//svg:path", ns)
        }
        # New vharfbuzz emits uses for spaces; usvg drops those empty paths.
        glyphs = (
            [use for use in uses if paths.get(use.get("href", "").removeprefix("#"))]
            if uses
            else svg.findall(".//svg:path", ns)
        )
        self.assertEqual(
            len(glyphs),
            len(reference.findall(".//svg:path", ns)),
            "specimen glyph payload differs from committed structure",
        )
        with (
            Image.open(self.root / "src_docs/md/images/baar.png") as im,
            Image.open(ROOT / "src_docs/md/images/baar.png") as ref,
        ):
            self.assertEqual(im.size, ref.size, "specimen canvas size changed")
            alpha = im.convert("RGBA").getchannel("A")
            bounds = alpha.getbbox()
            ref_bounds = ref.convert("RGBA").getchannel("A").getbbox()
            self.assertIsNotNone(bounds, "specimen must contain visible ink")
            self.assertGreaterEqual(
                bounds[2] - bounds[0],
                (ref_bounds[2] - ref_bounds[0]) * 0.9,
                "glyphs are clipped to a small part of the specimen",
            )
            self.assertTrue(
                0 < bounds[1] < bounds[3] < im.height, "vertical ink is clipped"
            )
            for left in range(0, ref_bounds[2] - 50, 50):
                self.assertIsNotNone(
                    alpha.crop((left, 0, left + 50, im.height)).getbbox(),
                    f"specimen has no ink in horizontal band {left}",
                )

    def test_svg_normalization_handles_zero_and_negative_origins(self) -> None:
        for viewbox, payload, output_height, expected in (
            ("0 0 100 100", '<path d="M10 10h30v20H10z"/>', 100, (10, 70, 40, 90)),
            (
                "-10 -20 100 100",
                '<defs><path id="ink" d="M10 10h30v20H10z"/></defs><use href="#ink"/>',
                1100,
                (20, 550, 50, 570),
            ),
        ):
            with self.subTest(viewbox=viewbox):
                raw = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox}" transform="matrix(1 0 0 -1 0 0)">
                {payload}</svg>'''
                normalized = build_getgo.normalize_specimen_svg(raw)
                svg = ET.fromstring(normalized)
                self.assertEqual(
                    svg.attrib["viewBox"],
                    f"0 0 100 {output_height}",
                    "viewBox normalization failed",
                )
                self.assertNotIn(
                    "transform",
                    svg.attrib,
                    "root transforms are not portable to CairoSVG",
                )
                png = build_getgo.cairosvg.svg2png(
                    bytestring=normalized.encode(), output_height=output_height
                )
                with Image.open(io.BytesIO(png)) as im:
                    self.assertEqual(
                        im.getbbox(), expected, "font-space transform is incorrect"
                    )

    def test_description_edit_never_renders_specimens(self) -> None:
        self.build()
        first = self.snapshot()
        yaml = self.root / "getgo-fonts/cc0/baar/baar.yaml"
        metadata = oyaml.read_yaml(yaml.read_text())
        metadata["description"] += " with revised description"
        yaml.write_text(oyaml.yaml_dump(metadata))
        with patch.object(
            build_getgo.vharfbuzz,
            "Vharfbuzz",
            side_effect=AssertionError("description edit rendered specimen"),
        ):
            self.build()
        self.assertIn(
            "revised description", (self.root / "src_docs/md/baar.md").read_text()
        )
        second = self.snapshot()
        for name, value in first.items():
            if name.startswith(("src_docs/md/images/", "src_docs/md/fonts/")):
                self.assertEqual(
                    value,
                    second[name],
                    f"description edit rewrote binary asset: {name}",
                )

    def test_generated_sample_is_used_after_yaml_rewrite(self) -> None:
        self.build()
        yaml = self.root / "getgo-fonts/cc0/baar/baar.yaml"
        metadata = oyaml.read_yaml(yaml.read_text())
        del metadata["sample_text"]
        yaml.write_text(oyaml.yaml_dump(metadata))
        baseline = self.committed_fixture()
        (self.root / ".cache/getgo-build.json").unlink()
        before = (self.root / "src_docs/md/images/baar.svg").read_bytes()
        with (
            patch.object(build_getgo, "committed_sources", return_value=baseline),
            patch.object(
                build_getgo.GetGoFont, "get_sample_text", return_value="DECODE"
            ),
        ):
            self.build()
        self.assertEqual(
            oyaml.read_yaml(yaml.read_text())["sample_text"],
            "DECODE",
            "missing sample was not generated",
        )
        self.assertNotEqual(
            before,
            (self.root / "src_docs/md/images/baar.svg").read_bytes(),
            "render decision preceded the YAML rewrite",
        )
        self.assertIn(
            ">DECODE</p>",
            (self.root / "src_docs/md/baar.md").read_text(),
            "page has a stale sample",
        )

    def test_fingerprint_mismatch_refreshes_all_pages_and_css(self) -> None:
        self.build()
        files = [self.root / f"src_docs/md/{name}.md" for name in ("baar", "star")]
        files.append(self.root / "src_docs/md/css/fonts.css")
        for file in files:
            file.write_text(file.read_text() + "\nSTALE TEMPLATE\n")
        with (
            patch.object(
                build_getgo, "generator_fingerprint", return_value="new generator"
            ),
            patch.object(
                build_getgo.vharfbuzz,
                "Vharfbuzz",
                side_effect=AssertionError("template change rendered specimen"),
            ),
        ):
            self.build()
        for file in files:
            self.assertNotIn(
                "STALE TEMPLATE",
                file.read_text(),
                f"generator change left stale output: {file.name}",
            )

    def test_fingerprint_tracks_script_version_and_dependencies(self) -> None:
        current = build_getgo.generator_fingerprint()
        with patch.object(build_getgo, "__version__", "changed version"):
            self.assertNotEqual(
                current,
                build_getgo.generator_fingerprint(),
                "version missing from fingerprint",
            )
        source = self.root / "changed_generator.py"
        source.write_text("# changed generator\n")
        with patch.object(build_getgo, "__file__", str(source)):
            self.assertNotEqual(
                current,
                build_getgo.generator_fingerprint(),
                "script bytes missing from fingerprint",
            )
        with patch.object(build_getgo, "version", return_value="changed dependency"):
            self.assertNotEqual(
                current,
                build_getgo.generator_fingerprint(),
                "dependencies missing from fingerprint",
            )

    def test_corrupt_cache_is_a_cold_cache(self) -> None:
        self.build()
        baseline = self.committed_fixture()
        first = {
            k: v for k, v in self.snapshot().items() if not k.startswith(".cache/")
        }
        for content in ("{", "[]", '{"sources": []}'):
            with self.subTest(content=content):
                (self.root / ".cache/getgo-build.json").write_text(content)
                with (
                    patch.object(
                        build_getgo, "committed_sources", return_value=baseline
                    ),
                    patch.object(
                        build_getgo.vharfbuzz,
                        "Vharfbuzz",
                        side_effect=AssertionError(
                            "corrupt cache bypassed Git bootstrap"
                        ),
                    ),
                ):
                    self.build()
                after = {
                    k: v
                    for k, v in self.snapshot().items()
                    if not k.startswith(".cache/")
                }
                self.assertEqual(first, after, "corrupt cache changed released outputs")

    def test_force_cli_rebuilds_existing_outputs(self) -> None:
        self.build()
        for file in ("baar.md", "css/fonts.css", "images/baar.png", "fonts/baar.woff2"):
            (self.root / "src_docs/md" / file).write_bytes(b"STALE OUTPUT")
        (self.root / "getgo-fonts-for-fontlab.zip").write_bytes(b"STALE ZIP")
        command = [
            sys.executable,
            str(ROOT / "tools/build_getgo.py"),
            "--root",
            str(self.root),
            "--force",
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, f"force build failed: {result.stderr}")
        self.assertNotIn(
            "STALE OUTPUT",
            (self.root / "src_docs/md/baar.md").read_text(),
            "forced page is stale",
        )
        self.assertNotIn(
            "STALE OUTPUT",
            (self.root / "src_docs/md/css/fonts.css").read_text(),
            "forced CSS is stale",
        )
        with Image.open(self.root / "src_docs/md/images/baar.png") as im:
            self.assertIsNotNone(im.getbbox(), "forced PNG has no ink")
        with TTFont(self.root / "src_docs/md/fonts/baar.woff2") as font:
            self.assertIn("name", font, "forced WOFF2 is invalid")
        with zipfile.ZipFile(self.root / "getgo-fonts-for-fontlab.zip") as z:
            self.assertIsNone(z.testzip(), "forced archive is corrupt")

    def committed_fixture(self) -> dict[str, str]:
        """Model Git's ls-tree using real fixture bytes; no test commits needed."""
        return {
            p.relative_to(self.root).as_posix(): hashlib.sha1(
                f"blob {len(p.read_bytes())}\0".encode() + p.read_bytes()
            ).hexdigest()
            for folder in ("getgo-fonts", "src_docs/md/illustrations")
            for p in (self.root / folder).rglob("*")
            if p.is_file()
        }

    def test_cold_cache_preserves_released_outputs_and_detects_dirty_font(self) -> None:
        self.build()
        baseline = self.committed_fixture()
        page = self.root / "src_docs/md/baar.md"
        page.write_text(
            page.read_text() + "\nReleased character map from older Unicode data.\n"
        )
        (self.root / ".cache/getgo-build.json").unlink()
        first = {
            k: v for k, v in self.snapshot().items() if not k.startswith(".cache/")
        }
        with patch.object(build_getgo, "committed_sources", return_value=baseline):
            with patch.object(
                build_getgo.vharfbuzz,
                "Vharfbuzz",
                side_effect=AssertionError("cold cache rendered unchanged font"),
            ):
                self.build()
            second = {
                k: v for k, v in self.snapshot().items() if not k.startswith(".cache/")
            }
            self.assertEqual(
                first,
                second,
                "cold cache must preserve released output bytes and mtimes",
            )
            (self.root / ".cache/getgo-build.json").unlink()
            font = self.root / "getgo-fonts/cc0/baar/baar.ttf"
            builder = build_getgo.GetGoDocs(self.root)
            self.assertFalse(
                builder.source_changed(font),
                "committed font must match the bootstrap hash",
            )
            stat = font.stat()
            font.write_bytes(font.read_bytes() + b"changed")
            os.utime(font, ns=(stat.st_atime_ns, stat.st_mtime_ns))
            self.assertTrue(
                builder.source_changed(font),
                "cold cache must detect changed bytes despite equal mtime",
            )

    def test_removed_archive_member_is_detected_without_a_cache(self) -> None:
        self.build()
        baseline = self.committed_fixture()
        (self.root / ".cache/getgo-build.json").unlink()
        (self.root / "getgo-fonts/cc0/baar/baar.vfj").unlink()
        with patch.object(build_getgo, "committed_sources", return_value=baseline):
            self.build()
        with zipfile.ZipFile(self.root / "getgo-fonts-for-fontlab.zip") as z:
            self.assertNotIn(
                "cc0/baar/baar.vfj", z.namelist(), "deleted source remains archived"
            )

    def test_vfj_edit_updates_zip_without_touching_site_outputs(self) -> None:
        self.build()
        first = self.snapshot()
        source = self.root / "getgo-fonts/cc0/baar/baar.vfj"
        source.write_bytes(source.read_bytes() + b"\n")
        with patch.object(
            build_getgo.vharfbuzz,
            "Vharfbuzz",
            side_effect=AssertionError("VFJ edit rendered specimen"),
        ):
            self.build()
        second = self.snapshot()
        for path, value in first.items():
            if path.startswith("src_docs/"):
                self.assertEqual(
                    value,
                    second[path],
                    f"VFJ edit rewrote unrelated site output: {path}",
                )
        with zipfile.ZipFile(self.root / "getgo-fonts-for-fontlab.zip") as z:
            self.assertEqual(
                source.read_bytes(),
                z.read("cc0/baar/baar.vfj"),
                "updated VFJ was not archived",
            )

    @unittest.skipUnless(shutil.which("usvg"), "optional usvg is not installed")
    def test_build_with_optional_usvg_is_idempotent(self) -> None:
        from sh import usvg

        with (
            patch.object(build_getgo, "is_usvg", True),
            patch.object(build_getgo, "usvg", usvg, create=True),
        ):
            self.build()
            first = self.snapshot()
            self.build()
            self.assertEqual(
                first,
                self.snapshot(),
                "optimizer caused unchanged outputs to be rewritten",
            )


if __name__ == "__main__":
    unittest.main()
