#!/usr/bin/env python3
"""
IsaacAI Agent - Main entry point
"""
import argparse
import sys
import time
import signal
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import Config, AgentMode
from state_reader import StateReader
from action_writer import ActionWriter, Action
from rules_engine import RulesEngine

class IsaacAgent:
    """Main agent class that coordinates state reading, decision making, and action writing."""
    
    def __init__(self, mode: AgentMode = AgentMode.RANDOM):
        self.config = Config()
        self.config.MODE = mode
        self.running = False
        
        self.state_reader = StateReader(self.config)
        self.action_writer = ActionWriter(self.config)
        self.rules_engine = None
        
        if mode == AgentMode.RULE_BASED:
            self.rules_engine = RulesEngine(self.config)
            print("[Agent] Rule-based mode initialized")
        elif mode == AgentMode.RANDOM:
            print("[Agent] Random mode initialized")
        else:
            raise NotImplementedError(f"Mode {mode} not yet implemented")
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print("\n[Agent] Shutdown signal received, stopping...")
        self.running = False
    
    def _decide_action(self, state) -> Action:
        """Decide what action to take based on current state."""
        if self.config.MODE == AgentMode.RANDOM:
            return self._random_action()
        elif self.config.MODE == AgentMode.RULE_BASED:
            return self.rules_engine.decide_action(state)
        else:
            return Action()
    
    def _random_action(self) -> Action:
        """Generate a random valid action."""
        import random
        return Action(
            move_x=random.choice([-1, 0, 1]),
            move_y=random.choice([-1, 0, 1]),
            shoot_x=random.choice([-1, 0, 1]),
            shoot_y=random.choice([-1, 0, 1])
        )
    
    def run(self):
        """Main agent loop."""
        print(f"[Agent] Starting in {self.config.MODE.value} mode...")
        self.config.print_config()
        print("[Agent] Press Ctrl+C to stop")
        print("-" * 60)
        
        self.running = True
        loop_count = 0
        last_status_time = time.time()
        status_interval = 5.0  # Print status every 5 seconds
        
        # Counters
        no_state_count = 0
        action_write_failures = 0
        
        try:
            while self.running:
                loop_count += 1
                
                # Read current game state
                state = self.state_reader.read_state()
                
                # Handle missing state
                if state is None:
                    no_state_count += 1
                    if no_state_count % 100 == 1:
                        print("[Agent] Waiting for game state...")
                    time.sleep(self.config.POLL_INTERVAL)
                    continue
                
                # Reset no-state counter when we get state
                if no_state_count > 0:
                    print(f"[Agent] Game state restored after {no_state_count} attempts")
                    no_state_count = 0
                
                # Decide action based on state
                action = self._decide_action(state)
                
                # Write action to file
                success = self.action_writer.write_action(action)
                if not success:
                    action_write_failures += 1
                
                # Print status periodically
                current_time = time.time()
                if current_time - last_status_time > status_interval:
                    elapsed = current_time - last_status_time
                    fps = loop_count / elapsed
                    
                    reader_stats = self.state_reader.get_stats()
                    writer_stats = self.action_writer.get_stats()
                    
                    print(f"[Agent] Frame {state.frame:6d} | "
                          f"HP: {state.player.hp:2d}/{state.player.max_hp:2d} | "
                          f"Enemies: {len(state.enemies):2d} | "
                          f"Projectiles: {len(state.projectiles):2d} | "
                          f"Loop FPS: {fps:.1f}")
                    
                    if self.config.VERBOSE:
                        print(f"        Read: {reader_stats['total_reads']} "
                              f"({reader_stats['error_count']} errors) | "
                              f"Write: {writer_stats['total_writes']} "
                              f"({writer_stats['error_count']} errors)")
                    
                    loop_count = 0
                    last_status_time = current_time
                
                # Sleep to control loop rate
                time.sleep(self.config.POLL_INTERVAL)
                
        except KeyboardInterrupt:
            print("\n[Agent] Interrupted by user")
        except Exception as e:
            print(f"[Agent] Error in main loop: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            print("[Agent] Cleaning up...")
            # Clear action file to stop movement
            self.action_writer.clear_action()
            
            # Print final statistics
            reader_stats = self.state_reader.get_stats()
            writer_stats = self.action_writer.get_stats()
            print(f"[Agent] Final stats:")
            print(f"        States read: {reader_stats['total_reads']}")
            print(f"        Actions written: {writer_stats['total_writes']}")
            print(f"        Read errors: {reader_stats['error_count']}")
            print(f"        Write errors: {writer_stats['error_count']}")
            print("[Agent] Stopped.")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="IsaacAI Agent - AI controller for The Binding of Isaac",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python agent.py --mode random          # Random movement
  python agent.py --mode rules           # Rule-based AI
  python agent.py --mode rules --verbose # Verbose output
  
  Set custom Isaac path:
  export ISAAC_PATH="/path/to/isaac"
  python agent.py --mode rules
        """
    )
    
    parser.add_argument(
        "--mode", 
        choices=["random", "rules", "train", "inference"], 
        default="random",
        help="Agent mode (default: random)"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable verbose output"
    )
    parser.add_argument(
        "--log-actions",
        action="store_true",
        help="Log every action taken"
    )
    
    args = parser.parse_args()
    
    # Map mode strings to enums
    mode_map = {
        "random": AgentMode.RANDOM,
        "rules": AgentMode.RULE_BASED,
        "train": AgentMode.TRAINING,
        "inference": AgentMode.INFERENCE
    }
    
    # Create and configure agent
    agent = IsaacAgent(mode=mode_map[args.mode])
    
    if args.verbose:
        agent.config.VERBOSE = True
    
    if args.log_actions:
        agent.config.LOG_ACTIONS = True
    
    # Ensure data directories exist
    Config.ensure_dirs()
    
    # Run agent
    agent.run()

if __name__ == "__main__":
    main()
