'''
A quick and dirty script (in progress) to read the geometry of a LucasArts Outlaws map
and import into Blender3D for further manipulation

Whole thing is basically held together with bubblegum and paperclips. Use at own risk.

Currently supports:
Sectors           ✓
Walls             ✓
Adjoins           ✓
Vadjoins          ✓
DadJoins          X
Slopes            X
Sprites           X
Textures          X
Special effects   X



Be warned: This script is still in development, and there is no friendly way to execute it.

Current usage:
-Ctrl-f this file for the phrase "C:\\", and modify the file path
to your liking.
-Copy-paste this entire file into Blenders "notepad" window.
-Run the script from the notepad window.
-If blender freezes, wait for up to 30 minutes before giving up. I am trying to fix this.
-Select all, and type rx90 if you want everything to be oriented correctly.

Questions/comments, email me. (no matter how many years have passed)

'''


import mathutils
import os
import bpy

###import olmLVTParse
import re

#I can find no documentation anywhere of what exactly these various parameters do, or even what to call them.
class OLShade:
    #Example line from level file:    "SHADE:  1 200 200 200 10 L"
    def __init__(self):
        parameter1 = 1
        parameter2 = 200
        parameter3 = 200
        parameter4 = 200
        parameter5 = 10
        parameter6 = "L"
    
class OLSectorFlags:
    #This is basically a giant bitfield, thank god we finally invented booleans.
    def __init__(self):
        self.sky = False
        self.pit = False
        self.skyAdjoin = False           #Makes the ceiling of this sector into a skybox.
        self.pitAdjoin = False           #I don't actually know if this is ever used. Logically it should eliminate the floor of the sector and make it a bottomless pit. There are no actual bottomless pits in outlaws, as far as I have seen, but there are pits that look like they *should* have been bottomless. Possible unimplemented feature?
        self.noWalls = False
        self.noSlidingOnSlope = False
        self.velocityForFloorOnly = False
        self.underwater = False
        self.door = False
        self.doorReverse = False
        self.unknown10 = False
        self.unknown11 = False
        self.secretArea = False
        self.unknown13 = False
        self.unknown14 = False
        self.unknown15 = False
        self.unknown16 = False
        self.unknown17 = False
        self.smallDamage = False             #Damage is applied as long as player is in sector.
        self.largeDamage = False
        self.deadlyDamage = False
        self.smallFloorDamage = False       #Same as above, but damage is only applied when player is touching floor.  Used for poisonous sludge or similar.
        self.largeFloorDamage = False
        self.deadlyFloorDamage = False
        self.deanWermerFlag = False         #I don't know either...
        self.secretTag = False              #Don't know how this differs from "secretArea"
        self.dontShadeFloor = False
        self.railTrackPullChain = False
        self.railLine = False
        self.hideOnMap = False
        self.floorSloped = False
        self.ceilingSloped = False
        self.olAlwaysZero = 0               #FLAGs in the level files are always accompanied by a zero. I have no idea what that zero does, but it is always there, and I've never seen it not be zero.
class OLWallFlags:
    def __init__(self):
        self.adjoiningMiddleTexture = False
        self.illuminatedSign = False
        self.flipTextureHorizontally = False
        self.wallTextureAnchored = False
        self.signAnchored = False
        self.tinting = False
        self.morphWithSector = False
        self.scrollTopTexture = False
        self.scrollMiddleTexture = False
        self.scrollBottomTexture = False
        self.scrollSignTexture = False
        self.nonPassable = False
        self.ignoreHeightChecks = False
        self.badGuysCantPass = False
        self.shatter = False
        self.projectileCanPass = False
        self.notARail = False
        self.dontShowOnMap = False
        self.neverShowOnMap = False
        self.unknown19 = False
        self.unknown20 = False
        self.unknown21 = False
        self.unknown22 = False
        self.unknown23 = False
        self.unknown24 = False
        self.unknown25 = False
        self.unknown26 = False
        self.unknown27 = False
        self.unknown28 = False
        self.unknown29 = False
        self.unknown30 = False
        self.unknown31 = False

