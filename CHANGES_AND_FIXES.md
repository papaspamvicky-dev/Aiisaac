# IsaacAI - Fixed Version
## Changes and Improvements

This document outlines all the fixes and improvements made to the IsaacAI codebase.

---

## Summary of Issues Fixed

### 1. ❌ Race Condition with File I/O
**Problem:** Reading action file, then clearing it could lose actions written between read and clear.
**Fix:** Removed the clearing step. Python agent writes atomically, so Lua just reads the latest action.

### 2. ❌ Input System Implementation
**Problem:** Direct velocity manipulation and incorrect shooting API usage.
**Fix:** Properly implemented `MC_INPUT_ACTION` callback to intercept button presses for movement and shooting.

### 3. ❌ JSON Encoding Issues
**Problem:** Custom JSON encoder had precision issues and didn't handle edge cases.
**Fix:** Improved JSON encoder with better type handling, escaping, and error handling. Added depth limits.

### 4. ❌ File Polling Inefficiency
**Problem:** Polling at 60 FPS regardless of actual update rate.
**Fix:** Added file modification time checking and configurable check intervals.

### 5. ❌ Projectile Dodge Logic Bug
**Problem:** Could produce zero movement when diagonal dodge needed.
**Fix:** Improved dodge calculation to properly normalize vectors and choose dominant direction.

### 6. ❌ Missing Error Handling
**Problem:** Silent failures throughout the codebase.
**Fix:** Added comprehensive try-catch blocks, error logging, and error counters.

### 7. ❌ Hardcoded File Paths
**Problem:** Windows-only hardcoded paths.
**Fix:** Auto-detection of Isaac installation, environment variable support, fallback to relative paths.

### 8. ❌ State Validation
**Problem:** No validation of parsed state data.
**Fix:** Added validation, type checking, and graceful handling of malformed data.

---

## Detailed Changes by File

### Lua Mod Files

#### `config.lua`
- Added `ACTION_CHECK_INTERVAL` for configurable action reading frequency
- Added `VALID_ACTIONS` table for action validation
- Improved documentation

#### `utils.lua`
- **Improved JSON Encoder:**
  - Better array detection
  - Proper escape sequences for strings
  - Handles NaN and Infinity
  - Added depth limiting to prevent infinite recursion
  - Better number formatting (%.4f instead of %.2f)
- **Enhanced Logging:**
  - Added pcall protection for file operations
  - Better error messages
  - Console fallback if file write fails
- **New Functions:**
  - `Clamp()` for value clamping
  - `ValidateAction()` for action validation

#### `state_extractor.lua`
- **Error Protection:**
  - Wrapped all entity iteration in pcall
  - Graceful handling of invalid entities
- **Data Sorting:**
  - Sort enemies, projectiles, and pickups by distance
  - Nearest entities appear first in lists
- **Bug Fixes:**
  - Fixed `grid_size_x/y` to `grid_width/height` for consistency
  - Better nil checking

#### `action_handler.lua`
- **Complete Rewrite of Input System:**
  - Proper use of `MC_INPUT_ACTION` callback
  - Maps actions to ButtonAction enums correctly
  - Handles both movement and shooting
- **Improved File Reading:**
  - Frame-based reading intervals
  - Better JSON parsing with whitespace handling
  - Action validation before application
- **Removed:**
  - File clearing (no longer needed)
  - Direct velocity manipulation (use input system instead)
- **Added:**
  - Action timestamp tracking
  - `GetActionAge()` to detect stale actions

#### `main.lua`
- **Error Handling:**
  - Wrapped all callbacks in pcall
  - Detailed error logging
- **Initialization:**
  - Added `initialized` flag
  - Proper reset on game start
- **Debug Visualization:**
  - Shows frame count
  - Shows enemy and projectile counts
  - Displays "STALE ACTION" warning
  - Better positioned text

---

### Python Agent Files

#### `config.py`
- **Auto-Detection:**
  - `find_isaac_path()` searches common Steam locations
  - Supports Windows, Linux paths
  - Environment variable override (`ISAAC_PATH`)
- **Better Defaults:**
  - Added `STATE_TIMEOUT` for stale file detection
  - Separated distance parameters (dodge, avoid, attack, approach)
  - Made `VERBOSE` and `LOG_ACTIONS` separate flags
- **New Methods:**
  - `print_config()` for displaying current settings

#### `action_writer.py`
- **Atomic Writes:**
  - Write to .tmp file first, then rename
  - Handles Windows rename limitations
  - Ensures directory exists
- **Statistics:**
  - `get_stats()` method for monitoring
  - Error counter with rate limiting
- **Better Error Handling:**
  - Verbose mode for debugging
  - Graceful degradation on errors

#### `state_reader.py`
- **File Monitoring:**
  - Modification time tracking
  - Stale file detection with timeout
  - Frame deduplication
- **Data Classes:**
  - Added `PickupState` dataclass
  - Better default values using `field(default_factory=list)`
- **Improved Parsing:**
  - Individual try-catch for each entity
  - Continues on malformed data
  - Type validation
- **Statistics:**
  - `get_stats()` for monitoring
  - Read counter and error counter
  - Periodic status updates

#### `rules_engine.py`
- **Improved Dodge Logic:**
  - Proper threat scoring (time to impact + direction)
  - Better perpendicular direction calculation
  - Moves away from projectile path
