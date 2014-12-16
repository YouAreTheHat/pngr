
### ### ### ### ### ### ### IMPORTANT ### ### ### ### ### ### ###
#                                                               #
# This module is a work in progress. Comments, particularly the #
# ones preceding a class or function definition, are intended   #
# to represent the desired end result of this code. Until such  #
# time as a version 1.0 of this work is published, with this    #
# warning removed, all the contents and functions herein are to #
# be considered experimental, incomplete, and mutable. All      #
# comments outside of this box are to be considered lies and    #
# wishful thinking, not accurate documentation.                 #
#                                                               #
### ### ### ### ### ### ### #### #### ### ### ### ### ### ### ###

import math, zlib

# A custom error raised for issues with this module only.
class PngError(Exception):
    
    def __init__(self, message=None):
        if message is None:
            message = "an unspecified error has occurred"
        self.message = message
        super(PngError, self).__init__(self.message)


# Reads PNG files.
# Largely acts as a wrapper for open(), automatically
# reading in positions and increments appropriate for the PNG format.
# Is also capable of spawning PngChunks.
class PngReader:
    """    !!! WIP !!!

    Reads PNG files and returns chunks of information.
    """
    
    def __init__(self, pngfile):
        self.png_path = pngfile #path to PNG file
        self.png = None
        # This will hold the file's first 8 bytes; in a PNG, these should
        # always be the static PNG signature
        self.png_sig = b''
        # Check if the passed file really is a PNG; if not, raise error
        if not self.is_valid():
            raise PngError("file {} is corrupt or not a PNG".format(\
                self.png_path))
        
    # For using the 'with' statement to initialize
    def __enter__(self):
        self.open_png()
        return self
    
    # For using the 'with' statement to initialize
    def __exit__(self, type, value, traceback):
        self.close_png()

    # Checks if the file location passed at init refers to a valid PNG.
    # Never call this if the file is already open
    def is_valid(self):
        # This is the signature of all properly constructed PNGs; if the first
        # 8 bytes of the file are not this, it isn't a PNG
        sig = b'\x89PNG\r\n\x1a\n'
        with open(self.png_path, 'rb') as f:
            self.png_sig = f.read(8)
            f.seek(0)
        if self.png_sig == sig:
            return True
        else:
            return False

    # Acts as a wrapper for open(); also records the cursor position
    def open_png(self):
        if (self.png is None) or (self.png and self.png.closed):
            self.png = open(self.png_path, 'rb')
            self.last_pos = self.png.tell()

    # Closes the PNG
    def close_png(self):
        if self.png and not self.png.closed:
            self.png.close()

    # Allows an instance to resume reading a file from the position in which
    # it was after its last successful open_png() or next_chunk() call.
    def resume(self):
        if self.png and not self.png.closed:
            self.png.seek(self.last_pos)

    # Reads the next chunk in the file and returns a PngChunk object.
    # If at the beginning of a file, it will skip the PNG signature.
    # It will fail if its associated PNG is not opened for reading.
    def next_chunk(self):
        # Skip the PNG signature because it is not a chunk
        if self.png.tell() == 0:
            self.png.seek(8)
        # Make a list to hold the chunk
        self.cur_chunk = []
        # Read the length, type, data, and crc
        self.cur_chunk.append(self.png.read(4))
        self.cur_chunk.append(self.png.read(4))
        self.cur_chunk.append(self.png.read(\
            int.from_bytes(self.cur_chunk[0], 'big')))
        self.cur_chunk.append(self.png.read(4))
        # Record the cursor position
        self.last_pos = self.png.tell()
        try:
            # Return a PngChunk for the read bytes
            return PngChunk(self.cur_chunk)
        finally:
            # We've finished reading, so forget about the current chunk
            # (since it's no longer "current")
            del self.cur_chunk

    # Check if there is at least one more chunk.
    # It will fail if its associated PNG is not opened for reading.
    def has_more(self):
        if len(self.png.read(12)) < 12:
            self.png.seek(self.last_pos)
            return False
        else:
            self.png.seek(self.last_pos)
            return True
            

