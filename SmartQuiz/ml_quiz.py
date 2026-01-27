"""
ML-Based Quiz Generation System with Progressive UI
"""

import streamlit as st
import json
import random
import sys
from pathlib import Path

# Add current directory to path for imports
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

class MLQuizInterface:
    def __init__(self):
        try:
            from ml_model import MLQuizGenerator
            self.quiz_gen = MLQuizGenerator()
            self.init_session_state()
        except ImportError as e:
            st.error(f"❌ Failed to load ML model: {str(e)}")
            st.info("Please ensure `ml_model.py` is in the same directory.")
            raise
    
    def init_session_state(self):
        """Initialize session state variables"""
        if 'ml_selected_sem' not in st.session_state:
            st.session_state.ml_selected_sem = None
        if 'ml_selected_subject' not in st.session_state:
            st.session_state.ml_selected_subject = None
        if 'ml_selected_topics' not in st.session_state:
            st.session_state.ml_selected_topics = []
        if 'ml_difficulty' not in st.session_state:
            st.session_state.ml_difficulty = None
        if 'ml_questions' not in st.session_state:
            st.session_state.ml_questions = []
        if 'ml_current_q' not in st.session_state:
            st.session_state.ml_current_q = 0
        if 'ml_answers' not in st.session_state:
            st.session_state.ml_answers = {}
        if 'ml_quiz_started' not in st.session_state:
            st.session_state.ml_quiz_started = False
        if 'ml_show_results' not in st.session_state:
            st.session_state.ml_show_results = False
        if 'ml_step' not in st.session_state:
            st.session_state.ml_step = 1  # Track current step

    def render_selection_page(self):
        """Render semester, subject, topic, and difficulty selection"""
        st.markdown("*Select your semester, subject, topics, and difficulty level*")
        
        # Step 1 & 2: Semester and Subject (shown together initially)
        if st.session_state.ml_step <= 2:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📚 Step 1: Select Semester")
                semesters = [f"Sem {i}" for i in range(1, 9)]
                selected_sem = st.selectbox(
                    "Choose your semester",
                    ["Select Semester..."] + semesters,
                    key="sem_select_ml"
                )
                
                if selected_sem != "Select Semester...":
                    st.session_state.ml_selected_sem = selected_sem
                    st.success(f"✅ {selected_sem} selected")
                else:
                    st.session_state.ml_selected_sem = None
            
            with col2:
                if st.session_state.ml_selected_sem:
                    st.markdown("#### 📖 Step 2: Select Subject")
                    subjects = self.quiz_gen.get_subjects(st.session_state.ml_selected_sem)
                    
                    if subjects:
                        selected_subject = st.selectbox(
                            "Choose your subject",
                            ["Select Subject..."] + subjects,
                            key="subject_select_ml"
                        )
                        
                        if selected_subject != "Select Subject...":
                            st.session_state.ml_selected_subject = selected_subject
                            st.success(f"✅ {selected_subject} selected")
                            # Automatically move to Step 3
                            st.session_state.ml_step = 3
                            st.rerun()
                        else:
                            st.session_state.ml_selected_subject = None
                    else:
                        st.warning("⚠️ No subjects found. Please train the model first.")
            
            # Back button at bottom for Step 1 & 2
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                 if st.button("⬅️ BACK TO MODE SELECTION", use_container_width=True):
                    self.reset_quiz()
                    st.session_state.quiz_state['quiz_mode'] = ''
                    st.rerun()
        
        # Step 3: Topic Selection (replaces Step 1 & 2)
        elif st.session_state.ml_step == 3:
            # Show selected semester and subject as info
            st.info(f"📚 **Semester:** {st.session_state.ml_selected_sem}  |  📖 **Subject:** {st.session_state.ml_selected_subject}")
            
            st.markdown("---")
            
            # Header with Select All button
            header_col1, header_col2 = st.columns([3, 1])
            with header_col1:
                st.markdown("#### 📝 Step 3: Select Topics (Choose 10-15 topics)")
            with header_col2:
                if st.button("✅ Select All Topics", use_container_width=True, key="select_all_btn"):
                    st.session_state.ml_all_topics_selected = True
                    st.rerun()
            
            topics = self.quiz_gen.get_topics(
                st.session_state.ml_selected_sem,
                st.session_state.ml_selected_subject
            )
            
            if topics:
                # Initialize flag if not exists
                if 'ml_all_topics_selected' not in st.session_state:
                    st.session_state.ml_all_topics_selected = False
                
                st.markdown("*Check the boxes to select topics*")
                cols = st.columns(3)
                selected_topics = []
                
                for idx, topic in enumerate(topics):
                    with cols[idx % 3]:
                        default_value = st.session_state.ml_all_topics_selected or (topic in st.session_state.ml_selected_topics)
                        if st.checkbox(topic, key=f"topic_ml_{idx}", value=default_value):
                            selected_topics.append(topic)
                
                # Reset the flag after rendering
                if st.session_state.ml_all_topics_selected:
                    st.session_state.ml_all_topics_selected = False
                
                st.session_state.ml_selected_topics = selected_topics
                
                # Show selected count with progress
                topic_count = len(selected_topics)
                st.markdown("---")
                
                if topic_count == 0:
                    st.info("📌 Please select 10-15 topics to continue")
                elif topic_count < 10:
                    st.warning(f"⚠️ Selected: {topic_count}/10 topics (Minimum 10 required)")
                elif topic_count <= 15:
                    st.success(f"✅ Perfect! Selected: {topic_count} topics")
                else:
                    st.error(f"❌ Too many! Selected: {topic_count}/15 topics (Maximum 15 allowed)")
                
                # Navigation buttons at bottom
                nav_col1, nav_col2 = st.columns(2)
                with nav_col1:
                    if st.button("⬅️ Back", use_container_width=True):
                        st.session_state.ml_step = 1
                        st.rerun()
                
                with nav_col2:
                    if 10 <= topic_count <= 15:
                        if st.button("➡️ Continue", use_container_width=True, type="primary"):
                            st.session_state.ml_step = 4
                            st.rerun()
                
                # # Back to Learning Modes button
                # st.markdown("---")
                # if st.button("🏠 Back to Learning Modes", use_container_width=True, type="secondary", key="back_step3"):
                #     self.reset_quiz()
                #     st.session_state.quiz_state['quiz_mode'] = ''
                #     st.rerun()
            else:
                st.warning("⚠️ No topics found for this subject.")
        
        # Step 4: Difficulty Selection
        elif st.session_state.ml_step == 4:
            # Show previous selections
            st.info(f"📚 **Semester:** {st.session_state.ml_selected_sem}  |  📖 **Subject:** {st.session_state.ml_selected_subject}  |  📝 **Topics:** {len(st.session_state.ml_selected_topics)} selected")
            
            st.markdown("---")
            st.markdown("#### 🎯 Step 4: Select Difficulty Level")
            
            difficulty_cols = st.columns(3)
            
            with difficulty_cols[0]:
                if st.button("🟢 Easy", use_container_width=True, 
                           type="primary" if st.session_state.ml_difficulty == "Easy" else "secondary"):
                    st.session_state.ml_difficulty = "Easy"
                    st.rerun()
                st.caption("Basic concepts & definitions")
            
            with difficulty_cols[1]:
                if st.button("🟡 Medium", use_container_width=True,
                           type="primary" if st.session_state.ml_difficulty == "Medium" else "secondary"):
                    st.session_state.ml_difficulty = "Medium"
                    st.rerun()
                st.caption("Application & analysis")
            
            with difficulty_cols[2]:
                if st.button("🔴 Hard", use_container_width=True,
                           type="primary" if st.session_state.ml_difficulty == "Hard" else "secondary"):
                    st.session_state.ml_difficulty = "Hard"
                    st.rerun()
                st.caption("Complex problem-solving")
            
            if st.session_state.ml_difficulty:
                st.success(f"✅ Difficulty: {st.session_state.ml_difficulty}")
            # else:
            #     # st.info("👆 Please select a difficulty level to continue")
            
            # Navigation buttons at bottom
            # st.markdown("---")
            # nav_col1, nav_col2 = st.columns(2)
            
            # with nav_col1:
            #     if st.button("⬅️ Back", use_container_width=True):
            #         st.session_state.ml_step = 3
            #         st.rerun()
            
            # with nav_col2:
            if st.session_state.ml_difficulty:
                    if st.button("🚀 Generate Quiz", use_container_width=True, type="primary"):
                        with st.spinner(f"🤖 AI is generating {st.session_state.ml_difficulty} level questions..."):
                            try:
                                questions = self.quiz_gen.generate_questions(
                                    st.session_state.ml_selected_sem,
                                    st.session_state.ml_selected_subject,
                                    st.session_state.ml_selected_topics,
                                    st.session_state.ml_difficulty
                                )
                                
                                if questions:
                                    st.session_state.ml_questions = questions
                                    st.session_state.ml_quiz_started = True
                                    st.session_state.ml_current_q = 0
                                    st.session_state.ml_answers = {}
                                    st.success(f"✅ Generated {len(questions)} {st.session_state.ml_difficulty} questions!")
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to generate questions. Please try again.")
                            except Exception as e:
                                st.error(f"❌ Error generating quiz: {str(e)}")
            
            # # Back to Learning Modes button
            # st.markdown("---")
            # if st.button("🏠 Back to Learning Modes", use_container_width=True, type="secondary", key="back_step4"):
            #     self.reset_quiz()
            #     st.session_state.quiz_state['quiz_mode'] = ''
            #     st.rerun()

    def render_quiz_page(self):
        """Render quiz questions with difficulty indicator"""
        questions = st.session_state.ml_questions
        current = st.session_state.ml_current_q
        
        if current >= len(questions):
            st.session_state.ml_show_results = True
            st.rerun()
            return
        
        q = questions[current]
        
        # Progress bar
        progress = (current + 1) / len(questions)
        st.progress(progress)
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(f"**Question {current + 1} of {len(questions)}**")
        with col2:
            difficulty_emoji = {"Easy": "🟢", "Medium": "🟡", "Hard": "🔴"}
            st.markdown(f"**{difficulty_emoji.get(st.session_state.ml_difficulty, '⚪')} {st.session_state.ml_difficulty}**")
        with col3:
            st.markdown(f"**Progress: {int(progress*100)}%**")
        
        st.markdown("---")
        
        # Question Display
        st.markdown(f"### Q{current + 1}. {q['question']}")
        st.caption(f"📚 Topic: {q['topic']}")
        st.markdown("")
        
        # Options
        st.markdown("#### Select your answer:")
        answer_key = f"q_ml_{current}"
        previous_answer = st.session_state.ml_answers.get(current, None)
        
        answer = st.radio(
            "Choose one:",
            q['options'],
            key=answer_key,
            index=q['options'].index(previous_answer) if previous_answer in q['options'] else 0,
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Navigation
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if current > 0:
                if st.button("⬅️ Previous", use_container_width=True):
                    st.session_state.ml_current_q -= 1
                    st.rerun()
        
        with col2:
            if st.button("💾 Save & Continue", use_container_width=True, type="primary"):
                st.session_state.ml_answers[current] = answer
                if current < len(questions) - 1:
                    st.session_state.ml_current_q += 1
                    st.rerun()
                else:
                    st.session_state.ml_show_results = True
                    st.rerun()
        
        with col3:
            if current < len(questions) - 1:
                if st.button("Next ➡️", use_container_width=True):
                    if answer:
                        st.session_state.ml_answers[current] = answer
                    st.session_state.ml_current_q += 1
                    st.rerun()
            else:
                if st.button("🏁 Finish Quiz", use_container_width=True, type="primary"):
                    if answer:
                        st.session_state.ml_answers[current] = answer
                    st.session_state.ml_show_results = True
                    st.rerun()
        
        st.markdown("---")
        answered = len(st.session_state.ml_answers)
        st.info(f"📝 Answered: {answered}/{len(questions)} questions")

    def render_results_page(self):
        """Render results with detailed solutions"""
        questions = st.session_state.ml_questions
        answers = st.session_state.ml_answers
        
        # Calculate score
        correct = 0
        for idx, q in enumerate(questions):
            if idx in answers and answers[idx] == q['correct_answer']:
                correct += 1
        
        score_percent = (correct / len(questions)) * 100
        
        # Header
        st.markdown("## 🎉 Quiz Completed!")
        st.markdown("---")
        
        # Score Display
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("📊 Total Questions", len(questions))
        with col2:
            st.metric("✅ Correct", correct)
        with col3:
            st.metric("❌ Incorrect", len(questions) - correct)
        with col4:
            difficulty_emoji = {"Easy": "🟢", "Medium": "🟡", "Hard": "🔴"}
            st.metric("🎯 Difficulty", f"{difficulty_emoji.get(st.session_state.ml_difficulty, '⚪')} {st.session_state.ml_difficulty}")
        with col5:
            st.metric("📈 Score", f"{score_percent:.1f}%")
        
        st.markdown("---")
        
        # Performance Badge
        if score_percent >= 90:
            st.success("🌟 **Outstanding Performance!** You've mastered this topic!")
        elif score_percent >= 75:
            st.success("🎉 **Great Job!** You have a strong understanding!")
        elif score_percent >= 60:
            st.info("👍 **Good Effort!** Keep practicing to improve!")
        elif score_percent >= 40:
            st.warning("📚 **Fair Attempt!** Review the concepts and try again!")
        else:
            st.error("💪 **Keep Learning!** Practice more to build your knowledge!")
        
        # Detailed Solutions
        st.markdown("---")
        st.markdown("## 📋 Detailed Solutions & Explanations")
        
        for idx, q in enumerate(questions):
            user_answer = answers.get(idx, "Not answered")
            correct_answer = q['correct_answer']
            is_correct = user_answer == correct_answer
            
            with st.expander(
                f"{'✅' if is_correct else '❌'} Question {idx + 1}: {q['question'][:70]}...",
                expanded=(not is_correct)
            ):
                st.markdown(f"### {q['question']}")
                st.caption(f"📚 Topic: {q['topic']}")
                st.markdown("---")
                
                st.markdown("#### Options:")
                for opt in q['options']:
                    if opt == correct_answer:
                        st.success(f"✅ **{opt}** ← Correct Answer")
                    elif opt == user_answer and not is_correct:
                        st.error(f"❌ **{opt}** ← Your Answer")
                    else:
                        st.markdown(f"⚪ {opt}")
                
                st.markdown("---")
                if is_correct:
                    st.success("✅ Your answer is correct!")
                else:
                    st.error(f"❌ Your answer was incorrect.")
                
                st.markdown("---")
                st.markdown("#### 💡 Explanation:")
                st.info(q['explanation'])
        
        #Action buttons
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Take Another ML Quiz", use_container_width=True, type="primary"):
                self.reset_quiz()
                st.rerun()
        
        with col2:
            if st.button("🏠 Back to Home", use_container_width=True):
                self.reset_quiz()
                st.session_state.quiz_state['quiz_mode'] = ''
                st.rerun()

    def reset_quiz(self):
        """Reset quiz state"""
        st.session_state.ml_selected_sem = None
        st.session_state.ml_selected_subject = None
        st.session_state.ml_selected_topics = []
        st.session_state.ml_difficulty = None
        st.session_state.ml_questions = []
        st.session_state.ml_current_q = 0
        st.session_state.ml_answers = {}
        st.session_state.ml_quiz_started = False
        st.session_state.ml_show_results = False
        st.session_state.ml_step = 1

    def render(self):
        """Main render method"""
        if st.session_state.ml_show_results:
            self.render_results_page()
        elif st.session_state.ml_quiz_started:
            self.render_quiz_page()
        else:
            self.render_selection_page()
    
    
def show_ml_quiz():
    """Main function to display ML quiz"""
    try:
        interface = MLQuizInterface()
        interface.render()
    except Exception as e:
        st.error(f"❌ Error initializing ML quiz: {str(e)}")
        st.info("Please check that all required files are present.")


