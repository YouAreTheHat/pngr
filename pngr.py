
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

import math

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
# The 'properties' dict is used to store information from the chunk which
# might be retrieved and/or analyzed. The keys should be a string of the
# standard name of the property, with the first letter capitalized (e.g.,
# 'Length'). Values should be stored in their most useful form (e.g., Length
# should be an int).
# Subclasses should extend the 'Meta' dict with chunk-specific properties
# (e.g., IHDR adds 'Width', 'Height', etc).
# The '_bin' list is not intended to be accessed except by 'get_binary' or
# by subclass functions; it should never be used outside of the (sub)class.
class PngChunk:
    """    !!! WIP !!!

    Stores organized data on a PNG chunk.
    """

    # Must be passed the entire binary chunk as a list
    def __init__(self, c_bytes):
        self.properties = {}
        self.properties['Length'] = int.from_bytes(c_bytes[0], 'big')
        self.properties['Type'] = c_bytes[1].decode()
        self.properties['Data'] = c_bytes[2]
        self.properties['CRC'] = c_bytes[3]
        self.properties['Meta'] = {}
        self.meta = self.properties['Meta']

    # Simple getter for a given property
    def get_property(self, property_name=None):
        if property_name is None:
            return self.properties
        return self.properties[property_name]

    # Getter for the binary form of the entire chunk
#    def get_binary(self):
#        bindat = b''
#        for v in self._bin:
#            bindat += v
#        return bindat

    # Getter for metadata; only useful for subclasses
    def get_meta(self, meta_property=None):
        if meta_property is None:
            return self.properties['Meta']
        return self.properties['Meta'][meta_property]


# Stores parsed data from the IHDR chunk.
# PngData objects can use IHDR 'Meta' dict to extract image properties
class IHDR(PngChunk):

    # IHDR can extract all of its metadata at init
    def __init__(self, genchunk):
        if not isinstance(genchunk, PngChunk):
            raise PngError("expected PngChunk, but {} found"\
                           .format(type(genchunk).__name__))
#        self._bin = genchunk._bin
        self.properties = genchunk.properties
        self.meta = self.properties['Meta']
        self.meta['Width'] = int.from_bytes(self.properties['Data'][:4],
                                            'big')
        self.meta['Height'] = int.from_bytes(self.properties['Data'][4:8],
                                             'big')
        self.meta['Bit depth'] = self.properties['Data'][8]
        self.meta['Color type'] = self.properties['Data'][9]
        self.meta['Interlace'] = self.properties['Data'][-1]


# Stores parsed data from an IDAT chunk.
class IDAT(PngChunk):

    # Init does not parse metadata because info from other chunks (IHDR and
    # possibly PLTE) is needed to understand the formatting
    def __init__(self, genchunk):
        if not isinstance(genchunk, PngChunk):
            raise PngError("expected PngChunk, but {} found"\
                           .format(type(genchunk).__name__))
#        self._bin = genchunk._bin
        self.properties = genchunk.properties
        self.meta = self.properties['Meta']


class PLTE(PngChunk):
    pass


class IEND(PngChunk):
    pass


# Stores PngChunks and displays and analyzes their attributes.
# Acts as an object representation of the PNG file, since it holds all of the
# file's data in chunk form.
# Generic PngChunks should be passed to it at initialization and through the
# 'addchunk' method; it will convert them to an appropriate subtype if one is
# defined.
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
    
    # May optionally leave out PNG signature since it is identical for all
    # PNGs (and any chunks making it to this class should always be from a
    # proper PNG anyway).
    def __init__(self, add_sig=True):
        self.signature = None
        if add_sig:
                self.signature = b'\x89PNG\r\n\x1a\n'
        self.chunks = []
        self.ihdr_pos = None
        self.plte_pos = None

    def add_chunk(self, chunk):
        if not isinstance(chunk, PngChunk):
            raise PngError("expected PngChunk, but {} found"\
                           .format(type(chunk).__name__))
        # placeholder; convert chunk to an appropriate subclass (if available)
        # before appending it.
        # also record position if IHDR or PLTE chunk
        self.chunks.append(chunk)


## Notes
# pngr_test.py has some testing, basic implementations, etc
# add PngChunk subclasses for each critical type (and hopefully important
#   ancillary types as well). use them for analyzing chunks more effectively.
# make a PngData method for converting chunks to their subtypes, or implement
#   that functionality in addchunk()
# make the above method record the position of the header and palette, or just
#   their meta-data
# ensure a PngData obj can pass IHDR and PLTE data to its IDAT(s) for scanline
#   organization
# project purpose has been changed: the goal is now to make a PNG decoder,
#   including parsing, modification, and re-writing
# for the above goal:
# - data class would hold meta-data attributes
# - only chunks which affect the reading/writing of IDAT/pixel data would need
#   to be parsed
# - only critical info/meta-data would be stored (and binary data)
# - maybe a gateway to stegosaurus?
# filter decoding 'methods' are present in pngr_test. move them here, break
#   the algorithms out, make filter and unfilter methods on data class
# make chunk subtypes able to init with bin arrays from reader
# OR
# eliminate subtypes and meta array, trust 'Type' for chunk typing, have data
#   class parse and store information to avoid redundant storage. this is
#   largely necessary for cat'ing IDATs and using IHDR and PLTE info anyway
# keep mem usage in mind. at minimum, entire file is in mem. decompressing
#   IDAT(s) all at once nearly doubles that. copying decomp'd data to array
#   doubles decomp'd data length, which is already longer than IDAT. working
#   with data in place as much as possible would be wise.
# the above may be complicated in the case of Adam7 interlacing
# docstrings (and function annotations) are useful. use them, at least so that
#   comments stop appearing as help() entries for this module.
##