class OLLevel:
    def __init__(self):
        self.levelFilePath = ""   #Example: "D:\OUTLAWS\data\LEVELS\Story\mill\MILL"
        self.levelFileDir = "",   #Automatically derived from levelPath for convenience. Example: "D:\OUTLAWS\data\LEVELS\Story\mill\"
        self.levelFileName = ""  #Automatically derived from levelPath for convenience. Example: "MILL"
        self.version = ""    #Outlaws version? Lawmaker version? Store it as a string instead of a float for saftey, in case it ever needs to contain multiple decimals or gets too long.
        self.palettes = []   #List of strings. Examples from hideout level: ["a51pal", "hideout", "uwhidot"]
        self.colorMaps = []      #What's a colorMap? Don't know, but we're including it.
        self.music = ""
        self.parallax = (0.0, 0.0)  #Don't know what those numbers refer to.
        self.lightSource = (0.0, 0.0, 0.0, 0.0) #Don't know what those numbers refer to.
        self.shades = []    #List of OLShade objects
        self.textures = []   #A list of strings, each one being the name.ext of a texture file.
        self.olSectors = []  #List of OLSector objects
        
class OLSector:
    def __init__(self):
        self.index = 0 #Sector number 0 through N.
        self.UID = "" #ex: 14C28 or 135EA
        self.name = "" #ex: "BRASS1" or "MINEDOOR". Most sectors don't have names.
        self.layer = 0 #The layer in which the sector resides. Layers are usually used to represent "floors" of a building and adjoined sectors always seem to be on different layers from their partner although I suspect this is not an absolute requirement.
        self.ambient = 0 #unknown
        self.palette = 0 #Refers to index in OLLevel.palettes
        self.colorMap = 0 #Refers to index in OLLevel.colorMaps
        
        self.friction = 1.0 #valid ranges unknown.
        self.gravity = -60 #valid ranges unknown.
        self.elasticity = 0.30 #valid ranges unknown.
        
        self.velocityX = 0.0 #Sector imparts this velocity to the player when the player is standing (or flying?) in it. (Used for conveyor belts? Does it also move the floor textures?)
        self.velocityY = 0.0
        self.velocityZ = 0.0
        
        self.floorSound = "" #No idea where it gets the list of sounds that this refers to.
        
        self.floorY = 0 #Height of floor on Y axis.
        self.floorTexture = 0   #Refers to an index in OLlevel.textures
        self.floorTextureOffsetX = 0.0
        self.floorTextureOffsetY = 0.0
        self.floorTextureAngle = 0.0
        
        self.ceilingY = 0 #Height of ceiling on Y axis.
        self.ceilingTexture = 0   #Refers to an index in OLlevel.textures
        self.ceilingTextureOffsetX = 0.0
        self.ceilingTextureOffsetY = 0.0
        self.ceilingTextureAngle = 0.0
        
        #Overlays seem to  be related to things like windows water surfaces(?) carpets paintings on walls etc.
        #I think the last one might be because outlaws lacks the ability to "ornament" a sprite to a wall.
        self.floorOverlayTexture = 0   #Refers to an index in OLlevel.textures
        self.floorOverlayTextureOffsetX = 0.0
        self.floorOverlayTextureOffsetY = 0.0
        self.floorOverlayTextureAngle = 0.0
        
        self.ceilingOverlayTexture = 0   #Refers to an index in OLlevel.textures
        self.ceilingOverlayTextureOffsetX = 0.0
        self.ceilingOverlayTextureOffsetY = 0.0
        self.ceilingOverlayTextureAngle = 0.0
        
        self.sectorFlags = OLSectorFlags()
        
        self.floorSlopeOriginSector = -1  #The sector that "floorSlopeOriginWall" resides in.
        self.floorSlopeOriginWall = -1    #The wall on which the slope pivots.
        self.floorSlopeMagnitude = -1     #Don't ask me what units "magnitude" is measured in. I've spent days trying to puzzle it out and gotton nowhere.
        
        self.ceilingSlopeOriginSector = -1
        self.ceilingSlopeOriginWall = -1
        self.ceilingSlopeMagnitude = -1
        
        self.vAdjoin = -1 #The index of the sector that this sector adjoins to vertically. -1 = none
            #It seems that there is no such thing as a VDadjoin.
        self.vertCoords = [] #List of 2-member tuples (XZ)
        self.walls = [] #List of OLWall objects



