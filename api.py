from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import uuid
import google.generativeai as genai
import time

# Import your modules
from assistant_bot import ActionExecutor, get_steps_from_gemini

app = Flask(__name__)
CORS(app)

# Global variables
current_executor = None
current_api_key = None
execution_logs = []

@app.route('/')
def root():
    return {"message": "AI Assistant API is running"}

@app.route('/api/api-key-status', methods=['GET'])
def api_key_status():
    """Check if API key is configured"""
    global current_api_key
    return jsonify({
        "hasApiKey": current_api_key is not None,
        "success": True
    })

@app.route('/api/validate-api-key', methods=['POST'])
def validate_api_key():
    """Validate the provided API key"""
    global current_api_key
    
    try:
        data = request.json
        if not data or not data.get('api_key'):
            return jsonify({
                "valid": False,
                "error": "API key is required"
            })
            
        api_key = data.get('api_key').strip()
        print(f"🔑 Testing API key: {api_key[:10]}...")
        
        try:
            # Configure Gemini with shorter timeout
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Quick validation with minimal tokens
            response = model.generate_content(
                "Test",
                generation_config=genai.types.GenerationConfig(
                    temperature=0,
                    candidate_count=1,
                    max_output_tokens=1
                )
            )
            
            if response and hasattr(response, 'text'):
                current_api_key = api_key
                print("✅ API key validation successful!")
                return jsonify({
                    "valid": True,
                    "message": "API key validated successfully"
                })
            
            return jsonify({
                "valid": False,
                "error": "Invalid API key or unexpected response"
            })
                
        except Exception as e:
            error_msg = str(e).lower()
            print(f"❌ Validation error: {error_msg}")
            
            if "invalid api key" in error_msg:
                return jsonify({
                    "valid": False,
                    "error": "Invalid API key"
                })
            elif "quota" in error_msg:
                return jsonify({
                    "valid": False,
                    "error": "API quota exceeded"
                })
            else:
                return jsonify({
                    "valid": False,
                    "error": f"Validation error: {str(e)}"
                })
                
    except Exception as e:
        print(f"❌ Server error: {str(e)}")
        return jsonify({
            "valid": False,
            "error": f"Server error: {str(e)}"
        })

