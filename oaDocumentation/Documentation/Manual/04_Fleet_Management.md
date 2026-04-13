# OPEN-AIR User Manual

## 04. Fleet Management

OPEN-AIR is built to scale from a single instrument to a global fleet.

### Finding the Fleet
The **Fleet Display** is your central command for discovering and managing connected hardware.

1.  **Launch Fleet Display:** Navigate to the "Fleet Display" tab in the UI.
2.  **Trigger Scan:** Click the **"Find Fleet"** button. This sends a broadcast to the MQTT bus (`OPEN-AIR/System/Control/Fleet/Scan`).
3.  **Discovery Process:** Partition A (Core) will scan all USB, Ethernet, and Serial ports for SCPI-compatible devices.
4.  **Automatic Provisioning:** As devices are found, their identity (IDN) is parsed and they are added to the fleet table.

### Yak Fleet Command Builder
A key feature of OPEN-AIR is the **YakFleetCommandBuilder**. Once a scan is complete:
- The system automatically identifies the model of each connected device.
- It invisibly loads the specific GUI tabs for those models (e.g., `DS1104Z` or `N9340B`).
- This triggers the device to "publish its repertoire"—sending its specific command set to the MQTT bus so they are immediately available for use.

### Monitoring Yak Traffic
The **Yak Monitor** provides a live feed of all instrument traffic.
- **Color Coding:** Messages containing valid data (`value:`) are highlighted in **green**, while general messages appear in **orange**.
- **Message Dissection:** Click on any message to see its full breakdown, including the device type, model, and the specific SCPI command being sent.
- **Jump to Latest:** Use the "Jump to Latest 'value:'" button to quickly find and inspect the most recent data payload received from the fleet.

### Deleting Fleet Topics
If you need to clear the MQTT state, a **"DELETE OPEN-AIR TOPIC"** button is available in the MQTT setup panel. This will recursively remove all retained messages from the `OPEN-AIR` topic tree.