class OLWall:
    def __init__(self):
        self.UID = ""
        self.v1 = 0            #refers to an index in the OLSector.vertCoords list
        self.v2 = 0
        self.midTexture = 0 #int representing texture index.
        self.midTextureOffsetX = 0.0
        self.midTextureOffsetY = 0.0
        self.topTexture = 0
        self.topTextureOffsetX = 0.0
        self.topTextureOffsetY = 0.0
        self.bottomTexture = 0
        self.bottomTextureOffsetX = 0.0
        self.bottomTextureOffsetY = 0.0
        self.overlayTexture = 0
        self.overlayTextureOffsetX = 0.0
        self.overlayTextureOffsetY = 0.0
        self.Adjoin = -1
        self.Mirror = -1
        self.DAdjoin = -1
        self.DMirror = -1
        
        self.flags = OLWallFlags()
        
        self.light = 0
        
        
        #lawmaker keeps track of these two for some reason, but they always seem to equal v1 and v2 with no change in order,
        #So why are they noted specifically? Keep this in mind as something that could come back to bite us.
        #lVert = ?  
        #rVert = ?


def sortAndRemoveDups(thing):
    oldLen=len(thing)
    print("removing duplicates from {0} items".format(oldLen))
    thing.sort()
    last = thing[-1]
    for i in range(len(thing)-2, -1, -1):
        if last == thing[i]:
            del thing[i]
        else:
            last = thing[i]
    print("removed {0} duplicates".format(oldLen-len(thing)))
    return(thing)

#recursively remove all blanks from nested list.
def removeBlanksFromList(thing1):
    thing2 = []
    for i in range(0,len(thing1)):
        if(type(thing1[i])==list):
            thing1[i] = removeBlanksFromList(thing1[i])

        if(thing1[i] != '' and thing1[i]):
            thing2.append(thing1[i])
    return(thing2)


