import streamlit as st
import speech_recognition as sr
from gtts import gTTS
import os
import tempfile
from datetime import datetime
import requests
import pygame
import time
from typing import List, Dict, Optional


class MockInterviewSystem:
    """Complete Mock Interview System with voice and AI integration"""
    
    def __init__(self, groq_api_key: str):
        self.groq_api_key = groq_api_key
        self.groq_api_url = "https://api.groq.com/openai/v1/chat/completions"
        
        self.available_models = {
            "llama-3.3-70b-versatile": "Llama 3.3 70B (Best)",
            "llama-3.1-8b-instant": "Llama 3.1 8B (Fastest)",
            "mixtral-8x7b-32768": "Mixtral 8x7B",
            "gemma2-9b-it": "Gemma 2 9B"
        }
        
        self.difficulty_guidelines = {
            "Easy": """
- Ask fundamental concepts and basic definitions
- Focus on simple applications and understanding
- Example: "What is a list in Python?" or "Explain what HTTP means" or "Difference between list and tuple?"
- Suitable for beginners or freshers
""",
            "Medium": """
- Ask about practical applications and problem-solving
- Include scenario-based questions
- Example: "How would you optimize a slow database query?" or "Explain the difference between INNER JOIN and LEFT JOIN with a use case" or "How do you handle exceptions in Python? Explain with an example."
- Suitable for intermediate developers
""",
            "Hard": """
- Ask about system design, scalability, and advanced concepts
- Include complex problem-solving scenarios
- Example: "Design a distributed caching system"
- Suitable for senior developers
"""
        }
    
    def initialize_session_state(self):
        """Initialize all session state variables"""
        defaults = {
            'interview_started': False,
            'conversation_history': [],
            'user_interests': None,
            'question_count': 0,
            'current_question': None,
            'selected_model': "llama-3.3-70b-versatile",
            'question_read': False,
            'first_answer_received': False,
            'auto_submitted': False,
            'difficulty_level': "Medium",
            'max_questions': 5
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    def call_groq_api(self, prompt: str, system_prompt: str = "You are a helpful AI assistant.") -> Optional[str]:
        """Call Groq API for chat completion"""
        try:
            if not self.groq_api_key:
                st.error("❌ API key missing!")
                return None
            
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": st.session_state.selected_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1024
            }
            
            response = requests.post(self.groq_api_url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            else:
                return None
                
        except Exception as e:
            return None
    
    def extract_user_interests(self, answer: str) -> Optional[str]:
        """Extract technical interests from candidate's introduction"""
        try:
            prompt = f"""Analyze this candidate's introduction and identify their technical interests and skills:

"{answer}"

Extract ONLY the key technical areas/technologies they mentioned (like Python, Machine Learning, React, Data Science, etc.).
Return as a comma-separated list of 3-5 main topics. Be specific and technical.

Format: topic1, topic2, topic3"""

            system_prompt = "You are an expert at analyzing candidate profiles and identifying technical skills."
            response = self.call_groq_api(prompt, system_prompt)
            return response
        except:
            return None
    
    def text_to_speech_and_play(self, text: str) -> bool:
        """Convert text to speech and auto-play it"""
        try:
            tts = gTTS(text=text, lang='en', slow=False)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
                temp_path = fp.name
                tts.save(temp_path)
            
            pygame.mixer.init()
            pygame.mixer.music.load(temp_path)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            pygame.mixer.music.unload()
            pygame.mixer.quit()
            
            try:
                os.unlink(temp_path)
            except:
                pass
                
            return True
            
        except Exception as e:
            return False
    
    def speech_to_text_with_timeout(self) -> str:
        """Record speech with 5 second silence timeout"""
        recognizer = sr.Recognizer()
        
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 2.0
        recognizer.phrase_time_limit = 120
        
        status_placeholder = st.empty()
        
        try:
            with sr.Microphone() as source:
                status_placeholder.markdown("""
                <div style='text-align: center; padding: 40px 0;'>
                    <div style='font-size: 150px; line-height: 1; animation: pulse 2s infinite;'>🎤</div>
                    <h2 style='margin-top: 20px; color: #ff4b4b;'>Recording...</h2>
                    <p style='color: #666; font-size: 14px;'>⚡ No voice in 5 sec → Auto Skip</p>
                </div>
                <style>
                    @keyframes pulse {
                        0%, 100% { transform: scale(1); }
                        50% { transform: scale(1.1); }
                    }
                </style>
                """, unsafe_allow_html=True)
                
                recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=120)
                
                status_placeholder.markdown("""
                <div style='text-align: center; padding: 40px 0;'>
                    <div style='font-size: 100px;'>💾</div>
                    <h3 style='color: #00cc00;'>Processing...</h3>
                </div>
                """, unsafe_allow_html=True)
            
            # Try recognition with multiple languages
            try:
                text = recognizer.recognize_google(audio, language="en-IN")
            except:
                try:
                    text = recognizer.recognize_google(audio, language="hi-IN")
                except:
                    try:
                        text = recognizer.recognize_google(audio, language="gu-IN")
                    except:
                        text = recognizer.recognize_google(audio)
            
            status_placeholder.empty()
            return text
            
        except sr.WaitTimeoutError:
            status_placeholder.empty()
            return "NO_ANSWER_TIMEOUT"
        except sr.UnknownValueError:
            status_placeholder.empty()
            return "NO_ANSWER_UNCLEAR"
        except Exception as e:
            status_placeholder.empty()
            return "NO_ANSWER_ERROR"
    
    def get_ai_question(self, conversation_history: List[Dict], question_count: int, 
                       user_interests: Optional[str], difficulty: str) -> str:
        """Generate next interview question"""
        try:
            if question_count == 0:
                return "Tell me about yourself and what areas of technology you're most interested in?"
            
            difficulty_guide = self.difficulty_guidelines.get(difficulty, self.difficulty_guidelines["Medium"])
            
            if question_count == 1 and user_interests:
                prompt = f"""The candidate mentioned these interests: {user_interests}

Difficulty Level: {difficulty}
{difficulty_guide}

Ask ONE relevant technical question based on their interests at {difficulty} level.
Keep it conversational. Only ONE question, no extra text."""
                
                system_prompt = "You are an expert technical interviewer."
                response = self.call_groq_api(prompt, system_prompt)
                return response
            
            else:
                context = "\n".join([
                    f"Q: {item['question']}\nA: {item['answer']}" 
                    for item in conversation_history[-3:]
                ])
                
                interests_context = f"\nCandidate's interests: {user_interests}" if user_interests else ""
                
                prompt = f"""You are conducting a technical interview.{interests_context}

Difficulty Level: {difficulty}
{difficulty_guide}

Recent conversation:
{context}

Ask the next relevant question at {difficulty} level. ONE clear question only."""
                
                system_prompt = "You are an expert technical interviewer."
                response = self.call_groq_api(prompt, system_prompt)
                return response
        
        except:
            return "Tell me about a challenging technical problem you solved recently?"
    
    def get_final_summary(self, conversation_history: List[Dict], 
                         user_interests: Optional[str], difficulty: str) -> str:
        """Generate comprehensive interview assessment"""
        try:
            qa_context = []
            for i, item in enumerate(conversation_history, 1):
                qa_context.append(f"Q{i}: {item['question']}\nA{i}: {item['answer']}")
            
            context = "\n\n".join(qa_context)
            interests_context = f"\nFocus: {user_interests}" if user_interests else ""
            
            prompt = f"""Technical Interview Assessment - {difficulty} Level{interests_context}

{context}

Provide assessment considering this was a {difficulty} level interview:

# QUESTION-BY-QUESTION FEEDBACK
For each question, give:
- Technical accuracy (for {difficulty} level)
- Strengths
- Improvements needed
- Rating (/10)

# OVERALL ASSESSMENT
1. Performance Summary (considering {difficulty} level expectations)
2. Top Strengths (3-4)
3. Areas to Develop (3-4)
4. Communication Skills
5. Recommendations for next steps
6. Final Score (/10)

Be concise and actionable."""
            
            system_prompt = "You are an expert technical interviewer."
            response = self.call_groq_api(prompt, system_prompt)
            return response
        
        except:
            return "Assessment could not be generated. Please try again."
    
    def render_setup_screen(self):
        """Render interview setup/configuration screen"""
        st.markdown("### 📊 Interview Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            difficulty = st.selectbox(
                "Difficulty Level",
                ["Easy", "Medium", "Hard"],
                index=1,
                help="Choose question difficulty"
            )
            
            if difficulty == "Easy":
                st.info("🟢 **Easy**: Basic concepts, suitable for beginners")
            elif difficulty == "Medium":
                st.warning("🟡 **Medium**: Practical problems, intermediate level")
            else:
                st.error("🔴 **Hard**: Advanced topics, senior level")
        
        with col2:
            max_questions = st.selectbox(
                "Number of Questions",
                options=list(range(3, 11)),
                index=2
            )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🚀 Start Interview", type="primary", use_container_width=True):
            st.session_state.interview_started = True
            st.session_state.max_questions = max_questions
            st.session_state.difficulty_level = difficulty
            st.session_state.question_count = 0
            st.session_state.conversation_history = []
            st.session_state.current_question = None
            st.session_state.user_interests = None
            st.session_state.first_answer_received = False
            st.session_state.question_read = False
            st.session_state.auto_submitted = False
            st.rerun()
        
        # st.info("👈 Select difficulty level and click 'Start Interview' to begin!")
    
    def render_interview_screen(self):
        """Render active interview screen"""
        if st.session_state.question_count < st.session_state.max_questions:
            # Generate question if needed
            if st.session_state.current_question is None:
                with st.spinner("⚡ Loading question..."):
                    question = self.get_ai_question(
                        st.session_state.conversation_history,
                        st.session_state.question_count,
                        st.session_state.user_interests,
                        st.session_state.difficulty_level
                    )
                    if question:
                        st.session_state.current_question = question
                        st.session_state.question_read = False
                        st.session_state.auto_submitted = False
                        st.rerun()
            
            # Display and process current question
            if st.session_state.current_question:
                st.markdown(f"### Q{st.session_state.question_count + 1}: {st.session_state.current_question}")
                
                # Read question aloud (once)
                if not st.session_state.question_read:
                    with st.spinner("🔊"):
                        self.text_to_speech_and_play(st.session_state.current_question)
                    st.session_state.question_read = True
                    st.rerun()
                
                st.markdown("---")
                
                # Auto-record answer
                if not st.session_state.auto_submitted:
                    answer = self.speech_to_text_with_timeout()
                    
                    # Handle timeout or error
                    if answer and answer.startswith("NO_ANSWER"):
                        st.session_state.conversation_history.append({
                            "question": st.session_state.current_question,
                            "answer": "[No answer provided]",
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        
                        st.warning("⏩ Skipped - Moving to next question")
                        time.sleep(1)
                        
                        st.session_state.question_count += 1
                        st.session_state.current_question = None
                        st.session_state.question_read = False
                        st.session_state.auto_submitted = False
                        st.rerun()
                    
                    # Valid answer received
                    elif answer:
                        st.session_state.conversation_history.append({
                            "question": st.session_state.current_question,
                            "answer": answer,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        
                        # Extract interests from first answer
                        if st.session_state.question_count == 0 and not st.session_state.first_answer_received:
                            interests = self.extract_user_interests(answer)
                            if interests:
                                st.session_state.user_interests = interests
                            st.session_state.first_answer_received = True
                        
                        st.success("✅ Answer saved!")
                        time.sleep(0.5)
                        
                        st.session_state.question_count += 1
                        st.session_state.current_question = None
                        st.session_state.question_read = False
                        st.session_state.auto_submitted = False
                        st.rerun()
        
        else:
            self.render_results_screen()
    
    def render_results_screen(self):
        """Render interview results and feedback"""
        st.success("🎉 Interview Complete!")
        st.balloons()
        
        with st.spinner("⚡ Generating comprehensive feedback..."):
            summary = self.get_final_summary(
                st.session_state.conversation_history,
                st.session_state.user_interests,
                st.session_state.difficulty_level
            )
            
            if summary:
                st.markdown("## 📋 Complete Assessment")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.session_state.user_interests:
                        st.info(f"🎯 Focus: {st.session_state.user_interests}")
                with col2:
                    diff_color = {"Easy": "🟢", "Medium": "🟡", "Hard": "🔴"}
                    st.info(f"{diff_color.get(st.session_state.difficulty_level, '🟡')} Level: {st.session_state.difficulty_level}")
                
                st.markdown(summary)
        
        st.markdown("---")
        st.markdown("## 💾 Transcript")
        
        for i, item in enumerate(st.session_state.conversation_history, 1):
            with st.expander(f"Q{i}: {item['question'][:40]}..."):
                st.markdown(f"**Q:** {item['question']}")
                st.markdown(f"**A:** {item['answer']}")
                st.caption(item['timestamp'])
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 New Interview", type="primary", use_container_width=True):
                st.session_state.interview_started = False
                st.session_state.question_count = 0
                st.session_state.conversation_history = []
                st.session_state.current_question = None
                st.session_state.user_interests = None
                st.session_state.first_answer_received = False
                st.session_state.question_read = False
                st.session_state.auto_submitted = False
                st.rerun()
        
        with col2:
            transcript = self.generate_transcript()
            st.download_button(
                label="📥 Download",
                data=transcript,
                file_name=f"interview_{st.session_state.difficulty_level}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )
    
    def generate_transcript(self) -> str:
        """Generate downloadable transcript"""
        transcript = f"""Interview Transcript
Difficulty: {st.session_state.difficulty_level}
Focus: {st.session_state.user_interests or 'General'}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{"="*50}

"""
        transcript += "\n\n".join([
            f"Q{i+1}: {item['question']}\n\nA{i+1}: {item['answer']}\n{'-'*50}"
            for i, item in enumerate(st.session_state.conversation_history)
        ])
        
        return transcript
    
   
    def add_back_to_home_button(self):
        """Add a floating back to home button on the left side"""

        st.markdown("""
        <style>
        .back-to-home-btn {
            position: fixed;
            left: 20px;
            top: 20px;
            z-index: 9999;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 24px;
            border-radius: 50px;
            text-decoration: none;
            font-weight: 600;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            transition: all 0.3s ease;
            cursor: pointer;
            border: none;
            font-size: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .back-to-home-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }
        
        .back-to-home-btn:active {
            transform: translateY(0px);
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Create the button
        if st.button("⬅️ Back to Home", key="back_home_btn", help="Return to main dashboard"):
            st.session_state.page = 'home'
            st.rerun()
    def run(self):
        """Main method to run the mock interview system"""
        self.add_back_to_home_button()

        st.title("🎤 AI Mock Interview")
        st.markdown("**⚡ Fast & Smart Interview** - Quick response based on your interests!")

        self.initialize_session_state()
        
        if not st.session_state.interview_started:
            self.render_setup_screen()
            st.markdown("<br>", unsafe_allow_html=True)
        else:
            self.render_interview_screen()
            
            
    # def add_back_to_home_button(self):
    #     """Floating back button"""
    #     st.markdown("""
    #     <style>
    #     .back-btn {
    #         position: fixed;
    #         left: 20px;
    #         top: 20px;
    #         z-index: 9999;
    #         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    #         color: white;
    #         padding: 10px 20px;
    #         border-radius: 30px;
    #         font-weight: 600;
    #         box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    #         transition: all 0.3s ease;
    #     }
        
    #     .back-btn:hover {
    #         transform: translateY(-2px);
    #         box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    #     }
    #     </style>
    #     """, unsafe_allow_html=True)
        
    #     if st.button("⬅️ Home", key="back_btn"):
    #         st.session_state.page = 'home'
    #         st.rerun()
    
    