@app.route('/api/clear-api-key', methods=['POST'])
def clear_api_key():
    """Clear the stored API key"""
    global current_api_key, current_executor
    
    try:
        current_api_key = None
        current_executor = None
        
        return jsonify({
            "success": True,
            "message": "API key cleared successfully"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/set-api-key', methods=['POST'])
def set_api_key():
    """Set API key (legacy endpoint for compatibility)"""
    global current_api_key
    try:
        data = request.json
        api_key = data.get('api_key')
        
        if not api_key:
            return jsonify({"success": False, "message": "API key is required"})
        
        current_api_key = api_key
        return jsonify({"success": True, "message": "API key set successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current execution status"""
    global current_api_key, execution_logs
    return jsonify({
        "status": "idle",
        "log": execution_logs[-10:] if execution_logs else [],
        "hasApiKey": current_api_key is not None
    })

@app.route('/api/stop', methods=['POST'])
def stop_execution():
    """Stop current execution"""
    return jsonify({
        "success": True,
        "message": "Execution stopped"
    })

@app.route('/api/execute', methods=['POST'])
def execute_automation():
    global current_executor, current_api_key
    
    try:
        data = request.json
        user_prompt = data.get('prompt')
        mode = data.get('mode')
        
        if not user_prompt:
            return jsonify({"success": False, "message": "Prompt is required"})
        
        if not current_api_key:
            return jsonify({"success": False, "message": "API key not set"})
            
        print(f"🤖 Executing prompt in {mode} mode: {user_prompt}")
        
        # Create executor if not exists
        if not current_executor:
            current_executor = ActionExecutor(api_key=current_api_key)
        
        # Handle web scraping mode
        if mode == 'scrape':
            try:
                # Extract URL from the prompt using regex or basic string parsing
                import re
                url_match = re.search(r'https?://[^\s]+', user_prompt)
                if not url_match:
                    return jsonify({
                        "success": False,
                        "error": "No valid URL found in prompt"
                    })
                
                url = url_match.group(0)
                description = user_prompt
                
                print(f"🌐 Scraping URL: {url}")
                
                # Add timeout to prevent hanging
                import threading
                from functools import partial
                
                result = {"success": False, "error": "Timeout"}
                
                def scrape_with_timeout():
                    nonlocal result
                    result = current_executor.scrape_website_data(url, description)
                
                # Create and start thread
                thread = threading.Thread(target=scrape_with_timeout)
                thread.start()
                thread.join(timeout=30)  # 30 second timeout
                
                if thread.is_alive():
                    # If thread is still running after timeout
                    print("⚠️ Scraping timeout - taking too long")
                    return jsonify({
                        "success": False,
                        "error": "Scraping timeout - operation took too long"
                    })
                    
                if result.get("success"):
                    return jsonify({
                        "success": True,
                        "type": "scrape",
                        "data": result.get("data", {}),
                        "message": "Content scraped successfully"
                    })
                else:
                    return jsonify({
                        "success": False,
                        "error": result.get("error", "Failed to scrape content")
                    })
                    
            except Exception as e:
                print(f"❌ Scraping error: {str(e)}")
                return jsonify({
                    "success": False,
                    "error": f"Failed to scrape content: {str(e)}"
                })
        
        # Generate steps with timeout
        print("🔄 Generating steps from Gemini...")
        try:
            steps = get_steps_from_gemini(user_prompt, current_api_key)
            if not steps:
                print("❌ No steps generated")
                return jsonify({"success": False, "message": "Could not generate execution steps"})
            print(f"✅ Generated {len(steps)} steps")
        except Exception as e:
            print(f"❌ Error generating steps: {str(e)}")
            return jsonify({"success": False, "message": f"Error generating steps: {str(e)}"})
        
        # Execute steps with timeout and progress tracking
        execution_id = str(uuid.uuid4())
        log = []
        
        print(f"🚀 Starting execution (ID: {execution_id})")
        for i, step in enumerate(steps, 1):
            try:
                action = step.get('action', 'unknown')
                print(f"\n▶️ Executing step {i}/{len(steps)}: {action}")
                
                success = current_executor.execute_step(step)
                log_message = f"Step {i}: {action} - {'Success' if success else 'Failed'}"
                log.append(log_message)
                print(f"{'✅' if success else '❌'} {log_message}")
                
                if not success:
                    print(f"⚠️ Step {i} failed, stopping execution")
                    break;
                    
            except Exception as e:
                error_msg = f"Step {i}: {action} - Error: {str(e)}"
                log.append(error_msg)
                print(f"❌ {error_msg}")
                break
        
        execution_logs.extend(log)
        
        print(f"\n🏁 Execution completed (ID: {execution_id})")
        return jsonify({
            "success": True,
            "execution_id": execution_id,
            "steps_executed": len(log),
            "steps_total": len(steps),
            "log": log,
            "message": f"Executed {len(log)} of {len(steps)} steps"
        })
        
    except Exception as e:
        error_message = f"Execution failed: {str(e)}"
        print(f"❌ {error_message}")
        return jsonify({
            "success": False, 
            "error": error_message
        })

@app.route('/api/workflows', methods=['GET'])
def list_workflows():
    global current_executor, current_api_key
    
    try:
        if not current_executor:
            current_executor = ActionExecutor(api_key=current_api_key)
        
        workflows = current_executor.list_workflows()
        return jsonify({
            "success": True,
            "workflows": workflows
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/workflow/record/start', methods=['POST'])
def start_recording():
    """Start recording a workflow"""
    global current_executor, current_api_key
    
    try:
        data = request.json
        name = data.get('name', 'untitled_workflow')
        
        print(f"🎬 Starting workflow recording: {name}")
        
        if not current_executor:
            current_executor = ActionExecutor(api_key=current_api_key)
        
        # Make sure workflow recorder is properly initialized
        if not hasattr(current_executor, 'workflow_recorder'):
            from workflow_recorder import WorkflowRecorder
            current_executor.workflow_recorder = WorkflowRecorder()
        
        success = current_executor.workflow_recorder.start_recording(name)
        
        if success:
            print(f"✅ Recording started successfully: {name}")
            return jsonify({
                "success": True,
                "message": f"Recording started: {name}"
            })
        else:
            print(f"❌ Failed to start recording: {name}")
            return jsonify({
                "success": False,
                "error": "Failed to start recording"
            })
            
    except Exception as e:
        print(f"❌ Error starting recording: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/workflow/record/stop', methods=['POST'])
def stop_recording():
    """Stop recording workflow"""
    global current_executor
    
    try:
        print("🛑 Stop recording request received")
        
        if not current_executor:
            print("❌ No executor available")
            return jsonify({
                "success": False, 
                "message": "No executor available",
                "error": "No active recording session"
            })
        
        if not hasattr(current_executor, 'workflow_recorder'):
            print("❌ No workflow recorder available")
            return jsonify({
                "success": False,
                "message": "No workflow recorder available",
                "error": "No recording system initialized"
            })
        
        # Check if actually recording
        if not current_executor.workflow_recorder.is_recording():
            print("⚠️ No active recording found")
            return jsonify({
                "success": True,  # Not an error, just already stopped
                "message": "No active recording to stop",
                "filename": None
            })
        
        print("📝 Attempting to stop recording...")
        filename = current_executor.workflow_recorder.stop_recording()
        
        # Give a moment to cleanup
        time.sleep(0.5)
        
        # Verify recording actually stopped
        if current_executor.workflow_recorder.is_recording():
            print("⚠️ Recording still active, forcing stop...")
            current_executor.workflow_recorder.force_stop()
            
        if filename:
            print(f"✅ Recording stopped successfully: {filename}")
            return jsonify({
                "success": True,
                "filename": filename,
                "message": f"Recording saved: {filename}"
            })
        else:
            print("⚠️ Recording stopped but no file saved")
            return jsonify({
                "success": True,
                "message": "Recording stopped (no actions recorded)",
                "filename": None
            })
            
    except Exception as e:
        print(f"❌ Error stopping recording: {str(e)}")
        
        # Force cleanup on error
        try:
            if current_executor and hasattr(current_executor, 'workflow_recorder'):
                current_executor.workflow_recorder.force_stop()
        except:
            pass
            
        return jsonify({
            "success": False,
            "error": str(e),
            "message": f"Error stopping recording: {str(e)}"
        })

@app.route('/api/workflow/record/force-stop', methods=['POST'])
def force_stop_recording():
    """Force stop recording (emergency cleanup)"""
    global current_executor
    
    try:
        if current_executor and hasattr(current_executor, 'workflow_recorder'):
            current_executor.workflow_recorder.force_stop()
            return jsonify({
                "success": True,
                "message": "Recording force stopped"
            })
        else:
            return jsonify({
                "success": True,
                "message": "No recorder to stop"
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/workflow/record/status', methods=['GET'])
def get_recording_status():
    """Get current recording status"""
    global current_executor
    
    try:
        if not current_executor or not hasattr(current_executor, 'workflow_recorder'):
            return jsonify({
                "recording": False,
                "workflow_name": None,
                "actions_count": 0,
                "duration": 0
            })
        
        status = current_executor.workflow_recorder.get_recording_status()
        return jsonify(status)
        
    except Exception as e:
        return jsonify({
            "recording": False,
            "error": str(e)
        })

@app.route('/api/screenshot', methods=['POST'])
def take_screenshot():
    global current_executor, current_api_key
    
    try:
        if not current_executor:
            current_executor = ActionExecutor(api_key=current_api_key)
        
        current_executor.take_screenshot("api_screenshot.png")
        return jsonify({
            "success": True,
            "screenshot_path": "api_screenshot.png"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/screen/analyze', methods=['POST'])
def analyze_screen():
    """Analyze current screen with AI"""
    global current_executor, current_api_key
    
    try:
        data = request.json
        prompt = data.get('prompt', 'Analyze this screen')
        
        if not current_api_key:
            return jsonify({"success": False, "message": "API key required"})
        
        if not current_executor:
            current_executor = ActionExecutor(api_key=current_api_key)
        
        result = current_executor.analyze_screen_with_ai(prompt)
        
        return jsonify({
            "success": True,
            "analysis": result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/chat', methods=['POST'])
def chat_with_ai():
    """Chat with AI assistant"""
    global current_executor, current_api_key
    
    try:
        data = request.json
        message = data.get('message')
        
        if not message:
            return jsonify({"success": False, "message": "Message required"})
        
        if not current_api_key:
            return jsonify({"success": False, "message": "API key required"})
        
        if not current_executor:
            current_executor = ActionExecutor(api_key=current_api_key)
        
        result = current_executor.chat_with_assistant(message)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/test', methods=['GET'])
def test_api():
    """Test if the API is working"""
    return jsonify({
        "success": True,
        "message": "API is working!",
        "timestamp": str(uuid.uuid4())
    })

@app.route('/api/test-gemini', methods=['POST'])
def test_gemini_connection():
    """Test Gemini API connection without saving the key"""
    try:
        data = request.json
        api_key = data.get('api_key')
        
        if not api_key:
            return jsonify({
                "success": False,
                "error": "API key required for testing"
            })
        
        print(f"🧪 Testing Gemini connection with key: {api_key[:10]}...")
        
        # Configure Gemini temporarily
        genai.configure(api_key=api_key.strip())
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Simple test
        response = model.generate_content("Say: Connection test successful")
        
        return jsonify({
            "success": True,
            "response": response.text if response else "No response",
            "message": "Gemini connection test completed"
        })
        
    except Exception as e:
        print(f"🧪 Gemini test failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

# Visual Detection Endpoints
@app.route('/api/visual/detect-buttons', methods=['POST'])
def detect_buttons():
    """Detect buttons on current screen"""
    global current_executor
    
    try:
        if not current_executor:
            current_executor = ActionExecutor(api_key=current_api_key)
        
        result = current_executor.visual_detector.find_buttons_advanced()
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/visual/detect-elements', methods=['POST'])
def detect_elements():
    """Detect UI elements on screen"""
    global current_executor
    
    try:
        data = request.json
        element_types = data.get('element_types', ['buttons', 'text_fields'])
        
        if not current_executor:
            current_executor = ActionExecutor(api_key=current_api_key)
        
        result = current_executor.screen_analyzer.detect_ui_elements(element_types)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/visual/find-by-color', methods=['POST'])
def find_by_color():
    """Find elements by color"""
    global current_executor
    
    try:
        data = request.json
        color_range = data.get('color_range', {"lower": [100, 50, 50], "upper": [130, 255, 255]})
        
        if not current_executor:
            current_executor = ActionExecutor(api_key=current_api_key)
        
        result = current_executor.visual_detector.find_element_by_color(color_range)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/visual/extract-text', methods=['POST'])
def extract_text_ocr():
    """Extract text from screen using OCR"""
    global current_executor
    
    try:
        if not current_executor:
            current_executor = ActionExecutor(api_key=current_api_key)
        
        result = current_executor.screen_analyzer.extract_text_from_screen()
        return jsonify({
            "success": True,
            "text": result.get("text", ""),
            "confidence": result.get("confidence", 0)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# Web Scraping Endpoints
@app.route('/api/web/scrape', methods=['POST'])
def scrape_website():
    """Scrape website using AI"""
    global current_executor, current_api_key
    
    try:
        data = request.json
        url = data.get('url')
        description = data.get('description')
        
        if not url or not description:
            return jsonify({"success": False, "error": "URL and description required"})
        
        if not current_api_key:
            return jsonify({"success": False, "error": "API key required"})
        
        if not current_executor:
            current_executor = ActionExecutor(api_key=current_api_key)
        
        result = current_executor.scrape_website_data(url, description)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/web/analyze', methods=['POST'])
def analyze_website():
    """Analyze website structure"""
    global current_executor, current_api_key
    
    try:
        data = request.json
        url = data.get('url')
        
        if not url:
            return jsonify({"success": False, "error": "URL required"})
        
        if not current_api_key:
            return jsonify({"success": False, "error": "API key required"})
        
        if not current_executor:
            current_executor = ActionExecutor(api_key=current_api_key)
        
        # Use web scraper to analyze structure
        if not current_executor.web_scraper.start_browser():
            return jsonify({"success": False, "error": "Failed to start browser"})
        
        try:
            # Navigate and get page info
            if current_executor.web_scraper.smart_navigate(url):
                page_title = current_executor.web_scraper.driver.title
                page_source = current_executor.web_scraper.driver.page_source[:2000]  # First 2000 chars
                
                return jsonify({
                    "success": True,
                    "url": url,
                    "title": page_title,
                    "content_preview": page_source,
                    "message": "Website analyzed successfully"
                })
            else:
                return jsonify({"success": False, "error": "Failed to navigate to URL"})
        finally:
            current_executor.web_scraper.close()
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == "__main__":
    print("🚀 Starting AI Assistant API...")
    print("📝 Available endpoints:")
    print("   - GET  /api/api-key-status")
    print("   - POST /api/validate-api-key")
    print("   - POST /api/clear-api-key")
    print("   - POST /api/execute")
    print("   - GET  /api/workflows")
    print("   - POST /api/screenshot")
    print("   - POST /api/chat")
    print("🌐 Frontend should connect to: http://localhost:8000")
    app.run(host="0.0.0.0", port=8000, debug=True)

