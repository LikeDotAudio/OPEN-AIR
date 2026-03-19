# OPEN-AIR Refactor Task List (Phase 1: Migration)

## Legend
- [ ] Pending
- [/] In Progress
- [x] Completed
- [!] Blocked / Needs Attention

---

## 1. Core Infrastructure (Orchestration)
- [x] **oaConfiguration:** Move `managers/configini/` content to `oaConfiguration/`
- [x] **oaLogging:** Move `workers/logger/` content to `oaLogging/`
- [x] **oaDependencies:** Move `Installation/dependancy/` content to `oaDependencies/`
- [x] **oaInstallation:** Move `Installation/Setup.py` to `oaInstallation/`
- [x] **oaThreadManager:** Initialize with `OpenAir.py` logic (Migration start).

## 2. Communication Layer (The Blind Workers)
- [x] **oaComBroker:** Move `managers/System_Core/` (Broker/Router) to `oaComBroker/`
- [x] **oaComVisa:** Move `workers/instruments/` and `managers/VISA/` to `oaComVisa/`
- [x] **oaComMidi:** Move `workers/midi/` and `managers/Midi/` to `oaComMidi/`
- [x] **oaComOSC:** Move `workers/osc/` to `oaComOSC/`
- [x] **oaComSNMP:** Move `workers/snmp/` to `oaComSNMP/`
- [x] **oaSplinker:** Move `workers/Splinker/` to `oaSplinker/`

## 3. Data Vaults (State & Storage)
- [x] **oaGuiDefinitions:** Move `oaGuiDefinitions/*.json` to `oaGuiDefinitions/`
- [x] **oaDataRunningFiles:** Move `oaDataRunningFiles/*.csv` to `oaDataRunningFiles/`
- [x] **oaDataLogs:** Move `oaDataLogs/*.log` to `oaDataLogs/`
- [x] **oaDataCache:** Move `oaDataCache/` to `oaDataCache/`
- [x] **oaDataSNMP:** Move `oaDataSNMP/` to `oaDataSNMP/`
- [x] **oaDataSplinks:** Move `oaDataSplinks/` to `oaDataSplinks/`

## 4. GUI Engine (The Consumer)
- [x] **oaGuiManager:** Move `managers/Display/` core logic to `oaGuiManager/`
- [x] **oaGuiBuild:** Move `managers/Display/builder/` to `oaGuiBuild/`
- [x] **oaGuiDestroy:** Move `managers/Display/cleaner/` (if exists) to `oaGuiDestroy/`
- [x] **oaGuiElements:** Move `oaGuiDefinitions/elements/` (or equivalent) to `oaGuiElements/`
- [x] **oaStyle:** Move `oaGuiDefinitions/themes/` (or equivalent) to `oaStyle/`

---

## 5. Verification Checklist (Post-Move)
- [x] Fix all absolute/relative imports in migrated files (Audited and major paths corrected).
- [x] Update `config.ini` paths if hardcoded (Verified none present).
- [x] Verify `OpenAir.py` can still boot the system using new paths (Import test successful).
- [/] Confirm MQTT Broker starts and Router maps topics correctly (Infrastructure code fixed).