#Parse the LVT into an object that represents the same level-storing logic that outlaws uses. Don't change anything into anything else, just record it in an object as written.
def parseLVT(lvtPath = "C:\\Users\\Russell\\outlaws\\map_decompile\\level.LVT"):
    level = OLLevel()
    
    print("Parsing LVT {")

    with open(lvtPath, 'rb') as levelFile:
        levelText = levelFile.read().decode("utf-8")
        levelFile.close()

    levelText = re.sub(r"[#].+$" , "", levelText)   #Remove all comments
    levelText = re.sub(r"[ \t]+" , " ", levelText)    #Make sure everything is separated by exactly ONE space. No tabs or multiple spaces in a row to screw with the regexes
    
    sectorsStart = re.search(r"^SECTOR ", levelText, re.MULTILINE).start()
    
    nonSectorText = levelText[:sectorsStart]
    sectorText = levelText[sectorsStart:]  #Trim the levelText right up to the line where the first sector starts

    ##Process non-sector level information
    nonSectorText = re.split("\r\n", nonSectorText)    #Split section into lines.
    for line in range(len(nonSectorText)):
        nonSectorText[line] = re.split(" ", nonSectorText[line])    #Split lines into tokens
        nonSectorText[line] = removeBlanksFromList(nonSectorText[line])

    for i in nonSectorText:
        if(i.count("LEVELNAME")):
            level.levelFilePath = str(i[1])
            #TODO: Deal with levels that have names but no paths.
            #TODO: Populate dir and name thingies.

        if(i.count("VERSION")):
            level.version = str(i[1])

        if(i.count("PALETTE:")):
             level.palettes.append(str(i[1]))

        if(i.count("CMAP:")):
            level.colorMaps.append(str(i[1]))

        if(i.count("MUSIC")):
            level.music = str(i[1])

        if(i.count("PARALLAX")):
            level.parallax = (float(i[1]), float(i[2]))

        if((i.count("LIGHT")==1 and i.count("SOURCE")==1)):
            level.lightSource = (   float(i[2]),float(i[3]),float(i[4]),float(i[5])  )

        if(i.count("SHADE:")):
            newShade = OLShade()
            newShade.parameter1=int(i[1])
            newShade.parameter2=int(i[2])
            newShade.parameter3=int(i[3])
            newShade.parameter4=int(i[4])
            newShade.parameter5=int(i[5])
            newShade.parameter6=str(i[6])
            level.shades.append(newShade)
        if(i.count("TEXTURE:")):
            level.textures.append(str(i[1]))
    ##Finished processing non-sector level info.

    ##Process sector level information
    allSectors = re.split(r"SECTOR", sectorText, 0)
    for i in range(len(allSectors)):
        allSectors[i] = re.split("\r\n", allSectors[i])    #Split sector into lines.
        for line in range(len(allSectors[i])):
            allSectors[i][line] = re.split(" ", allSectors[i][line])    #Split lines into tokens
    allSectors=removeBlanksFromList(allSectors)

    
    for currentSector in allSectors:

        newSector = OLSector()

        newSector.UID= str(currentSector[0][0])
        for i in currentSector:
            if(i.count("NAME")):
                if(len(i) == 2):
                    newSector.name = str(i[1])
            if(i.count("AMBIENT")):
                newSector.ambient = int(i[1])
            if(i.count("PALETTE")):
                newSector.palette = int(i[1])
            if(i.count("CMAP")):
                newSector.colorMap = int(i[1])
            if(i.count("FRICTION")):
                newSector.friction = float(i[1])
            if(i.count("GRAVITY")):
                newSector.gravity = int(i[1])
            if(i.count("ELASTICITY")):
                newSector.elasticity = float(i[1])
            if(i.count("VELOCITY")):
                newSector.velocityX = float(i[1])
                newSector.velocityY = float(i[1])
                newSector.velocityZ = float(i[1])
            if(i.count("VADJOIN")):
                newSector.vAdjoin = int(i[1])
            if((i.count("FLOOR")==1 and i.count("SOUND")==1)):
                newSector.floorSound = str(i[2])
            if((i.count("FLOOR")==1 and i.count("OFFSETS")==1)):
                #There are offsets. Doesn't matter, we'll just search for the following line regardless, and if it exists, it exists, if not, not:
                pass
            if(i.count("OFFSET:")):

                pass
                #Don't know what this line means.
                #OFFSET:  -1.00   4    0.00    0.00  FLAGS: 0 0

                
            if((i.count("FLOOR")==1 and i.count("Y")==1)):
                newSector.floorY = float(i[2])
                newSector.floorTexture = int(i[3])
                newSector.floorTextureOffsetX = float(i[4])
                newSector.floorTextureOffsetY = float(i[5])
                newSector.floorTextureAngle = float(i[6])
            if((i.count("CEILING")==1 and i.count("Y")==1)):
                newSector.ceilingY = float(i[2])
                newSector.ceilingTexture = int(i[3])
                newSector.ceilingTextureOffsetX = float(i[4])
                newSector.ceilingTextureOffsetY = float(i[5])
                newSector.ceilingTextureAngle = float(i[6])
            if(i.count("F_OVERLAY")):
                newSector.floorOverlayTexture = int(i[1])
                newSector.floorOverlayTextureOffsetX = float(i[2])
                newSector.floorOverlayTextureOffsetY = float(i[3])
                newSector.floorOverlayTextureAngle = float(i[4])
            if(i.count("C_OVERLAY")):
                newSector.ceilingOverlayTexture = int(i[1])
                newSector.ceilingOverlayTextureOffsetX = float(i[2])
                newSector.ceilingOverlayTextureOffsetY = float(i[3])
                newSector.ceilingOverlayTextureAngle = float(i[4])
            if(i[0]=="FLAGS"): #can't count() for flags, because walls use the same keyword.
                #Process flags elsewhere for sanity.
                newSector.sectorFlags = handleSectorFlags(int(i[1]), int(i[2]))                
            if(i.count("SLOPEDFLOOR")):
                newSector.floorSlopeOriginSector = int(i[1])
                newSector.floorSlopeOriginWall = int(i[2])
                newSector.floorSlopeMagnitude = float(i[3])
            if(i.count("SLOPEDCEILING")):
                newSector.ceilingSlopeOriginSector = int(i[1])
                newSector.ceilingSlopeOriginWall = int(i[2])
                newSector.ceilingSlopeMagnitude = float(i[3])
            if(i.count("LAYER")):
                newSector.layer = int(i[1])
                
            if(i.count("X:")):
                newSector.vertCoords.append(   (float(i[1]),float(i[3]))   )

            if(i.count("WALL:")):
                newWall = OLWall()
                newWall.UID = str(i[1])
                newWall.v1 = int(i[3])
                newWall.v2 = int(i[5])
                newWall.midTexture = int(i[7])
                newWall.midTextureOffsetX = float(i[8])
                newWall.midTextureOffsetY = float(i[9])
                newWall.topTexture = int(i[11])
                newWall.topTextureOffsetX = float(i[12])
                newWall.topTextureOffsetY = float(i[13])
                newWall.bottomTexture = int(i[15])
                newWall.bottomTextureOffsetX = float(i[16])
                newWall.bottomTextureOffsetY = float(i[17])
                newWall.overlayTexture = int(i[19])
                newWall.overlayTextureOffsetX = float(i[20])
                newWall.overlayTextureOffsetY = float(i[21])
                newWall.Adjoin = int(i[23])
                newWall.Mirror = int(i[25])
                newWall.DAdjoin = int(i[27])
                newWall.DMirror = int(i[29])

                #Process flags elsewhere for sanity.
                newWall.flags = handleWallFlags(int(i[31]), int(i[32]))

                newWall.light = int(i[34])
                #print "appending wall {0} to sector {1}".format(newWall.UID, newSector.UID)
                newSector.walls.append(newWall)
            #No more lines to check for this sector           
            
        #Done with this sector.
        level.olSectors.append(newSector)

    ##Done processing sectors

    #print("Sector %s processed\n" % currentSectorObject.index)
    #print("processed total of %s out of supposed %s sectors" % (numSectorsProcessed, level.numSectors))

    return level


