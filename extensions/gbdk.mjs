
/** Write text to given path.
 *  @param {string} path
 *  @param {string} object
 */
export function fileWrite(path, text) {
	let file = new TextFile(path, TextFile.ReadWrite)
	file.write(text)
	file.commit()
}

/** Convert 8x8 gameboy tile to 2BPP.
 *  @param {image} Image
 *  @returns an array of 2bpp data
 */
function tile2bpp(image) {
	let w = image.width / 8
	let h = image.height / 8
	let out = Array.from({ length: 16 })
	out.fill(0)

	// Iterate each tile of image
	for (let iy = 0; iy < h; ++iy) {
		for (let ix = 0; ix < w; ++ix) {

			// Get offset within output data
			let o = ix * 16 + iy * 128

			// Iterate pixels of this 8x8 tile
			for (let ty = 0; ty < 8; ++ty) {
				for (let tx = 0; tx < 8; ++tx) {
					let r = 3 - ((image.pixel(8 * ix + tx, 8 * iy + ty) >> 16) & 0xFF) / 85
					out[o + 2 * ty + 0] |= (r & 0x01) >> 0 << (7 - tx)
					out[o + 2 * ty + 1] |= (r & 0x02) >> 1 << (7 - tx)
				}
			}
		}
	}

	return out;
}

tiled.registerTilesetFormat('gbdk', {
	name: 'GBDK Tileset',
	extension: 'tsx.c',

	write: (tileset, filename) => {
		let name = tileset.name
		let image = new Image(tileset.image)
		let w = image.width / 8
		let h = image.height / 8
		let length = w * h
		
		let palettes = Array.from({ length: 4 }, () => 0)
		let tilesCGB = Array.from({ length }, () => 0)
		let tiles = tile2bpp(image)
		
		fileWrite(filename, `
#pragma bank 255
#include <gb/gb.h>
#include <gb/cgb.h>
#include "TilesInfo.h"

const UINT16 ${name}_palettes[4] = { ${palettes.join(',')} };

const unsigned char ${name}CGB[] = { ${tilesCGB} };

const unsigned char ${name}_tiles[] = { ${tiles.join(',')} };

const void __at(255) __bank_${name};

const struct TilesInfo ${name} = {
	${length},			// num_tiles
	${name}_tiles, 		// tiles
	1,					// num_palettes
	${name}_palettes,	// palettes
	${name}CGB			// CGB palette
};`)
	}
})

tiled.registerMapFormat('gbdk', {
	name: 'GBDK Map',
	extension: 'tmx.c',

	write: (map, filename) => {
		let name = FileInfo.baseName(filename)
		let tileset = map.tilesets[0]
		let tiles = tileset.name

		let layer = map.layers.find(layer => layer.isTileLayer)
		let width = layer.width
		let height = layer.height

		let cells = []
		for (let y = 0; y < height; ++y) {
			for (let x = 0; x < width; ++x) {
				cells.push(layer.cellAt(x, y).tileId)
			}
		}

		fileWrite(filename, `
#pragma bank 255
#include <gb/gb.h>
#include "TilesInfo.h"
#include "MapInfo.h"

const unsigned char ${name}_map[] = { ${cells.join(',')}};

extern const void __bank_${tiles};

extern const struct TilesInfo ${tiles};

const void __at(255) __bank_${name};

const struct MapInfo ${name} = {
	${name}_map,		//map
	${width},			//width
	${height},			//height
	0,					//attributes
	BANK(${tiles}),		//tiles bank
	&${tiles},			//tiles info
};`)
	}
})