# Stores organized data for a single chunk of a PNG.
# Superclass for specific chunk types.
# The 'meta' dict is sued to stores the store the attributes of the chunk
# which the chunk itself stores (length, type, CRC).
# Subclasses should extend the 'info' dict with the parsed information the
# chunk actually carries (e.g., IHDR adds 'Width', 'Height', etc).
class PngChunk:
    """    !!! WIP !!!

    Stores organized data on a PNG chunk.
    """

    # Must be passed the entire binary chunk as a list
    def __init__(self, c_bytes):
        self.meta = {}
        self.meta['Length'] = int.from_bytes(c_bytes[0], 'big')
        self.meta['Type'] = c_bytes[1].decode()
        self.meta['CRC'] = c_bytes[3]
        self.data = bytearray(c_bytes[2])
        self.info = {}

    # Getter for chunk meta-data
    def get_meta(self, property_name=None):
        """\tReturns dict of chunk length, type, and CRC.

        Specify a key to return only that value."""
        if property_name is None:
            return self.meta
        return self.meta[property_name]

    # Getter for raw data
    def get_data(self, buffer=None):
        """\tReturns generator over unparsed data, <buffer> bytes at a time.
        Defaults to entire data field at once.

        This does not include the length, type, or CRC fields.
        Use get_raw() for a binary version of the entire chunk.
        WARNING: may be up to 2^31 bytes long w/o buffer, use with caution"""
        return self._raw_generator(buffer, 8, -4)

    # Getter for parsed contents; most useful for subtypes
    def get_info(self, info_name=None):
        """\tReturns parsed chunk data as dict (may be empty).

        For known chunk types, this should return their stored information
        in human-readable form."""
        if info_name is None:
            return self.info
        return self.info[info_name]

    # Getter for the binary data of the entire chunk
    def get_raw(self, buffer: '4 to 2147483659'=None):
        """\tReturns generator over binary chunk, <buffer> bytes at a time.
        Defaults to entire chunk at once.

        WARNING: may be over 2^31 bytes long w/o buffer, use with caution"""
        if buffer is not None:
            if buffer < 4:
                raise PngError("buffer length out of range")
        return self._raw_generator(buffer)

    # Makes generator over binary form of chunk (or part of chunk)
    def _raw_generator(self, buffer, start=0, end=0):
        l = 12 + len(self.data)
        if end < 0:
            l += end
        if start >= 0:
            num = start
        elif abs(start) <= l:
            num = l + start
        if buffer is None:
            buffer  = l
        while num < l:
            result, toread = b'', buffer
            while toread > 0:
                b_l = len(result)
                if num < 4:
                    result += self.meta['Length'].to_bytes(4, 'big')\
                              [num:num + toread]
                elif num >= 4 and num < 8:
                    result += bytes(self.meta['Type'], 'utf8')\
                              [num - 4:num - 4 + toread]
                elif num >= 8 and num < (l - 4):
                    result += self.data[num - 8:num - 8 + toread]
                elif num - l + toread < 0:
                    result += self.meta['CRC'][num - l:num - l + toread]
                else:
                    result += self.meta['CRC'][num - l:]
                    toread = 0
                num += len(result) - b_l
                toread -= len(result) - b_l
            yield result

    # Sets the 'Length' to the actual length of its raw data
    def set_length(self):
        """\tSet 'Length' to length of raw data.

        Returns difference between new and old lengths."""
        if self.meta('Length') != len(self.raw):
            oldlen = self.meta('Length')
            self.meta('Length') = len(self.raw)
            return (self.meta('Length') - oldlen)
        return 0


# Stores parsed data from the IHDR chunk.
# PngData objects can use IHDR info dict to extract image properties
class IHDR(PngChunk):

    # IHDR can extract all of its info at init
    def __init__(self, genchunk):
        if not isinstance(genchunk, PngChunk):
            raise PngError("expected PngChunk, but {} found"\
                           .format(type(genchunk).__name__))
        self.meta = genchunk.meta
        self.data = genchunk.data
        self.info = genchunk.info
        self.info['Width'] = int.from_bytes(self.data[:4], 'big')
        self.info['Height'] = int.from_bytes(self.data[4:8], 'big')
        self.info['Bit depth'] = self.data[8]
        self.info['Color type'] = self.data[9]
        self.info['Interlace'] = self.data[-1]


