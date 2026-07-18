/**
 * Device identity derivation — guidelines D2, as a contract in code.
 * Priority: serial → protocol-native stable address → FNV-1a 64-bit content
 * hash of make|model|address. Both languages implement THIS file's rules
 * (Rust twin: contracts/rust/src/identity.rs); the vector suite pins them,
 * because two agents deriving different IDs for one instrument recreates
 * the duplicate-34401A bug on the bus.
 */

const ID_KEY_SAFE = /[^A-Za-z0-9._:-]/g

/** Replace anything outside the deviceId key charset with '-'. */
function sanitizeKey(value: string): string {
  return value.replace(ID_KEY_SAFE, '-')
}

/** FNV-1a 64-bit over UTF-8 bytes, lowercase hex (16 chars). */
export function fnv1a64(input: string): string {
  const OFFSET = 0xcbf29ce484222325n
  const PRIME = 0x100000001b3n
  const MASK = 0xffffffffffffffffn
  let hash = OFFSET
  for (const byte of new TextEncoder().encode(input)) {
    hash ^= BigInt(byte)
    hash = (hash * PRIME) & MASK
  }
  return hash.toString(16).padStart(16, '0')
}

export interface DeviceIdentitySource {
  protocol: string
  serial?: string | undefined
  address?: string | undefined
  make?: string | undefined
  model?: string | undefined
}

/** The D2 rule. Returns `{protocol}:{stableKey}`. */
export function deviceIdFor(src: DeviceIdentitySource): string {
  const serial = src.serial?.trim()
  if (serial) return `${src.protocol}:${sanitizeKey(serial)}`
  const address = src.address?.trim()
  if (address) return `${src.protocol}:${sanitizeKey(address)}`
  const content = `${src.make ?? ''}|${src.model ?? ''}|${src.address ?? ''}`
  return `${src.protocol}:${fnv1a64(content)}`
}
