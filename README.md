# IsaacAI - Fixed and Improved Version

An autonomous AI agent that plays The Binding of Isaac: Rebirth/Repentance using file-based communication between a Lua mod and Python agent.

## What's New in This Version

✅ Fixed race conditions in file I/O  
✅ Proper input system implementation  
✅ Improved JSON encoding/decoding  
✅ Better error handling throughout  
✅ Auto-detection of Isaac installation path  
✅ Enhanced projectile dodging logic  
✅ Statistics tracking and monitoring  
✅ Comprehensive logging and debugging  

See `CHANGES_AND_FIXES.md` for detailed list of all improvements.

---

## Quick Start

### 1. Install the Lua Mod

Copy the `lua_mod` folder contents to your Isaac mods directory:

**Windows:**
```
C:/Program Files (x86)/Steam/steamapps/common/The Binding of Isaac Rebirth/mods/deep_learner/
```

**Linux:**
```
~/.steam/steam/steamapps/common/The Binding of Isaac Rebirth/mods/deep_learner/
```

Structure should be:
```
mods/deep_learner/
├── main.lua
├── config.lua
└── src/
    ├── utils.lua
    ├── state_extractor.lua
    └── action_handler.lua
```

### 2. Enable the Mod

1. Launch The Binding of Isaac
2. Go to Mods menu
3. Enable "IsaacAI"
4. Restart the game

### 3. Run the Python Agent

```bash
cd python_agent

# Random movement (for testing)
python agent.py --mode random

# Rule-based AI (recommended)
python agent.py --mode rules

# With verbose output
python agent.py --mode rules --verbose
```

### 4. Start Playing!

Start a new run in Isaac. The agent will automatically take control once you enter the first room.

---

## Architecture

### Lua Mod (runs inside game)
- **main.lua** - Entry point, coordinates all modules
- **config.lua** - Configuration settings
- **state_extractor.lua** - Extracts game state (player, enemies, projectiles)
- **action_handler.lua** - Reads actions and controls input
- **utils.lua** - Helper functions (JSON, logging, math)

### Python Agent (runs outside game)
- **agent.py** - Main loop, coordinates modules
- **config.py** - Configuration with auto-path detection
- **state_reader.py** - Reads and parses state.json
- **action_writer.py** - Writes actions to action.json
- **rules_engine.py** - Rule-based decision making

### Communication
```
Game → state.json → Python Agent → action.json → Game
```

---

## Agent Modes

### Random Mode
```bash
python agent.py --mode random
```
Generates random valid actions. Useful for testing the pipeline.

### Rule-Based Mode (Recommended)
```bash
python agent.py --mode rules
```
Smart AI with prioritized behaviors:
1. **Dodge projectiles** - Avoid incoming shots
2. **Avoid enemies** - Keep distance from contact damage
3. **Attack nearest** - Shoot at closest enemy
4. **Approach enemies** - Move into attack range

### Training Mode (Coming Soon)
```bash
python agent.py --mode train
```
Will record episodes for reinforcement learning.

### Inference Mode (Coming Soon)
```bash
python agent.py --mode inference
```
Will use trained neural network for decisions.

---

## Configuration

### Environment Variables

```bash
# Set custom Isaac path
export ISAAC_PATH="/path/to/isaac"
python agent.py --mode rules
```

### Lua Config (`config.lua`)

```lua
Config.FRAME_INTERVAL = 1        -- Write state every N frames
Config.ACTION_CHECK_INTERVAL = 1 -- Read actions every N frames
Config.MAX_ENEMIES = 20          -- Max enemies in state
Config.MAX_PROJECTILES = 30      -- Max projectiles in state
Config.DEBUG = true              -- Show debug overlay
```

### Python Config (`config.py`)

```python
Config.POLL_INTERVAL = 0.016      # 60 FPS polling
Config.DODGE_DISTANCE = 100.0     # Start dodging at this distance
Config.AVOID_DISTANCE = 50.0      # Avoid enemy contact distance
Config.ATTACK_RANGE = 300.0       # Shoot enemies in this range
Config.VERBOSE = False            # Detailed logging
```

---

## Command Line Options

```bash
python agent.py --mode {random|rules|train|inference}
                [--verbose]       # Enable detailed logging
                [--log-actions]   # Log every action taken
```

Examples:
```bash
# Basic usage
python agent.py --mode rules

# Debug mode
python agent.py --mode rules --verbose --log-actions

# Test connection
python agent.py --mode random
```

---

## Debug Information

### In-Game Overlay (when DEBUG = true)

```
AI: Move[1,0] Shoot[-1,0] Frame:1234
E:5 P:3
```

- **Move[x,y]** - Current movement action
- **Shoot[x,y]** - Current shooting action  
- **E** - Enemy count
- **P** - Projectile count
- **Green M** - Movement direction indicator
- **Red S** - Shooting direction indicator

### Console Output

```
[Agent] Frame   1234 | HP:  6/ 6 | Enemies:  5 | Projectiles:  3 | Loop FPS: 59.8
```

---

## File Locations

### Generated Files

