#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"""

__version__ = '0.0.1'

import fontTools.ttLib
from sympy import Order
import fontTools.unicodedata as ucd
from pathlib import Path, PurePath

from collections import OrderedDict
import random
from yaplon import oyaml, ojson
import json

class GetGoDocs(object):

    def __init__(self):
        self.paths = OrderedDict()
        self.redo_woff = False
        self.redo_yaml = False
        self.root_folder = Path(Path(__file__).parent, '..').resolve()
        self.font_folder = Path(self.root_folder, 'getgo-fonts').resolve()
        self.download_base = 'https://raw.githubusercontent.com/fontlabcom/getgo-fonts/main/getgo-fonts'
        self.github_base = 'https://github.com/fontlabcom/getgo-fonts/blob/main/getgo-fonts'
        self.gitdownload_base = 'https://downgit.github.io/#/home?url=https://github.com/fontlabcom/getgo-fonts/blob/main/getgo-fonts'
        self.data = OrderedDict()

    def make_paths(self):
        md_folder = Path(self.root_folder, 'srcdocs').resolve()
        docs_folder = Path(self.root_folder, 'docs').resolve()
        woff_folder = Path(self.root_folder, 'docs', 'fonts').resolve()

        for font_path in self.font_folder.glob('**/*.?tf'):
            font_path = font_path.resolve()
            self.paths[font_path] = {}
            frec = self.paths[font_path]
            frec['md'] = Path(
                font_path.parent, str(font_path.stem) + '.md'
                ).resolve()
            frec['yaml'] = Path(
                font_path.parent, str(font_path.stem) + '.yaml'
                ).resolve()
            frec['vfj'] = Path(
                font_path.parent, str(font_path.stem) + '.vfj'
                ).resolve()
            frec['ttf'] = Path(
                font_path.parent, str(font_path.stem) + '.ttf'
            ).resolve()
            frec['woff'] = Path(
                woff_folder, font_path.stem + '.woff2'
                ).resolve()

    def make_woff(self, font, path):
        if self.redo_woff or not path.is_file():
            font.flavor = 'woff2'
            font.save(path)

    def get_sample_text(self, font, words=5, chars=6):
        unicodes = sorted(list(font.getBestCmap().keys()))
        cats = OrderedDict()
        for u in unicodes:
            cat = ucd.category(chr(u))[0]
            if cat in 'LNS':
                cats[cat] = cats.get(cat, []) + [u]
        unicodes = sorted(cats.items(), key=lambda t: len(t[1]), reverse=True)[0][1]
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

    def get_family_name(self, font):
        name = font['name']
        family = name.getName(16, 3, 1)
        if not family:
            family = name.getName(1, 3, 1)
        return family.toUnicode() if family else ''

    def get_full_name(self, font):
        name = font['name']
        full_name = name.getName(4, 3, 1)
        return full_name.toUnicode() if full_name else ''

    def get_copyright(self, font):
        name = font['name']
        copyright = name.getName(0, 3, 1)
        return copyright.toUnicode() if copyright else ''

    def get_license(self, font):
        name = font['name']
        license = name.getName(13, 3, 1)
        return license.toUnicode() if license else ''

    def get_scripts(self, font):
        scripts = OrderedDict()
        unicodes = sorted(list(font.getBestCmap().keys()))
        for u in unicodes:
            if ucd.category(chr(u))[0] not in ('N', 'C'):
                script = ucd.script(chr(u))
                scripts[script] = scripts.get(script, 0) + 1
        scripts = OrderedDict(sorted(
            scripts.items(), key=lambda t: t[1], reverse=True
        ))
        for k in ('Zyyy', 'Zinh', 'Zzzz'):
            if k in scripts.keys():
                del scripts[k]
        if len(unicodes) < 10000:
            for k in list(scripts.keys()):
                if scripts[k]/len(unicodes) < 0.11:
                    del scripts[k]
        script_names = [
            ucd.script_name(script)
            for script in list(scripts.keys())
            ]
        return script_names

    def process_metadata(self, font, frec):
        metadata = OrderedDict()
        if not self.redo_yaml and frec['yaml'].is_file():
            with open(frec['yaml'], 'r', encoding='utf-8') as f:
                metadata = oyaml.read_yaml(f)
        metadata['full_name'] = metadata.get('full_name', self.get_full_name(font))
        metadata['family_name'] = metadata.get('family_name', self.get_family_name(font))
        metadata['copyright'] = metadata.get('copyright', self.get_copyright(font))
        metadata['license'] = metadata.get('license', self.get_license(font))
        metadata['description'] = metadata.get('description', 'Font')
        metadata['scripts'] = metadata.get('scripts', self.get_scripts(font))
        metadata['sample_text'] = metadata.get('sample_text', self.get_sample_text(font))
        with open(frec['yaml'], 'w', encoding='utf-8') as f:
            oyaml.yaml_dump(metadata, f)
        return metadata

    def process_font(self, path, frec):
        font = fontTools.ttLib.TTFont(path)
        self.make_woff(font, frec['woff'])
        metadata = self.process_metadata(font, frec)
        return metadata

    def get_download_url(self, path):
        return str(path).replace(
            str(self.font_folder),
            str(self.download_base)
            )

    def process_fonts(self):
        for path, frec in self.paths.items():
            metadata = self.process_font(path, frec)
            self.data[metadata['full_name']] = OrderedDict()
            drec = self.data[metadata['full_name']]
            drec.update(metadata)
            drec['vfj_url'] = self.get_download_url(frec['vfj'])
            drec['ttf_url'] = self.get_download_url(frec['ttf'])
            drec['md_url'] = self.get_download_url(frec['md'])
        print(json.dumps(self.data, ensure_ascii=False, indent=2))

    def make(self):
        self.make_paths()
        self.process_fonts()

def main():
    ggd = GetGoDocs()
    ggd.make()

if __name__ == '__main__':
    main()