#Is there any sane, non-brute-force way to map a bitfield into a dictionary?
#If there is, I haven't found it.
def handleSectorFlags(oldFlag, olAlwaysZero):
    newFlag = OLSectorFlags()
    newFlag.sky = ((oldFlag & 2**0) >= 1)
    newFlag.pit = ((oldFlag & 2**1) >= 1)
    newFlag.skyAdjoin = ((oldFlag & 2**2) >= 1)
    newFlag.pitAdjoin = ((oldFlag & 2**3) >= 1)
    newFlag.noWalls = ((oldFlag & 2**4) >= 1)
    newFlag.noSlidingOnSlope = ((oldFlag & 2**5) >= 1)
    newFlag.velocityForFloorOn = ((oldFlag & 2**6) >= 1)
    newFlag.underwater = ((oldFlag & 2**7) >= 1)
    newFlag.door = ((oldFlag & 2**8) >= 1)
    newFlag.doorReverse = ((oldFlag & 2**9) >= 1)
    newFlag.unknown10 = ((oldFlag & 2**10) >= 1)
    newFlag.unknown11 = ((oldFlag & 2**11) >= 1)
    newFlag.secretArea = ((oldFlag & 2**12) >= 1)
    newFlag.unknown13 = ((oldFlag & 2**13) >= 1)
    newFlag.unknown14 = ((oldFlag & 2**14) >= 1)
    newFlag.unknown15 = ((oldFlag & 2**15) >= 1)
    newFlag.unknown16 = ((oldFlag & 2**16) >= 1)
    newFlag.unknown17 = ((oldFlag & 2**17) >= 1)
    newFlag.smallDamage = ((oldFlag & 2**18) >= 1)
    newFlag.largeDamage = ((oldFlag & 2**19) >= 1)
    newFlag.deadlyDamage = ((oldFlag & 2**20) >= 1)
    newFlag.smallFloorDamage = ((oldFlag & 2**21) >= 1)
    newFlag.largeFloorDamage = ((oldFlag & 2**22) >= 1)
    newFlag.deadlyFloorDamage = ((oldFlag & 2**23) >= 1)
    newFlag.deanWermerFlag = ((oldFlag & 2**24) >= 1)
    newFlag.secretTag = ((oldFlag & 2**25) >= 1)
    newFlag.dontShadeFloor = ((oldFlag & 2**26) >= 1)
    newFlag.railTrackPullChain = ((oldFlag & 2**27) >= 1)
    newFlag.railLine = ((oldFlag & 2**28) >= 1)
    newFlag.hideOnMap = ((oldFlag & 2**29) >= 1)
    newFlag.floorSloped = ((oldFlag & 2**30) >= 1)
    newFlag.ceilingSloped = ((oldFlag & 2**31) >= 1)
    newFlag.olAlwaysZero = olAlwaysZero
    return(newFlag)

