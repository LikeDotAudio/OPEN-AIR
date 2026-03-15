# Description of the Invention

## Background of the Invention

The present invention relates to software applications for controlling and monitoring test and measurement instruments, and more particularly to a software application that provides a dynamic and extensible user interface for controlling and visualizing data from RF spectrum analyzers and similar instruments.

Controlling and monitoring test and measurement instruments, such as RF spectrum analyzers, traditionally involves using software with static, hard-coded user interfaces. These interfaces are often rigid and difficult to customize, requiring significant software development effort to modify the layout or add new features. Furthermore, the software is often tightly coupled to the specific hardware it is designed to control, making it difficult to adapt to different instrument models or to extend its functionality.

This tight coupling and lack of flexibility can be a significant drawback in a laboratory or field environment where engineers and technicians may need to work with a variety of instruments or to customize the user interface to suit their specific needs. For example, a user may want to rearrange the display to show a large view of the spectrum, while another user may want to see a more compact view with additional information about the signal.

Therefore, there is a need for a more flexible and extensible software solution for controlling and monitoring test and measurement instruments that can overcome the limitations of existing software.

## Summary of the Invention

The present invention provides a software application for controlling and monitoring test and measurement instruments that overcomes the limitations of existing solutions by providing a dynamic and extensible user interface, a decoupled, message-driven architecture, and a command abstraction protocol.

The application's most novel feature is its ability to dynamically generate a graphical user interface (GUI) at runtime by interpreting the directory and file structure of the application's installation folder. The layout of the GUI, including the arrangement of panes, tabs, and content, is determined by the folder hierarchy. This allows for profound UI reorganization without changing the core application code. For example, a user can create a new folder to add a new tab to the interface, or move a file to a different folder to change its location in the GUI.

The application employs a decoupled, message-driven architecture where distinct software components communicate asynchronously via an MQTT message bus. These components include:

*   **Managers:** Passive components that manage the desired state of the instrument (e.g., target frequency, bandwidth). They react to user input from the GUI.
*   **Workers:** Active background processes that continuously acquire data from the instrument (e.g., polling for the current peak signal) and publish it for other components to consume.
*   **Display:** The dynamically generated GUI, which both sends commands and subscribes to data streams over MQTT.

This decoupled architecture makes the application highly modular and extensible. New features can be added by creating new managers or workers without affecting the rest of the application.

A command abstraction protocol, 'YAK', is used to translate abstract, application-level commands into the specific SCPI (Standard Commands for Programmable Instruments) commands required by the connected hardware. This creates a powerful abstraction layer that makes the software adaptable to different instrument models. A central manager, the `YaketyYakManager`, is responsible for this translation.

The combination of a filesystem-driven GUI, a decoupled, message-driven architecture, and a command abstraction protocol provides a highly modular, extensible, and user-friendly solution for instrument control and data visualization.

## Detailed Description of the Invention

The software application is implemented in Python and is designed to run on a desktop computer. The main components of the application are the `main.py` entry point, the `display` module for the GUI, the `managers` module for state management, and the `workers` module for data acquisition.

### Filesystem-Driven Dynamic GUI Construction

The GUI is dynamically constructed at runtime by the `gui_display.py` module. This module recursively scans the `display` directory and builds the GUI based on the directory and file structure it finds.

The naming of the directories and files in the `display` directory follows a specific convention:

*   **`left_50/` or `right_50/`:** These directories create a vertical split in the main window, with the specified percentage of the width.
*   **`top_10/` or `bottom_90/`:** These directories create a horizontal split in the main window, with the specified percentage of the height.
*   **`tab_.../`:** Directories starting with `tab_` create a new tab in the GUI.
*   **Python files:** Python files within these directories are dynamically loaded to populate the UI.

This filesystem-driven approach to GUI generation is a key innovation of the present invention. It allows for a high degree of customization and extensibility without requiring any changes to the core application code.

### Decoupled, Message-Driven Architecture

The application's components communicate with each other using an MQTT message bus. This provides a clean separation between the different parts of the application and allows for a high degree of flexibility.

The `main.py` file is responsible for launching the GUI, the managers, and the workers as distinct components and providing the MQTT utility that links them.

The `managers` are responsible for managing the state of the instrument. They subscribe to messages from the GUI and publish messages to the workers. The `managers/manager_launcher.py` file enumerates and instantiates all the high-level state and control managers, such as the `FrequencyManager`, `BandwidthManager`, and `VisaConnectionManager`.

The `workers` are responsible for acquiring data from the instrument. They subscribe to messages from the managers and publish data to the GUI. The `workers/Worker_Launcher.py` file enumerates and instantiates the background data acquisition workers, such as the `ActivePeakPublisher`.

### YAK Command Abstraction Protocol

The 'YAK' protocol is a custom, internal protocol that runs over MQTT. It is used to abstract hardware-level commands into application-level concepts. For example, instead of sending a raw SCPI command to set the frequency of the instrument, the application sends a YAK message with the desired frequency.

The `managers/yak_manager/manager_yakety_yak.py` module is the core of the YAK command abstraction layer. It receives YAK messages and translates them into the specific SCPI commands for the connected hardware. This decouples the application's logic from the instrument's specific command set, which is a key architectural feature.