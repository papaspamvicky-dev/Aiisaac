"""Rule-based decision engine - Phase 2 implementation."""
import math
from typing import Optional, Tuple, List
from state_reader import GameState, PlayerState, EnemyState, ProjectileState
from action_writer import Action

class RulesEngine:
    """
    Simple rule-based AI for Isaac.

    Strategy priority:
    1. Dodge projectiles (survival)
    2. Avoid enemy contact
    3. Shoot nearest enemy
    4. Move toward enemies if not in range
    """

    def __init__(self, config=None):
        from config import Config
        self.config = config or Config()
        self.dodge_distance = self.config.DODGE_DISTANCE
        self.avoid_distance = self.config.AVOID_DISTANCE
        self.attack_range = self.config.ATTACK_RANGE
        self.approach_range = self.config.APPROACH_RANGE

    def decide_action(self, state: GameState) -> Action:
        """Generate action based on current game state."""
        if not state or not state.player:
            return Action()  # No-op if no state

        player = state.player

        # Priority 1: Dodge projectiles
        dodge_action = self._dodge_projectiles(player, state.projectiles)
        if dodge_action:
            # Still try to shoot while dodging
            attack_action = self._attack_nearest(player, state.enemies)
            return Action(
                move_x=dodge_action.move_x,
                move_y=dodge_action.move_y,
                shoot_x=attack_action.shoot_x if attack_action else 0,
                shoot_y=attack_action.shoot_y if attack_action else 0
            )

        # Priority 2: Avoid enemy contact
        avoid_action = self._avoid_enemies(player, state.enemies)

        # Priority 3: Attack nearest enemy
        attack_action = self._attack_nearest(player, state.enemies)

        # Combine avoid and attack (avoid takes precedence for movement)
        if avoid_action:
            return Action(
                move_x=avoid_action.move_x,
                move_y=avoid_action.move_y,
                shoot_x=attack_action.shoot_x if attack_action else 0,
                shoot_y=attack_action.shoot_y if attack_action else 0
            )

        # Priority 4: Move toward enemies if not attacking
        approach_action = self._approach_enemies(player, state.enemies)
        if approach_action:
            return Action(
                move_x=approach_action.move_x,
                move_y=approach_action.move_y,
                shoot_x=attack_action.shoot_x if attack_action else 0,
                shoot_y=attack_action.shoot_y if attack_action else 0
            )

        return attack_action if attack_action else Action()

    def _dodge_projectiles(self, player: PlayerState, 
                          projectiles: List[ProjectileState]) -> Optional[Action]:
        """Generate dodge action if projectiles are near."""
        if not projectiles:
            return None

        # Find most threatening projectile
        most_dangerous = None
        min_threat_score = float('inf')

        for proj in projectiles:
            if not proj.is_hostile:
                continue

            # Calculate distance
            dist = proj.distance
            if dist > self.dodge_distance or dist < 1:
                continue

            # Calculate projectile speed
            speed = math.sqrt(proj.vx**2 + proj.vy**2)
            if speed < 0.1:
                continue

            # Calculate if projectile is moving toward player
            dx = player.x - proj.x
            dy = player.y - proj.y
            
            # Normalize direction to player
            player_dir_len = math.sqrt(dx**2 + dy**2)
            if player_dir_len < 0.1:
                continue
                
            dx_norm = dx / player_dir_len
            dy_norm = dy / player_dir_len
            
            # Dot product to check if moving toward player
            dot = (dx_norm * proj.vx + dy_norm * proj.vy)
            
            if dot <= 0:  # Not moving toward player
                continue

            # Calculate time to impact
            time_to_impact = dist / speed

            # Threat score: lower is more dangerous
            threat_score = time_to_impact * (1.0 - dot * 0.5)
            
            if threat_score < min_threat_score:
                min_threat_score = threat_score
                most_dangerous = proj

        if not most_dangerous or min_threat_score > 2.0:
            return None

        # Calculate dodge direction (perpendicular to projectile velocity)
        vx, vy = most_dangerous.vx, most_dangerous.vy
        
        # Normalize velocity
        vel_len = math.sqrt(vx**2 + vy**2)
        if vel_len < 0.1:
            return None
            
        vx_norm = vx / vel_len
        vy_norm = vy / vel_len

        # Two perpendicular directions
        perp1_x, perp1_y = -vy_norm, vx_norm
        perp2_x, perp2_y = vy_norm, -vx_norm

        # Choose the perpendicular direction that keeps us further from projectile
        dx_to_proj = most_dangerous.x - player.x
        dy_to_proj = most_dangerous.y - player.y

        dot1 = perp1_x * dx_to_proj + perp1_y * dy_to_proj
        dot2 = perp2_x * dx_to_proj + perp2_y * dy_to_proj

        # Pick direction that moves away from projectile
        if dot1 < dot2:
            dodge_x, dodge_y = perp1_x, perp1_y
        else:
            dodge_x, dodge_y = perp2_x, perp2_y

        # Convert to discrete actions
        move_x = 0
        move_y = 0
        
        if abs(dodge_x) > abs(dodge_y):
            move_x = 1 if dodge_x > 0 else -1
        else:
            move_y = 1 if dodge_y > 0 else -1

        return Action(move_x=move_x, move_y=move_y)

    def _avoid_enemies(self, player: PlayerState, 
                      enemies: List[EnemyState]) -> Optional[Action]:
        """Generate avoidance action if enemies are too close."""
        if not enemies:
            return None

        # Find all enemies within avoid distance
        close_enemies = [e for e in enemies if e.distance < self.avoid_distance and e.distance > 0]
        
        if not close_enemies:
            return None

        # Calculate average avoidance vector from all close enemies
        avoid_x = 0.0
        avoid_y = 0.0
        
        for enemy in close_enemies:
            dx = player.x - enemy.x
            dy = player.y - enemy.y
            
            # Weight by inverse distance (closer = stronger push)
            weight = 1.0 / max(enemy.distance, 1.0)
            
            avoid_x += dx * weight
            avoid_y += dy * weight

        # Normalize
        avoid_len = math.sqrt(avoid_x**2 + avoid_y**2)
        if avoid_len < 0.1:
            return None

        avoid_x /= avoid_len
        avoid_y /= avoid_len

        # Convert to discrete actions
        if abs(avoid_x) > abs(avoid_y):
            return Action(move_x=1 if avoid_x > 0 else -1, move_y=0)
        else:
            return Action(move_x=0, move_y=1 if avoid_y > 0 else -1)

    def _attack_nearest(self, player: PlayerState, 
                       enemies: List[EnemyState]) -> Optional[Action]:
        """Generate shooting action toward nearest enemy."""
        if not enemies:
            return None

        # Find nearest enemy within attack range
        nearest = None
        for enemy in enemies:
            if enemy.distance <= self.attack_range:
                nearest = enemy
                break  # Already sorted by distance

        if not nearest:
            return None

        # Calculate aim direction
        dx = nearest.x - player.x
        dy = nearest.y - player.y

        # Lead the target based on velocity
        if abs(nearest.vx) > 0.1 or abs(nearest.vy) > 0.1:
            # Simple leading: add velocity scaled by distance
            lead_factor = nearest.distance / 200.0  # Adjust based on tear speed
            dx += nearest.vx * lead_factor
            dy += nearest.vy * lead_factor

        # Normalize to get direction
        aim_len = math.sqrt(dx**2 + dy**2)
        if aim_len < 0.1:
            return None

        dx /= aim_len
        dy /= aim_len

        # Convert to discrete shooting direction
        if abs(dx) > abs(dy):
            return Action(shoot_x=1 if dx > 0 else -1, shoot_y=0)
        else:
            return Action(shoot_x=0, shoot_y=1 if dy > 0 else -1)

    def _approach_enemies(self, player: PlayerState, 
                         enemies: List[EnemyState]) -> Optional[Action]:
        """Generate movement toward enemies if not in attack range."""
        if not enemies:
            return None

        # Find nearest enemy
        nearest = enemies[0]  # Already sorted by distance

        # Only approach if outside attack range but within approach range
        if nearest.distance < self.attack_range or nearest.distance > self.approach_range:
            return None

        # Move toward enemy
        dx = nearest.x - player.x
        dy = nearest.y - player.y

        # Normalize
        move_len = math.sqrt(dx**2 + dy**2)
        if move_len < 0.1:
            return None

        dx /= move_len
        dy /= move_len

        # Convert to discrete actions
        if abs(dx) > abs(dy):
            return Action(move_x=1 if dx > 0 else -1, move_y=0)
        else:
            return Action(move_x=0, move_y=1 if dy > 0 else -1)
