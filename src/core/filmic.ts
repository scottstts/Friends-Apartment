/** Blender Filmic view transform, Very High Contrast look.
 *
 * Blender 3.6's OCIO chain is:
 *   scene-linear sRGB -> Filmic Log -> Very High Contrast -> sRGB display.
 * The log allocation constants and highlight desaturation threshold come from
 * Blender's bundled config. The 4096-entry `filmic_to_1.20_1-00.spi1d` look is
 * a logistic curve; these coefficients fit the official table to < 4.9e-5.
 */
import { clamp, exp, float, log2, max, mix, sRGBTransferEOTF, vec3 } from 'three/tsl'
import type { N } from '../mats/tsl'

const LOG_MIN_EV = -12.473931188
const LOG_RANGE_EV = 25.0
const LOG_DISPLAY_MAX = 0.66
const DESAT_START = 0.625

const LOOK_SLOPE = 13.721
const LOOK_MIDPOINT = 0.6066
const LOOK_BLACK = 1 / (1 + Math.exp(LOOK_SLOPE * LOOK_MIDPOINT))
const LOOK_WHITE = 1 / (1 + Math.exp(-LOOK_SLOPE * (1 - LOOK_MIDPOINT)))

/** Returns display-linear sRGB so Three's sole output transform can encode it. */
export function blenderFilmicVeryHighContrast(sceneLinear: N): N {
  // Filmic first allocates a 25-stop scene-linear range into 0..1. Its 65^3
  // shaper is identity through ordinary values and progressively removes
  // chroma only at the extreme highlight end, keeping bulbs from clipping to
  // coloured primaries.
  const allocated = clamp(
    log2(max(sceneLinear, vec3(2 ** LOG_MIN_EV))).sub(LOG_MIN_EV).div(LOG_RANGE_EV),
    0,
    1,
  )
  const peak = max(allocated.r, max(allocated.g, allocated.b))
  const desatProgress = clamp(peak.sub(DESAT_START).div(1 - DESAT_START), 0, 1)
  const desatAmount = desatProgress.oneMinus().pow(1.35).oneMinus()
  const filmicLog = clamp(mix(allocated, vec3(peak), desatAmount).div(LOG_DISPLAY_MAX), 0, 1)

  // Very High Contrast is `filmic_to_1.20_1-00`: an S-shaped display curve
  // normalised to exact black and white.
  const sigmoid = float(1).div(exp(filmicLog.sub(LOOK_MIDPOINT).mul(-LOOK_SLOPE)).add(1))
  const displayEncoded = clamp(sigmoid.sub(LOOK_BLACK).div(LOOK_WHITE - LOOK_BLACK), 0, 1)

  // The look table is display-encoded. Convert back to display-linear here;
  // PostProcessing performs the one and only sRGB output encoding afterwards.
  return sRGBTransferEOTF(displayEncoded)
}
