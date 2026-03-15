# Claims

What is claimed is:

1.  A method for dynamically generating a graphical user interface (GUI) for a software application, the method comprising:
    *   providing a file system directory structure for the software application;
    *   parsing the directory structure at runtime to identify a plurality of directories and files;
    *   interpreting the names of the directories to determine a layout for the GUI, wherein the layout includes one or more panes, tabs, or other container elements; and
    *   dynamically loading one or more of the identified files to populate the content of the container elements.

2.  The method of claim 1, wherein the names of the directories include a prefix or a suffix that specifies the type of container element to be created.

3.  The method of claim 2, wherein the directory names specify a percentage of a parent container's dimensions to be occupied by the new container element.

4.  A software system for controlling and monitoring a test and measurement instrument, the system comprising:
    *   a graphical user interface (GUI);
    *   a plurality of manager components for managing a desired state of the instrument;
    *   a plurality of worker components for acquiring data from the instrument; and
    *   a message bus for enabling asynchronous communication between the GUI, the manager components, and the worker components.

5.  The system of claim 4, wherein the GUI is dynamically generated at runtime by parsing a file system directory structure.

6.  The system of claim 4, further comprising a command abstraction protocol for translating abstract, application-level commands into specific commands for the instrument.

7.  The system of claim 6, wherein the command abstraction protocol is implemented by a dedicated manager component that subscribes to abstract command messages on the message bus and publishes translated, instrument-specific commands.

8.  A non-transitory computer-readable medium having stored thereon a program that, when executed by a processor, causes the processor to perform the method of claim 1.

9.  A non-transitory computer-readable medium having stored thereon a program that, when executed by a processor, implements the system of claim 4.