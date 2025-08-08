# -*- coding: utf-8 -*-
"""
LinkedIn Jobs Skills Analyzer Streamlit Chat Interface
AI-powered chatbot với tích hợp các tool phân tích skills và hiển thị chart

Usage:
    streamlit run streamlit_chat.py
"""

import json
import os
import sys
import tempfile
from datetime import datetime
from typing import Dict, List, Any
import streamlit as st
import pandas as pd
from io import BytesIO
import ast



# Fix import errors for tools modules
import sys
import os
tools_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools")
if tools_path not in sys.path:
    sys.path.append(tools_path)

try:
    from chatbot_class import SkillsAnalyzerChatbot
except ImportError as e:
    st.error(f"⚠️ Import error: {e}")
    st.error("Make sure all required files are in the same directory")
    st.stop()

# Load environment variables
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

class StreamlitSkillsAnalyzerChatbot:
    def __init__(self):
        if not API_KEY:
            st.error("❌ GEMINI_API_KEY not found in environment variables")
            st.stop()
        
        # Initialize the main chatbot class with verbose mode for detailed output
        self.chatbot = SkillsAnalyzerChatbot(verbose=True)
        
        # Initialize session state
        if 'conversation_history' not in st.session_state:
            st.session_state.conversation_history = []
        if 'session_active' not in st.session_state:
            st.session_state.session_active = True
        if 'show_debug_info' not in st.session_state:
            st.session_state.show_debug_info = False

    

    def display_message(self, message: str) -> None:
        """
        Displays a message in Streamlit chat interface.

        Args:
            message (str): The message string to display.

        Returns:
            None
        """
        st.chat_message("assistant").write(message)

    def end_session(self) -> None:
        """
        Ends the chatbot session by setting session_active to False.

        Args:
            None

        Returns:
            None
        """
        st.session_state.session_active = False
        st.chat_message("assistant").write("👋 Session ended. Refresh the page to start a new conversation!")

    def create_test_chart(self, data_json: str, chart_type: str = "bar", 
                         title: str = "Test Chart") -> None:
        """
        Creates and displays a test chart directly in Streamlit.

        Args:
            data_json (str): Dictionary data as JSON string.
            chart_type (str): Type of chart ("bar", "pie", "line").
            title (str): Title of the chart.

        Returns:
            None
        """
        chart_buffer = self.create_chart_from_data(
            data_json, 
            chart_type=chart_type,
            title=title,
            xlabel="Categories",
            ylabel="Values"
        )
        if chart_buffer.getvalue():  # Check if buffer has data
            # Store chart in session state to persist after button clicks
            chart_key = f"chart_{title}_{chart_type}"
            st.session_state[chart_key] = chart_buffer.getvalue()
            
            # Display small chart with download and expand options
            st.image(chart_buffer, caption=f"{title} - {chart_type.title()} Chart", width=400)
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Download button
                st.download_button(
                    label="📥 Download Chart",
                    data=st.session_state[chart_key],
                    file_name=f"{title.replace(' ', '_').lower()}_{chart_type}.png",
                    mime="image/png"
                )
            
            with col2:
                # Expand button using button + session state
                if st.button("🔍 View Full Size", key=f"expand_btn_{title}"):
                    st.session_state[f"show_full_{title}"] = not st.session_state.get(f"show_full_{title}", False)
            
            # Show full size if toggled
            if st.session_state.get(f"show_full_{title}", False):
                st.markdown("**Full Size Chart:**")
                st.image(BytesIO(st.session_state[chart_key]), caption=f"{title} - Full Size", use_column_width=True)
        else:
            st.error("❌ Failed to create chart")

    def display_skills_chart(self, data_json: str, analysis_type: str) -> None:
        """
        Displays chart for skills analysis data.

        Args:
            data_json (str): Skills analysis data from tools as JSON string.
            analysis_type (str): Type of analysis to determine chart format.

        Returns:
            None
        """
        try:
            data = json.loads(data_json)
        except:
            st.error("❌ Invalid data format for chart display")
            return
            
        if not data.get("success"):
            st.error(f"❌ {data.get('message', 'Analysis failed')}")
            return
        
        result = data["data"]
        
        if analysis_type == "all_skills" and result.get('top_skills'):
            # Create bar chart for top skills
            skills_data = {}
            for skill in result['top_skills'][:10]:
                skills_data[skill['skill']] = float(skill['frequency'])
            
            chart_buffer = self.create_chart_from_data(
                json.dumps(skills_data), 
                chart_type="bar",
                title="Top 10 Most In-Demand Skills",
                xlabel="Skills",
                ylabel="Number of Jobs"
            )
            
            # Display chart with controls
            if chart_buffer.getvalue():
                # Store chart in session state
                st.session_state["chart_top_skills"] = chart_buffer.getvalue()
                
                st.image(chart_buffer, caption="Top Skills Analysis", width=400)
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.download_button(
                        label="📥 Download Chart",
                        data=st.session_state["chart_top_skills"],
                        file_name="top_skills_analysis.png",
                        mime="image/png"
                    )
                
                with col2:
                    if st.button("🔍 View Full Size", key="expand_top_skills"):
                        st.session_state["show_full_top_skills"] = not st.session_state.get("show_full_top_skills", False)
                
                # Show full size if toggled
                if st.session_state.get("show_full_top_skills", False):
                    st.markdown("**Full Size Chart:**")
                    st.image(BytesIO(st.session_state["chart_top_skills"]), caption="Top Skills Analysis - Full Size", use_column_width=True)
            else:
                st.error("❌ Failed to create top skills chart")
        
        elif analysis_type == "hot_skills" and result.get('hot_skills'):
            # Create pie chart for hot skills
            hot_skills_data = {}
            for skill in result['hot_skills'][:8]:
                hot_skills_data[skill['skill']] = float(skill['frequency'])
            
            chart_buffer = self.create_chart_from_data(
                json.dumps(hot_skills_data),
                chart_type="pie", 
                title="Hot Skills Distribution - Last Month"
            )
            
            # Display chart with controls
            if chart_buffer.getvalue():
                # Store chart in session state
                st.session_state["chart_hot_skills"] = chart_buffer.getvalue()
                
                st.image(chart_buffer, caption="Hot Skills Distribution", width=400)
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.download_button(
                        label="📥 Download Chart",
                        data=st.session_state["chart_hot_skills"],
                        file_name="hot_skills_distribution.png",
                        mime="image/png"
                    )
                
                with col2:
                    if st.button("🔍 View Full Size", key="expand_hot_skills"):
                        st.session_state["show_full_hot_skills"] = not st.session_state.get("show_full_hot_skills", False)
                
                # Show full size if toggled
                if st.session_state.get("show_full_hot_skills", False):
                    st.markdown("**Full Size Chart:**")
                    st.image(BytesIO(st.session_state["chart_hot_skills"]), caption="Hot Skills Distribution - Full Size", use_column_width=True)
            else:
                st.error("❌ Failed to create hot skills chart")
        
        elif analysis_type == "category_skills":
            # Create multiple charts for different categories
            for cat_key, cat_info in result.items():
                if cat_info.get('skills') and len(cat_info['skills']) > 0:
                    cat_data = {}
                    for skill in cat_info['skills'][:5]:
                        cat_data[skill['skill']] = float(skill['frequency'])
                    
                    if cat_data:
                        chart_buffer = self.create_chart_from_data(
                            json.dumps(cat_data),
                            chart_type="bar",
                            title=f"Top Skills in {cat_info['name']}",
                            xlabel="Skills",
                            ylabel="Frequency"
                        )
                        
                        # Display chart with controls
                        if chart_buffer.getvalue():
                            # Store chart in session state
                            chart_key = f"chart_{cat_key}"
                            st.session_state[chart_key] = chart_buffer.getvalue()
                            
                            st.image(chart_buffer, caption=f"{cat_info['name']} Skills", width=400)
                            
                            col1, col2 = st.columns([1, 1])
                            
                            with col1:
                                st.download_button(
                                    label="📥 Download Chart",
                                    data=st.session_state[chart_key],
                                    file_name=f"{cat_info['name'].replace(' ', '_').lower()}_skills.png",
                                    mime="image/png",
                                    key=f"download_{cat_key}"
                                )
                            
                            with col2:
                                if st.button("🔍 View Full Size", key=f"expand_{cat_key}"):
                                    st.session_state[f"show_full_{cat_key}"] = not st.session_state.get(f"show_full_{cat_key}", False)
                            
                            # Show full size if toggled
                            if st.session_state.get(f"show_full_{cat_key}", False):
                                st.markdown("**Full Size Chart:**")
                                st.image(BytesIO(st.session_state[chart_key]), caption=f"{cat_info['name']} Skills - Full Size", use_column_width=True)
                        else:
                            st.error(f"❌ Failed to create {cat_info['name']} chart")

    def format_skills_response(self, data_json: str, analysis_type: str) -> str:
        """
        Format the analysis results for chatbot response.

        Args:
            data_json (str): Analysis data from tools as JSON string.
            analysis_type (str): Type of analysis performed.

        Returns:
            str: Formatted response string.
        """
        try:
            data = json.loads(data_json)
        except:
            return "❌ Invalid data format for response formatting"
            
        if not data.get("success"):
            return f"❌ {data.get('message', 'Analysis failed')}"
        
        result = data["data"]
        
        if analysis_type == "all_skills":
            response = f"📊 **GENERAL SKILLS ANALYSIS**\n\n"
            response += f"📈 Total jobs analyzed: {result.get('total_jobs', 0)}\n"
            response += f"📋 Jobs with skills info: {result.get('valid_jobs', 0)}\n"
            response += f"🔍 Unique skills found: {result.get('total_unique_skills', 0)}\n\n"
            
            response += "🏆 **TOP SKILLS:**\n"
            for i, skill in enumerate(result.get('top_skills', [])[:10], 1):
                response += f"{i:2d}. {skill['skill']} - {skill['frequency']} jobs ({skill['percentage']}%)\n"
        
        elif analysis_type == "hot_skills":
            response = f"🔥 **HOT SKILLS - LAST MONTH**\n\n"
            response += f"📅 Period: {result.get('period', 'Recent')}\n"
            response += f"📊 Jobs analyzed: {result.get('total_recent_jobs', 0)}\n\n"
            
            response += "🚀 **TOP HOT SKILLS:**\n"
            for i, skill in enumerate(result.get('hot_skills', [])[:10], 1):
                fire_level = "🔥" * min(int(skill['percentage_of_valid'] / 10) + 1, 5)
                response += f"{i:2d}. {skill['skill']} - {skill['frequency']} jobs ({skill['percentage_of_valid']:.1f}%) {fire_level}\n"
        
        elif analysis_type == "category_skills":
            response = f"📂 **SKILLS BY CATEGORY**\n\n"
            for cat_key, cat_info in result.items():
                if cat_info.get('skills'):
                    response += f"🔸 **{cat_info['name']}:**\n"
                    for skill in cat_info['skills'][:5]:
                        response += f"   • {skill['skill']} - {skill['frequency']} jobs\n"
                    response += "\n"
        
        elif analysis_type == "trends":
            response = f"📈 **SKILLS TRENDS ANALYSIS**\n\n"
            response += f"📅 Period: {result.get('analysis_period', 'Recent')}\n"
            response += f"📊 Total jobs: {result.get('total_jobs_in_period', 0)}\n\n"
            
            response += "🏆 **TOP TRENDING SKILLS:**\n"
            for i, (skill, count) in enumerate(result.get('top_skills_overall', [])[:10], 1):
                response += f"{i:2d}. {skill} - {count} mentions\n"
        
        elif analysis_type == "job_categories":
            response = f"💼 **SKILLS BY JOB CATEGORIES**\n\n"
            for category, data in result.items():
                response += f"🔹 **{category}** ({data['job_count']} jobs):\n"
                for skill, count in data['top_skills'][:5]:
                    response += f"   • {skill}: {count}\n"
                response += "\n"
        
        return response

    def chat(self, user_message: str) -> str:
        """
        Main chat function using the SkillsAnalyzerChatbot class with a refined UI.
        The Thinking Process is always shown, while Debug Info is optional.
        """
        try:
            # Capture stdout to show thinking and tool processes
            import io
            import contextlib
            
            # Create a string buffer to capture print output
            captured_output = io.StringIO()
            
            # Use the main chatbot class for processing
            with contextlib.redirect_stdout(captured_output):
                chat_result = self.chatbot.chat(user_message)
            
            # Store result for process display
            st.session_state.last_chat_result = chat_result
            
            # Get captured output
            debug_output = captured_output.getvalue()
            
            # Handle the structured response
            if not isinstance(chat_result, dict):
                clean_response = str(chat_result)
            else:
                if not chat_result.get("success", False):
                    clean_response = chat_result.get("final_response", "❌ Error processing request")
                    if "error" in chat_result:
                        clean_response += f"\nError details: {chat_result['error']}"
                else:
                    clean_response = chat_result.get("final_response", "🤖 No response generated")
                    
                    # Handle career advisor mode responses
                    if chat_result.get("career_mode", False) or st.session_state.career_advisor_mode:
                        # Check if response contains career advisor tool results
                        process_sequence = chat_result.get("process_sequence", [])
                        has_career_tool_result = any(
                            step.get("type") == "tool_result" and step.get("tool_name") == "career_advisor_tool"
                            for step in process_sequence
                        )
                        
                        if has_career_tool_result:
                            st.success("✅ **Career Advisor đã phân tích xong:**")
                            
                            # Find career tool result
                            for step in process_sequence:
                                if (step.get("type") == "tool_result" and 
                                    step.get("tool_name") == "career_advisor_tool" and 
                                    step.get("success", False)):
                                    
                                    # Try to parse career advisor result
                                    try:
                                        import ast
                                        tool_result = step.get("result", "")
                                        
                                        # If result is a string representation of dict, parse it
                                        if isinstance(tool_result, str) and tool_result.startswith("{"):
                                            career_result = ast.literal_eval(tool_result)
                                            
                                            # Extract final response from career advisor
                                            career_response = career_result.get("final_response", "")
                                            
                                            # Try to parse JSON from career response
                                            if career_response:
                                                try:
                                                    import json
                                                    json_response = json.loads(career_response)
                                                    
                                                    if json_response.get("status") == "input_required":
                                                        st.info("💡 **Cần thêm thông tin:**")
                                                        st.write(json_response.get("message", ""))
                                                        if json_response.get("next_questions"):
                                                            st.markdown("**Gợi ý câu hỏi:**")
                                                            for q in json_response["next_questions"]:
                                                                st.markdown(f"• {q}")
                                                    
                                                    elif json_response.get("career_recommendations"):
                                                        recs = json_response["career_recommendations"]
                                                        
                                                        if recs.get("personality_analysis"):
                                                            st.markdown("**🧠 Phân tích tính cách:**")
                                                            st.write(recs["personality_analysis"])
                                                        
                                                        if recs.get("recommended_skills"):
                                                            st.markdown("**🛠️ Kỹ năng đề xuất:**")
                                                            for skill in recs["recommended_skills"][:5]:
                                                                st.markdown(f"• {skill}")
                                                        
                                                        if recs.get("career_paths"):
                                                            st.markdown("**💼 Lộ trình nghề nghiệp:**")
                                                            for path in recs["career_paths"][:3]:
                                                                st.markdown(f"• {path}")
                                                        
                                                        if recs.get("market_insights"):
                                                            st.markdown("**📊 Thông tin thị trường:**")
                                                            for insight in recs["market_insights"][:3]:
                                                                st.markdown(f"• {insight}")
                                                
                                                except json.JSONDecodeError:
                                                    # Display as raw text if not JSON
                                                    pass
                                    
                                    except (ValueError, SyntaxError):
                                        # If parsing fails, display raw result
                                        pass
                        
                    # Display thinking process (for both modes)
                    process_sequence = chat_result.get("process_sequence", [])
                    if process_sequence:
                        process_title = "🎯 **Career Analysis Process**" if st.session_state.career_advisor_mode else "🧠 **Thinking Process**"
                        with st.expander(f"{process_title} ({len(process_sequence)} steps)", expanded=False):
                            self._display_process_sequence(process_sequence)

                    # Check for chart data in tool results (only for skills analyzer mode)
                    if not st.session_state.career_advisor_mode:
                        self._check_and_display_charts(chat_result)
            
            # --- CHANGE 3: The "Raw Backend Response" expander has been completely removed. ---

            # --- CHANGE 4: This block correctly remains inside the debug 'if' condition. ---
            # It will only appear when the "Show Debug Info" checkbox is ticked.
            if st.session_state.get('show_debug_info', True) and debug_output.strip():
                with st.expander("🔍 **Debug Information** (Console Output)", expanded=False):
                    self._display_debug_output(debug_output)
            
            # Store conversation in Streamlit session state (only clean response)
            st.session_state.conversation_history.append(f"User: {user_message}")
            st.session_state.conversation_history.append(f"Assistant: {clean_response}")
            
            return clean_response
            
        except Exception as e:
            error_msg = f"❌ Error processing your request: {str(e)}"
            st.session_state.conversation_history.append(f"User: {user_message}")
            st.session_state.conversation_history.append(f"Assistant: {error_msg}")
            return error_msg
    
    def _check_and_display_charts(self, chat_result: Dict[str, Any]) -> None:
        """
        Check for chart data in chat result and display charts using Streamlit.
        """
        try:
            print("[STREAMLIT_DEBUG] Calling _check_and_display_charts...")
            process_sequence = chat_result.get("process_sequence", [])
            
            for step in process_sequence:
                print(f"[STREAMLIT_DEBUG] Inspecting process step of type: {step.get('type')}")

                if step.get("type") == "tool_result" and step.get("success"):
                    result_str = step.get("result")
                    
                    # --- START OF THE FIX ---
                    # The tool result is a string representation of a Python dict.
                    # We use ast.literal_eval() to safely parse it back into a dictionary.
                    if isinstance(result_str, str):
                        try:
                            # Use ast.literal_eval for Python dict strings
                            result = ast.literal_eval(result_str)
                            print("[STREAMLIT_DEBUG] Successfully parsed tool result string using ast.literal_eval()")
                        except (ValueError, SyntaxError):
                            print(f"[STREAMLIT_DEBUG] Could not parse tool result string: {result_str[:100]}...")
                            continue # Skip to the next step if parsing fails
                    else:
                        # If it's already a dict, just use it
                        result = result_str
                    # --- END OF THE FIX ---

                    # Now 'result' is a proper dictionary, and this check will work
                    if (isinstance(result, dict) and 
                        result.get("chart_data") is not None and 
                        result.get("chart_type") is not None):
                        
                        print("[STREAMLIT_DEBUG] FOUND A VALID CHART TO DISPLAY in tool result!")
                        self._display_streamlit_chart(result) # This will now be called
                        
        except Exception as e:
            st.warning(f"⚠️ A failure occurred in _check_and_display_charts: {str(e)}")
            print(f"[STREAMLIT_ERROR] in _check_and_display_charts: {e}")
    
    def _display_streamlit_chart(self, result: Dict[str, Any]) -> None:
        """
        Displays a chart with a dynamic title based on the analysis type.
        This version correctly unpacks data serialized with pandas' .to_dict('split').
        """
        try:
            chart_data_dict = result.get("chart_data")
            
            # --- START OF THE FIX ---
            # 1. Get the summary dictionary provided by the tool.
            summary = result.get("summary", {})
            # 2. Get the specific analysis type from the summary. Default to "Analysis Trend".
            analysis_type = summary.get("analysis_type", "Analysis Trend")
            # --- END OF THE FIX ---

            # Validation: Check if chart data exists.
            if chart_data_dict is None:
                st.warning("📊 No chart data was received from the tool.")
                return

            # Conversion: Reconstruct the DataFrame from the clean dictionary.
            chart_data = pd.DataFrame(
                chart_data_dict['data'],
                index=pd.to_datetime(chart_data_dict['index']),
                columns=chart_data_dict['columns']
            )

            # --- USE THE DYNAMIC TITLE ---
            # 3. Display the chart with the dynamic title from the summary.
            st.subheader(f"📈 {analysis_type} (Last 4 Weeks)")
            st.line_chart(chart_data)

        except Exception as e:
            # Basic error handling in case the reconstruction or display fails.
            st.error(f"❌ Failed to display the chart. Error: {e}")
            print(f"[STREAMLIT_ERROR] A failure occurred in _display_streamlit_chart: {e}")
    
    def _display_process_sequence(self, process_sequence: List[Dict[str, Any]]) -> None:
        """
        Display the structured process sequence in Streamlit.

        Args:
            process_sequence (List[Dict[str, Any]]): Process sequence from chatbot

        """
        for i, step in enumerate(process_sequence, 1):
            step_type = step.get("type", "unknown")
            timestamp = step.get("timestamp", "")
            
            # Create a clean timestamp display
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime("%H:%M:%S")
                except:
                    time_str = timestamp[-8:] if len(timestamp) >= 8 else timestamp
            else:
                time_str = ""
            
            if step_type == "thought":
                with st.container():
                    st.success(f"🧠 **THOUGHT** ({time_str})")
                    content = step.get('content', '')
                    if content:
                        st.write(content)
                    if step.get('thought_signature'):
                        st.caption(f"Signature: {step.get('thought_signature')}")
                        
            elif step_type == "tool_call":
                with st.container():
                    st.warning(f"🛠️ **TOOL CALL** ({time_str})")
                    st.write(f"**Tool:** {step.get('tool_name', '')}")
                    tool_args = step.get('tool_args', {})
                    if tool_args:
                        st.json(tool_args)
                        
            elif step_type == "tool_result":
                with st.container():
                    success = step.get('success', False)
                    if success:
                        st.success(f"📊 **TOOL RESULT** ({time_str})")
                    else:
                        st.error(f"❌ **TOOL ERROR** ({time_str})")
                    
                    st.write(f"**Tool:** {step.get('tool_name', '')}")
                    result = step.get('result', '')
                    
                    # Display result based on length and content
                    if len(str(result)) > 500:
                        with st.expander("View Result", expanded=False):
                            st.text(str(result))
                    else:
                        st.code(str(result))
                    
                    if not success and step.get('error'):
                        st.error(f"Error: {step.get('error')}")
                        
            elif step_type == "response":
                with st.container():
                    st.info(f"💬 **INTERMEDIATE RESPONSE** ({time_str})")
                    content = step.get('content', '')
                    if content:
                        st.write(content)
                        
            elif step_type == "final_response":
                with st.container():
                    st.success(f"🎯 **FINAL RESPONSE** ({time_str})")
                    content = step.get('content', '')
                    if content:
                        st.write(content)
                        
            elif step_type == "error":
                with st.container():
                    st.error(f"❌ **ERROR** ({time_str})")
                    st.write(step.get('content', ''))
                    if step.get('error'):
                        st.code(step.get('error'), language='text')
            
            # Add separator between steps (except for last step)
            if i < len(process_sequence):
                st.write("---")

    def _clean_response_from_debug(self, response: str) -> str:
        """
        Remove debug information from response to get clean user-facing content.
        
        Args:
            response (str): Raw response from chatbot including debug info
            
        Returns:
            str: Clean response without debug information
        """
        if not response:
            return response
            
        lines = response.split('\n')
        clean_lines = []
        skip_line = False
        
        for line in lines:
            line_stripped = line.strip()
            
            # Skip debug-related lines
            if (line_stripped.startswith(('🧠 **THINKING:', '🧠 **THOUGHT:', '💬 **RESPONSE:', 
                                        '🔧 **Using tool:', '🔧 **TOOL USED:', 
                                        '📊 **Tool result', '📊 **TOOL RESULT',
                                        '🐍 **Executing code:', '🐍 **CODE EXECUTION:',
                                        '✅ **Code execution result:', '✅ **CODE RESULT:',
                                        '[Gemini Part Fields]', '🧠 Generating response')) or
                line_stripped.startswith('-' * 20) or
                line_stripped.startswith('Arguments:') or
                line_stripped.startswith('**Arguments:**')):
                skip_line = True
                continue
            
            # Reset skip flag if we encounter non-debug content
            if line_stripped and not any(line_stripped.startswith(prefix) for prefix in 
                                       ['🧠', '🔧', '📊', '🐍', '✅', '[Gemini', 'Arguments']):
                skip_line = False
            
            # Add line if not skipping
            if not skip_line and line_stripped:
                clean_lines.append(line)
        
        # Join and clean up extra whitespace
        clean_response = '\n'.join(clean_lines).strip()
        
        # Remove any remaining debug patterns
        import re
        clean_response = re.sub(r'🧠 \*\*ANALYSIS:\*\*.*?(?=\n\n|\Z)', '', clean_response, flags=re.DOTALL)
        clean_response = re.sub(r'🧠 \*\*PLAN:\*\*.*?(?=\n\n|\Z)', '', clean_response, flags=re.DOTALL)
        
        return clean_response.strip()
    
    def _display_debug_output(self, debug_output: str) -> None:
        """
        Display debug output in a structured way for Streamlit.
        
        Args:
            debug_output (str): Captured debug output from chatbot
        """
        lines = debug_output.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Parse different types of output
            if line.startswith('🧠 Generating response'):
                st.info(f"⚡ {line}")
            elif line.startswith('🧠 **THINKING:**') or line.startswith('🧠 **THOUGHT:**'):
                thinking_text = line.replace('🧠 **THINKING:** ', '').replace('🧠 **THOUGHT:** ', '')
                st.success(f"🧠 **THINKING:** {thinking_text}")
            elif line.startswith('💬 **RESPONSE:**'):
                response_text = line.replace('💬 **RESPONSE:** ', '')
                st.info(f"💬 **RESPONSE:** {response_text}")
            elif line.startswith('🔧 **Using tool:**'):
                tool_text = line.replace('🔧 **Using tool:** ', '')
                st.warning(f"🔧 **TOOL CALL:** {tool_text}")
            elif line.startswith('🛠️  MODEL YÊU CẦU GỌI TOOL:'):
                tool_text = line.replace('🛠️  MODEL YÊU CẦU GỌI TOOL: ', '')
                st.warning(f"🛠️ **TOOL REQUEST:** {tool_text}")
            elif line.startswith('Tham số:'):
                args_text = line.replace('Tham số: ', '')
                st.text(f"   📋 Parameters: {args_text}")
            elif line.startswith('   Arguments:'):
                args_text = line.replace('   Arguments: ', '')
                st.text(f"   📋 Arguments: {args_text}")
            elif line.startswith('📊 **Tool result:**'):
                result_text = line.replace('📊 **Tool result:** ', '')
                st.success(f"✅ **Tool Result:** {result_text}")
            elif line.startswith('📊 **Tool result from'):
                result_text = line
                st.success(f"✅ {result_text}")
            elif line.startswith('🧠 **FINAL RESPONSE:**'):
                st.success("🎯 **FINAL RESPONSE GENERATED**")
            elif line.startswith('[Gemini Part Fields]'):
                # Show Gemini part fields for debugging
                st.code(line, language='json')
            elif line.startswith('-' * 20):
                st.divider()
            elif line.startswith('❌'):
                st.error(line)
            else:
                # Regular debug output
                if line:
                    st.text(line)
    
    def set_debug_mode(self, enabled: bool) -> None:
        """Toggle debug information display"""
        st.session_state.show_debug_info = enabled
        self.chatbot.set_verbose_mode(enabled)
    
    def new_chat(self) -> None:
        """Start a new chat session"""
        self.chatbot.new_chat()
        st.session_state.conversation_history = []
        st.session_state.session_active = True
    
    def get_session_stats(self) -> dict:
        """Get current session statistics"""
        return self.chatbot.get_session_stats()
    
    def set_thinking_budget(self, budget: int) -> None:
        """Set thinking budget for the chatbot"""
        self.chatbot.set_thinking_budget(budget)
    
    def set_generation_preset(self, preset: str) -> None:
        """Set generation preset for the chatbot"""
        self.chatbot.set_generation_preset(preset)
    
    def display_conversation_with_debug(self) -> None:
        """Display conversation history with enhanced formatting"""
        for i, message in enumerate(st.session_state.conversation_history):
            if message.startswith("User: "):
                with st.chat_message("user"):
                    st.write(message[6:])
            elif message.startswith("Assistant: "):
                with st.chat_message("assistant"):
                    # Get clean response content
                    response_text = message[11:]
                    
                    # Display the clean response (debug info is shown separately)
                    if response_text.strip():
                        st.write(response_text)
                    else:
                        st.write("_No response content_")
    
    def _display_structured_response(self, response_text: str) -> None:
        """Display structured response with different sections"""
        lines = response_text.split('\n')
        current_section = None
        section_content = []
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('🧠 **THINKING:**'):
                if current_section:
                    self._render_section(current_section, section_content)
                current_section = "thinking"
                section_content = [line.replace('🧠 **THINKING:** ', '')]
            elif line.startswith('🔧 **TOOL'):
                if current_section:
                    self._render_section(current_section, section_content)
                current_section = "tool"
                section_content = [line]
            elif line.startswith('📊 **TOOL RESULT'):
                if current_section:
                    self._render_section(current_section, section_content)
                current_section = "result"
                section_content = [line]
            elif line and current_section:
                section_content.append(line)
            elif line and not current_section:
                # Regular text outside sections
                st.write(line)
        
        # Render final section
        if current_section:
            self._render_section(current_section, section_content)
    
    def _render_section(self, section_type: str, content: list) -> None:
        """Render a specific section with appropriate styling"""
        if section_type == "thinking":
            with st.expander("🧠 **Thinking Process**", expanded=False):
                for line in content:
                    st.write(line)
        elif section_type == "tool":
            with st.expander("🔧 **Tool Usage**", expanded=False):
                for line in content:
                    if line.startswith('**Arguments:**'):
                        st.code(line, language='json')
                    else:
                        st.write(line)
        elif section_type == "result":
            with st.expander("📊 **Tool Results**", expanded=False):
                for line in content:
                    st.write(line)

