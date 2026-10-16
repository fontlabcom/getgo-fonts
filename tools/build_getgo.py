#!/usr/bin/env python3
# this_file: tools/build_getgo.py
"""Build catalogue sources and assets without rewriting unchanged output."""

__version__ = "1.0.0"

import argparse
import hashlib
import io
import json
import logging
import math
import random
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from collections import OrderedDict
from importlib.metadata import version
from pathlib import Path

import cairosvg
import fontTools.ttLib
import fontTools.unicodedata as ucd
import vharfbuzz
from PIL import Image
from yaplon import ojson, oyaml

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)
SPECIMEN_PADDING = 500  # Font units above/below the legacy vharfbuzz specimen.

is_usvg = False
try:
    from sh import usvg

    is_usvg = True
except ImportError:
    logger.info("Optional SVG optimizer unavailable: cargo install usvg")


def write_if_changed(path: Path, content: str | bytes) -> None:
    """Preserve output bytes and mtimes when the generated content is equal."""
    data = content.encode("utf-8") if isinstance(content, str) else content
    if path.is_file() and path.read_bytes() == data:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def committed_sources(root: Path) -> dict[str, str]:
    """Bootstrap a cold cache from committed input blobs, without trusting mtimes."""
    if not shutil.which("git"):
        return {}
    result = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "ls-tree",
            "-rz",
            "HEAD",
            "--",
            "getgo-fonts",
            "src_docs/md/illustrations",
        ],
        capture_output=True,
        check=False,
    )
    if result.returncode:
        return {}
    records = (
        record.split(b"\t", 1) for record in result.stdout.split(b"\0") if record
    )
    return {
        path.decode("utf-8"): info.split()[2].decode("ascii") for info, path in records
    }


def generator_fingerprint() -> str:
    """Invalidate templates when generator code, version or dependencies change."""
    packages = (
        "CairoSVG",
        "fontTools",
        "Pillow",
        "sh",
        "vharfbuzz",
        "yaplon",
        "uharfbuzz",
        "unicodedata2",
    )
    versions = [__version__, *(f"{name}={version(name)}" for name in packages)]
    return hashlib.sha256(
        Path(__file__).read_bytes() + "\n".join(versions).encode()
    ).hexdigest()


