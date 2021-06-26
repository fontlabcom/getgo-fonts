#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"""

__version__ = '1.0.0'

import io
import logging
import random
import re
from collections import OrderedDict
from pathlib import Path

import cairosvg
import fontTools.ttLib
import fontTools.unicodedata as ucd
import vharfbuzz
from PIL import Image
from yaplon import ojson, oyaml

logging.basicConfig(level=logging.WARNING)

is_usvg = False
try:
    from sh import usvg
    is_usvg = True
except ImportError:
    logging.warn('Install Rust, then usvg via: cargo install usvg')

class GetGoFont(object):

    def __init__(self, path, folders, url_bases, redo):
        self.path = path
        self.folders = folders
        self.url_bases = url_bases
        self.redo = redo
        self.vfj_path = Path(
            self.path.parent, str(self.path.stem) + '.vfj'
        ).resolve()
        self.ttf_path = Path(
            self.path.parent, str(self.path.stem) + '.ttf'
        ).resolve()
        self.md_path = Path(
            self.path.parent, str(self.path.stem) + '.md'
        ).resolve()
        self.svg_path = Path(
            self.folders['svg'], str(self.path.stem) + '.svg'
        ).resolve()
        self.png_path = Path(
            self.path.parent, str(self.path.stem) + '.png'
        ).resolve()
        self.woff_path = Path(
            self.folders['woff'], str(self.path.stem) + '.woff2'
        ).resolve()
        self.yaml_path = Path(
            self.path.parent, str(self.path.stem) + '.yaml'
        ).resolve()
        self.font = fontTools.ttLib.TTFont(self.path)
        self.name_table = self.font['name']
        self.family = self.get_family_name()
        self.full_name = self.get_full_name()
        self.copyright = self.get_copyright()
        self.license = self.get_license()
        self.unicodes = sorted(list(self.font.getBestCmap().keys()))
        self.scripts = OrderedDict()
        self.script_names = OrderedDict()
        self.metadata = OrderedDict()
        self.process()


    def get_download_url(self, path):
        url = str(path).replace(
            str(self.folders['root']),
            str(self.url_bases['download'])
        )
        return url

    def get_family_name(self):
        family = self.name_table.getName(16, 3, 1)
        if not family:
            family = self.name_table.getName(1, 3, 1)
        return family.toUnicode() if family else ''

    def get_full_name(self):
        full_name = self.name_table.getName(4, 3, 1)
        return full_name.toUnicode() if full_name else ''

    def get_copyright(self):
        copyright = self.name_table.getName(0, 3, 1)
        return copyright.toUnicode() if copyright else ''

    def get_license(self):
        licenses = {
            'apache': 'Apache',
            'cc0': 'CC-0',
            'ofl': 'OFL'
        }
        license = str(self.path).replace(
            str(self.folders['font']) + '/', ''
            ).split('/')[0]
        license = licenses.get(license, license)
        return license

    def build_scripts(self):
        scripts = OrderedDict()
        scripts_coverage = OrderedDict()
        for u in self.unicodes:
            if ucd.category(chr(u))[0] not in ('N', 'C'):
                script = ucd.script(chr(u))
                scripts[script] = scripts.get(script, 0) + 1
                scripts_coverage[script] = scripts_coverage.get(script, []) + [u]
        scripts = OrderedDict(sorted(
            scripts.items(), key=lambda t: t[1], reverse=True
        ))
        script_sample = ''
        for k, v in scripts_coverage.items():
            if len(v) > 2:
                script_sample += chr(v[0]) + chr(v[1])
        print(self.path)
        print(script_sample)
        for k in ('Zyyy', 'Zinh', 'Zzzz'):
            if k in scripts.keys():
                del scripts[k]
        if len(self.unicodes) < 10000:
            for k in list(scripts.keys()):
                if scripts[k] / len(self.unicodes) < 0.001:
                    del scripts[k]
        self.scripts = list(scripts.keys()) if len(scripts.keys()) else ['Zsym']
        self.script_names = [
            ucd.script_name(script)
            for script in list(scripts.keys())
        ]

    def save_woff(self):
        if self.redo['woff'] or not self.woff_path.is_file():
            self.font.flavor = 'woff2'
            self.font.save(self.woff_path)

    def get_font_css(self):
        url = str(self.woff_path).replace(
            str(self.folders['docs']),
            str('../..')
        )
        return f"""

@font-face {{
  font-family: '{self.family}';
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url({url}) format('woff2');
}}"""

    def build_metadata(self):
        metadata = OrderedDict()
        if not self.redo['yaml'] and self.yaml_path.is_file():
            with open(self.yaml_path, 'r', encoding='utf-8') as f:
                metadata = oyaml.read_yaml(f)
        metadata['full_name'] = metadata.get(
            'full_name', self.get_full_name())
        metadata['family_name'] = metadata.get(
            'family_name', self.get_family_name())
        metadata['copyright'] = self.get_copyright()
        metadata['license'] = metadata.get('license', self.get_license())
        metadata['description'] = metadata.get('description', 'Font')
        metadata['scripts'] = self.script_names
        if self.redo['sample_text']:
            metadata['sample_text'] = self.get_sample_text()
        else:
            metadata['sample_text'] = metadata.get(
                'sample_text', self.get_sample_text()
            )
        with open(self.yaml_path, 'w', encoding='utf-8') as f:
            oyaml.yaml_dump(metadata, f)
        self.metadata = metadata

    def get_sample_text(self, words=5, chars=6):
        cats = OrderedDict()
        for u in self.unicodes:
            cat = ucd.category(chr(u))[0]
            if cat in 'LNS' and ucd.script(chr(u)) == self.scripts[0]:
                cats[cat] = cats.get(cat, []) + [u]
        try:
            unicodes = sorted(cats.items(), key=lambda t: len(
                t[1]), reverse=True)[0][1]
        except:
            unicodes = self.unicodes
        lensample = words*chars
        if lensample > len(unicodes):
            lensample = len(unicodes)
        sample = "".join([
            chr(u) for u in random.sample(unicodes, lensample)
        ])
        words = [
            sample[0+i:chars+i]
            for i in range(0, len(sample), chars)
        ]
        newwords = []
        for wordi, word in enumerate(words):
            if int(wordi/len(words)+0.7):
                newwords.append(word.lower())
            else:
                newwords.append(word.upper())
        return " ".join(newwords)

    def render_sample_text(self, text=None):
        if not self.redo['sample']:
            return

        if not text:
            text = self.metadata['sample_text']
        v = vharfbuzz.Vharfbuzz(self.path)
        buf = v.shape(text, {'script': self.scripts[0]})
        svg = v.buf_to_svg(buf)
        svg = re.sub(
            r"""<svg xmlns="http://www\.w3\.org/2000/svg" viewBox="0 0 (.*?) (.*?)" transform="matrix\(1 0 0 -1 0 0\)">""",
            r"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 \g<1> \g<2>" transform="translate(0, \g<2>) scale(1, -1)">""",
            svg
        )
        png = io.BytesIO()
        with open(self.svg_path, 'w') as f:
            f.write(svg)
        if is_usvg:
            usvg(self.svg_path, self.svg_path)
        cairosvg.svg2png(
            bytestring=svg,
            write_to=png,
            output_height=56
        )
        im = Image.open(png)
        im = im.crop((0, 0, 600, 56))
        im.save(self.png_path, 'PNG')

    def get_md(self):
        md = ''
        download_url = str(self.path).replace(
            str(self.folders['font']), self.url_bases['git_download']
            )
        svg_link = str(self.svg_path).replace(
            str(self.folders['docs']) + '/', ''
        )
        md += f"""

### {self.full_name}

![{self.metadata["sample_text"]}]({svg_link})

{self.metadata["description"]} \| [Download font]({download_url}){{: target="_blank" }}

---
"""

        return md

    def process(self):
        self.build_scripts()
        self.build_metadata()
        self.save_woff()
        self.render_sample_text()


class GetGoDocs(object):

    def __init__(self):
        self.paths = OrderedDict()
        self.redo = {}
        self.redo['woff'] = False
        self.redo['yaml'] = False
        self.redo['sample_text'] = False
        self.redo['sample'] = False
        self.folders = {}
        self.folders['root'] = Path(Path(__file__).parent, '..').resolve()
        self.folders['font'] = Path(self.folders['root'], 'getgo-fonts').resolve()
        self.folders['md'] = Path(self.folders['root'], 'srcdocs').resolve()
        self.folders['docs'] = Path(self.folders['root'], 'docs').resolve()
        self.folders['woff'] = Path(self.folders['docs'], 'fonts').resolve()
        self.folders['svg'] = Path(self.folders['docs'], 'images').resolve()
        self.folders['css'] = Path(self.folders['docs'], '_sass', 'custom').resolve()

        self.url_bases = {}

        self.url_bases['web'] = 'https://raw.githubusercontent.com/fontlabcom/getgo-fonts/main/docs'
        self.url_bases['download'] = 'https://raw.githubusercontent.com/fontlabcom/getgo-fonts/main'
        self.url_bases['github'] = 'https://github.com/fontlabcom/getgo-fonts/blob/main/getgo-fonts'
        self.url_bases['git_download'] = 'https://downgit.github.io/#/home?url=https://github.com/fontlabcom/getgo-fonts/blob/main/getgo-fonts'
        self.data = OrderedDict()
        self.font_css = ''
        self.md = ''

    def find_fonts(self):
        for self.path in self.folders['font'].glob('**/*.?tf'):
            self.path = self.path.resolve()
            self.paths[self.path] = {}
        sorted_paths = sorted(self.paths.keys(), key=lambda p: p.stem)
        self.paths = OrderedDict((key, self.paths[key]) for key in sorted_paths)

    def process(self):
        with open(Path(self.folders['md'], 'prolog.md'), 'r', encoding='utf-8') as f:
            self.md += f.read() + """

## Fonts

"""

        for path in self.paths:
            fo = GetGoFont(path, self.folders, self.url_bases, self.redo)

            self.data[fo.metadata['full_name']] = OrderedDict()
            drec = self.data[fo.metadata['full_name']]
            drec.update(fo.metadata)
            drec['url'] = OrderedDict()
            drec['url']['vfj'] = fo.get_download_url(fo.vfj_path)
            drec['url']['ttf'] = fo.get_download_url(fo.ttf_path)
            drec['url']['md'] = fo.get_download_url(fo.md_path)
            drec['url']['svg'] = fo.get_download_url(fo.svg_path)
            drec['url']['png'] = fo.get_download_url(fo.png_path)
            self.font_css += fo.get_font_css()
            self.md += fo.get_md()

        with open(Path(self.folders['css'], 'fonts.scss'), 'w', encoding='utf-8') as f:
            f.write(self.font_css)
        with open(Path(self.folders['root'], 'fonts.json'), 'w', encoding='utf-8') as f:
            ojson.json_dump(self.data, f)
        with open(Path(self.folders['docs'], 'index.md'), 'w', encoding='utf-8') as f:
            f.write(self.md)

    def make(self):
        self.find_fonts()
        self.process()

def main():
    ggd = GetGoDocs()
    ggd.redo['sample'] = False
    ggd.make()

if __name__ == '__main__':
    main()
