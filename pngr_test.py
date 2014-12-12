"""This is just a test."""

import sys
import os, os.path
sys.path.insert(0, os.getcwd())
import pngr
#import binascii
#import codecs
#import re
import math
import zlib

## The following must be modified to fit the new interface of PngChunk
"""
d = []
   
with pngr.PngReader(os.path.join(os.getcwd(), "gradient3.png")) as p:
    while p.has_more():
        a = p.next_chunk()
        if a.get_property('Type') == 'IDAT':
            d.append(pngr.IDAT(a))
        elif a.get_property('Type') == 'IHDR':
            d.append(pngr.IHDR(a))

for h in [c for c in d if isinstance(c, pngr.IHDR)]:
    if h.get_meta('Color type') == 2:
        ch_count = 3
    ch_depth = h.get_meta('Bit depth')//8
    px_depth = ch_depth * ch_count
    px_w, px_h = h.get_meta('Width'), h.get_meta('Height')

cmp = b''
for t in [c for c in d if isinstance(c, pngr.IDAT)]:
    cmp += t.get_property('Data')
    
dcmp = zlib.decompress(cmp)
lines = []
for i in range(0, len(dcmp), ((px_depth * px_w) + 1)):
    lines.append(dcmp[i:i+((px_depth * px_w) + 1)])

## For parsing filters
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
##
"""

## Tests for generator function (reading data with buffer)
mylist = [25, "WORD", bytearray(16), b'foop']

def gen_func(buf):
    num = 0
    l = 12 + len(mylist[2])
    while num < l:
        result, toread = b'', buf
        while toread > 0:
            b_l = len(result)
            if num < 4:
                result += mylist[0].to_bytes(4, 'big')[num:num + toread]
            elif num >= 4 and num < 8:
                result += bytes(mylist[1], 'utf8')[num - 4:num - 4 + toread]
            elif num >= 8 and num < (l - 4):
                result += mylist[2][num - 8:num - 8 + toread]
            elif num - l + toread < 0:
                result += mylist[3][num - l:num - l + toread]
            else:
                result += mylist[3][num - l:]
                toread = 0
            num += len(result) - b_l
            toread -= len(result) - b_l
        yield result
            
def dothething(buffer):
    if buffer < 4:
        print("Buffer too small!")
        return
    for somebytes in gen_func(buffer):
        print(somebytes)
##

## For formatting as hex
#h = ["{:02x}".format(i).upper() for i in a.get_binary()]
#for i in range(math.ceil(len(h)/24)):
#    print(' '.join(h[i * 24:(i + 1) * 24]))
##