def load_cache(path: Path) -> dict:
    """Treat invalid JSON/schema as a cold cache; accept legacy source hashes."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
        return {}
    if not isinstance(data, dict) or not data:
        return {}
    sources, samples = data.get("sources", data), data.get("samples", {})
    if not all(
        isinstance(mapping, dict) and all(isinstance(v, str) for v in mapping.values())
        for mapping in (sources, samples)
    ) or not isinstance(data.get("generator", ""), str):
        return {}
    return {
        "sources": sources,
        "samples": samples,
        "generator": data.get("generator", ""),
    }


def normalize_specimen_svg(svg: str) -> str:
    """Map both vharfbuzz viewport formats from font coordinates to SVG space."""
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    root = ET.fromstring(svg)
    box = root.get("viewBox") or f"0 0 {root.attrib['width']} {root.attrib['height']}"
    x, y, width, height = map(float, box.replace(",", " ").split())
    if not all(map(math.isfinite, (x, y, width, height))) or width <= 0 or height <= 0:
        raise ValueError("Specimen SVG requires a finite, positive viewBox")
    # 0.2.x paths already include 500-unit margins and a baseline offset.
    # 0.3.x defs/use glyphs stay in font coordinates and omit those margins.
    padding = (
        SPECIMEN_PADDING
        if root.find("{http://www.w3.org/2000/svg}defs") is not None
        else 0
    )
    root.set("viewBox", f"0 0 {width:g} {height + 2 * padding:g}")
    root.set("width", f"{width:g}")
    root.set("height", f"{height + 2 * padding:g}")
    root.attrib.pop("transform", None)
    # CairoSVG ignores SVG2 root transforms. Keep defs/use payload intact inside
    # a group, and account for the nonzero/negative origin emitted by 0.3.x.
    group = ET.Element(
        "{http://www.w3.org/2000/svg}g",
        transform=f"matrix(1 0 0 -1 {-x:g} {y + height + padding:g})",
    )
    group.extend(root)
    root[:] = [group]
    return ET.tostring(root, encoding="unicode")


class GetGoFont:
    def __init__(
        self, path, folders, url_bases, redo, previous_sample: str | None = None
    ):
        self.path = path
        self.folders = folders
        self.url_bases = url_bases
        self.redo = redo
        self.previous_sample = previous_sample
        self.page_url = (
            str(self.path.stem).replace("[", "").replace("]", "").replace(",", "-")
        )
        self.vfj_path = Path(self.path.parent, str(self.path.stem) + ".vfj").resolve()
        self.ttf_path = Path(self.path.parent, str(self.path.stem) + ".ttf").resolve()
        self.md_path = Path(self.path.parent, str(self.path.stem) + ".md").resolve()
        self.md_outpath = Path(self.folders["docs"], self.page_url + ".md").resolve()
        self.svg_path = Path(self.folders["images"], self.page_url + ".svg").resolve()
        self.illu_path = Path(self.folders["illu"], self.page_url + ".png").resolve()
        self.png_path = Path(self.folders["images"], self.page_url + ".png").resolve()
        self.woff_path = Path(self.folders["woff"], self.page_url + ".woff2").resolve()
        self.yaml_path = Path(self.path.parent, str(self.path.stem) + ".yaml").resolve()
        self.font = fontTools.ttLib.TTFont(self.path, recalcTimestamp=False)
        self.name_table = self.font["name"]
        self.family = self.get_family_name()
        self.full_name = self.get_full_name()
        self.copyright = self.get_copyright()
        self.license = self.get_license()
        self.unicodes = []
        self.glyphs_count = len(self.font.getGlyphSet().keys())
        self.scripts = OrderedDict()
        self.script_names = OrderedDict()
        self.metadata = OrderedDict()
        self.index_md = ""
        self.font_md = ""
        self.process()

    def get_download_url(self, path):
        if path.is_relative_to(self.folders["images"]):
            return f"{self.url_bases['web']}/images/{path.name}"
        return f"{self.url_bases['download']}/{path.relative_to(self.folders['root']).as_posix()}"

    def get_family_name(self):
        family = self.name_table.getName(16, 3, 1)
        if not family:
            family = self.name_table.getName(1, 3, 1)
        return family.toUnicode() if family else ""

    def get_full_name(self):
        full_name = self.name_table.getName(4, 3, 1)
        return full_name.toUnicode() if full_name else ""

    def get_copyright(self):
        copyright = self.name_table.getName(0, 3, 1)
        return copyright.toUnicode() if copyright else ""

    def get_license(self):
        licenses = {"apache": "Apache", "cc0": "CC-0", "ofl": "OFL"}
        license = (
            str(self.path).replace(str(self.folders["font"]) + "/", "").split("/")[0]
        )
        license = licenses.get(license, license)
        return license

    def build_scripts(self):
        scripts = OrderedDict()
        unicodes = []
        for u in sorted(self.font.getBestCmap()):
            if ucd.category(chr(u))[0] not in ("N", "C") and u not in (0xFFFD, 0x0023):
                unicodes.append(u)
                script = ucd.script(chr(u))
                scripts[script] = scripts.get(script, 0) + 1
        self.unicodes = sorted(unicodes)
        scripts = OrderedDict(sorted(scripts.items(), key=lambda t: t[1], reverse=True))
        for k in ("Zyyy", "Zinh", "Zzzz"):
            if k in scripts:
                del scripts[k]
        if len(self.unicodes) < 10000:
            for k in list(scripts.keys()):
                if scripts[k] / len(self.unicodes) < 0.001:
                    del scripts[k]
        self.scripts = list(scripts.keys()) if len(scripts.keys()) else ["Zsym"]
        self.script_names = [ucd.script_name(script) for script in list(scripts.keys())]

    def save_woff(self):
        if self.redo["woff"] or not self.woff_path.is_file():
            self.font.flavor = "woff2"
            output = io.BytesIO()
            self.font.save(output)
            self.font.flavor = None
            write_if_changed(self.woff_path, output.getvalue())

    def get_font_css(self):
        url = str(self.woff_path).replace(str(self.folders["docs"]), "..")
        return f"""

