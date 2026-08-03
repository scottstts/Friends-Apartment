"""Crop a region out of an image and write it enlarged.

Reading a 1280 px reference at full frame loses exactly the detail the build
depends on - how a bracket is fixed, how many rods a sign hangs from.  This
pulls a normalised box out and scales it up so it can be looked at properly.

    crop.py <src> <dst> <x0> <y0> <x1> <y1> [zoom]

Coordinates are fractions of width/height, origin top-left.
"""
import sys
import OpenImageIO as oiio


def crop(src, dst, x0, y0, x1, y1, zoom=3.0):
    buf = oiio.ImageBuf(src)
    spec = buf.spec()
    w, h = spec.width, spec.height
    px0, py0 = int(x0 * w), int(y0 * h)
    px1, py1 = int(x1 * w), int(y1 * h)
    roi = oiio.ROI(px0, px1, py0, py1, 0, 1, 0, spec.nchannels)
    cut = oiio.ImageBufAlgo.cut(buf, roi)
    ow = int((px1 - px0) * zoom)
    oh = int((py1 - py0) * zoom)
    out = oiio.ImageBufAlgo.resize(cut, roi=oiio.ROI(0, ow, 0, oh, 0, 1,
                                                    0, spec.nchannels))
    out.write(dst)
    print("%s  %dx%d -> %s  %dx%d" % (src, px1 - px0, py1 - py0, dst, ow, oh))


if __name__ == "__main__":
    a = sys.argv[1:]
    crop(a[0], a[1], *[float(v) for v in a[2:]])
