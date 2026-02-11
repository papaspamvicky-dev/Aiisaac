-- IsaacAI Configuration
local Config = {}

Config.STATE_FILE = "state.json"
Config.ACTION_FILE = "action.json"
Config.LOG_FILE = "isaac_ai_log.txt"

Config.FRAME_INTERVAL = 1   -- Write state every N frames
Config.ACTION_CHECK_INTERVAL = 1  -- Check for actions every N frames

Config.MAX_ENEMIES = 20
Config.MAX_PROJECTILES = 30
Config.MAX_PICKUPS = 10

Config.DEBUG = true

-- Action validation
Config.VALID_ACTIONS = {[-1]=true, [0]=true, [1]=true}

return Config