@font-face {{
  font-family: '{self.full_name}';
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url({url}) format('woff2');
}}"""

    def build_metadata(self):
        metadata = OrderedDict()
        if not self.redo["yaml"] and self.yaml_path.is_file():
            with open(self.yaml_path, "r", encoding="utf-8") as f:
                metadata = oyaml.read_yaml(f)
        metadata["full_name"] = self.get_full_name()
        metadata["family_name"] = self.get_family_name()
        metadata["copyright"] = self.get_copyright()
        metadata["license"] = metadata.get("license", self.get_license())
        metadata["description"] = metadata.get("description", "Font")
        # Keep the authored order (including ties such as Pixa's). Append newly
        # detected scripts in coverage order and remove scripts no longer present.
        previous = metadata.get("scripts", [])
        self.script_names = [s for s in previous if s in self.script_names] + [
            s for s in self.script_names if s not in previous
        ]
        metadata["scripts"] = self.script_names
        if self.redo["sample_text"] or "sample_text" not in metadata:
            metadata["sample_text"] = self.get_sample_text()
        metadata["download_large"] = metadata.get("download_large", False)
        write_if_changed(self.yaml_path, oyaml.yaml_dump(metadata))
        self.metadata = metadata

    def get_sample_text(self, words=5, chars=6):
        cats = OrderedDict()
        for u in self.unicodes:
            cat = ucd.category(chr(u))[0]
            if cat in "LNS" and ucd.script(chr(u)) == self.scripts[0]:
                cats[cat] = cats.get(cat, []) + [u]
        unicodes = max(cats.values(), key=len, default=self.unicodes)
        lensample = words * chars
        lensample = min(lensample, len(unicodes))
        rng = random.Random(hashlib.sha256(self.path.read_bytes()).digest())
        sample = "".join([chr(u) for u in rng.sample(unicodes, lensample)])
        words = [sample[0 + i : chars + i] for i in range(0, len(sample), chars)]
        newwords = []
        for wordi, word in enumerate(words):
            if int(wordi / len(words) + 0.7):
                newwords.append(word.lower())
            else:
                newwords.append(word.upper())
        return " ".join(newwords)

    def render_sample_text(self, text=None):
        if (
            self.redo["sample"]
            or not self.png_path.is_file()
            or not self.svg_path.is_file()
        ):
            if not text:
                text = self.metadata["sample_text"]
            v = vharfbuzz.Vharfbuzz(self.path)
            buf = v.shape(text, {"script": self.scripts[0]})
            svg = normalize_specimen_svg(v.buf_to_svg(buf))
            png = io.BytesIO()
            write_if_changed(self.svg_path, svg)
            if is_usvg:
                usvg(self.svg_path, self.svg_path)
            cairosvg.svg2png(
                bytestring=svg.encode("utf-8"), write_to=png, output_height=56
            )
            im = Image.open(png)
            im = im.crop((0, 0, 600, 56))
            output = io.BytesIO()
            im.save(output, "PNG")
            write_if_changed(self.png_path, output.getvalue())

    def build_md(self):
        git_download_url = (
            self.url_bases["git_download_large"]
            if self.metadata["download_large"]
            else self.url_bases["git_download"]
        )
        download_url = str(self.vfj_path).replace(
            str(self.folders["font"]), git_download_url
        )
        svg_link = str(self.svg_path).replace(str(self.folders["docs"]) + "/", "")
        md_font_description = rf"""license: {self.license} \| {self.metadata["description"]} \| glyphs: {self.glyphs_count} \| scripts: {", ".join(self.script_names)}"""
        with open(self.md_path, "r", encoding="utf-8") as f:
            md_article = f.read()

        self.index_md += f"""

### {self.full_name}

[![{self.metadata["sample_text"]}]({svg_link})]({self.page_url + "/"})

[Download FontLab VFJ]({download_url}){{: .md-button target="_blank" }}

{md_font_description} \\| [Read more…]({self.page_url + "/"})

---
"""

        illu = ""
        if self.illu_path.is_file():
            illu_link = str(self.illu_path).replace(str(self.folders["docs"]) + "/", "")

            illu = f"""

[![{self.metadata["full_name"]}]({illu_link})]({illu_link}){{: .fancybox data-caption='{self.metadata["full_name"]}' data-fancybox='getgo'}}

"""

        self.font_md += f"""---
this_file: src_docs/md/{self.page_url}.md
layout: default
title: "{self.full_name}"
---

# {self.full_name}

<small>You can type in the box below to preview the font:</small>

<div contenteditable="true" class="texteditor" style="font-family: '{self.full_name}';">
<p spellcheck="false">{self.metadata["sample_text"]}</p>
</div>

[Download FontLab VFJ]({download_url}){{: .md-button .md-button--primary target="_blank" }}

{md_font_description}

---
{illu}
{md_article}

---

## Character map

<div style="font-family: '{self.full_name}'; font-size: 2em;">
{" ".join([chr(u) for u in self.unicodes]).strip()}
</div>

