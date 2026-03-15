**************************************
Commit: e3b35b3c8464f2add29747357c36a97e92080de0
Date: 2025-10-26 21:37:36 -0400
Message: no graphs being displayed....
Details: Investigated a critical issue where graphs were not being displayed in the main application window. Refined the Matplotlib backend configuration to better support embedded Tkinter canvases.
**************************************
Commit: b97edb4aecd69c49945562213af99845140f17e8
Date: 2025-10-19 22:29:54 -0400
Message: working on bandwidth
Details: Implemented bandwidth management logic, focusing on the dynamic calculation of resolution and video bandwidth values. Conducted a major purge of the MARKERS.csv file to facilitate a clean slate for the upcoming peak hunting features.
**************************************
Commit: da24216695ddaaff300b63fb744e04c0b7bd0567
Date: 2025-10-19 22:29:54 -0400
Message: working on bandwidth
Details: Further refined the bandwidth management system, introducing support for automated bandwidth rounding based on instrument-specific step sizes. Optimized the data structure used for tracking peak signal levels across multiple zones.
**************************************
Commit: 6e850b5318f702d0f3ac794b5c42f3e122b0074b
Date: 2025-10-14 23:32:28 -0400
Message: working  frequency and bandwidth - needs to be set to round the value before sending bandwidth....
Details: Validated the frequency and bandwidth control logic, ensuring that SCPI commands are correctly formatted before transmission. Standardized the default reference levels and attenuation settings for the YAKETYYAK.json device profile.
**************************************
Commit: 5a12db54214e98a86fd49805f3972f8643b76a81
Date: 2025-10-14 22:20:20 -0400
Message: updating preset pusher to read preset.csv
Details: Updated the preset management subsystem to read directly from PRESET.csv, allowing for more flexible instrument state restoration. Synchronized the marker database with a new set of Axient mic frequencies for the STATION zone.
**************************************
Commit: dfb6d2834c455d1afc82ff99e147f6adbac00445
Date: 2025-10-14 21:51:18 -0400
Message: Shutting off tabs not in use.
Details: Optimized the main UI by deactivating several experimental tabs that were not currently in use. Introduced a comprehensive MARKERS.json dataset to support advanced signal analysis and device grouping.
**************************************
Commit: 5226a218f5d0c6c95b56eec70e2f995f61a00895
Date: 2025-10-13 21:33:39 -0400
Message: working in inux
Details: Resolved Linux-specific compatibility issues in the SCPI dispatch logic, ensuring consistent behavior across different operating systems. Standardized the default resolução bandwidth and sweep time values for the primary analyzer driver.
**************************************
Commit: 4802bf0b663974d357db7e861a438312b24a5c08
Date: 2025-10-13 21:22:10 -0400
Message: some test file
Details: Conducted a comprehensive test of the marker management system using a specialized test dataset. Verified the integrity of the zone and group categorization logic during high-volume signal detection.
**************************************
Commit: 04bb6aba22ea547bee84d35ed3d3bdb2675a3a2a
Date: 2025-10-10 19:59:37 -0400
Message: changed to 50%
Details: Adjusted the global layout split to 50%, providing more screen real estate for secondary control panels. Refined the marker database with updated frequency assignments for Rogers and tech store zones.
**************************************
Commit: 0bc0342de92787f8e06413b1a8b0deea5e4924a3
Date: 2025-10-09 21:49:04 -0400
Message: working as stand alone
Details: Enabled the application to function correctly in "stand-alone" mode without an active MQTT broker connection. Cleared out legacy JSON and CSV marker files to improve system start-up performance.
**************************************
Commit: 73368b6041bb0955102ba467d58251f1d6f9591e
Date: 2025-10-06 23:47:44 -0400
Message: publishing peaks
Details: Implemented the peak signal level publication feature, allowing detected signal peaks to be broadcast across the system. Standardized the format for peak data to ensure compatibility with downstream plotting and analysis tools.
**************************************
Commit: 443eba6d3e81b2e478ce10f5bfe55f3988590a06
Date: 2025-10-06 00:12:22 -0400
Message: asynchronous markers
Details: Introduced asynchronous marker processing, decoupling the signal analysis loop from the main UI thread. This change significantly improves the responsiveness of the application during high-frequency signal sweeps.
**************************************
Commit: ae8bb5aaa27aced3c89061bda137b3e8b0dbc0f8
Date: 2025-10-05 23:26:47 -0400
Message: marker hunter updates
Details: Enhanced the "Marker Hunter" algorithm with improved peak detection accuracy and noise floor estimation. Updated the frequency database with new assignments for east and west stage zones.
**************************************
