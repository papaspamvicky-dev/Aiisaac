"""State reader module - handles reading and parsing state.json."""
import json
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

@dataclass
class PlayerState:
    """Player data structure."""
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    hp: int = 0
    max_hp: int = 0
    bombs: int = 0
    keys: int = 0
    coins: int = 0
    charge: int = 0
    has_flight: bool = False

@dataclass
class EnemyState:
    """Enemy data structure."""
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    hp: float = 0.0
    max_hp: float = 0.0
    type_id: int = 0
    variant: int = 0
    subtype: int = 0
    distance: float = 0.0

@dataclass
class ProjectileState:
    """Projectile data structure."""
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    distance: float = 0.0
    is_hostile: bool = True

@dataclass
class PickupState:
    """Pickup data structure."""
    x: float
    y: float
    variant: int = 0
    subtype: int = 0
    distance: float = 0.0

@dataclass
class RoomState:
    """Room data structure."""
    type_id: int = 0
    shape: int = 0
    stage: int = 0
    stage_type: int = 0
    is_clear: bool = False
    room_index: int = 0
    grid_width: int = 0
    grid_height: int = 0

@dataclass
class GameState:
    """Complete game state."""
    frame: int = 0
    timestamp: int = 0
    player: Optional[PlayerState] = None
    enemies: List[EnemyState] = field(default_factory=list)
    projectiles: List[ProjectileState] = field(default_factory=list)
    pickups: List[PickupState] = field(default_factory=list)
    room: Optional[RoomState] = None
    game_seed: int = 0
    difficulty: int = 0
    challenge: int = 0