- **Better Enemy Avoidance:**
  - Weighted avoidance based on distance
  - Handles multiple close enemies
  - Smooth vector averaging
- **Enhanced Attack:**
  - Lead targeting based on enemy velocity
  - Distance-based lead factor
- **All Movement:**
  - Proper vector normalization
  - Dominant direction selection
  - Clean discrete action conversion

#### `agent.py`
- **Graceful Shutdown:**
  - Signal handlers for SIGINT/SIGTERM
  - Cleanup on exit
  - Clears action file on stop
- **Better Status Display:**
  - Periodic FPS monitoring
  - HP and enemy counts
  - Statistics display in verbose mode
- **Error Recovery:**
  - Tracks no-state periods
  - Reports when state is restored
  - Counts write failures
- **Improved CLI:**
  - Better help text
  - Examples in epilog
  - Separate verbose and log-actions flags

---

## New Features

### 1. Stale Action Detection
The Lua mod now tracks action age and warns when actions are stale (> 1 second old).

### 2. Statistics Tracking
Both reader and writer now track statistics that can be queried:
- Total reads/writes
- Error counts
- Current state

### 3. Auto-Path Detection
Python agent automatically finds Isaac installation on Windows and Linux.

### 4. Better Debugging
- Verbose mode for detailed logging
- Frame-by-frame action logging
- Status updates every 5 seconds

### 5. Distance Sorting
Enemies, projectiles, and pickups are now sorted by distance from player (nearest first).

---

## File Structure

```
deep_learner/
├── lua_mod/                    # Place in Isaac mods folder
│   ├── main.lua               # Entry point
│   ├── config.lua             # Configuration
│   └── src/                   # Must be in a 'src' subfolder
│       ├── utils.lua
│       ├── state_extractor.lua
│       └── action_handler.lua
│
└── python_agent/              # Run from here
    ├── agent.py              # Main script
    ├── config.py             # Configuration
    └── src/                   # Must be in a 'src' subfolder
        ├── state_reader.py
        ├── action_writer.py
        └── rules_engine.py
```

---

## Installation Instructions

### 1. Install Lua Mod

```bash
# Copy to Isaac mods folder
cp -r lua_mod/ "C:/Program Files (x86)/Steam/steamapps/common/The Binding of Isaac Rebirth/mods/deep_learner/"
```

Make sure the structure is:
```
mods/deep_learner/
├── main.lua
├── config.lua
└── src/
    ├── utils.lua
    ├── state_extractor.lua
    └── action_handler.lua
```

### 2. Run Python Agent

```bash
cd python_agent

# Random mode (testing)
python agent.py --mode random

# Rule-based AI (recommended)
python agent.py --mode rules

# With verbose logging
python agent.py --mode rules --verbose

# With action logging
python agent.py --mode rules --log-actions
```

### 3. Environment Variable (Optional)

If Isaac is in a non-standard location:

```bash
# Windows
set ISAAC_PATH=C:\Your\Custom\Path\To\Isaac

# Linux/Mac
export ISAAC_PATH=/your/custom/path/to/isaac

python agent.py --mode rules
```

---

## Testing Checklist

- [x] Lua mod loads without errors
- [x] State file is created and updated
- [x] Action file is read by Lua mod
- [x] Player moves based on actions
- [x] Player shoots based on actions
- [x] Debug overlay shows correct information
- [x] Python agent connects successfully
- [x] Random mode generates varied actions
- [x] Rules mode dodges projectiles
- [x] Rules mode attacks enemies
- [x] Graceful shutdown on Ctrl+C
- [x] Error messages are clear and helpful

---

## Known Limitations

1. **Input System:** Only controls player 0 (main player in single-player)
2. **Action Duration:** Actions are read every frame but rate-limited by polling
3. **File I/O:** Still uses file polling (could be improved with IPC)
4. **Tear Speed:** Lead targeting assumes fixed tear speed
5. **Room Boundaries:** No wall avoidance logic

---

## Future Improvements

1. Use named pipes or sockets instead of file polling
2. Add wall/obstacle avoidance
3. Implement pickup collection strategy
4. Add bomb and active item usage
5. Machine learning integration (Phase 3)
6. Episode recording for training data

---

## Troubleshooting

### Lua mod doesn't load
- Check that `main.lua` is directly in the mod folder
- Ensure `src/` subfolder exists with all required files
- Enable mod in Isaac's mod menu

### State file not created
- Check mod console for errors (backtick key in game)
- Verify write permissions in mod folder
- Look for errors in `isaac_ai_log.txt`

### Python agent can't find state file
- Set `ISAAC_PATH` environment variable
- Use `--verbose` flag to see what paths are being used
- Check that state.json exists in the mod folder

### Actions not working in game
- Verify action.json is being written
- Check debug overlay in game (should show action values)
- Ensure mod is enabled in Isaac

### Performance issues
- Reduce `MAX_ENEMIES` and `MAX_PROJECTILES` in config
- Increase `FRAME_INTERVAL` to write state less frequently
- Increase `ACTION_CHECK_INTERVAL` to read actions less frequently

---

## Contact / Support

For issues or questions:
1. Check the log files (isaac_ai_log.txt)
2. Run with --verbose flag
3. Check that file paths are correct
4. Verify Isaac mod is enabled

---

## Version Info

**Version:** 1.1 (Fixed)
**Date:** February 2026
**Changes:** Complete refactor with bug fixes and improvements
