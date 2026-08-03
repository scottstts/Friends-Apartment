"""Sample the average colour of a box in an image, as sRGB hex.

    pick.py <img> <x0> <y0> <x1> <y1> [<x0> <y0> <x1> <y1> ...]

Coordinates are fractions of width/height, origin top-left.  Eyeballing a
colour off a photograph and typing a guess into a palette is how the couch
ended up salmon; this reads the number the reference actually holds.
"""
import sys
import OpenImageIO as oiio


def pick(src, boxes):
    buf = oiio.ImageBuf(src)
    sp = buf.spec()
    w, h = sp.width, sp.height
    out = []
    for (x0, y0, x1, y1) in boxes:
        roi = oiio.ROI(int(x0 * w), int(x1 * w), int(y0 * h), int(y1 * h),
                       0, 1, 0, min(3, sp.nchannels))
        st = oiio.ImageBufAlgo.computePixelStats(oiio.ImageBufAlgo.cut(buf, roi))
        avg = [min(1.0, max(0.0, v)) for v in st.avg[:3]]
        out.append("".join("%02X" % int(round(v * 255)) for v in avg))
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    nums = [float(v) for v in a[1:]]
    boxes = [tuple(nums[i:i + 4]) for i in range(0, len(nums), 4)]
    for b, hexv in zip(boxes, pick(a[0], boxes)):
        print("%-28s %s" % (str(b), hexv))
