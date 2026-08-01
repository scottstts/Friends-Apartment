interface UserAgentDataLike {
  mobile: boolean
  brands?: readonly { brand: string }[]
}

interface NavigatorWithUserAgentData extends Navigator {
  userAgentData?: UserAgentDataLike
}

const MOBILE_UA = /Android|iPhone|iPad|iPod|Mobile|Tablet/i
const CHROMIUM_UA = /(?:Chrome|Chromium|Edg|OPR|Brave)\/[\d.]+/i
const CHROMIUM_BRAND = /^(?:Chromium|Google Chrome|Microsoft Edge|Opera|Brave)$/i

/** The game intentionally targets WebGPU-capable Chromium desktop browsers. */
export function isDesktopChromium(navigatorLike: Navigator): boolean {
  const nav = navigatorLike as NavigatorWithUserAgentData
  if (nav.userAgentData?.mobile || MOBILE_UA.test(nav.userAgent)) return false

  const brands = nav.userAgentData?.brands
  if (brands?.length) return brands.some(({ brand }) => CHROMIUM_BRAND.test(brand))

  return CHROMIUM_UA.test(nav.userAgent)
}
