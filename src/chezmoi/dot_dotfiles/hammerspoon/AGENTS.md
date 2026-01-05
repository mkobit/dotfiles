# Hammerspoon

Hammerspoon is a tool for powerful automation of macOS. At its core, Hammerspoon is just a bridge between the operating system and a Lua scripting engine. It allows you to write Lua scripts to interact with macOS APIs for applications, windows, mouse pointers, filesystems, audio devices, batteries, screens, low-level keyboard/mouse events, and more.

Official documentation can be found at [https://www.hammerspoon.org/docs/](https://www.hammerspoon.org/docs/).

## Configuration directory

By default, Hammerspoon uses `~/.hammerspoon` for configuration. This dotfiles setup configures Hammerspoon to use the chezmoi-managed configuration directory at `.dotfiles/hammerspoon`.

The configuration location is set using the `MJConfigFile` preference, pointing to `{{ .chezmoi.destDir }}/.dotfiles/hammerspoon/init.lua` in templates.

**Important:** Spoons (Hammerspoon extensions) are computed relative to the config file location. Hammerspoon must be restarted after changing the configuration path.

References:
- [GitHub Issue #1734 - XDG config directory support](https://github.com/Hammerspoon/hammerspoon/issues/1734)
- [GitHub Discussion #3730 - Custom config with nix-darwin](https://github.com/Hammerspoon/hammerspoon/discussions/3730)

## API reference

Below is a table of the core Hammerspoon API modules, with links to their official documentation pages.

| Module | Description |
| :--- | :--- |
| [`hs`](https://www.hammerspoon.org/docs/hs.html) | Core Hammerspoon functionality |
| [`hs.alert`](https://www.hammerspoon.org/docs/hs.alert.html) | Simple on-screen alerts |
| [`hs.appfinder`](https://www.hammerspoon.org/docs/hs.appfinder.html) | Easily find hs.application and hs.window objects |
| [`hs.applescript`](https://www.hammerspoon.org/docs/hs.applescript.html) | Execute AppleScript code |
| [`hs.application`](https://www.hammerspoon.org/docs/hs.application.html) | Manipulate running applications |
| [`hs.application.watcher`](https://www.hammerspoon.org/docs/hs.application.watcher.html) | Watch for application launch/terminate events |
| [`hs.audiodevice`](https://www.hammerspoon.org/docs/hs.audiodevice.html) | Manipulate the system's audio devices |
| [`hs.audiodevice.datasource`](https://www.hammerspoon.org/docs/hs.audiodevice.datasource.html) | Inspect/manipulate the data sources of an audio device |
| [`hs.audiodevice.watcher`](https://www.hammerspoon.org/docs/hs.audiodevice.watcher.html) | Watch for system level audio hardware events |
| [`hs.axuielement`](https://www.hammerspoon.org/docs/hs.axuielement.html) | This module allows you to access the accessibility objects of running applications, their windows, menus, and other user interface elements that support the OS X accessibility API. |
| [`hs.axuielement.axtextmarker`](https://www.hammerspoon.org/docs/hs.axuielement.axtextmarker.html) | This submodule allows hs.axuielement to support using AXTextMarker and AXTextMarkerRange objects as parameters for parameterized Accessibility attributes with applications that support them. |
| [`hs.axuielement.observer`](https://www.hammerspoon.org/docs/hs.axuielement.observer.html) | This submodule allows you to create observers for accessibility elements and be notified when they trigger notifications. Not all notifications are supported by all elements and not all elements support notifications, so some trial and error will be necessary, but for compliant applications, this can allow your code to be notified when an application's user interface changes in some way. |
| [`hs.base64`](https://www.hammerspoon.org/docs/hs.base64.html) | Base64 encoding and decoding |
| [`hs.battery`](https://www.hammerspoon.org/docs/hs.battery.html) | Battery/power information |
| [`hs.battery.watcher`](https://www.hammerspoon.org/docs/hs.battery.watcher.html) | Watch for battery/power state changes |
| [`hs.bonjour`](https://www.hammerspoon.org/docs/hs.bonjour.html) | Find and publish network services advertised by multicast DNS (Bonjour) with Hammerspoon. |
| [`hs.bonjour.service`](https://www.hammerspoon.org/docs/hs.bonjour.service.html) | Represents the service records that are discovered or published by the hs.bonjour module. |
| [`hs.brightness`](https://www.hammerspoon.org/docs/hs.brightness.html) | Inspect/manipulate display brightness |
| [`hs.caffeinate`](https://www.hammerspoon.org/docs/hs.caffeinate.html) | Control system power states (sleeping, preventing sleep, screen locking, etc) |
| [`hs.caffeinate.watcher`](https://www.hammerspoon.org/docs/hs.caffeinate.watcher.html) | Watch for display and system sleep/wake/power events |
| [`hs.camera`](https://www.hammerspoon.org/docs/hs.camera.html) | Inspect the system's camera devices |
| [`hs.canvas`](https://www.hammerspoon.org/docs/hs.canvas.html) | A different approach to drawing in Hammerspoon |
| [`hs.canvas.matrix`](https://www.hammerspoon.org/docs/hs.canvas.matrix.html) | A sub module to hs.canvas which provides support for basic matrix manipulations which can be used as the values for transformation attributes in the hs.canvas module. |
| [`hs.chooser`](https://www.hammerspoon.org/docs/hs.chooser.html) | Graphical, interactive tool for choosing/searching data |
| [`hs.console`](https://www.hammerspoon.org/docs/hs.console.html) | Some functions for manipulating the Hammerspoon console. |
| [`hs.crash`](https://www.hammerspoon.org/docs/hs.crash.html) | Various features/facilities for developers who are working on Hammerspoon itself, or writing extensions for it. It is extremely unlikely that you should need any part of this extension, in a normal user configuration. |
| [`hs.deezer`](https://www.hammerspoon.org/docs/hs.deezer.html) | Controls for Deezer music player. |
| [`hs.dialog`](https://www.hammerspoon.org/docs/hs.dialog.html) | A collection of useful dialog boxes, alerts and panels for user interaction. |
| [`hs.dialog.color`](https://www.hammerspoon.org/docs/hs.dialog.color.html) | A panel that allows users to select a color. |
| [`hs.distributednotifications`](https://www.hammerspoon.org/docs/hs.distributednotifications.html) | Interact with NSDistributedNotificationCenter |
| [`hs.doc`](https://www.hammerspoon.org/docs/hs.doc.html) | Create documentation objects for interactive help within Hammerspoon |
| [`hs.doc.builder`](https://www.hammerspoon.org/docs/hs.doc.builder.html) | Builds documentation support files. Still experimental. |
| [`hs.doc.hsdocs`](https://www.hammerspoon.org/docs/hs.doc.hsdocs.html) | Manage the internal documentation web server. |
| [`hs.doc.markdown`](https://www.hammerspoon.org/docs/hs.doc.markdown.html) | Markdown to HTML and plaintext conversion support used by hs.doc |
| [`hs.dockicon`](https://www.hammerspoon.org/docs/hs.dockicon.html) | Control Hammerspoon's dock icon |
| [`hs.drawing`](https://www.hammerspoon.org/docs/hs.drawing.html) | DEPRECATED. Primitives for drawing on the screen in various ways. |
| [`hs.drawing.color`](https://www.hammerspoon.org/docs/hs.drawing.color.html) | Provides access to the system color lists and a wider variety of ways to represent color within Hammerspoon. |
| [`hs.eventtap`](https://www.hammerspoon.org/docs/hs.eventtap.html) | Tap into input events (mouse, keyboard, trackpad) for observation and possibly overriding them. |
| [`hs.eventtap.event`](https://www.hammerspoon.org/docs/hs.eventtap.event.html) | Create, modify and inspect events for hs.eventtap. |
| [`hs.expose`](https://www.hammerspoon.org/docs/hs.expose.html) | Keyboard-driven expose replacement/enhancement |
| [`hs.fnutils`](https://www.hammerspoon.org/docs/hs.fnutils.html) | Functional programming utility functions |
| [`hs.fs`](https://www.hammerspoon.org/docs/hs.fs.html) | Access/inspect the filesystem |
| [`hs.fs.volume`](https://www.hammerspoon.org/docs/hs.fs.volume.html) | Interact with OS X filesystem volumes |
| [`hs.fs.xattr`](https://www.hammerspoon.org/docs/hs.fs.xattr.html) | Get and manipulate extended attributes for files and directories |
| [`hs.geometry`](https://www.hammerspoon.org/docs/hs.geometry.html) | Utility object to represent points, sizes and rects in a bidimensional plane |
| [`hs.grid`](https://www.hammerspoon.org/docs/hs.grid.html) | Move/resize windows within a grid |
| [`hs.hash`](https://www.hammerspoon.org/docs/hs.hash.html) | This module provides various hashing algorithms for use within Hammerspoon. |
| [`hs.hid`](https://www.hammerspoon.org/docs/hs.hid.html) | HID interface for Hammerspoon, controls and queries caps lock state |
| [`hs.hid.led`](https://www.hammerspoon.org/docs/hs.hid.led.html) | HID LED interface for Hammerspoon, controls the state of keyboard LEDs |
| [`hs.hints`](https://www.hammerspoon.org/docs/hs.hints.html) | Switch focus with a transient per-application keyboard shortcut |
| [`hs.host`](https://www.hammerspoon.org/docs/hs.host.html) | Inspect information about the machine Hammerspoon is running on |
| [`hs.host.locale`](https://www.hammerspoon.org/docs/hs.host.locale.html) | Retrieve information about the user's Language and Region settings. |
| [`hs.hotkey`](https://www.hammerspoon.org/docs/hs.hotkey.html) | Create and manage global keyboard shortcuts |
| [`hs.hotkey.modal`](https://www.hammerspoon.org/docs/hs.hotkey.modal.html) | Create/manage modal keyboard shortcut environments |
| [`hs.http`](https://www.hammerspoon.org/docs/hs.http.html) | Perform HTTP requests |
| [`hs.httpserver`](https://www.hammerspoon.org/docs/hs.httpserver.html) | Simple HTTP server |
| [`hs.httpserver.hsminweb`](https://www.hammerspoon.org/docs/hs.httpserver.hsminweb.html) | Minimalist Web Server for Hammerspoon |
| [`hs.httpserver.hsminweb.cgilua`](https://www.hammerspoon.org/docs/hs.httpserver.hsminweb.cgilua.html) | Provides support functions in the cgilua module for Hammerspoon Minimal Web Server Lua templates. |
| [`hs.httpserver.hsminweb.cgilua.lp`](https://www.hammerspoon.org/docs/hs.httpserver.hsminweb.cgilua.lp.html) | Support functions for the CGILua compatibility module for including and translating Lua template pages into Lua code for execution within the Hammerspoon environment to provide dynamic content for http requests. |
| [`hs.httpserver.hsminweb.cgilua.urlcode`](https://www.hammerspoon.org/docs/hs.httpserver.hsminweb.cgilua.urlcode.html) | Support functions for the CGILua compatibility module for encoding and decoding URL components in accordance with RFC 3986. |
| [`hs.image`](https://www.hammerspoon.org/docs/hs.image.html) | A module for capturing and manipulating image objects from other modules for use with hs.drawing. |
| [`hs.inspect`](https://www.hammerspoon.org/docs/hs.inspect.html) | Produce human-readable representations of Lua variables (particularly tables) |
| [`hs.ipc`](https://www.hammerspoon.org/docs/hs.ipc.html) | Provides Hammerspoon with the ability to create both local and remote message ports for inter-process communication. |
| [`hs.itunes`](https://www.hammerspoon.org/docs/hs.itunes.html) | Controls for iTunes music player |
| [`hs.javascript`](https://www.hammerspoon.org/docs/hs.javascript.html) | Execute JavaScript code |
| [`hs.json`](https://www.hammerspoon.org/docs/hs.json.html) | JSON encoding and decoding |
| [`hs.keycodes`](https://www.hammerspoon.org/docs/hs.keycodes.html) | Convert between key-strings and key-codes. Also provides functionality for querying and changing keyboard layouts. |
| [`hs.layout`](https://www.hammerspoon.org/docs/hs.layout.html) | Window layout manager |
| [`hs.location`](https://www.hammerspoon.org/docs/hs.location.html) | Determine the machine's location and useful information about that location |
| [`hs.location.geocoder`](https://www.hammerspoon.org/docs/hs.location.geocoder.html) | Converts between GPS coordinates and more user friendly representations like an address or points of interest. |
| [`hs.logger`](https://www.hammerspoon.org/docs/hs.logger.html) | Simple logger for debugging purposes |
| [`hs.math`](https://www.hammerspoon.org/docs/hs.math.html) | Various helpful mathematical functions |
| [`hs.menubar`](https://www.hammerspoon.org/docs/hs.menubar.html) | Create and manage menubar icons |
| [`hs.messages`](https://www.hammerspoon.org/docs/hs.messages.html) | Send messages via iMessage and SMS Relay (note, SMS Relay requires OS X 10.10 and an established SMS Relay pairing between your Mac and an iPhone running iOS8) |
| [`hs.midi`](https://www.hammerspoon.org/docs/hs.midi.html) | MIDI Extension for Hammerspoon. |
| [`hs.milight`](https://www.hammerspoon.org/docs/hs.milight.html) | Simple controls for the MiLight LED WiFi bridge (also known as LimitlessLED and EasyBulb) |
| [`hs.mjomatic`](https://www.hammerspoon.org/docs/hs.mjomatic.html) | tmuxomatic-like window management |
| [`hs.mouse`](https://www.hammerspoon.org/docs/hs.mouse.html) | Inspect/manipulate the position of the mouse pointer |
| [`hs.network`](https://www.hammerspoon.org/docs/hs.network.html) | This module provides functions for inquiring about and monitoring changes to the network. |
| [`hs.network.configuration`](https://www.hammerspoon.org/docs/hs.network.configuration.html) | This sub-module provides access to the current location set configuration settings in the system's dynamic store. |
| [`hs.network.host`](https://www.hammerspoon.org/docs/hs.network.host.html) | This sub-module provides functions for acquiring host information, such as hostnames, addresses, and reachability. |
| [`hs.network.ping`](https://www.hammerspoon.org/docs/hs.network.ping.html) | This module provides a basic ping function which can test host availability. Ping is a network diagnostic tool commonly found in most operating systems which can be used to test if a route to a specified host exists and if that host is responding to network traffic. |
| [`hs.network.ping.echoRequest`](https://www.hammerspoon.org/docs/hs.network.ping.echoRequest.html) | Provides lower-level access to the ICMP Echo Request infrastructure used by the hs.network.ping module. In general, you should not need to use this module directly unless you have specific requirements not met by the hs.network.ping module and the hs.network.ping object methods. |
| [`hs.network.reachability`](https://www.hammerspoon.org/docs/hs.network.reachability.html) | This sub-module can be used to determine the reachability of a target host. A remote host is considered reachable when a data packet, sent by an application into the network stack, can leave the local device. Reachability does not guarantee that the data packet will actually be received by the host. |
| [`hs.noises`](https://www.hammerspoon.org/docs/hs.noises.html) | Contains two low latency audio recognizers for different mouth noises, which can be used to trigger actions like scrolling or clicking. |
| [`hs.notify`](https://www.hammerspoon.org/docs/hs.notify.html) | This module allows you to create on screen notifications in the User Notification Center located at the right of the users screen. |
| [`hs.osascript`](https://www.hammerspoon.org/docs/hs.osascript.html) | Execute Open Scripting Architecture (OSA) code - AppleScript and JavaScript |
| [`hs.pasteboard`](https://www.hammerspoon.org/docs/hs.pasteboard.html) | Inspect/manipulate pasteboards (more commonly called clipboards). Both the system default pasteboard and custom named pasteboards can be interacted with. |
| [`hs.pasteboard.watcher`](https://www.hammerspoon.org/docs/hs.pasteboard.watcher.html) | Watch for Pasteboard Changes. |
| [`hs.pathwatcher`](https://www.hammerspoon.org/docs/hs.pathwatcher.html) | Watch paths recursively for changes |
| [`hs.plist`](https://www.hammerspoon.org/docs/hs.plist.html) | Read and write Property List files |
| [`hs.razer`](https://www.hammerspoon.org/docs/hs.razer.html) | Razer device support. |
| [`hs.redshift`](https://www.hammerspoon.org/docs/hs.redshift.html) | Inverts and/or lowers the color temperature of the screen(s) on a schedule, for a more pleasant experience at night |
| [`hs.screen`](https://www.hammerspoon.org/docs/hs.screen.html) | Manipulate screens (i.e. monitors) |
| [`hs.screen.watcher`](https://www.hammerspoon.org/docs/hs.screen.watcher.html) | Watch for screen layout changes |
| [`hs.serial`](https://www.hammerspoon.org/docs/hs.serial.html) | Communicate with external devices through a serial port (most commonly RS-232). |
| [`hs.settings`](https://www.hammerspoon.org/docs/hs.settings.html) | Serialize simple Lua variables across Hammerspoon launches |
| [`hs.sharing`](https://www.hammerspoon.org/docs/hs.sharing.html) | Share items with the macOS Sharing Services under the control of Hammerspoon. |
| [`hs.shortcuts`](https://www.hammerspoon.org/docs/hs.shortcuts.html) | List and run shortcuts from the Shortcuts app |
| [`hs.socket`](https://www.hammerspoon.org/docs/hs.socket.html) | Talk to custom protocols using asynchronous TCP sockets. |
| [`hs.socket.udp`](https://www.hammerspoon.org/docs/hs.socket.udp.html) | Talk to custom protocols using asynchronous UDP sockets. |
| [`hs.sound`](https://www.hammerspoon.org/docs/hs.sound.html) | Load/play/manipulate sound files |
| [`hs.spaces`](https://www.hammerspoon.org/docs/hs.spaces.html) | This module provides some basic functions for controlling macOS Spaces. |
| [`hs.spaces.watcher`](https://www.hammerspoon.org/docs/hs.spaces.watcher.html) | Watches for the current Space being changed |
| [`hs.speech`](https://www.hammerspoon.org/docs/hs.speech.html) | This module provides access to the Speech Synthesizer component of OS X. |
| [`hs.speech.listener`](https://www.hammerspoon.org/docs/hs.speech.listener.html) | This module provides access to the Speech Recognizer component of OS X. |
| [`hs.spoons`](https://www.hammerspoon.org/docs/hs.spoons.html) | Utility and management functions for Spoons |
| [`hs.spotify`](https://www.hammerspoon.org/docs/hs.spotify.html) | Controls for Spotify music player |
| [`hs.spotlight`](https://www.hammerspoon.org/docs/hs.spotlight.html) | This module allows Hammerspoon to preform Spotlight metadata queries. |
| [`hs.spotlight.group`](https://www.hammerspoon.org/docs/hs.spotlight.group.html) | This sub-module is used to access results to a spotlightObject query which have been grouped by one or more attribute values. |
| [`hs.spotlight.item`](https://www.hammerspoon.org/docs/hs.spotlight.item.html) | This sub-module is used to access the individual results of a spotlightObject or a spotlightGroupObject. |
| [`hs.sqlite3`](https://www.hammerspoon.org/docs/hs.sqlite3.html) | Interact with SQLite databases |
| [`hs.streamdeck`](https://www.hammerspoon.org/docs/hs.streamdeck.html) | Configure/control an Elgato Stream Deck. |
| [`hs.styledtext`](https://www.hammerspoon.org/docs/hs.styledtext.html) | This module adds support for controlling the style of the text in Hammerspoon. |
| [`hs.tabs`](https://www.hammerspoon.org/docs/hs.tabs.html) | Place the windows of an application into tabs drawn on its titlebar |
| [`hs.tangent`](https://www.hammerspoon.org/docs/hs.tangent.html) | Tangent Control Surface Extension |
| [`hs.task`](https://www.hammerspoon.org/docs/hs.task.html) | Execute processes in the background and capture their output |
| [`hs.timer`](https://www.hammerspoon.org/docs/hs.timer.html) | Execute functions with various timing rules |
| [`hs.timer.delayed`](https://www.hammerspoon.org/docs/hs.timer.delayed.html) | Specialized timer objects to coalesce processing of unpredictable asynchronous events into a single callback |
| [`hs.uielement`](https://www.hammerspoon.org/docs/hs.uielement.html) | A generalized framework for working with OSX UI elements |
| [`hs.uielement.watcher`](https://www.hammerspoon.org/docs/hs.uielement.watcher.html) | Watch for events on certain UI elements (including windows and applications) |
| [`hs.urlevent`](https://www.hammerspoon.org/docs/hs.urlevent.html) | Allows Hammerspoon to respond to URLs |
| [`hs.usb`](https://www.hammerspoon.org/docs/hs.usb.html) | Inspect USB devices |
| [`hs.usb.watcher`](https://www.hammerspoon.org/docs/hs.usb.watcher.html) | Watch for USB device connection/disconnection events |
| [`hs.utf8`](https://www.hammerspoon.org/docs/hs.utf8.html) | Functions providing basic support for UTF-8 encodings |
| [`hs.vox`](https://www.hammerspoon.org/docs/hs.vox.html) | Controls for VOX music player |
| [`hs.watchable`](https://www.hammerspoon.org/docs/hs.watchable.html) | A minimalistic Key-Value-Observer framework for Lua. |
| [`hs.websocket`](https://www.hammerspoon.org/docs/hs.websocket.html) | Simple websocket client. |
| [`hs.webview`](https://www.hammerspoon.org/docs/hs.webview.html) | Display web content in a window from Hammerspoon |
| [`hs.webview.datastore`](https://www.hammerspoon.org/docs/hs.webview.datastore.html) | Provides methods to list and purge the various types of data used by websites visited with hs.webview. |
| [`hs.webview.toolbar`](https://www.hammerspoon.org/docs/hs.webview.toolbar.html) | Create and manipulate toolbars which can be attached to the Hammerspoon console or hs.webview objects. |
| [`hs.webview.usercontent`](https://www.hammerspoon.org/docs/hs.webview.usercontent.html) | This module provides support for injecting custom JavaScript user content into your webviews and for JavaScript to post messages back to Hammerspoon. |
| [`hs.wifi`](https://www.hammerspoon.org/docs/hs.wifi.html) | Inspect WiFi networks |
| [`hs.wifi.watcher`](https://www.hammerspoon.org/docs/hs.wifi.watcher.html) | Watch for changes to the associated wifi network |
| [`hs.window`](https://www.hammerspoon.org/docs/hs.window.html) | Inspect/manipulate windows |
| [`hs.window.filter`](https://www.hammerspoon.org/docs/hs.window.filter.html) | Filter windows by application, title, location on screen and more, and easily subscribe to events on these windows |
| [`hs.window.highlight`](https://www.hammerspoon.org/docs/hs.window.highlight.html) | Highlight the focused window |
| [`hs.window.layout`](https://www.hammerspoon.org/docs/hs.window.layout.html) | WARNING: EXPERIMENTAL MODULE. DO NOT USE IN PRODUCTION. |
| [`hs.window.switcher`](https://www.hammerspoon.org/docs/hs.window.switcher.html) | Window-based cmd-tab replacement |
| [`hs.window.tiling`](https://www.hammerspoon.org/docs/hs.window.tiling.html) | WARNING: EXPERIMENTAL MODULE. DO NOT USE IN PRODUCTION. |