class StateReader:
    """Handles reading and parsing game state from JSON."""

    def __init__(self, config=None):
        from config import Config, MAX_ENEMIES, MAX_PROJECTILES
        self.config = config or Config()
        self.max_enemies = MAX_ENEMIES
        self.max_projectiles = MAX_PROJECTILES
        self.last_read_time = 0
        self.last_frame = -1
        self.last_mtime = 0
        self._cached_state: Optional[GameState] = None
        self.error_count = 0
        self.read_count = 0

    def read_state(self) -> Optional[GameState]:
        """
        Read and parse state.json file.
        Returns None if file doesn't exist, is corrupted, or hasn't changed.
        """
        try:
            path = Path(self.config.STATE_FILE_PATH)
            
            # Check if file exists
            if not path.exists():
                if self.error_count == 0 and self.config.VERBOSE:
                    print(f"[StateReader] State file does not exist: {path}")
                self.error_count += 1
                return self._cached_state

            # Get file modification time
            try:
                mtime = path.stat().st_mtime
            except OSError as e:
                if self.config.VERBOSE:
                    print(f"[StateReader] Error getting file stats: {e}")
                return self._cached_state

            # Check if file has been modified since last read
            if mtime == self.last_mtime:
                return self._cached_state

            # Check if file is stale
            current_time = time.time()
            file_age = current_time - mtime
            if file_age > self.config.STATE_TIMEOUT:
                if self.config.VERBOSE and self.error_count % 100 == 0:
                    print(f"[StateReader] State file is stale ({file_age:.1f}s old)")
                return self._cached_state

            self.last_mtime = mtime

            # Read and parse
            with open(path, 'r') as f:
                data = json.load(f)

            state = self._parse_state(data)

            # Only update cache if we got a newer frame
            if state and state.frame > self.last_frame:
                self.last_frame = state.frame
                self._cached_state = state
                self.read_count += 1
                self.error_count = 0  # Reset error count on success
                
                if self.config.VERBOSE and self.read_count % 60 == 0:
                    print(f"[State] Frame {state.frame}, {len(state.enemies)} enemies, "
                          f"{len(state.projectiles)} projectiles, HP: {state.player.hp}/{state.player.max_hp}")

            return self._cached_state

        except json.JSONDecodeError as e:
            if self.config.VERBOSE and self.error_count < 3:
                print(f"[StateReader] JSON parse error: {e}")
            self.error_count += 1
            return self._cached_state
        except Exception as e:
            if self.config.VERBOSE and self.error_count < 3:
                print(f"[StateReader] Error reading state: {e}")
            self.error_count += 1
            return self._cached_state

    def _parse_state(self, data: Dict[str, Any]) -> Optional[GameState]:
        """Parse raw JSON dict into GameState dataclass."""
        try:
            # Parse player
            player_data = data.get('player', {})
            if not player_data:
                return None
                
            player = PlayerState(
                x=float(player_data.get('x', 0)),
                y=float(player_data.get('y', 0)),
                vx=float(player_data.get('vx', 0)),
                vy=float(player_data.get('vy', 0)),
                hp=int(player_data.get('hp', 0)),
                max_hp=int(player_data.get('max_hp', 0)),
                bombs=int(player_data.get('bombs', 0)),
                keys=int(player_data.get('keys', 0)),
                coins=int(player_data.get('coins', 0)),
                charge=int(player_data.get('charge', 0)),
                has_flight=bool(player_data.get('has_flight', False))
            )

            # Parse enemies
            enemies = []
            for e in data.get('enemies', [])[:self.max_enemies]:
                try:
                    enemies.append(EnemyState(
                        x=float(e.get('x', 0)),
                        y=float(e.get('y', 0)),
                        vx=float(e.get('vx', 0)),
                        vy=float(e.get('vy', 0)),
                        hp=float(e.get('hp', 0)),
                        max_hp=float(e.get('max_hp', 0)),
                        type_id=int(e.get('type', 0)),
                        variant=int(e.get('variant', 0)),
                        subtype=int(e.get('subtype', 0)),
                        distance=float(e.get('distance', 0))
                    ))
                except (ValueError, TypeError):
                    continue

            # Parse projectiles
            projectiles = []
            for p in data.get('projectiles', [])[:self.max_projectiles]:
                try:
                    projectiles.append(ProjectileState(
                        x=float(p.get('x', 0)),
                        y=float(p.get('y', 0)),
                        vx=float(p.get('vx', 0)),
                        vy=float(p.get('vy', 0)),
                        distance=float(p.get('distance', 0)),
                        is_hostile=bool(p.get('is_hostile', True))
                    ))
                except (ValueError, TypeError):
                    continue

            # Parse pickups
            pickups = []
            for pk in data.get('pickups', []):
                try:
                    pickups.append(PickupState(
                        x=float(pk.get('x', 0)),
                        y=float(pk.get('y', 0)),
                        variant=int(pk.get('variant', 0)),
                        subtype=int(pk.get('subtype', 0)),
                        distance=float(pk.get('distance', 0))
                    ))
                except (ValueError, TypeError):
                    continue

            # Parse room
            room_data = data.get('room', {})
            room = RoomState(
                type_id=int(room_data.get('type', 0)),
                shape=int(room_data.get('shape', 0)),
                stage=int(room_data.get('stage', 0)),
                stage_type=int(room_data.get('stage_type', 0)),
                is_clear=bool(room_data.get('is_clear', False)),
                room_index=int(room_data.get('room_index', 0)),
                grid_width=int(room_data.get('grid_width', 0)),
                grid_height=int(room_data.get('grid_height', 0))
            )

            # Parse game info
            game_data = data.get('game', {})

            return GameState(
                frame=int(data.get('frame', 0)),
                timestamp=int(data.get('timestamp', 0)),
                player=player,
                enemies=enemies,
                projectiles=projectiles,
                pickups=pickups,
                room=room,
                game_seed=int(game_data.get('seed', 0)),
                difficulty=int(game_data.get('difficulty', 0)),
                challenge=int(game_data.get('challenge', 0))
            )

        except Exception as e:
            if self.config.VERBOSE:
                print(f"[StateReader] Error parsing state: {e}")
            return None

    def get_cached_state(self) -> Optional[GameState]:
        """Get last successfully read state without reading file."""
        return self._cached_state
    
    def get_stats(self) -> Dict:
        """Get reader statistics."""
        return {
            'total_reads': self.read_count,
            'error_count': self.error_count,
            'last_frame': self.last_frame,
            'has_state': self._cached_state is not None
        }