def _filter_response_for_display(response: str) -> str:
    """Filter out debug information from response for clean display"""
    lines = response.split('\n')
    filtered_lines = []
    
    for line in lines:
        # Skip debug lines
        if (line.strip().startswith(('🧠 **THINKING:', '🔧 **TOOL', '📊 **TOOL', 
                                    '[Gemini Part Fields]', '💬 **RESPONSE:')) or
            line.strip().startswith('-' * 20)):
            continue
        
        # Keep regular content
        if line.strip():
            filtered_lines.append(line)
    
    return '\n'.join(filtered_lines).strip()

def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="LinkedIn Jobs Skills Analyzer",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Title and description
    st.title("🤖 LinkedIn Jobs Skills Analyzer")
    st.markdown("""
<span style='font-size:2em'>👋</span> **Hi, I'm the LinkedIn Jobs Skills Analyzer Chatbot!** 🤖

<span style='font-size:1.2em'>✨ I am an AI-powered assistant designed to help you explore the job market and analyze skills trends.</span>

<span style='font-size:1.1em'>
I can:

- 🔍 **Search and analyze** the job market database
- 🧑 **Find jobs** that match your requirements
- 🤝 **Recommend jobs** based on your skills, industry, and position
- 📈 **Analyze and visualize** trending skills, job categories, and hiring trends
- 📊 **Display interactive charts** and statistics
- 💬 **Answer your questions** about job market data, skills, and trends
</span>

<span style='font-size:1.1em'>💡 Just type your questions or requests below and I'll get started!</span>
""", unsafe_allow_html=True)

    # Sidebar with help information and controls
    with st.sidebar:
        # Mode Selection Switch
        st.header("🎯 Chế độ hoạt động")
        
        # Initialize mode in session state if not exists
        if 'career_advisor_mode' not in st.session_state:
            st.session_state.career_advisor_mode = False
        
        # Mode toggle buttons
        col1, col2 = st.columns(2)
        
        with col1:
            skills_button_style = "primary" if not st.session_state.career_advisor_mode else "secondary"
            if st.button(
                "🔧 Skills Analyzer", 
                type=skills_button_style,
                help="Phân tích thị trường việc làm và kỹ năng",
                use_container_width=True
            ):
                st.session_state.career_advisor_mode = False
                if 'chatbot' in st.session_state:
                    st.session_state.chatbot.chatbot.toggle_career_advisor_mode(False)
                st.rerun()
        
        with col2:
            career_button_style = "primary" if st.session_state.career_advisor_mode else "secondary"
            if st.button(
                "🎯 Career Advisor", 
                type=career_button_style,
                help="Tư vấn nghề nghiệp cá nhân hóa",
                use_container_width=True
            ):
                st.session_state.career_advisor_mode = True
                if 'chatbot' in st.session_state:
                    st.session_state.chatbot.chatbot.toggle_career_advisor_mode(True)
                st.rerun()
        
        # Display current mode with styling
        current_mode = "Career Advisor" if st.session_state.career_advisor_mode else "Skills Analyzer"
        mode_emoji = "🎯" if st.session_state.career_advisor_mode else "🔧"
        mode_color = "#FF6B6B" if st.session_state.career_advisor_mode else "#4ECDC4"
        
        st.markdown(f"""
        <div style="
            background-color: {mode_color}20;
            border: 2px solid {mode_color};
            border-radius: 10px;
            padding: 10px;
            text-align: center;
            margin: 10px 0px;
        ">
            <strong>{mode_emoji} {current_mode} Mode</strong>
        </div>
        """, unsafe_allow_html=True)
        
        # Mode-specific help text
        if st.session_state.career_advisor_mode:
            st.markdown("""
            **🎯 Career Advisor Mode:**
            - Phân tích tính cách và sở thích
            - Tư vấn nghề nghiệp phù hợp
            - Lộ trình phát triển sự nghiệp
            - Đề xuất kỹ năng cần học
            
            *Ví dụ: "Tôi giỏi toán, thích công nghệ, muốn tư vấn nghề nghiệp"*
            """)
        else:
            st.markdown("""
            **🔧 Skills Analyzer Mode:**
            - Phân tích thị trường việc làm
            - Xu hướng kỹ năng hot
            - Thống kê ngành nghề
            - Biểu đồ và báo cáo
            
            *Ví dụ: "analyze trending skills", "top programming jobs"*
            """)
        
        st.divider()
        
        st.header("📋 Help & Commands")
        st.markdown("""
        **📊 General Analysis:**
        - "analyze all skills"
        - "most in-demand skills"
        - "top 10 hot jobs"

        **🔥 Hot Skills:**
        - "hot skills this month"  
        - "trending skills"

        **📂 Skills by Category:**
        - "programming skills"
        - "AI skills" 
        - "data science skills"
        - "cloud skills"

        **📈 Trends:**
        - "skills trends"
        - "what's trending"

        **💼 Job Categories:**
        - "job categories analysis"
        - "skills by job type"
        """)
        
        st.divider()
        
        # Chatbot controls
        st.header("⚙️ Chatbot Settings")
        
        # Debug mode toggle
        debug_mode = st.checkbox(
            "🔍 Show Debug Info",
            value=st.session_state.get('show_debug_info', True),
            help="Show thinking process, tool calls, and debug information"
        )
        if debug_mode != st.session_state.get('show_debug_info', True):
            st.session_state.chatbot.set_debug_mode(debug_mode)
        
        # Generation preset
        preset = st.selectbox(
            "Generation Mode:",
            ["balanced", "analytical", "focused", "creative"],
            index=0,
            help="Choose the AI generation style"
        )
        if st.button("Apply Preset"):
            st.session_state.chatbot.set_generation_preset(preset)
            st.success(f"Applied '{preset}' preset!")
        
        # Thinking budget
        thinking_budget = st.slider(
            "Thinking Budget (tokens):",
            min_value=1024,
            max_value=8192,
            value=4096,
            step=512,
            help="How much thinking the AI can do"
        )
        if st.button("Set Thinking Budget"):
            st.session_state.chatbot.set_thinking_budget(thinking_budget)
            st.success(f"Set thinking budget to {thinking_budget} tokens!")
        
        st.divider()
        
        # Session controls
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 New Chat"):
                st.session_state.chatbot.new_chat()
                st.session_state.conversation_history = []
                st.session_state.session_active = True
                st.rerun()
        
        with col2:
            if st.button("📊 Stats"):
                stats = st.session_state.chatbot.get_session_stats()
                st.info(f"Messages: {stats.get('total_messages', 0)}")
                st.info(f"Duration: {stats.get('session_duration', '0 minutes')}")
        
        # Show last process info if available
        if hasattr(st.session_state, 'last_chat_result') and st.session_state.last_chat_result:
            result = st.session_state.last_chat_result
            if result.get('success') and result.get('process_sequence'):
                st.divider()
                st.subheader("📋 Last Response Process")
                st.caption(f"Steps: {result.get('total_steps', 0)}")
                
                # Count different step types
                steps = result.get('process_sequence', [])
                thoughts = sum(1 for s in steps if s.get('type') == 'thought')
                tool_calls = sum(1 for s in steps if s.get('type') == 'tool_call')
                
                if thoughts > 0:
                    st.caption(f"🧠 Thoughts: {thoughts}")
                if tool_calls > 0:
                    st.caption(f"🛠️ Tool calls: {tool_calls}")
                    
                if st.button("🔍 View Details"):
                    with st.expander("Process Details", expanded=True):
                        st.session_state.chatbot._display_process_sequence(steps)
        
        if st.button("🗑️ Clear History"):
            st.session_state.conversation_history = []
            st.session_state.session_active = True
            st.rerun()

    # Initialize chatbot
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = StreamlitSkillsAnalyzerChatbot()
    
    # Sync chatbot mode with session state
    if hasattr(st.session_state.chatbot, 'chatbot'):
        current_chatbot_mode = st.session_state.chatbot.chatbot.is_career_advisor_mode()
        if current_chatbot_mode != st.session_state.career_advisor_mode:
            st.session_state.chatbot.chatbot.toggle_career_advisor_mode(st.session_state.career_advisor_mode)

    # Display chat history with enhanced formatting
    st.session_state.chatbot.display_conversation_with_debug()

    # Chat input
    if st.session_state.session_active:
        # Dynamic placeholder based on mode
        if st.session_state.career_advisor_mode:
            placeholder = "Ví dụ: 'Tôi giỏi toán, thích công nghệ, muốn tư vấn nghề nghiệp phù hợp...'"
        else:
            placeholder = "Ask me about job market skills and trends..."
            
        user_input = st.chat_input(placeholder)
        
        if user_input:
            # Display user message
            with st.chat_message("user"):
                st.write(user_input)
            
            # Process and display assistant response
            with st.chat_message("assistant"):
                with st.spinner("🤔 Analyzing your request..."):
                    response = st.session_state.chatbot.chat(user_input)
                
                # Display the clean response (debug info already shown separately)
                if response and response.strip():
                    st.write(response)
                else:
                    st.write("_No response generated_")
    else:
        st.info("Session ended. Click 'New Chat' to start a new conversation.")

    # Footer
    st.markdown("---")

if __name__ == "__main__":
    main()
