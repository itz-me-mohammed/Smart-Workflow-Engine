import json
import time
import os
from datetime import datetime
from pynput import mouse, keyboard
import threading

class WorkflowRecorder:
    def __init__(self):
        self.recording = False
        self.workflow_name = None
        self.start_time = None
        self.recorded_actions = []
        self.mouse_listener = None
        self.keyboard_listener = None
        self._stop_event = threading.Event()

        # Create workflows directory if it doesn't exist
        if not os.path.exists('workflows'):
            os.makedirs('workflows')

    def start_recording(self, workflow_name):
        """Start recording user actions"""
        if self.recording:
            print("⚠️ Recording already in progress - stopping previous recording first")
            self.stop_recording()
            time.sleep(1)  # Give time for cleanup
            
        print(f"🎬 Starting recording: {workflow_name}")
        
        # Reset state
        self.recording = True
        self.workflow_name = workflow_name
        self.start_time = time.time()
        self.recorded_actions = []
        self._stop_event.clear()
        
        try:
            # Start listeners with better error handling
            self.mouse_listener = mouse.Listener(
                on_click=self._on_mouse_click,
                on_scroll=self._on_mouse_scroll,
                suppress=False
            )
            
            self.keyboard_listener = keyboard.Listener(
                on_press=self._on_key_press,
                suppress=False
            )
            
            # Start listeners in separate threads
            self.mouse_listener.start()
            self.keyboard_listener.start()
            
            print(f"✅ Recording started: {workflow_name}")
            print("📝 Recording mouse clicks, scrolls, and key presses...")
            print("🛑 Press ESC to stop recording")
            return True
            
        except Exception as e:
            print(f"❌ Error starting recording: {e}")
            self.recording = False
            return False

    def stop_recording(self):
        """Stop recording and save workflow"""
        if not self.recording:
            print("⚠️ No active recording to stop")
            return None
            
        print("🛑 Stopping recording...")
        self.recording = False
        self._stop_event.set()
        
        try:
            # Stop listeners with proper cleanup
            if self.mouse_listener and self.mouse_listener.running:
                print("🖱️ Stopping mouse listener...")
                self.mouse_listener.stop()
                self.mouse_listener.join(timeout=2)  # Wait up to 2 seconds
                
            if self.keyboard_listener and self.keyboard_listener.running:
                print("⌨️ Stopping keyboard listener...")
                self.keyboard_listener.stop()
                self.keyboard_listener.join(timeout=2)  # Wait up to 2 seconds
            
            # Clear listener references
            self.mouse_listener = None
            self.keyboard_listener = None
            
            print(f"📊 Recorded {len(self.recorded_actions)} actions during session")
            
            # Save workflow
            filename = self._save_workflow()
            
            if filename:
                print(f"✅ Recording stopped and saved: {filename}")
                return filename
            else:
                print("❌ Failed to save workflow")
                return None
            
        except Exception as e:
            print(f"❌ Error stopping recording: {e}")
            # Force cleanup
            self.recording = False
            self.mouse_listener = None
            self.keyboard_listener = None
            return None

    def _on_mouse_click(self, x, y, button, pressed):
        """Handle mouse click events"""
        if not self.recording or self._stop_event.is_set():
            return
        
        if pressed:  # Only record press events
            action = {
                "type": "mouse_click",
                "x": int(x),
                "y": int(y),
                "button": str(button).replace('Button.', ''),
                "timestamp": time.time() - self.start_time
            }
            self.recorded_actions.append(action)
            print(f"🖱️ Recorded click at ({x}, {y})")

    def _on_mouse_scroll(self, x, y, dx, dy):
        """Handle mouse scroll events"""
        if not self.recording or self._stop_event.is_set():
            return
            
        action = {
            "type": "mouse_scroll",
            "x": int(x),
            "y": int(y),
            "dx": int(dx),
            "dy": int(dy),
            "timestamp": time.time() - self.start_time
        }
        self.recorded_actions.append(action)
        print(f"🖱️ Recorded scroll at ({x}, {y}) dy={dy}")

    def _on_key_press(self, key):
        """Handle keyboard press events"""
        if not self.recording or self._stop_event.is_set():
            return
        
        # Handle ESC key to stop recording
        if key == keyboard.Key.esc:
            print("🛑 ESC pressed - stopping recording")
            self.stop_recording()
            return
        
        try:
            if hasattr(key, 'char') and key.char:
                key_str = key.char
            else:
                key_str = str(key).replace('Key.', '')
                
            action = {
                "type": "key_press",
                "key": key_str,
                "timestamp": time.time() - self.start_time
            }
            self.recorded_actions.append(action)
            print(f"⌨️ Recorded key: {key_str}")
        except:
            pass

    def _save_workflow(self):
        """Save workflow to file"""
        try:
            # Create workflows directory
            workflows_dir = "workflows"
            os.makedirs(workflows_dir, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_name = "".join(c for c in self.workflow_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_')
            filename = f"{workflows_dir}/{safe_name}_{timestamp}.json"
            
            # Create workflow data
            workflow_data = {
                "name": self.workflow_name,
                "created_at": datetime.now().isoformat(),
                "duration": time.time() - self.start_time if self.start_time else 0,
                "actions_count": len(self.recorded_actions),
                "actions": self.recorded_actions
            }
            
            # Save to file
            with open(filename, 'w') as f:
                json.dump(workflow_data, f, indent=2)
                
            print(f"💾 Workflow saved: {filename}")
            print(f"📊 Recorded {len(self.recorded_actions)} actions")
            
            # Reset state after saving
            self._reset_state()
            
            return filename
            
        except Exception as e:
            print(f"❌ Error saving workflow: {e}")
            return None

    def _reset_state(self):
        """Reset recorder state"""
        self.workflow_name = None
        self.start_time = None
        self.recorded_actions = []
        self.recording = False
        self._stop_event.set()

    def is_recording(self):
        """Check if currently recording"""
        return self.recording

    def get_recording_status(self):
        """Get detailed recording status"""
        return {
            "recording": self.recording,
            "workflow_name": self.workflow_name,
            "actions_count": len(self.recorded_actions) if self.recorded_actions else 0,
            "duration": time.time() - self.start_time if self.start_time else 0
        }

    def force_stop(self):
        """Force stop recording (emergency cleanup)"""
        print("🚨 Force stopping workflow recording...")
        
        self.recording = False
        self._stop_event.set()
        
        # Force stop listeners
        try:
            if self.mouse_listener:
                self.mouse_listener.stop()
                self.mouse_listener = None
        except:
            pass
            
        try:
            if self.keyboard_listener:
                self.keyboard_listener.stop()
                self.keyboard_listener = None
        except:
            pass
        
        self._reset_state()
        print("✅ Force stop completed")

    def list_workflows(self):
        """List all saved workflows"""
        try:
            workflows_dir = "workflows"
            if not os.path.exists(workflows_dir):
                return []
                
            workflows = []
            for filename in os.listdir(workflows_dir):
                if filename.endswith('.json'):
                    try:
                        filepath = os.path.join(workflows_dir, filename)
                        with open(filepath, 'r') as f:
                            data = json.load(f)
                            
                        workflows.append({
                            "filename": filename,
                            "name": data.get('name', 'Unknown'),
                            "created_at": data.get('created_at', ''),
                            "actions_count": data.get('actions_count', 0),
                            "duration": data.get('duration', 0)
                        })
                    except Exception as e:
                        print(f"⚠️ Error reading workflow {filename}: {e}")
                        
            return sorted(workflows, key=lambda x: x['created_at'], reverse=True)
            
        except Exception as e:
            print(f"❌ Error listing workflows: {e}")
            return []

    def replay_workflow(self, workflow_file, speed_multiplier=1.0):
        """Replay a recorded workflow"""
        try:
            # Handle relative path
            if not workflow_file.startswith('workflows/'):
                workflow_file = f"workflows/{workflow_file}"
                
            print(f"🔄 Loading workflow: {workflow_file}")
            
            if not os.path.exists(workflow_file):
                print(f"❌ File not found: {workflow_file}")
                return False
            
            with open(workflow_file, 'r') as f:
                workflow_data = json.load(f)
                
            actions = workflow_data.get('actions', [])
            workflow_name = workflow_data.get('name', 'Unknown')
            
            if not actions:
                print("⚠️ No actions to replay")
                return True
                
            print(f"🔄 Replaying: {workflow_name} ({len(actions)} actions)")
            
            import pyautogui
            pyautogui.FAILSAFE = True
            
            # Wait before starting
            print("⏳ Starting replay in 2 seconds...")
            time.sleep(2)
            
            # Replay each action
            last_timestamp = 0
            for i, action in enumerate(actions, 1):
                try:
                    # Calculate delay between actions
                    current_timestamp = action.get('timestamp', 0)
                    delay = (current_timestamp - last_timestamp) / speed_multiplier
                    if delay > 0:
                        time.sleep(min(delay, 2.0))  # Cap maximum delay
                    
                    # Execute action based on type
                    if action['type'] == 'mouse_click':
                        x, y = action['x'], action['y']
                        pyautogui.click(x=x, y=y)
                        print(f"🖱️ Clicking ({x}, {y}) - {i}/{len(actions)}")
                        
                    elif action['type'] == 'key_press':
                        key = action['key']
                        if len(key) == 1:  # Single character
                            pyautogui.write(key)
                        else:  # Special key
                            key_mapping = {
                                'ctrl_l': 'ctrl', 'ctrl_r': 'ctrl',
                                'alt_l': 'alt', 'alt_r': 'alt',
                                'shift_l': 'shift', 'shift_r': 'shift',
                                'cmd': 'cmd', 'esc': 'escape',
                                'enter': 'enter', 'tab': 'tab',
                                'space': 'space', 'backspace': 'backspace',
                                'delete': 'delete'
                            }
                            mapped_key = key_mapping.get(key.lower(), key)
                            pyautogui.press(mapped_key)
                        print(f"⌨️ Key: {key} - {i}/{len(actions)}")
                        
                    elif action['type'] == 'mouse_scroll':
                        x, y, dy = action['x'], action['y'], action['dy']
                        pyautogui.scroll(dy, x=x, y=y)
                        print(f"🖱️ Scroll dy={dy} at ({x},{y}) - {i}/{len(actions)}")
                
                    last_timestamp = current_timestamp
                    
                except Exception as e:
                    print(f"⚠️ Error executing action {i}: {e}")
                    continue
        
            print("✅ Workflow replay completed!")
            return True
            
        except Exception as e:
            print(f"❌ Error replaying workflow: {e}")
            return False