# DbgPack
A python utility library for creating a Namelist from .pack2 files.

Usage:
Edit assetsDir in NameListExtractor.py to point to the folder containing .pack2 files.

It is *strongly recomended* that you do not work on your live game files. If anything gets borked, battleye will bonk you. Make a backup, and work on that.

Run NameListExtractor.py. This will take a long time. Its scraping the entire game directory to find filenames. Once its done, a Namelist will be created in the same location as ..Extractor.py which contains all the found filenames and their current hashes.

To rebuild the Namelist; change nameListFile in NameListExtractor.py, or just run the file as is but with the NameList no longer present.

This repo contains code from https://github.com/RhettVX/forgelight-toolbox. I tried to find a way to merge the histories to keep contributers but failed. I apologize.
