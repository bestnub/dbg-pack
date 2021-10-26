from collections import ChainMap
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, ChainMap as ChainMapType
from re import search, compile, IGNORECASE
from argparse import ArgumentParser
from glob import glob
import os
from pathlib import Path
from struct import unpack
from typing import List, Dict, Set
from zlib import decompress
from .hash import crc64
from .abc import AbstractPack, AbstractAsset
from .loose_pack import LoosePack
from .pack1 import Pack1
from .pack2 import Pack2
from .asset2 import Asset2

known_exts = ('adr agr ags apb apx bat bin cdt cnk0 cnk1 cnk2 cnk3 cnk4 cnk5 crc crt cso cur dat db dds def dir dll '
            'dma dme dmv dsk dx11efb dx11rsb dx11ssb eco efb exe fsb fxd fxo gfx gnf i64 ini jpg lst lua mrn pak '
            'pem playerstudio png prsb psd pssb tga thm tome ttf txt vnfo wav xlsx xml xrsb xssb zone').split()

file_pattern = compile(bytes(r'([><\w-]+\.(' + r'|'.join(known_exts) + r'))', 'utf-8'))

def saveDict(toSave, filepath: str):
    with open(filepath, "w") as text_file:
        for key in toSave.keys():
            text_file.write(str(key)+ ":" + str(toSave[key]) + "\n")

def read_cstring(data: bytes) -> bytes:
    chars = []
    for c in data:
        if c == 0x0:
            return bytes(chars)
        chars.append(c)

def scrapeNames(rawPack: AbstractPack, limit_files=True) -> Dict[int, str]:

    """

    this function was taken from https://github.com/RhettVX/forgelight-toolbox

    :param rawPack: pack file without namelist
    :param limit_files: Limit scraping to known file formats
    :return: List of scraped names
    """
    names = {}
    for a in rawPack:
        data = a.get_data()
        # If no name, check file header.  If no match, skip this file
        if a.data_length > 0 and limit_files:
            if data[:1] == b'#':  # flatfile
                pass
            elif data[:14] == b'<ActorRuntime>':  # adr
                mo = search(b'<Base fileName="([\\w-]+)_LOD0\\.dme"', data, IGNORECASE)
                if mo:
                    name = mo[1] + b'.adr'
                    names[crc64(name)] = name.decode('utf-8')
            elif data[:10] == b'<ActorSet>':  # agr
                pass
            elif data[:5] == b'<?xml':  # xml
                pass
            elif data[:12] == b'*TEXTUREPART':  # eco
                pass
            elif data[:4] == b'DMAT':  # dma
                pass
            elif data[:4] == b'DMOD':  # dme
                pass
            elif data[:4] == b'FSB5':  # fsb
                header_size = unpack('<I', data[12:16])[0]
                pos = 64 + header_size
                name = read_cstring(data[pos:]) + b'.fsb'

                names[crc64(name)] = name.decode('utf-8')
                continue
            elif data[:3] == b'CFX':  # gfx
                data = decompress(data[8:])

            else:
                continue

        found_names = []

        mo = file_pattern.findall(data)
        if mo:
            for m in mo:
                if b'<gender>' in m[0]:
                    found_names.append(m[0].replace(b'<gender>', b'Male'))
                    found_names.append(m[0].replace(b'<gender>', b'Female'))
                elif b'.efb' in m[0]:
                    found_names.append(m[0])
                    found_names.append(m[0].replace(b'.efb', b'.dx11efb'))  # .fxo might also be usable as dx11efb
                elif b'<' in m[0] or b'>' in m[0]:
                    found_names.append(m[0].replace(b'>', b''))

                else:
                    found_names.append(m[0])

            for n in found_names:
                names[crc64(n)] = n.decode('utf-8')
    return names

@dataclass
class HashNameLookup:
    hashDict : Dict[int, str]
    nameDict : Dict[str, int]

    def __init__(self, nameLookup : str, packDirectory : str = None): #if there is a chance the lookup must be rebuilt, include pack directory
        if not os.path.isfile(nameLookup):
            print(nameLookup + " does not exist, creating")
            names = {}
            for path in glob(packDirectory + "\*.pack2"):
                print("Scraping " + path)
                names.update(scrapeNames(Pack2(Path(path), {})))
            saveDict(names, nameLookup)
        
        hashes = []
        names = []
        for line in open(nameLookup, "r").read().splitlines(): #expect data in hashxxxxxxx:name_name_name.name format
            temp = line.split(':')
            hashes.append(int(temp[0]))
            names.append(temp[1])
        self.hashDict = dict(zip(hashes, names))
        self.nameDict = dict(zip(names, hashes))
        print("Found " + str(len(hashes)) + " lookups")

    def __len__(self):
        return len(self.hashDict.keys())

    def __NameToHash__(self, name : str) -> str:
        if name in nameDict:
            return nameDict[name]
        else:
            print(name + " not found in lookup")
            return name

    def __HashToName__(self, hash : int) -> str:
        if hash in hashDict:
            return hashDict[hash]
        else:
            print(str(hash) + " not found in lookup")
            return hash


@dataclass
class AssetManager:
    packs : List[AbstractPack]
    assets : ChainMapType[str, AbstractAsset] = field(repr=False)
    raw_assets : ChainMapType[int, Asset2] = field(repr=False)
    lookup: HashNameLookup


    @staticmethod
    def load_pack(filePath: str, hashDict: Dict[int, str] = None):
        path = Path(filePath)
        print("Loading: " + filePath)
        if path.is_file():
            if path.suffix == '.pack':
                return Pack1(path)
            elif path.suffix == '.pack2':
                return Pack2(path, hashDict)
        else:
            return LoosePack(path)

    def __init__(self, packDirectory: str, lookupFile: str):
        self.lookup = HashNameLookup(lookupFile, packDirectory)
        self.packs = [AssetManager.load_pack(path, self.lookup.hashDict) for path in glob(packDirectory + "\*.pack2")]
        self.assets = ChainMap(*[p.assets for p in self.packs])
        self.raw_assets = ChainMap(*[p.raw_assets for p in self.packs if type(p) is Pack2])

    def export_pack2(self, name: str, outdir: Path, raw=False):
        Pack2.export(list(self.assets.values()), name, outdir, raw)

    def __len__(self):
        return len(self.assets)

    def __contains__(self, item):
        return item in self.assets

    def __getitem__(self, item):
        return self.assets[item]

    def __iter__(self):
        return iter(self.raw_assets.values())

    def __lenHash__(self):
        return len(self.raw_assets)

    def __containsHash__(self, item: int):
        return item in self.raw_assets

    def __getitemHash__(self, item: int):
        return self.raw_assets[item]

    def __iterHash__(self):
        return iter(self.raw_assets())

    

    
