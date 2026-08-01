/** Python-compatible `random.Random` (MT19937 + CPython method semantics).
 *
 * The Blender build seeds `random.Random(n)` everywhere to scatter shelf
 * clutter, jitter chairs and pick palette entries.  Reproducing CPython's
 * generator bit-for-bit keeps every one of those layouts identical, which is
 * part of scene parity: the same jar ends up on the same shelf.
 */

const N = 624
const M = 397
const MATRIX_A = 0x9908b0df
const UPPER_MASK = 0x80000000
const LOWER_MASK = 0x7fffffff

export class PyRandom {
  private mt = new Uint32Array(N)
  private mti = N + 1

  constructor(seed: number) {
    this.seedInt(seed)
  }

  private initGenrand(s: number): void {
    this.mt[0] = s >>> 0
    for (let i = 1; i < N; i++) {
      const prev = this.mt[i - 1] ^ (this.mt[i - 1] >>> 30)
      // 1812433253 * prev + i, in 32-bit — split multiply to stay exact
      const lo = (prev & 0xffff) * 1812433253
      const hi = (((prev >>> 16) * 1812433253) & 0xffff) << 16
      this.mt[i] = (((hi + lo) >>> 0) + i) >>> 0
    }
    this.mti = N
  }

  private initByArray(key: Uint32Array): void {
    this.initGenrand(19650218)
    let i = 1
    let j = 0
    let k = Math.max(N, key.length)
    for (; k; k--) {
      const prev = this.mt[i - 1] ^ (this.mt[i - 1] >>> 30)
      const lo = (prev & 0xffff) * 1664525
      const hi = (((prev >>> 16) * 1664525) & 0xffff) << 16
      this.mt[i] = ((((this.mt[i] ^ (((hi + lo) >>> 0) >>> 0)) >>> 0) + key[j] + j) >>> 0) >>> 0
      i++
      j++
      if (i >= N) {
        this.mt[0] = this.mt[N - 1]
        i = 1
      }
      if (j >= key.length) j = 0
    }
    for (k = N - 1; k; k--) {
      const prev = this.mt[i - 1] ^ (this.mt[i - 1] >>> 30)
      const lo = (prev & 0xffff) * 1566083941
      const hi = (((prev >>> 16) * 1566083941) & 0xffff) << 16
      this.mt[i] = ((((this.mt[i] ^ (((hi + lo) >>> 0) >>> 0)) >>> 0) - i) >>> 0) >>> 0
      i++
      if (i >= N) {
        this.mt[0] = this.mt[N - 1]
        i = 1
      }
    }
    this.mt[0] = 0x80000000
    this.mti = N
  }

  /** CPython random_seed for a non-negative int: split into 32-bit words. */
  private seedInt(n: number): void {
    n = Math.floor(Math.abs(n))
    const words: number[] = []
    if (n === 0) words.push(0)
    while (n > 0) {
      words.push(n % 4294967296)
      n = Math.floor(n / 4294967296)
    }
    this.initByArray(Uint32Array.from(words))
  }

  private genrandUint32(): number {
    let y: number
    if (this.mti >= N) {
      const mt = this.mt
      let kk: number
      for (kk = 0; kk < N - M; kk++) {
        y = (mt[kk] & UPPER_MASK) | (mt[kk + 1] & LOWER_MASK)
        mt[kk] = (mt[kk + M] ^ (y >>> 1) ^ (y & 1 ? MATRIX_A : 0)) >>> 0
      }
      for (; kk < N - 1; kk++) {
        y = (mt[kk] & UPPER_MASK) | (mt[kk + 1] & LOWER_MASK)
        mt[kk] = (mt[kk + (M - N)] ^ (y >>> 1) ^ (y & 1 ? MATRIX_A : 0)) >>> 0
      }
      y = (mt[N - 1] & UPPER_MASK) | (mt[0] & LOWER_MASK)
      mt[N - 1] = (mt[M - 1] ^ (y >>> 1) ^ (y & 1 ? MATRIX_A : 0)) >>> 0
      this.mti = 0
    }
    y = this.mt[this.mti++]
    y ^= y >>> 11
    y = (y ^ ((y << 7) & 0x9d2c5680)) >>> 0
    y = (y ^ ((y << 15) & 0xefc60000)) >>> 0
    y ^= y >>> 18
    return y >>> 0
  }

  /** random_random: 53-bit resolution float in [0, 1). */
  random(): number {
    const a = this.genrandUint32() >>> 5
    const b = this.genrandUint32() >>> 6
    return (a * 67108864.0 + b) * (1.0 / 9007199254740992.0)
  }

  uniform(a: number, b: number): number {
    return a + (b - a) * this.random()
  }

  private getrandbits(k: number): number {
    // k <= 32 is all we ever need
    return this.genrandUint32() >>> (32 - k)
  }

  private randbelow(n: number): number {
    if (n <= 0) return 0
    const k = 32 - Math.clz32(n - 1 || 1)
    if (n === 1) return 0
    let r = this.getrandbits(k)
    while (r >= n) r = this.getrandbits(k)
    return r
  }

  randint(a: number, b: number): number {
    return a + this.randbelow(b - a + 1)
  }

  /** random.choice(seq) */
  choice<T>(seq: readonly T[]): T {
    return seq[this.randbelow(seq.length)]
  }

  /** random.choices(population, weights)[0] — single draw, like the build uses. */
  choicesWeighted<T>(population: readonly T[], weights: readonly number[]): T {
    let total = 0
    const cum: number[] = []
    for (const w of weights) {
      total += w
      cum.push(total)
    }
    const x = this.random() * total
    // bisect_right
    let lo = 0
    let hi = cum.length - 1 // hi = len - 1, as CPython passes
    while (lo < hi) {
      const mid = (lo + hi) >> 1
      if (x < cum[mid]) hi = mid
      else lo = mid + 1
    }
    return population[lo]
  }
}
