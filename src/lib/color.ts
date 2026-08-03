/** Light-colour helpers shared by every scene's practical fixtures.
 * Extracted from the props.py port (scenes/monica/props). */

/** Linear-sRGB tint of a Planckian radiator at `kelvin` (props.blackbody). */
export function blackbody(kelvin: number): [number, number, number] {
  const g = (x: number, mu: number, s1: number, s2: number) =>
    Math.exp(-(((x - mu) / (x < mu ? s1 : s2)) ** 2) / 2.0)
  let X = 0
  let Y = 0
  let Z = 0
  for (let nm = 380; nm <= 780; nm += 5) {
    const lm = nm * 1e-9
    const sp = 1.0 / (lm ** 5 * (Math.exp(1.4387769e-2 / (lm * kelvin)) - 1.0))
    X += sp * (1.056 * g(nm, 599.8, 37.9, 31.0) + 0.362 * g(nm, 442.0, 16.0, 26.7) - 0.065 * g(nm, 501.1, 20.4, 26.2))
    Y += sp * (0.821 * g(nm, 568.8, 46.9, 40.5) + 0.286 * g(nm, 530.9, 16.3, 31.1))
    Z += sp * (1.217 * g(nm, 437.0, 11.8, 36.0) + 0.681 * g(nm, 459.0, 26.0, 13.8))
  }
  const rgb: [number, number, number] = [
    3.2406 * X - 1.5372 * Y - 0.4986 * Z,
    -0.9689 * X + 1.8758 * Y + 0.0415 * Z,
    0.0557 * X - 0.204 * Y + 1.057 * Z,
  ]
  const m = Math.max(...rgb)
  return [Math.max(rgb[0] / m, 0), Math.max(rgb[1] / m, 0), Math.max(rgb[2] / m, 0)]
}
