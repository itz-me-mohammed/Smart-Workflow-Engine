import json
import google.generativeai as genai
from datetime import datetime
import os

class AIChatInterface:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.chat_history = []
        self.conversation_context = []
        self.max_history = 50
        
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Load chat history if exists
        self.load_chat_history()
    
    def chat(self, user_message, include_automation_context=True):
        """Have a conversation with the AI assistant"""
        try:
            # Add user message to history
            self.add_to_history("user", user_message)
            
            # Build context for the AI
            context = self.build_context(include_automation_context)
            
            # Create the conversation prompt
            prompt = f"""
            You are an AI assistant that helps users with computer automation tasks.
            You can help users understand automation concepts, troubleshoot issues, and suggest improvements.
            
            Context:
            {context}
            
            Recent conversation:
            {self.format_recent_conversation()}
            
            User: {user_message}
            
            Respond helpfully and conversationally. If the user is asking about automation tasks,
            provide practical advice. If they're having issues, help troubleshoot.
            """
            
            response = self.model.generate_content(prompt)
            ai_response = response.text.strip()
            
            # Add AI response to history
            self.add_to_history("assistant", ai_response)
            
            # Save history
            self.save_chat_history()
            
            return {
                "success": True,
                "response": ai_response,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_response = f"I'm sorry, I encountered an error: {str(e)}"
            self.add_to_history("assistant", error_response)
            
            return {
                "success": False,
                "response": error_response,
                "error": str(e)
            }
    
    def analyze_automation_task(self, task_description):
        """Analyze a proposed automation task and provide insights"""
        try:
            analysis_prompt = f"""
            Analyze this automation task and provide insights:
            
            Task: {task_description}
            
            Please provide:
            1. Complexity assessment (Easy/Medium/Hard)
            2. Potential challenges
            3. Suggested approach
            4. Estimated steps needed
            5. Alternative methods
            6. Tips for success
            
            Format your response as a structured analysis.
            """
            
            response = self.model.generate_content(analysis_prompt)
            
            return {
                "success": True,
                "analysis": response.text.strip(),
                "task": task_description
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def suggest_improvements(self, execution_log):
        """Suggest improvements based on execution logs"""
        try:
            # Parse the execution log
            log_text = "\n".join(execution_log) if isinstance(execution_log, list) else str(execution_log)
            
            improvement_prompt = f"""
            Analyze this automation execution log and suggest improvements:
            
            Execution Log:
            {log_text}
            
            Please suggest:
            1. Ways to make it more reliable
            2. Optimizations to reduce execution time
            3. Better error handling
            4. Alternative approaches
            5. User experience improvements
            
            Be specific and practical in your suggestions.
            """
            
            response = self.model.generate_content(improvement_prompt)
            
            return {
                "success": True,
                "suggestions": response.text.strip()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def help_with_coordinates(self, application_name, element_description):
        """Help find better coordinates for UI elements"""
        try:
            coordinate_prompt = f"""
            Help find coordinates for UI automation:
            
            Application: {application_name}
            Element: {element_description}
            
            Based on common UI patterns and the application type, suggest:
            1. Likely coordinate ranges
            2. Alternative selectors to try
            3. Tips for finding the element
            4. Common issues with this type of element
            
            Provide practical guidance for improving click accuracy.
            """
            
            response = self.model.generate_content(coordinate_prompt)
            
            return {
                "success": True,
                "guidance": response.text.strip(),
                "application": application_name,
                "element": element_description
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def add_to_history(self, role, message):
        """Add message to chat history"""
        self.chat_history.append({
            "role": role,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep history manageable
        if len(self.chat_history) > self.max_history:
            self.chat_history = self.chat_history[-self.max_history:]
    
    def build_context(self, include_automation_context):
        """Build context for the AI"""
        context = "You are helping with computer automation using Python, Selenium, and PyAutoGUI."
        
        if include_automation_context:
            context += """
            
            Available automation capabilities:
            - Web automation (Selenium)
            - Desktop automation (PyAutoGUI)
            - Application launching
            - Screen capture and analysis
            - Visual element detection
            - Web scraping
            - Workflow recording and playback
            
            Common issues you can help with:
            - Coordinate accuracy problems
            - Element detection failures
            - Timing and synchronization
            - Error handling strategies
            - Performance optimization
            """
        
        return context
    
    def format_recent_conversation(self, last_n=5):
        """Format recent conversation for context"""
        recent = self.chat_history[-last_n:] if len(self.chat_history) > last_n else self.chat_history
        
        formatted = []
        for entry in recent:
            role = entry["role"].title()
            message = entry["message"][:200] + "..." if len(entry["message"]) > 200 else entry["message"]
            formatted.append(f"{role}: {message}")
        
        return "\n".join(formatted)
    
    def save_chat_history(self):
        """Save chat history to file"""
        try:
            chat_dir = "chat_logs"
            os.makedirs(chat_dir, exist_ok=True)
            
            history_file = os.path.join(chat_dir, "chat_history.json")
            
            with open(history_file, 'w') as f:
                json.dump(self.chat_history, f, indent=2)
                
        except Exception as e:
            print(f"Failed to save chat history: {e}")
    
    def load_chat_history(self):
        """Load chat history from file"""
        try:
            history_file = os.path.join("chat_logs", "chat_history.json")
            
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    self.chat_history = json.load(f)
                    
        except Exception as e:
            print(f"Failed to load chat history: {e}")
            self.chat_history = []
    
    def clear_history(self):
        """Clear chat history"""
        self.chat_history = []
        self.save_chat_history()
    
    def get_conversation_summary(self):
        """Get a summary of the conversation"""
        if not self.chat_history:
            return "No conversation history"
        
        try:
            # Get recent messages
            recent_messages = [entry["message"] for entry in self.chat_history[-10:]]
            conversation_text = "\n".join(recent_messages)
            
            summary_prompt = f"""
            Summarize this conversation in 2-3 sentences:
            
            {conversation_text}
            
            Focus on the main topics discussed and any automation tasks or issues addressed.
            """
            
            response = self.model.generate_content(summary_prompt)
            return response.text.strip()
            
        except Exception as e:
            return f"Could not generate summary: {str(e)}"

# Add to ActionExecutor
class ActionExecutor:
    def __init__(self, logger=print, api_key=None):
        # ...existing code...
        self.chat_interface = AIChatInterface(api_key)
    
    def chat_with_assistant(self, message):
        """Chat with the AI assistant"""
        return self.chat_interface.chat(message)
    
    def get_task_analysis(self, task_description):
        """Get AI analysis of an automation task"""
        return self.chat_interface.analyze_automation_task(task_description)
    
    def get_improvement_suggestions(self, execution_log):
        """Get AI suggestions for improvement"""
        return self.chat_interface.suggest_improvements(execution_log)