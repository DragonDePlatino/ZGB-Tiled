import os, sys, json
from textwrap import dedent
import xml.etree.ElementTree as ET

# Usage: python w2h.py input.world output.h output.c
worldPath = sys.argv[1]
includePath = sys.argv[2]
sourcePath = sys.argv[3]

# All the world information
world = {}
maps = []
tileSize = 8

with open(worldPath, "r") as data:
	# Parse the JSON
	world = json.loads(data.read() )

	# Get all the maps information
	for i in world["maps"]:
		# Parse the file name into a string for its enum id
		id = i["fileName"].replace("rooms/", "").replace(".tmx", "").upper()
		id = id[:4] + "_" + id[4:]

		# All size and positional values are in tile-space!
		map = {
			# roomName, ROOM_NAME, x, y, w, h
			"bank": i["fileName"].replace("rooms/", "").replace(".tmx", ""),
			"id": id,
			"x": int(i["x"] / tileSize),
			"y": int(i["y"] / tileSize),
			"w": int(i["width"] / tileSize),
			"h": int(i["height"] / tileSize)
		}

		# Add map to the maps array
		maps.append(map)


def getRoomInfo() -> str:
	# Container for room information
	rooms:dict = {}

	# Iterate through each map file referenced inside the .world file
	for i, map in enumerate(world["maps"] ):
		roomData = ET.parse("../res/" + world["maps"][i]["fileName"] )
		root = roomData.getroot()

		# Create empty room information
		bank = maps[i]["bank"]
		rooms[bank]:dict = {}

		# If an object layer doesn't exist, continue
		if (root.find("objectgroup") is None):
			continue
		
		# If no layer named "Objects" exists, continue
		if (root.find("objectgroup").attrib["name"] != "Objects"):
			continue

		# Interate through objects in the "Objects" layer
		rooms[bank]["exits"] = {}
		for ii, obj in enumerate(root.find("objectgroup").iter("object") ):
			# If the object isn't an exit, continue
			if (obj.attrib["type"] != "exit"):
				continue
			
			# Create a room exit "object"
			roomExit = {
				"id":	0,
				"side":	0,
			}

			# Interate over the objects properties
			for property in obj.find("properties"):
				if (property.get("name") == "room"):
					# Adds the room id in the format of ROOM_NAME
					valueAsEnum = property.get("value").replace(".tmx", "").upper()
					valueAsEnum = valueAsEnum[:4] + "_" + valueAsEnum[4:]
					roomExit["id"] = valueAsEnum
				
				if (property.get("name") == "side"):
					roomExit["side"] = property.get("value")
			
			# Store the exits
			rooms[bank]["exits"][ii] = "{{ {}, {} }}".format(roomExit["id"], roomExit["side"] )

	# Write the RoomExit .c code
	roomExitsArrayString = ""
	for i, map in enumerate(world["maps"] ):
		bank = maps[i]["bank"]

		if not "exits" in rooms[bank]:
			continue

		# Start the .c code
		roomExitsArrayString += f"RoomExit {bank}Exits[]"

		# End the array if there's no exits
		if not "exits" in rooms[bank]:
			roomExitsArrayString += ";\n"
			continue

		roomExitsArrayString += " = { "

		# Iterate through the exits and add them to the string
		for j in rooms[bank]["exits"]:
			roomExitsArrayString += rooms[bank]["exits"][j]
			if (j < len(rooms[bank]["exits"] ) - 1): roomExitsArrayString += ", "

		# Add the closing stuff
		roomExitsArrayString += " };\n"
	

	# Write the roomInfo .c code
	roomInfoString = "\nconst RoomInfo roomInfo[ROOM_COUNT] = {\n"
	for i, map in enumerate(world["maps"] ):
		bank = maps[i]["bank"]

		# Store world positions from the .world file
		worldX = int(map["x"] / tileSize)
		worldY = int(map["y"] / tileSize)

		# Check if the rooms has exits, and if not, don't add them
		exitCount = 0
		if "exits" in rooms[bank]:
			exitCount = len(rooms[bank]["exits"] )
		else:
			roomInfoString += f"\t {{ BANK({bank}), &{bank}, 0, {worldX}, {worldY} }}"
			if (i < len(maps) - 1): roomInfoString += ",\n"
			continue

		roomInfoString += f"\t {{ BANK({bank}), &{bank}, {exitCount}, {bank}Exits, {worldX}, {worldY} }}"
		if (i < len(maps) - 1): roomInfoString += ",\n"
	
	# Add the closing stuff
	roomInfoString += "\n};"

	# Return combined string
	return roomExitsArrayString + roomInfoString


def createHeaderString() -> str:
	# Build the .h file
	header = dedent(f"""\
	// This code was generated based on the data inside {sys.argv[1]}
	// All coordinates are based in tile-space
	#ifndef ROOMS_H
	#define ROOMS_H
	
	#include <main.h>
	#include <types.h>
	#include "MapInfo.h"
		 
	typedef enum {{\n""")

	# Populate the ROOM_ID enum
	for index, i in enumerate(maps):
		header += "\t" + str(i["id"] ) + ",\n"
	
	header += dedent(f"""\
	\tROOM_COUNT
	}} ROOM_ID;
	
	typedef enum {{
		  SIDE_TOP,
		  SIDE_RIGHT,
		  SIDE_BOTTOM,
		  SIDE_LEFT
	}} SIDES;
	
	typedef struct {{
		ROOM_ID id;
		SIDES side;
	}} RoomExit;
	     
	typedef struct {{
		UINT8 bank;
		struct MapInfo* map;
		UINT8 exitCount;
		RoomExit* exits;
		INT16 worldX;
		INT16 worldY;
	}} RoomInfo;
	
	extern const RoomInfo roomInfo[];
	
	#endif
	""")

	return header

def createSourceString() -> str:
	source = dedent(f"""\
	#include <main.h>
	#include <types.h>
	#include "{os.path.basename(includePath)}"
	#include "MapInfo.h"
	\n""")

	# Add map imports
	for map in maps:
		source += f"IMPORT_MAP({map['bank']});\n"
	
	# Add room info
	source += "\n" + getRoomInfo() + "\n"

	return source

def buildExportFile():
	# Write the .h file
	headerFile = open(includePath, "w")
	headerFile.write(createHeaderString() )
	headerFile.close()

	# Write the .c file
	sourceFile = open(sourcePath, "w")
	sourceFile.write(createSourceString() )
	sourceFile.close()

buildExportFile()
