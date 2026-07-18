/**
 * @openair/contracts — the single source of truth for every cross-boundary
 * shape in OPEN-AIR: topic grammar, DeviceRecord, AgentHeartbeat, the GUI
 * envelope, layout JSON, and the YAK contracts.
 *
 * This file is the ONLY public surface of the package (Phase 1 §1.2).
 *
 * Rollout (Documents/Strategies/Phase 1.md §7):
 *   step 2 — topics/ (grammar + legacy map + vectors)          ← YOU ARE HERE
 *   step 3 — heartbeat.ts, device-record.ts
 *   step 4 — layout/, yak/ (incl. the yak_handler runtime message)
 *   step 5 — validate CLI ratchet
 *   step 6 — Rust adoption seed
 */

export const CONTRACTS_VERSION = '0.1.0' as const

export {
  AgentHeartbeatSchema,
  AgentStatusSchema,
  LegacyFailoverHeartbeatV0Schema,
  heartbeatLwt,
  type AgentHeartbeat,
  type AgentStatus,
  type LegacyFailoverHeartbeatV0,
} from './heartbeat.js'
export {
  DeviceExtraSchema,
  DeviceRecordSchema,
  DeviceStatusSchema,
  LegacyVisaRecordV0Schema,
  mapV40VisaRecord,
  type DeviceExtra,
  type DeviceRecord,
  type DeviceStatus,
  type LegacyVisaRecordV0,
} from './device-record.js'
export { deviceIdFor, fnv1a64, type DeviceIdentitySource } from './identity.js'
export { fromUnixSeconds } from './time.js'

export {
  CONTAINER_TYPES,
  EXACT_LEAF_TYPES,
  LEAF_SUBSTRINGS,
  LEGACY_WIDGET_TYPES,
  classifyWidgetType,
  type ContainerType,
  type WidgetTypeClass,
} from './layout/widget-types.js'
export { KNOWN_CONVERTERS, YakBindingSchema, lintYakBinding, type YakBinding } from './layout/yak-binding.js'
export { isStrictValid, validateLayoutDocument, type LayoutIssue, type LayoutIssueLevel } from './layout/node.js'
export { findOrderCollisions, parseFolderName, type FolderCollision, type ParsedFolderName } from './layout/folder-grammar.js'
export {
  YakHandlerWireSchema,
  YakIncomingMessageSchema,
  type YakHandlerWire,
  type YakIncomingMessage,
} from './yak/verbs.js'

export { Topics, type ParsedTopic } from './topics/builders.js'
export {
  GUI_ROOT,
  LOG_LEVELS,
  MONITOR_DIRS,
  ROOT,
  TopicError,
  YAK_VERBS,
  type LogLevel,
  type MonitorDir,
  type YakVerb,
} from './topics/grammar.js'
export { guiPrefixFromPanelPath, guiSegmentsFromPanelPath } from './topics/gui-path.js'
export { V40_ALIASES, type LegacyFamily, type LegacyParsed } from './topics/legacy.js'
export { TOPIC_FAMILIES, retainClassOf, type FamilyKind, type RetainClass, type TopicFamily } from './topics/tree.js'
