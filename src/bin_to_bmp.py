from struct import unpack, iter_unpack
from PIL import Image
import numpy as np
from Tile import Tile, unpack_tile
from Cps2TileBuilder import Cps2TileBuilder
from Cps2TileWriter import Cps2TileWriter


#need some kind of reader? something to handle data input - FileHandler
#need something to build a single 8x8 and 16x16 tile - TileBuilder
#need something to assemble 16x16 tiles into a larger thing -
#need to print out tiles
def interleave_tiles(subtiles):
    tile_halfs = []
    tile_halfs.append(np.concatenate([subtiles[0], subtiles[2]], axis=1))
    tile_halfs.append(np.concatenate([subtiles[1], subtiles[3]], axis=1))
    return np.concatenate(tile_halfs, axis=0)

def tile_to_array(tile_data, dim):
    unpacked_tile = tile_data

    if dim == '8':
        pixel_data = [unpacked_tile[i:i+8] for i in range(0, len(unpacked_tile), 8)]
        pixel_data = [unpack(8 * 'c', row) for row in pixel_data]
        pixel_array = np.array(pixel_data)
        return pixel_array

    if dim == '16':
        tiles = []
        tile_fmt = 64 * 'c'
        tile_iter = iter_unpack(tile_fmt, unpacked_tile)
        for tile in tile_iter:
            pixel_data = [tile[i:i+8] for i in range(0, len(tile), 8)]
            pixel_data = [unpack(8 * 'c', b''.join(row)) for row in pixel_data]
            tiles.append(np.array(pixel_data))

        return interleave_tiles(tiles)


def test_make_tile8(file, addr):
    read_data = 0
    with open(file, 'rb') as f:
        f.seek(int(addr, 16))
        read_data = f.read(32)

    tile = Tile(addr, read_data, '8')
    pixel_array = tile_to_array(unpack_tile(tile), tile.dimensions)

    image = Image.fromarray(pixel_array, 'P')
    image.save("outputs/bin_to_bmp/struct_test.bmp")

def test_make_tile16(file, addr):
    read_data = 0
    with open(file, 'rb') as f:
        f.seek(int(addr, 16))
        read_data = f.read(128)

    tile16 = Tile(addr, read_data, '16')
    pixel_array = tile_to_array(unpack_tile(tile16), tile16.dimensions)

    image = Image.fromarray(pixel_array, 'P')
    image.save("outputs/bin_to_bmp/struct_test.bmp")

#converts the addresses mame displays when you press 'F4' to something else,,
def convert_mame_addr(mame_addr, tile_size):
    tile_bytes = 0
    addr = int(mame_addr, 16)
    if tile_size is '8':
        tile_bytes = 32
    if tile_size is '16':
        tile_bytes = 128

    converted_addr = addr * tile_bytes
    memory_bank_size = int('0x1000000', 16)

    #currently the 8 eproms are split into 2 banks
    if converted_addr > memory_bank_size:
        converted_addr -= memory_bank_size

    return converted_addr

#the way a group of 16x16 tiles is given, is how the final picture is assembled
def process_tile_order(gfx_file, addresses, tile_dim):
    dim = tile_dim
    builder = Cps2TileBuilder()
    tiles = []
    with open(gfx_file, 'rb') as f:
        for row_of_addresses in addresses:
            row = []
            for tile_addr in row_of_addresses:
                if tile_addr != 'blank':
                    f.seek(convert_mame_addr(tile_addr, dim))
                    if dim == '8':
                        chunks = f.read(32)
                    if dim == '16':
                        chunks = [f.read(32), f.read(32), f.read(32), f.read(32)]
                    row.append(builder.make_tile(chunks, dim))
                else:
                    row.append(builder.make_blank_tile16())
            tiles.append(row)

    array_rows = []
    for row in tiles:
        array_rows.append(np.concatenate(row, axis=1))
    assembled = np.concatenate(array_rows, axis=0)
    image = Image.fromarray(assembled, 'P')
    file_name = "temp_ass"
    image.save("outputs/bin_to_bmp/tiles/" + file_name + ".bmp")


def main():
    addrs = [['blank', '2F810', '2F811', '2F812', '2F813', '2F814'],
             ['blank', '2F820', '2F821', '2F822', '2F823', '2F824'],
             ['2F7FF', '2F830', '2F831', '2F832', '2F833', '2F834'],
             ['2F80F', '2F840', '2F841', '2F842', '2F843', '2F844'],
             ['2F815', '2F816', '2F817', '2F818', '2F819', 'blank']]

    #test_make_tile8("inputs/tiles_to_write/vm3_14_16_18_20_final_edited_test", '00000200')
    test_make_tile16("inputs/tiles_to_write/vm3_14_16_18_20_final_edited_test", '00000200')
    #process_tile_order("inputs/vm3_14_16_18_20_final", addrs, '16')
    #writer = Cps2TileWriter()
    #img = writer.read_image("inputs/tiles_to_write/temp_ass_edit.bmp")
    #writer.write_to_gfx(img, "inputs/tiles_to_write/vm3_14_16_18_20_final", addrs, '16')

if __name__ == "__main__":
    main()
