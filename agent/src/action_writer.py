"""Action writer module - handles writing actions to action.json."""
import json
import os
import time
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class Action:
    """Action data structure matching Lua expectations."""
    move_x: int = 0  # -1, 0, 1
    move_y: int = 0  # -1, 0, 1
    shoot_x: int = 0  # -1, 0, 1
    shoot_y: int = 0  # -1, 0, 1

    def __post_init__(self):
        """Clamp values to valid range."""
        self.move_x = max(-1, min(1, int(self.move_x)))
        self.move_y = max(-1, min(1, int(self.move_y)))
        self.shoot_x = max(-1, min(1, int(self.shoot_x)))
        self.shoot_y = max(-1, min(1, int(self.shoot_y)))

    def to_dict(self) -> Dict:
        return {
            'move_x': self.move_x,
            'move_y': self.move_y,
            'shoot_x': self.shoot_x,
            'shoot_y': self.shoot_y
        }

    def is_zero(self) -> bool:
        """Check if action is do-nothing."""
        return (self.move_x == 0 and self.move_y == 0 and 
                self.shoot_x == 0 and self.shoot_y == 0)

    def __str__(self) -> str:
        return f"Action(M:[{self.move_x},{self.move_y}], S:[{self.shoot_x},{self.shoot_y}])"

class ActionWriter:
    """Handles writing actions to JSON file for Lua mod to read."""

    def __init__(self, config=None):
        from config import Config
        self.config = config or Config()
        self.last_write_time = 0
        self.last_action: Optional[Action] = None
        self.write_count = 0
        self.error_count = 0

    def write_action(self, action: Action) -> bool:
        """
        Write action to action.json file using atomic write operation.
        Returns True if successful.
        """
        if action is None:
            if self.config.VERBOSE:
                print("[ActionWriter] Received None action")
            return False

        try:
            path = Path(self.config.ACTION_FILE_PATH)
            
            # Ensure parent directory exists
            path.parent.mkdir(parents=True, exist_ok=True)

            # Write atomically using temporary file
            temp_path = path.with_suffix('.tmp')
            
            # Write to temp file
            with open(temp_path, 'w') as f:
                json.dump(action.to_dict(), f, separators=(',', ':'))
            
            # Atomic rename (on Windows, need to remove destination first)
            try:
                if os.name == 'nt' and path.exists():
                    path.unlink()
                temp_path.rename(path)
            except Exception as e:
                # Fallback to non-atomic write on Windows
                if self.config.VERBOSE:
                    print(f"[ActionWriter] Atomic rename failed, using fallback: {e}")
                with open(path, 'w') as f:
                    json.dump(action.to_dict(), f, separators=(',', ':'))

            self.last_write_time = time.time()
            self.last_action = action
            self.write_count += 1
            self.error_count = 0  # Reset error count on success

            if self.config.LOG_ACTIONS:
                print(f"[Action] {action}")

            return True

        except Exception as e:
            self.error_count += 1
            if self.config.VERBOSE or self.error_count <= 3:
                print(f"[ActionWriter] Error writing action: {e}")
            return False

    def clear_action(self) -> bool:
        """Write zero action (stop all movement/shooting)."""
        return self.write_action(Action())

    def get_last_action(self) -> Optional[Action]:
        """Get last written action."""
        return self.last_action
    
    def get_stats(self) -> Dict:
        """Get writer statistics."""
        return {
            'total_writes': self.write_count,
            'error_count': self.error_count,
            'last_action': str(self.last_action) if self.last_action else 'None'
        }