def handleWallFlags(oldFlag, olAlwaysZero):
    newFlag = OLWallFlags()
    newFlag.adjoiningMiddleTexture = ((oldFlag & 2**0) >= 1)
    newFlag.illuminatedSign = ((oldFlag & 2**1) >= 1)
    newFlag.flipTextureHorizontally = ((oldFlag & 2**2) >= 1)
    newFlag.wallTextureAnchored = ((oldFlag & 2**3) >= 1)
    newFlag.signAnchored = ((oldFlag & 2**4) >= 1)
    newFlag.tinting = ((oldFlag & 2**5) >= 1)
    newFlag.morphWithSector = ((oldFlag & 2**6) >= 1)
    newFlag.scrollTopTexture = ((oldFlag & 2**7) >= 1)
    newFlag.scrollMiddleTexture = ((oldFlag & 2**8) >= 1)
    newFlag.scrollBottomTexture = ((oldFlag & 2**9) >= 1)
    newFlag.scrollSignTexture = ((oldFlag & 2**10) >= 1)
    newFlag.nonPassable = ((oldFlag & 2**11) >= 1)
    newFlag.ignoreHeightChecks = ((oldFlag & 2**12) >= 1)
    newFlag.badGuysCantPass = ((oldFlag & 2**13) >= 1)
    newFlag.shatter = ((oldFlag & 2**14) >= 1)
    newFlag.projectileCanPass = ((oldFlag & 2**15) >= 1)
    newFlag.notARail = ((oldFlag & 2**16) >= 1)
    newFlag.dontShowOnMap = ((oldFlag & 2**17) >= 1)
    newFlag.neverShowOnMap = ((oldFlag & 2**18) >= 1)
    newFlag.unknown19 = ((oldFlag & 2**19) >= 1)
    newFlag.unknown20 = ((oldFlag & 2**20) >= 1)
    newFlag.unknown21 = ((oldFlag & 2**21) >= 1)
    newFlag.unknown22 = ((oldFlag & 2**22) >= 1)
    newFlag.unknown23 = ((oldFlag & 2**23) >= 1)
    newFlag.unknown24 = ((oldFlag & 2**24) >= 1)
    newFlag.unknown25 = ((oldFlag & 2**25) >= 1)
    newFlag.unknown26 = ((oldFlag & 2**26) >= 1)
    newFlag.unknown27 = ((oldFlag & 2**27) >= 1)
    newFlag.unknown28 = ((oldFlag & 2**28) >= 1)
    newFlag.unknown29 = ((oldFlag & 2**29) >= 1)
    newFlag.unknown30 = ((oldFlag & 2**30) >= 1)
    newFlag.unknown31 = ((oldFlag & 2**31) >= 1)
    newFlag.olAlwaysZero = olAlwaysZero
    return(newFlag)



###




def findHeightOfFloorPointInSlopedSector(level, sector):
    sector.floorSlopeOriginSector
    sector.floorSlopeOriginWall
    sector.floorSlopeMagnitude


'''So here I think is what has to happen:
1. draw a line between the two points of floorSlopeOriginWall
2. draw a line perpendicular to line #1 going in the direction of target point.
3. Create a line running away from target point to perpendicularly intercept line #2
4. Determine height of hypothetical point at intersection of line #1 & #2
'''