"""

    def process(self):
        self.build_scripts()
        self.build_metadata()
        # Decide after metadata normalization, which can add a missing sample.
        self.redo["sample"] |= self.metadata["sample_text"] != self.previous_sample
        self.save_woff()
        self.render_sample_text()


class GetGoDocs:
    def __init__(self, root: Path | None = None, force: bool = False) -> None:
        self.paths = OrderedDict()
        self.redo = {}
        self.redo["woff"] = force
        self.redo["yaml"] = False
        self.redo["sample_text"] = False
        self.redo["sample"] = force
        self.redo["zip"] = True
        self.folders = {}
        self.folders["root"] = (root or Path(__file__).parent.parent).resolve()
        self.cache_path = self.folders["root"] / ".cache/getgo-build.json"
        cache = load_cache(self.cache_path)
        self.previous_hashes = cache.get("sources", {})
        self.previous_samples = cache.get("samples", {})
        self.fingerprint = generator_fingerprint()
        self.force = force
        self.refresh_pages = (
            force or bool(cache) and cache.get("generator") != self.fingerprint
        )
        self.hashes = {}
        self.samples = {}
        self.committed = (
            committed_sources(self.folders["root"])
            if not self.previous_hashes or not self.previous_samples
            else {}
        )
        self.folders["font"] = Path(self.folders["root"], "getgo-fonts").resolve()
        self.folders["md"] = Path(self.folders["root"], "srcdocs").resolve()
        self.folders["docs"] = Path(self.folders["root"], "src_docs", "md").resolve()
        self.folders["woff"] = Path(self.folders["docs"], "fonts").resolve()
        self.folders["illu"] = Path(self.folders["docs"], "illustrations").resolve()
        self.folders["images"] = Path(self.folders["docs"], "images").resolve()
        self.folders["css"] = Path(self.folders["docs"], "css").resolve()

        self.url_bases = {}

        self.url_bases["web"] = (
            "https://raw.githubusercontent.com/fontlabcom/getgo-fonts/main/docs"
        )
        self.url_bases["download"] = (
            "https://raw.githubusercontent.com/fontlabcom/getgo-fonts/main"
        )
        self.url_bases["github"] = (
            "https://github.com/fontlabcom/getgo-fonts/blob/main/getgo-fonts"
        )
        self.url_bases["git_download"] = (
            "https://cdn.jsdelivr.net/gh/fontlabcom/getgo-fonts/getgo-fonts"
        )
        self.url_bases["git_download_large"] = (
            "https://minhaskamal.github.io/DownGit/#/home?url=https://github.com/fontlabcom/getgo-fonts/blob/main/getgo-fonts"
        )
        self.data = OrderedDict()
        self.font_css = "/* this_file: src_docs/md/css/fonts.css */\n"
        self.index_md = ""

    def source_changed(self, path: Path) -> bool:
        """Compare SHA-256 inputs, or Git's blob digest on the first checkout run."""
        path = path.resolve()
        key = path.relative_to(self.folders["root"]).as_posix()
        if not path.is_file():
            return key in self.previous_hashes or key in self.committed
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        previous = self.previous_hashes.get(key)
        self.hashes[key] = digest
        if previous is not None:
            return previous != digest
        blob = self.committed.get(key, "")
        algorithm = "sha256" if len(blob) == 64 else "sha1"
        return (
            hashlib.new(algorithm, f"blob {len(data)}\0".encode() + data).hexdigest()
            != blob
        )

    def find_fonts(self):
        for path in self.folders["font"].glob("**/*.?tf"):
            self.paths[path.resolve()] = {}
        sorted_paths = sorted(self.paths.keys(), key=lambda p: p.stem)
        self.paths = OrderedDict((key, self.paths[key]) for key in sorted_paths)

    def previous_sample(self, path: Path, metadata_changed: bool) -> str | None:
        """Use cached text, or committed YAML for a dirty, uncached checkout."""
        key = path.relative_to(self.folders["root"]).as_posix()
        if key in self.previous_samples:
            return self.previous_samples[key]
        yaml = path.with_suffix(".yaml")
        yaml_key = yaml.relative_to(self.folders["root"]).as_posix()
        if metadata_changed and yaml_key in self.committed:
            result = subprocess.run(
                ["git", "-C", str(self.folders["root"]), "show", f"HEAD:{yaml_key}"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                return oyaml.read_yaml(result.stdout).get("sample_text")
        if yaml.is_file():
            return oyaml.read_yaml(yaml.read_text(encoding="utf-8")).get("sample_text")
        return None

    def process(self):
        with open(Path(self.folders["md"], "prolog.md"), "r", encoding="utf-8") as f:
            self.index_md += (
                f.read()
                + """

## Fonts

"""
            )

        if "this_file:" not in self.index_md:
            self.index_md = self.index_md.replace(
                "---\n", "---\nthis_file: src_docs/md/index.md\n", 1
            )

        for path in self.paths:
            redo = self.redo.copy()
            font_changed = self.source_changed(path)
            metadata_changed = self.source_changed(path.with_suffix(".yaml"))
            article_changed = self.source_changed(path.with_suffix(".md"))
            illustration_changed = self.source_changed(
                self.folders["illu"] / f"{path.stem}.png"
            )
            redo["woff"] |= font_changed
            redo["sample"] |= font_changed or redo["sample_text"]
            fo = GetGoFont(
                path,
                self.folders,
                self.url_bases,
                redo,
                self.previous_sample(path, metadata_changed),
            )
            # Metadata may have been refreshed from the font during processing.
            metadata_changed |= self.source_changed(fo.yaml_path)
            self.samples[path.relative_to(self.folders["root"]).as_posix()] = (
                fo.metadata["sample_text"]
            )

            self.data[fo.metadata["full_name"]] = OrderedDict()
            drec = self.data[fo.metadata["full_name"]]
            drec.update(fo.metadata)
            drec["categories"] = sorted(
                list(drec.get("categories", [])) + list(drec.get("scripts", []))
            )
            if "scripts" in drec:
                del drec["scripts"]
            drec["url"] = OrderedDict()
            drec["url"]["vfj"] = fo.get_download_url(fo.vfj_path)
            drec["url"]["ttf"] = fo.get_download_url(fo.ttf_path)
            drec["url"]["md"] = fo.get_download_url(fo.md_path)
            drec["url"]["svg"] = fo.get_download_url(fo.svg_path)
            drec["url"]["png"] = fo.get_download_url(fo.png_path)
            self.font_css += fo.get_font_css()
            fo.build_md()
            self.index_md += fo.index_md
            if (
                font_changed
                or metadata_changed
                or article_changed
                or illustration_changed
                or self.refresh_pages
                or not fo.md_outpath.is_file()
            ):
                write_if_changed(fo.md_outpath, fo.font_md)
            fo.font.close()

        write_if_changed(self.folders["css"] / "fonts.css", self.font_css)
        output = io.StringIO()
        ojson.json_dump(self.data, output)
        write_if_changed(self.folders["root"] / "fonts.json", output.getvalue())
        write_if_changed(self.folders["docs"] / "index.md", self.index_md)

    def make_zip(self):
        """Update the download when archived sources change or the ZIP is missing."""
        archive = self.folders["root"] / "getgo-fonts-for-fontlab.zip"
        files = {
            p.relative_to(self.folders["font"]).as_posix(): p
            for p in sorted(self.folders["font"].rglob("*"))
            if p.is_file()
        }
        changed = [self.source_changed(path) for path in files.values()]
        baseline = self.previous_hashes or self.committed
        removed = {key for key in baseline if key.startswith("getgo-fonts/")} - set(
            self.hashes
        )
        # Released archives may use older metadata serialization. Preserve them
        # byte-for-byte until an archived source is added, edited or removed.
        if archive.is_file() and not any(changed) and not removed and not self.force:
            return
        if archive.is_file() and not self.force:
            with zipfile.ZipFile(archive) as z:
                names = [n for n in z.namelist() if not n.endswith("/")]
                if (
                    len(names) == len(files)
                    and set(names) == set(files)
                    and all(
                        hashlib.sha256(z.read(n)).digest()
                        == hashlib.sha256(p.read_bytes()).digest()
                        for n, p in files.items()
                    )
                ):
                    return
        temporary = archive.with_suffix(".zip.tmp")
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for name, path in files.items():
                info = zipfile.ZipInfo(
                    name
                )  # Fixed 1980 timestamp; ignore source mtimes.
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = (
                    3  # Unix permissions, including on Windows builders.
                )
                info.external_attr = 0o644 << 16
                z.writestr(info, path.read_bytes())
        temporary.replace(archive)

    def make(self):
        for folder in ("woff", "images", "css"):
            self.folders[folder].mkdir(parents=True, exist_ok=True)
        self.find_fonts()
        self.process()
        if self.redo["zip"]:
            self.make_zip()
        write_if_changed(
            self.cache_path,
            json.dumps(
                {
                    "generator": self.fingerprint,
                    "sources": self.hashes,
                    "samples": self.samples,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        help="Build another repository copy (default: script's repository)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate pages, webfonts, specimens and ZIP even with unchanged inputs",
    )
    args = parser.parse_args()
    ggd = GetGoDocs(args.root, force=args.force)
    ggd.make()


if __name__ == "__main__":
    main()
