import sys, OpenImageIO as oiio
for f in sys.argv[1:]:
    b = oiio.ImageBuf(f); s = oiio.ImageBufAlgo.computePixelStats(b)
    avg = s.avg[:3]; lum = 0.2126*avg[0]+0.7152*avg[1]+0.0722*avg[2]
    # rough saturation: mean of (max-min) per channel over the average colour
    sat = (max(avg)-min(avg))/max(1e-6, max(avg))
    print("%-46s  lum %.3f  rgb %.3f %.3f %.3f  sat %.2f  min %.2f max %.2f" %
          (f.split('/')[-1], lum, avg[0], avg[1], avg[2], sat,
           min(s.min[:3]), max(s.max[:3])))