def parseWallFaces(level):
    print("Translating OLwalls to wall faces")

    wallFaces = []
    for sector in level.olSectors:
        for wall in sector.walls:

            '''
            TODO: Problems when handling these dadjoin things.
            '''

            #Worst case: Wall is joined to two sectors, one above, one below, and we don't really know which is which.
            if False: #((wall.Adjoin != -1) and (wall.DAdjoin != -1)):
                a=sector.floorY
                b=sector.ceilingY
                c=level.olSectors[wall.Adjoin].floorY
                d=level.olSectors[wall.Adjoin].ceilingY
                e=level.olSectors[wall.DAdjoin].floorY
                f=level.olSectors[wall.DAdjoin].ceilingY

                v1x=sector.vertCoords[wall.v1][0]
                v1z=sector.vertCoords[wall.v1][1]
                v2x=sector.vertCoords[wall.v2][0]
                v2z=sector.vertCoords[wall.v2][1]
            
                relevantHeights = [a,b,c,d,e,f]
                relevantHeights.sort()

                height=0

                '''Two possibilities here
                Either it goes something like this:
                --------------------
                        |          |
                ---------          |
                    aj             |
                ---------    sect  |
                        |          |
                ---------          |
                    dj             |
                --------------------

                or something like this:
                --------------------
                        |          |
                ---------          |
                    aj             |
                ---------    sect  |
                        |          |
                ---------          |
                    dj             |
                --------------------
                '''
                

                if(relevantHeights[0] != relevantHeights[1]):
                    height=0
                    wallFaces.append([
                    (v1x, relevantHeights[height], v1z),
                    (v2x, relevantHeights[height], v2z),
                    (v1x, relevantHeights[height+1], v1z),
                    (v2x, relevantHeights[height+1], v2z)  ])
                else:
                    height=1
                    wallFaces.append([
                    (v1x, relevantHeights[height], v1z),
                    (v2x, relevantHeights[height], v2z),
                    (v1x, relevantHeights[height+1], v1z),
                    (v2x, relevantHeights[height+1], v2z)  ])

                if(relevantHeights[2] != relevantHeights[3]):
                    height=2
                    wallFaces.append([
                    (v1x, relevantHeights[height], v1z),
                    (v2x, relevantHeights[height], v2z),
                    (v1x, relevantHeights[height+1], v1z),
                    (v2x, relevantHeights[height+1], v2z)  ])
                if(relevantHeights[4] != relevantHeights[5]):
                    height=4
                    wallFaces.append([
                    (v1x, relevantHeights[height], v1z),
                    (v2x, relevantHeights[height], v2z),
                    (v1x, relevantHeights[height+1], v1z),
                    (v2x, relevantHeights[height+1], v2z)  ])
                
            #Simpler case: Wall is joined to only one sector.
                    
            #The following line simply takes the XOR of:
            #   (wall.Adjoin != -1) and 
            #   (wall.DAdjoin != -1)
            #It would be much more concise if python had a built-in xor operator, but that is sadly not the case.
            #It would also be more concise if we could define a xor() function, but I've tried that, and it somehow multiplies the script run-time by 10x. :shrug:
            elif False: #((wall.Adjoin != -1) and not (wall.DAdjoin != -1)) or (not (wall.Adjoin != -1) and (wall.DAdjoin != -1)):

                a=sector.floorY
                b=sector.ceilingY
                c=level.olSectors[wall.Adjoin].floorY
                d=level.olSectors[wall.Adjoin].ceilingY

                v1x=sector.vertCoords[wall.v1][0]
                v1z=sector.vertCoords[wall.v1][1]
                v2x=sector.vertCoords[wall.v2][0]
                v2z=sector.vertCoords[wall.v2][1]
            
                relevantHeights = [a,b,c,d]
                relevantHeights.sort()
                
                if(relevantHeights[0] != relevantHeights[1]):
                    height=0
                    wallFaces.append([
                    (v1x, relevantHeights[height], v1z),
                    (v2x, relevantHeights[height], v2z),
                    (v1x, relevantHeights[height+1], v1z),
                    (v2x, relevantHeights[height+1], v2z)  ])
                if(relevantHeights[2] != relevantHeights[3]):
                    height=2
                    wallFaces.append([
                    (v1x, relevantHeights[height], v1z),
                    (v2x, relevantHeights[height], v2z),
                    (v1x, relevantHeights[height+1], v1z),
                    (v2x, relevantHeights[height+1], v2z)  ])

            #Simplest case: Wall is not joined to anything. 
            elif ((wall.Adjoin == -1) and (wall.DAdjoin == -1)):
                relevantHeights = [sector.floorY,sector.ceilingY]

                relevantHeights.sort()

                wallFaces.append([
                    (sector.vertCoords[wall.v1][0], relevantHeights[0], sector.vertCoords[wall.v1][1]),
                    (sector.vertCoords[wall.v2][0], relevantHeights[0], sector.vertCoords[wall.v2][1]),
                    (sector.vertCoords[wall.v1][0], relevantHeights[1], sector.vertCoords[wall.v1][1]),
                    (sector.vertCoords[wall.v2][0], relevantHeights[1], sector.vertCoords[wall.v2][1])  ])

            else:
                print("Mysterious adjoin/dadjoin case on wall {0}".format(wall.UID))

    print("Walls parsed to planes")

    wallFaces = sortAndRemoveDups(wallFaces)
    
    return(wallFaces)


