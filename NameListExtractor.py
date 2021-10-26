from DbgPack import AssetManager

assetsDir = r"E:\10-23-2021 Planetside 2 Resources" #replace this with the directoy of your .pack2 assets
nameListFile = "NameList.txt"; #The namelist file

print("Loading packs")
current_manager = AssetManager(assetsDir, nameListFile)
