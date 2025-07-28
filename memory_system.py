# memory_system.py

import json
import os
from datetime import datetime

class MemorySystem:
    def __init__(self, memory_file='memory_log.json'):
        self.memory_file = memory_file
        self.memory = []
        self.load_memory()

    def load_memory(self):
        if os.path.exists(self.memory_file):
            with open(self.memory_file, 'r') as f:
                try:
                    self.memory = json.load(f)
                except json.JSONDecodeError:
                    self.memory = []

    def save_memory(self):
        with open(self.memory_file, 'w') as f:
            json.dump(self.memory, f, indent=4)

    def log_task(self, user_prompt, actions):
        task_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_prompt": user_prompt,
            "actions": actions
        }
        self.memory.append(task_entry)
        self.save_memory()

    def save_step(self, step):
        """
        Save an individual step to memory. Used during step-by-step execution.
        """
        task_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_prompt": "step-execution",
            "actions": [step]
        }
        self.memory.append(task_entry)
        self.save_memory()

    def get_recent_tasks(self, limit=5):
        return self.memory[-limit:]

    def search_tasks(self, keyword):
        return [task for task in self.memory if keyword.lower() in task['user_prompt'].lower()]

    def get_similar_tasks(self, user_prompt, limit=3):
        """Find similar tasks to the current one"""
        # Simple implementation - could be enhanced with embedding similarity
        matching_tasks = []
        words = set(user_prompt.lower().split())
        
        for task in self.memory:
            if 'user_prompt' in task:
                task_words = set(task['user_prompt'].lower().split())
                common_words = words.intersection(task_words)
                
                # If there's significant overlap
                if len(common_words) > 2:
                    similarity_score = len(common_words) / len(words)
                    matching_tasks.append((similarity_score, task))
        
        # Sort by similarity score
        matching_tasks.sort(reverse=True)
        return [task for _, task in matching_tasks[:limit]]

    def get_successful_patterns(self):
        """Analyze memory to find successful action patterns"""
        # This could be expanded with more sophisticated analysis
        pattern_counts = {}
        
        for entry in self.memory:
            if 'actions' in entry:
                # Create a pattern string from the sequence of actions
                pattern = ' > '.join([action.get('action', 'unknown') for action in entry['actions']])
                
                if pattern in pattern_counts:
                    pattern_counts[pattern] += 1
                else:
                    pattern_counts[pattern] = 1
        
        # Sort patterns by frequency
        sorted_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_patterns
