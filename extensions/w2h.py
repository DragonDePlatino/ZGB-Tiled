import sys
import json
from textwrap import dedent

with open(sys.argv[1], "r") as data:
	# Parse the JSON
	world = json.loads(data.read() )

	# Get all the maps information
	maps = []
	for i in world["maps"]:
		# Parse the file name into a string for its enum id
		id = i["fileName"].replace("rooms/", "").replace(".tmx", "").upper()
		id = id[:4] + "_" + id[4:]

		# All size and positional values are in tile-space!
		tileSize = 8
		map = {
			"id": id,
			"w": int(i["width"] / tileSize),
			"h": int(i["height"] / tileSize),
			"x": int(i["x"] / tileSize),
			"y": int(i["y"] / tileSize)
		}

		# Add map to the maps array
		maps.append(map)
	
def headerString():
	# Build the .h file
	h = dedent(f"""\
	#ifndef ROOMS_H
	#define ROOMS_H
	
	#include <types.h>

	// Room ID's for all rooms inside {sys.argv[1]}
	typedef enum {{\n""")

	# Populate the ROOM_ID enum
	for index, i in enumerate(maps):
		h += "\t" + str(i["id"] ) + ",\n"
	
	h += dedent(f"""\
	\tROOM_COUNT
	}} ROOM_ID;
	
	// AABB based in tile-space!
	typedef struct {{
		ROOM_ID id;
		UINT8 x;
		UINT8 y;
		UINT8 w;
		UINT8 h;
	}} RoomExit;
	
	typedef struct {{
		UINT8 type;
		UINT8 x;
		UINT8 y;
	}} Object;
	
	UINT8 exitCount = 4;
	     
	typedef struct {{
		UINT8 bank;
		struct MapInfo* map;
		RoomExit exits[exitCount];
	}} RoomInfo;
	""")

	# Next step is to create each RoomInfo with their exist and objects

	h += dedent("""
	#endif
	""")

	return h

# Write the .h file
headerFile = open(sys.argv[2], "w")
headerFile.write(headerString() )
headerFile.close()