```
mods/deep_learner/
├── state.json           # Game state (written by Lua)
├── action.json          # Actions (written by Python)
└── isaac_ai_log.txt     # Debug log (written by Lua)
```

### State JSON Structure

```json
{
  "frame": 1234,
  "timestamp": 123456789,
  "player": {
    "x": 320.0, "y": 280.0,
    "vx": 0.0, "vy": 0.0,
    "hp": 6, "max_hp": 6,
    "bombs": 1, "keys": 0, "coins": 5
  },
  "enemies": [
    {"x": 400.0, "y": 300.0, "hp": 10.0, "distance": 85.4},
    ...
  ],
  "projectiles": [
    {"x": 350.0, "y": 290.0, "vx": 2.5, "vy": 0.0, "is_hostile": true},
    ...
  ],
  "room": {
    "type": 1,
    "is_clear": false,
    "stage": 1
  }
}
```

### Action JSON Structure

```json
{
  "move_x": 1,   # -1 (left), 0 (none), 1 (right)
  "move_y": 0,   # -1 (up), 0 (none), 1 (down)
  "shoot_x": -1, # -1 (left), 0 (none), 1 (right)
  "shoot_y": 0   # -1 (up), 0 (none), 1 (down)
}
```

---

## Troubleshooting

### Mod doesn't load
1. Check file structure (main.lua must be in mod root)
2. Verify src/ folder exists with all files
3. Enable mod in Isaac's Mods menu
4. Check for errors in game console (` key)

### Python can't find Isaac
```bash
# Set path manually
export ISAAC_PATH="/your/path/to/isaac"

# Or use --verbose to see what's being checked
python agent.py --mode rules --verbose
```

### Agent not controlling player
1. Check that mod is enabled and loaded
2. Verify state.json is being created (check mod folder)
3. Verify action.json is being written (check mod folder)
4. Look for errors in isaac_ai_log.txt
5. Enable debug overlay in config.lua

### Poor performance
1. Reduce MAX_ENEMIES and MAX_PROJECTILES in config.lua
2. Increase FRAME_INTERVAL to write state less often
3. Increase ACTION_CHECK_INTERVAL to read actions less often

### Actions seem delayed
- Normal! File I/O has ~16ms latency at 60 FPS
- Consider using faster polling (decrease POLL_INTERVAL)
- Future versions may use IPC for lower latency

---

## Development Roadmap

### Phase 1: Data Pipeline ✅
- [x] Lua mod extracts game state
- [x] JSON serialization
- [x] Python agent reads state
- [x] Python agent writes actions
- [x] Lua mod applies actions

### Phase 2: Rule-Based AI ✅
- [x] Projectile dodging
- [x] Enemy avoidance
- [x] Combat behavior
- [x] Movement strategy

### Phase 3: Machine Learning (Planned)
- [ ] Episode recording
- [ ] Reward function design
- [ ] Neural network architecture
- [ ] Training pipeline
- [ ] Model evaluation

### Phase 4: Advanced Features (Planned)
- [ ] Pickup collection
- [ ] Bomb usage
- [ ] Active item timing
- [ ] Room optimization
- [ ] Boss strategies

---

## Performance Tips

1. **Reduce entity limits** if game lags:
   ```lua
   Config.MAX_ENEMIES = 10
   Config.MAX_PROJECTILES = 15
   ```

2. **Reduce update frequency** for slower systems:
   ```lua
   Config.FRAME_INTERVAL = 2        -- Update every 2 frames
   Config.ACTION_CHECK_INTERVAL = 2  -- Check every 2 frames
   ```

3. **Disable debug overlay** for better FPS:
   ```lua
   Config.DEBUG = false
   ```

---

## Contributing

This is a learning project for AI/RL experimentation. Feel free to:
- Report bugs
- Suggest improvements
- Add new features
- Optimize performance

---

## Credits

**Original Concept:** papaspamvicky-dev  
**Fixed Version:** Claude (Anthropic)  
**Game:** The Binding of Isaac: Rebirth/Repentance by Edmund McMillen

---

## License

This is a mod for educational purposes. The Binding of Isaac and all related assets are property of Edmund McMillen and Nicalis, Inc.

---

## FAQ

**Q: Does this work with Repentance/Afterbirth+?**  
A: Should work with all versions, but tested on Rebirth.

**Q: Will I get banned for using this?**  
A: No, this is a single-player mod with no online components.

**Q: Can I use this for speedrunning?**  
A: This is for AI research/fun, not competitive play.

**Q: How accurate is the rule-based AI?**  
A: It can handle basic rooms but struggles with bosses and complex patterns.

**Q: When will ML training be available?**  
A: Phase 3 is in development. Episode recording needed first.

**Q: Can I modify the rules?**  
A: Yes! Edit `rules_engine.py` to change behavior.

**Q: Does it use computer vision?**  
A: No, it reads game state directly from memory via Lua API.

---

## Support

For issues:
1. Check `isaac_ai_log.txt` for errors
2. Run with `--verbose` flag
3. Verify file paths are correct
4. Make sure mod is enabled in game

Happy AI training! 🤖
