# MoErgo Glove80 Voice Dictation Guide (macOS & Windows/WSL)

This guide outlines how to configure a seamless, cross-platform voice dictation hotkey for your MoErgo Glove80 using the Glorious Engrammer layout.

The goal is to achieve **zero host-side configuration**—meaning no third-party daemons (like Karabiner-Elements, AutoHotkey, or skhd) need to be installed. We leverage the OS-native dictation tools and configure the Glove80 via ZMK to send the correct signals depending on your active OS layer.

## The Strategy: Layer-Specific Keycodes

Your Glove80 natively supports switching between a **Mac Layer** and a **Windows Layer**. We will pick a physical key combination (e.g., a thumb cluster modifier + a home row key, or a dedicated macro key) and assign it different outputs based on the active layer.

### 1. macOS (The "Mac Layer")

macOS has built-in dictation. Apple keyboards have a dedicated "Microphone/Dictation" media key. In ZMK, we can emulate this exact media control code.

**Primary Approach:**
In your MoErgo Configurator (or ZMK `.keymap` file), bind your chosen dictation key on the Mac layer to:
`&kp C_VOICE_COMMAND` (Consumer code `0x00CF`).
* *Note:* In some newer ZMK forks, this might be aliased as `&kp C_DICTATION`.

**Why this is best:** macOS natively interprets this as the "Start Dictation" key. You do not need to configure any custom shortcuts in macOS Settings.

**Fallback Approach (If C_VOICE_COMMAND fails):**
If `C_VOICE_COMMAND` does not trigger dictation on your specific macOS version:
1. In the Glove80 Configurator, map the key to a complex, non-conflicting shortcut, such as `Hyper + D`:
   `&kp LS(LC(LA(LG(D))))`
2. On your Mac, go to **System Settings > Keyboard > Dictation**.
3. Under "Shortcut", select **Customize...** and press that exact combo (`Cmd+Ctrl+Opt+Shift+D`).

### 2. Windows / WSL (The "Windows Layer")

Windows includes a built-in "Voice Typing" overlay that works flawlessly for dictating text into standard Windows apps as well as WSL terminals. The hardcoded native shortcut is `Windows Key + H`.

**Primary Approach:**
In your MoErgo Configurator, bind the exact same physical key on the Windows layer to:
`&kp LG(H)` (Left GUI / Windows Key + H).

**Why this is best:** Windows Voice Typing requires zero setup. Hitting `Win+H` will immediately bring up the dictation UI.

**Fallback Approach (If `Win+H` conflicts):**
If you have remapped `Win+H` or it conflicts with another tool:
1. Map the Glove80 Windows layer key to `Hyper + D`: `&kp LS(LC(LA(LG(D))))`.
2. Install **PowerToys** (from the Microsoft Store).
3. Open PowerToys -> **Keyboard Manager** -> **Remap a shortcut**.
4. Map `Ctrl + Alt + Shift + Win + D` to output `Win + H`.

---

## Implementation Summary for MoErgo Configurator

1. Open the [MoErgo Layout Editor](https://my.moergo.com/).
2. Identify the physical key you want to use for dictation (e.g., a specific thumb key or a combo).
3. Switch to your **Mac Layer**, and set the behavior to `&kp C_VOICE_COMMAND`.
4. Switch to your **Windows Layer**, and set the behavior to `&kp LG(H)`.
5. Flash the updated firmware to your Glove80 halves.