# Stores parsed data from an IDAT chunk.
class IDAT(PngChunk):

    # Init does not parse info because info from other chunks (IHDR and
    # possibly others) is needed to understand the formatting.
    # Plus, it's kind of a large and memory-intensive process.
    def __init__(self, genchunk):
        if not isinstance(genchunk, PngChunk):
            raise PngError("expected PngChunk, but {} found"\
                           .format(type(genchunk).__name__))
        self.meta = genchunk.meta
        self.data = genchunk.data
        self.info = genchunk.info


class PLTE(PngChunk):
    pass


class IEND(PngChunk):
    pass


# Stores PngChunks and analyzes their attributes.
# Acts as an object representation of the PNG file, since it holds all of the
# file's data in chunk form.
# Generic PngChunks should be passed to it  through the 'addchunk' method;
# it will convert them to an appropriate subtype if one is defined.
class PngData:
    """    !!! WIP !!!

    Stores and analyzes PngChunks and prints their data.
    """

    # Static mapping of chunk types to chunk subclasses.
    # Used to replace generic chunks with their specific classes for
    # analyzation.
    # Critical chunks are unconditionally supported; ancillary chunks will
    # be supported selectively as they are developed and added to the module.
    chunktypes = {'IHDR': IHDR,
                  'IDAT': IDAT,
                  'PLTE': PLTE,
                  'IEND': IEND}

    # Static mapping of color types to their sample information.
    # The first value in the tuple is the number of samples/channels in the
    # decompressed IDAT stream. This should be used for parsing the filter
    # and, consequently, the scanlines.
    # The second value reflects the presence of a PLTE. True means that a PLTE
    # must appear; False means it must not appear; None means it may appear,
    # but may also be safely ignored.
    # Note that type 3 implies that the pixels in PLTE are 3-tuples of 1-byte
    # samples (a bit depth less than 8 just adds leading zeroes).
    colortypes = {0: (1, False),
                  2: (3, None),
                  3: (1, True),
                  4: (2, False),
                  6: (4, None)}

    # Static PNG signature; it will be needed when writing
    signature = b'\x89PNG\r\n\x1a\n'

    def __init__(self):
        self.chunks = []
        self.ihdr_pos = None
        self.plte_pos = None

    def add_chunk(self, chunk):
        if not isinstance(chunk, PngChunk):
            raise PngError("expected PngChunk, but {} found"\
                           .format(type(chunk).__name__))
        ctype = chunk.get_meta('Type')
        if ctype in self.chunktypes.keys():
            if ctype == 'IHDR':
                self.ihdr_pos = len(self.chunks)
            elif ctype == 'PLTE':
                self.plte_pos = len(self.chunks)
            self.chunks.append(self.chunktypes[ctype](chunk))
        else:
            self.chunks.append(chunk)

    # Rough unfiltering method.
    # Currently works naively on an array of scanlines.
    # No support for interlacing. Requires precalculated pixel depth. May
    # work improperly on color type 0 for bit depths less than 8.
    def _unfilter(self, lines, px_depth):
        for i in range(len(lines)):
            l = bytearray(lines[i])
            if l[0] == 0: #filter 'none'
                pass
            elif l[0] == 1: #filter 'sub'
                for j in range((1 + px_depth), len(l)):
                    l[j] = (l[j] + l[j - px_depth])%256
            elif l[0] == 2: #filter 'up'
                for j in range(1, len(l)):
                    if i == 0:
                        prior = 0
                    else:
                        prior = lines[i - 1][j - 1]
                    l[j] = (l[j] + prior)%256
            elif l[0] == 3: #filter 'average'
                for j in range(1, len(l)):
                    if j in range(1, (1 + px_depth)):
                        prev = 0
                    else:
                        prev = l[j - px_depth]
                    if i == 0:
                        prior = 0
                    else:
                        prior = lines[i - 1][j - 1]
                    l[j] = (l[j] + math.floor((prev + prior)/2))%256
            elif l[0] == 4: #filter 'Paeth'
                for j in range(1, len(l)):
                    flg = False
                    if j in range(1, (1 + px_depth)):
                        prev = 0
                        flg = True
                    else:
                        prev = l[j - px_depth]
                    if i == 0:
                        prior = 0
                        flg = True
                    else:
                        prior = lines[i - 1][j - 1]
                    if flg:
                        prevpri = 0
                    else:
                        prevpri = lines[i - 1][(j - 1) - px_depth]
                    p_p = prev + prior + prevpri
                    p_d = []
                    for p_v in [prev, prior, prevpri]:
                        p_d.append(math.abs(p_p - p_v))
                    if p_d[0] <= p_d[1] and p_d[0] <= p_d[2]:
                        paeth = prev
                    elif p_d[1] <= p_d[2]:
                        paeth = prior
                    else:
                        paeth = prevpri
                    l[j] = (l[j] + paeth)%256
            l = l[1:]
            lines[i] = l
        return lines

    # Rough method for extracting pixel data from IDATs
    # Currently works naively on all data at once, returns array. No support
    # for interlacing. May work improperly on color type 0 for bit depths less
    # than 8.
    def get_scanlines(self):
        info = self.chunks[self.ihdr_pos].get_info()
        if info['Interlace']:
            raise PngError("interlacing not supported")
        c_count = self.colortypes[info['Color type']][0]
        c_depth = max([info['Bit depth']//8, 1])
        p_depth = c_depth * c_count
        p_w, p_h = info['Width'], info['Height']
        cmp = b''
        for chunk in [c for c in self.chunks if isinstance(c, IDAT)]:
            for d in chunk.get_data():
                cmp += d
        dcmp = zlib.decompress(cmp)
        scanlines = []
        for i in range(0, len(dcmp), ((p_depth * p_w) + 1)):
            scanlines.append(dcmp[i:i + ((p_depth * p_w) + 1)])
        scanlines  = self._unfilter(scanlines, p_depth)
        return scanlines


## Notes
# pngr_test.py has some testing, basic implementations, etc
# add PngChunk subclasses for each critical type (and hopefully important
#   ancillary types as well). use them for analyzing chunks more effectively.
# project purpose has been changed: the goal is now to make a PNG decoder,
#   including parsing, modification, and re-writing
# for the above goal:
# - data class would hold info attributes (probably)
# - only chunks which affect the reading/writing of IDAT/pixel data would need
#   to be parsed (others are optional)
# - only critical info/data would need to be stored
# - maybe a gateway to stegosaurus?
# make chunk subtypes able to init with bin arrays from reader
#   ...because reasons?
# OR
# eliminate subtypes and meta array, trust 'Type' for chunk typing, have data
#   class parse and store information to avoid redundant storage. this may
#   be necessary for cat'ing IDATs and using IHDR and PLTE info anyway
# for the above, only certain data has to be stored; chunks can still be
#   mostly responsible for themselves.
# keep mem usage in mind. at minimum, entire file is in mem. decompressing
#   IDAT(s) all at once nearly doubles that. copying decomp'd data to array
#   doubles decomp'd data length, which is already longer than IDAT. working
#   with data in place as much as possible would be wise.
# the above may be complicated in the case of Adam7 interlacing
# (de)compression, making scanlines, and (un)filtering may also benefit from
#   generators/buffered IO (or be impossible - look into that)
# scanline and unfiltering functions are very rough; revise to ensure they are
#   compatible withh color types and bit depths. also include a buffered read
#   by way of a generator.
# for above, carefully consider how decompression and unfiltering will work;
#   the compressed data must be at least 2 scanlines long to be useful for
#   unfiltering.
# if this will work as a proper PNG decoder, ensure that all requirements from
#   the PNG standard are followed.
##