def createWallFaces(level):
    
    wallFaces = parseWallFaces(level)

    print("creating wall faces")
    
    for i in range(len(wallFaces)):
        create_mesh_object(wallFaces[i], [[0,1],[1,3],[3,2],[2,0]], [[0,1,3,2]], "mesh")

    print("Wall faces created")



def createFloorsAndCeilings(level):

    print("creating FC faces")
    
    for sector in level.olSectors:

        '''
        todo:
        1. Don't draw ceilings marked as sky, or floors marked as pit
        2. Severe optimizations.
        '''

        #Assemble verts for this sector. One set for floor, one for ceiling.
        floorVerts = []
        ceilingVerts = []
        for vert in sector.vertCoords:
            floorVerts.append([vert[0], sector.floorY, vert[1]])
            ceilingVerts.append([vert[0], sector.ceilingY, vert[1]])

        #assemble edges, which will be the same for ceiling and floor.
        edges = []
        for wall in sector.walls:
            edges.append([wall.v1,wall.v2])

        #We can't really assemble faces here without getting in
        #way deeper than I want to go. We will call on blender
        #to fill them in for us in a moment...
        faces = []

        
        base = create_mesh_object(floorVerts, edges, faces, "mesh")
        if (not(sector.sectorFlags.pit or sector.sectorFlags.pitAdjoin)):
            #Is base selected right now? Can we safely assume that?
            bpy.ops.object.mode_set(mode = 'EDIT')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.fill()
            bpy.ops.object.mode_set(mode = 'OBJECT')

        
        base = create_mesh_object(ceilingVerts, edges, faces, "mesh")
        if (not(sector.sectorFlags.sky or sector.sectorFlags.skyAdjoin)):
            #Is base selected right now? Can we safely assume that?
            bpy.ops.object.mode_set(mode = 'EDIT')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.fill()
            bpy.ops.object.mode_set(mode = 'OBJECT')
        


    print("FC faces created")
    


def create_mesh_object(verts, edges, faces, name):

    # Create new mesh
    mesh = bpy.data.meshes.new(name)

    # Make a mesh from a list of verts/edges/faces.
    mesh.from_pydata(verts, edges, faces)

    # Update mesh geometry after adding stuff.
    mesh.update()

    theObj = bpy.data.objects.new(mesh.name, mesh)

    theObjBase = bpy.context.scene.objects.link(theObj)
    theObjBase.select = True
    bpy.context.scene.objects.active = theObj

    return theObjBase



def a():


    level = parseLVT()


    oldGlobalUndoSetting = bpy.context.user_preferences.edit.use_global_undo
    oldUndoStepsSetting = bpy.context.user_preferences.edit.undo_steps
    bpy.context.user_preferences.edit.use_global_undo=False
    bpy.context.user_preferences.edit.undo_steps=0


    createWallFaces(level)
    createFloorsAndCeilings(level)

    #in the following line, notice the orphaned comma in the construct: "value=(3.14159/2,)"
    #   This construct is suprisingly valid, and apparently neccessary to cast 90 as a sequence rather than an int. Why we are casting shit in python I don't know.
    #Also: The pi/2 thing worries me for reasons of precision.

    #Oh wait, this entire thing doesn't work anyway. Fuck it I guess we're just typing "rx90" after every single run of the script.
    #bpy.ops.transform.rotate(value=(3.14159/2,), axis=(1, 0, 0), constraint_axis=(True, False, False))

    bpy.context.user_preferences.edit.use_global_undo = oldGlobalUndoSetting
    bpy.context.user_preferences.edit.undo_steps = oldUndoStepsSetting


    
a()





















