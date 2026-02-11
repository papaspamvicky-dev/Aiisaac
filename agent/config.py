"""Agent configuration and constants."""
import os
from enum import Enum
from pathlib import Path

# Try to auto-detect Steam installation
def find_isaac_path():
    """Attempt to find Isaac installation directory."""
    possible_paths = [
        # Windows paths
        Path("C:/Program Files (x86)/Steam/steamapps/common/The Binding of Isaac Rebirth"),
        Path("C:/Program Files/Steam/steamapps/common/The Binding of Isaac Rebirth"),
        # Add other common Steam library locations
        Path(os.path.expanduser("~/Steam/steamapps/common/The Binding of Isaac Rebirth")),
        # Linux paths
        Path(os.path.expanduser("~/.steam/steam/steamapps/common/The Binding of Isaac Rebirth")),
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    return None

# Get base path
ISAAC_BASE_PATH = os.getenv("ISAAC_PATH")
if ISAAC_BASE_PATH:
    ISAAC_BASE_PATH = Path(ISAAC_BASE_PATH)
else:
    ISAAC_BASE_PATH = find_isaac_path()

if ISAAC_BASE_PATH:
    MOD_PATH = ISAAC_BASE_PATH / "mods" / "deep_learner"
    STATE_FILE = str(MOD_PATH / "state.json")
    ACTION_FILE = str(MOD_PATH / "action.json")
else:
    # Fallback to relative paths
    print("Warning: Could not find Isaac installation. Using relative paths.")
    STATE_FILE = "state.json"
    ACTION_FILE = "action.json"

DATA_DIR = "data/episodes"

# State processing limits
MAX_ENEMIES = 20
MAX_PROJECTILES = 30

# Action space
VALID_ACTIONS = [-1, 0, 1]

class AgentMode(Enum):
    """Agent operation modes."""
    RANDOM = "random"      # Phase 1: Random valid actions
    RULE_BASED = "rules"   # Phase 2: Rule-based decisions
    TRAINING = "train"     # Phase 3: RL training
    INFERENCE = "inference"  # Phase 4: Trained model

class Config:
    """Main configuration class."""

    # Mode
    MODE: AgentMode = AgentMode.RANDOM

    # File I/O
    STATE_FILE_PATH: str = STATE_FILE
    ACTION_FILE_PATH: str = ACTION_FILE

    # Timing (seconds)
    POLL_INTERVAL: float = 0.016  # ~60 FPS
    STATE_TIMEOUT: float = 5.0  # Consider state stale after this many seconds
    
    # State processing
    MAX_ENEMIES: int = MAX_ENEMIES
    MAX_PROJECTILES: int = MAX_PROJECTILES

    # Debug
    VERBOSE: bool = False
    LOG_ACTIONS: bool = False

    # Rule-based parameters (Phase 2)
    DODGE_DISTANCE: float = 100.0  # Distance to start dodging projectiles
    AVOID_DISTANCE: float = 50.0   # Distance to avoid enemies
    ATTACK_RANGE: float = 300.0    # Ideal range to attack from
    APPROACH_RANGE: float = 400.0  # Range at which to approach enemies

    @classmethod
    def ensure_dirs(cls):
        """Ensure data directories exist."""
        os.makedirs(DATA_DIR, exist_ok=True)
    
    @classmethod
    def print_config(cls):
        """Print current configuration."""
        print(f"[Config] State file: {cls.STATE_FILE_PATH}")
        print(f"[Config] Action file: {cls.ACTION_FILE_PATH}")
        print(f"[Config] Mode: {cls.MODE.value}")
        print(f"[Config] Poll interval: {cls.POLL_INTERVAL}s")
        print(f"[Config] Verbose: {cls.VERBOSE}")
