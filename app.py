"""
CareerIQ - Main Application
"""
import streamlit as st
import time
from PIL import Image
from datetime import datetime
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt
from docx import Document
import io
import base64
from SmartQuiz.aimockinterview import MockInterviewSystem
import plotly.graph_objects as go
from streamlit_lottie import st_lottie
import requests
from config.courses import COURSES_BY_CATEGORY, RESUME_VIDEOS, INTERVIEW_VIDEOS, get_courses_for_role, get_category_for_role
from config.job_roles import JOB_ROLES
from config.database import (
    get_database_connection, save_resume_data, save_analysis_data,
    init_database, verify_admin, log_admin_action, save_ai_analysis_data,
    get_ai_analysis_stats, reset_ai_analysis_stats, get_detailed_ai_analysis_stats
)
from ui_components import (
    apply_modern_styles, hero_section, feature_card, about_section,
    page_header, render_analytics_section, render_activity_section,
    render_suggestions_section
)

from jobs.job_search import render_job_search
from feedback.feedback import FeedbackManager
from dashboard.dashboard import DashboardManager
from utils.ai_resume_analyzer import AIResumeAnalyzer
from utils.resume_builder import ResumeBuilder
from utils.portfolio_builder import PortfolioBuilder
from utils.resume_analyzer import ResumeAnalyzer
from SmartQuiz.aimocktest import run_quiz 

import traceback
import plotly.express as px
import pandas as pd
import json
import datetime
from dotenv import load_dotenv
import os

load_dotenv()  # Load from .env file
google_api_key = os.getenv("GOOGLE_API_KEY")

if not google_api_key:
    raise Exception("Google API key not found. Please set it in your .env file.")


# Set page config at the very beginning
st.set_page_config(
    page_title="CareerIQ ",
    layout="wide"
)

class ResumeApp:
    def __init__(self):
        """Initialize the application"""
        if 'form_data' not in st.session_state:
            st.session_state.form_data = {
                'personal_info': {
                    'full_name': '',
                    'email': '',
                    'phone': '',
                    'location': '',
                    'linkedin': '',
                    'portfolio': ''
                },
                'summary': '',
                'experiences': [],
                'education': [],
                'projects': [],
                'skills_categories': {
                    'technical': [],
                    'soft': [],
                    'languages': [],
                    'tools': []
                }
            }

        # Initialize navigation state
        if 'page' not in st.session_state:
            st.session_state.page = 'home'

        # Initialize admin state
        if 'is_admin' not in st.session_state:
            st.session_state.is_admin = False

        self.pages = {
            "🏠 HOME": self.render_home,
            "📝 RESUME BUILDER": self.render_builder,
            "🔍 RESUME ANALYZER": self.render_analyzer,
            "🧩 SmartPrep AI ": self.render_quiz, 
            "📁 PORTFOLIO BUILDER": self.render_portfolio_builder,
            "🎯 JOB SEARCH": self.render_job_search,
            "📊 DASHBOARD": self.render_dashboard,
            "💬 FEEDBACK": self.render_feedback_page,


        }

        # Initialize dashboard manager
        self.dashboard_manager = DashboardManager()
        self.analyzer = ResumeAnalyzer()
        self.ai_analyzer = AIResumeAnalyzer()
        self.portfolio_builder = PortfolioBuilder()  # <-- ADD THIS

        self.builder = ResumeBuilder()
        self.job_roles = JOB_ROLES

        # Initialize session state
        if 'user_id' not in st.session_state:
            st.session_state.user_id = 'default_user'
        if 'selected_role' not in st.session_state:
            st.session_state.selected_role = None

        # Initialize database
        init_database()

        # Load external CSS
        with open('style/style.css') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

        # Load Google Fonts
        st.markdown("""
            <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&family=Poppins:wght@400;500;600&display=swap" rel="stylesheet">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
        """, unsafe_allow_html=True)

        if 'resume_data' not in st.session_state:
            st.session_state.resume_data = []
        if 'ai_analysis_stats' not in st.session_state:
            st.session_state.ai_analysis_stats = {
                'score_distribution': {},
                'total_analyses': 0,
                'average_score': 0
            }

    def load_lottie_url(self, url: str):
        """Load Lottie animation from URL"""
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    
    # Rest of your portfolio builder UI...
    def apply_global_styles(self):
        st.markdown("""
        <style>
        /* Custom Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: #1a1a1a;
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb {
            background: #4CAF50;
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #45a049;
        }

        /* Global Styles */
        .main-header {
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
            text-align: center;
            position: relative;
            overflow: hidden;
        }

        .main-header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(45deg, transparent 0%, rgba(255,255,255,0.1) 100%);
            z-index: 1;
        }

        .main-header h1 {
            color: white;
            font-size: 2.5rem;
            font-weight: 600;
            margin: 0;
            position: relative;
            z-index: 2;
        }

        /* Template Card Styles */
        .template-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 2rem;
            padding: 1rem;
        }

        .template-card {
            background: rgba(45, 45, 45, 0.9);
            border-radius: 20px;
            padding: 2rem;
            position: relative;
            overflow: hidden;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .template-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            border-color: #4CAF50;
        }

        .template-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(45deg, transparent 0%, rgba(76,175,80,0.1) 100%);
            z-index: 1;
        }

        .template-icon {
            font-size: 3rem;
            color: #4CAF50;
            margin-bottom: 1.5rem;
            position: relative;
            z-index: 2;
        }

        .template-title {
            font-size: 1.8rem;
            font-weight: 600;
            color: white;
            margin-bottom: 1rem;
            position: relative;
            z-index: 2;
        }

        .template-description {
            color: #aaa;
            margin-bottom: 1.5rem;
            position: relative;
            z-index: 2;
            line-height: 1.6;
        }

        /* Feature List Styles */
        .feature-list {
            list-style: none;
            padding: 0;
            margin: 1.5rem 0;
            position: relative;
            z-index: 2;
        }

        .feature-item {
            display: flex;
            align-items: center;
            margin-bottom: 1rem;
            color: #ddd;
            font-size: 0.95rem;
        }

        .feature-icon {
            color: #4CAF50;
            margin-right: 0.8rem;
            font-size: 1.1rem;
        }

        /* Button Styles */
        .action-button {
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            color: white;
            padding: 1rem 2rem;
            border-radius: 50px;
            border: none;
            font-weight: 500;
            cursor: pointer;
            width: 100%;
            text-align: center;
            position: relative;
            overflow: hidden;
            z-index: 2;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .action-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(76,175,80,0.3);
        }

        .action-button::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.2) 50%, transparent 100%);
            transition: all 0.6s ease;
        }

        .action-button:hover::before {
            left: 100%;
        }

        /* Form Section Styles */
        .form-section {
            background: rgba(45, 45, 45, 0.9);
            border-radius: 20px;
            padding: 2rem;
            margin: 2rem 0;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }

        .form-section-title {
            font-size: 1.8rem;
            font-weight: 600;
            color: white;
            margin-bottom: 1.5rem;
            padding-bottom: 0.8rem;
            border-bottom: 2px solid #4CAF50;
        }

        .form-group {
            margin-bottom: 1.5rem;
        }

        .form-label {
            color: #ddd;
            font-weight: 500;
            margin-bottom: 0.8rem;
            display: block;
        }

        .form-input {
            width: 100%;
            padding: 1rem;
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.1);
            background: rgba(30, 30, 30, 0.9);
            color: white;
            transition: all 0.3s ease;
        }

        .form-input:focus {
            border-color: #4CAF50;
            box-shadow: 0 0 0 2px rgba(76,175,80,0.2);
            outline: none;
        }

        /* Skill Tags */
        .skill-tag-container {
            display: flex;
            flex-wrap: wrap;
            gap: 0.8rem;
            margin-top: 1rem;
        }

        .skill-tag {
            background: rgba(76,175,80,0.1);
            color: #4CAF50;
            padding: 0.6rem 1.2rem;
            border-radius: 50px;
            border: 1px solid #4CAF50;
            font-size: 0.9rem;
            transition: all 0.3s ease;
            cursor: pointer;
        }

        .skill-tag:hover {
            background: #4CAF50;
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(76,175,80,0.2);
        }

        /* Progress Circle */
        .progress-container {
            position: relative;
            width: 150px;
            height: 150px;
            margin: 2rem auto;
        }

        .progress-circle {
            transform: rotate(-90deg);
            width: 100%;
            height: 100%;
        }

        .progress-circle circle {
            fill: none;
            stroke-width: 8;
            stroke-linecap: round;
            stroke: #4CAF50;
            transform-origin: 50% 50%;
            transition: all 0.3s ease;
        }

        .progress-text {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 1.5rem;
            font-weight: 600;
            color: white;
        }
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .feature-card {
            background-color: #1e1e1e;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        /* Animations */
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .animate-slide-in {
            animation: slideIn 0.6s cubic-bezier(0.4, 0, 0.2, 1) forwards;
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .template-container {
                grid-template-columns: 1fr;
            }

            .main-header {
                padding: 1.5rem;
            }

            .main-header h1 {
                font-size: 2rem;
            }

            .template-card {
                padding: 1.5rem;
            }

            .action-button {
                padding: 0.8rem 1.6rem;
            }
        }
        </style>
        """, unsafe_allow_html=True)
        
    def render_quiz(self):
        """Render the AI Quiz page"""
        try:
            # Add a header for consistency with your app
            apply_modern_styles()
            self.add_back_to_home_button()

    
        # Page Header
            page_header(
            "AI-Powered Quiz",
            "Choose your preferred learning experience and challenge yourself across various domains with our advanced assessment system."
        )
            st.markdown("""
    <style>
    /* Center align and style tab container */
    .stTabs [data-baseweb="tab-list"] {
        justify-content: center;
        margin-top: 20px;
        margin-bottom: 20px;
        gap: 10px;
    }

    /* Base style for each tab */
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f0f0;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 10px 24px;
        font-size: 16px;
        font-weight: 600;
        color: #333;
        transition: all 0.2s ease-in-out;
    }

    /* Hover effect */
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #e0f5ec;
        border-color: #00bfa5;
        color: #111;
        transform: translateY(-2px);
        cursor: pointer;
    }

    /* Selected/active tab style */
    .stTabs [aria-selected="true"] {
        background-color: #00bfa5 !important;
        color: white !important;
        border: 1px solid #00bfa5;
        font-weight: 700;
        box-shadow: 0px 4px 12px rgba(0, 191, 165, 0.2);
    }
    </style>
""", unsafe_allow_html=True)
            
            # Call the quiz function
            run_quiz()
            
        except Exception as e:
            st.error(f"❌ Error loading quiz: {str(e)}")
            st.info("Please ensure the quiz module is properly configured.")
            
            # Optional: Add a refresh button
            if st.button("🔄 Refresh Quiz"):
                st.rerun()
                
    def add_footer(self):
        st.markdown("<hr style='margin-top: 50px; margin-bottom: 20px;'>", unsafe_allow_html=True)
    
        st.markdown("""
        <div style="
            text-align: center;
            font-family: Arial, sans-serif;
            font-size: 14px;
            color: #555;
        ">
            <p style="margin: 5px 0;">
                © 2025 <strong>CareerIQ.</strong> All rights reserved. Empowering careers with AI.
                &nbsp;|&nbsp;
                <a href="?page=privacy" style="color:#00bfa5; text-decoration:none;">Privacy</a>
                &nbsp;|&nbsp;
                <a href="https://github.com/akshpatel26/CareerIQ" style="color:#00bfa5; text-decoration:none;">GitHub</a>
                &nbsp;|&nbsp;
                <a href="mailto:contact." style="color:#00bfa5; text-decoration:none;">Contact</a>
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    
    def render_dashboard(self):
        """Render the dashboard page"""
        self.dashboard_manager.render_dashboard()


    def render_empty_state(self, icon, message):
        """Render an empty state with icon and message"""
        return f"""
            <div style='text-align: center; padding: 2rem; color: #666;'>
                <i class='{icon}' style='font-size: 2rem; margin-bottom: 1rem; color: #00bfa5;'></i>
                <p style='margin: 0;'>{message}</p>
            </div>
        """

    def analyze_resume(self, resume_text):
        """Analyze resume and store results"""
        analytics = self.analyzer.analyze_resume(resume_text)
        st.session_state.analytics_data = analytics
        return analytics


    def render_builder(self):
        apply_modern_styles()
        self.add_back_to_home_button()
    
        # Page Header
        page_header(
            "Resume Builder",
            "Create your professional resume"
        )
        st.markdown("""
    <style>
    /* Center align and style tab container */
    .stTabs [data-baseweb="tab-list"] {
        justify-content: center;
        margin-top: 20px;
        margin-bottom: 20px;
        gap: 10px;
    }

    /* Base style for each tab */
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f0f0;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 10px 24px;
        font-size: 16px;
        font-weight: 600;
        color: #333;
        transition: all 0.2s ease-in-out;
    }

    /* Hover effect */
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #e0f5ec;
        border-color: #00bfa5;
        color: #111;
        transform: translateY(-2px);
        cursor: pointer;
    }

    /* Selected/active tab style */
    .stTabs [aria-selected="true"] {
        background-color: #00bfa5 !important;
        color: white !important;
        border: 1px solid #00bfa5;
        font-weight: 700;
        box-shadow: 0px 4px 12px rgba(0, 191, 165, 0.2);
    }
    </style>
""", unsafe_allow_html=True)

        

        # Template selection
        template_options = ["Modern", "Professional", "Minimal", "Creative"]
        selected_template = st.selectbox(
    "Select Resume Template", template_options)
        st.success(f"🎨 Currently using: {selected_template} Template")

        # Personal Information
        st.subheader("Personal Information")

        col1, col2 = st.columns(2)
        with col1:
            # Get existing values from session state
            existing_name = st.session_state.form_data['personal_info'].get('full_name', '')
            existing_email = st.session_state.form_data['personal_info'].get('email', '')
            existing_phone = st.session_state.form_data['personal_info'].get('phone', '')
    
            # Input fields with existing values
            full_name = st.text_input(
                "Full Name *",
                value=existing_name,
                placeholder="John Doe",
                help="Enter your full name as you want it to appear"
            )
            email = st.text_input(
                "Email *",
                value=existing_email,
                key="email_input",
                placeholder="john.doe@example.com",
                help="Your professional email address"
            )
            phone = st.text_input(
                "Phone *",
                value=existing_phone,
                placeholder="+1-234-567-8900",
                help="Your contact number with country code"
            )
    
            # Immediately update session state after email input
            if 'email_input' in st.session_state:
                st.session_state.form_data['personal_info']['email'] = st.session_state.email_input
    
        with col2:
            # Get existing values from session state
            existing_location = st.session_state.form_data['personal_info'].get('location', '')
            existing_linkedin = st.session_state.form_data['personal_info'].get('linkedin', '')
            existing_portfolio = st.session_state.form_data['personal_info'].get('portfolio', '')
    
            # Input fields with existing values
            location = st.text_input(
                "Location *",
                value=existing_location,
                placeholder="New York, NY",
                help="Your city and state/country"
            )
            linkedin = st.text_input(
                "LinkedIn URL *",
                value=existing_linkedin,
                placeholder="https://linkedin.com/in/johndoe",
                help="Your LinkedIn profile URL"
            )
            portfolio = st.text_input(
                "Portfolio Website *",
                value=existing_portfolio,
                placeholder="https://www.johndoe.com",
                help="Your personal website or portfolio"
            )
    
        # Update personal info in session state
        st.session_state.form_data['personal_info'] = {
            'full_name': full_name,
            'email': email,
            'phone': phone,
            'location': location,
            'linkedin': linkedin,
            'portfolio': portfolio
        }

        # Professional Summary
        st.subheader("Professional Summary")
        summary = st.text_area("Professional Summary", value=st.session_state.form_data.get('summary', ''), height=150,
                             placeholder="Dynamic professional with X+ years of experience in...",
        help="Write a brief summary highlighting your key skills, experience, and career goals (3-5 sentences)")

        # ====================
        # WORK EXPERIENCE & EDUCATION - 2 COLUMN LAYOUT
        # ====================
        st.markdown("---")
        col_exp, col_edu = st.columns(2)
    
        # LEFT COLUMN - Work Experience
        with col_exp:
            st.markdown("###  Work Experience")
            if 'experiences' not in st.session_state.form_data:
                st.session_state.form_data['experiences'] = []
    
            if st.button(" Add Experience", use_container_width=True):
                st.session_state.form_data['experiences'].append({
                    'company': '',
                    'position': '',
                    'start_date': '',
                    'end_date': '',
                    'description': '',
                    'responsibilities': [],
                    'achievements': []
                })
                st.rerun()
    
            for idx, exp in enumerate(st.session_state.form_data['experiences']):
                with st.expander(f"📌 Experience {idx + 1}: {exp.get('position', 'New Position')}", expanded=True):
                    exp['company'] = st.text_input(
                        "Company Name",
                        key=f"company_{idx}",
                        value=exp.get('company', ''),
                        placeholder="Google Inc."
                    )
                    exp['position'] = st.text_input(
                        "Position",
                        key=f"position_{idx}",
                        value=exp.get('position', ''),
                        placeholder="Senior Software Engineer"
                    )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        exp['start_date'] = st.text_input(
                            "Start Date",
                            key=f"start_date_{idx}",
                            value=exp.get('start_date', ''),
                            placeholder="Jan 2020"
                        )
                    with col2:
                        exp['end_date'] = st.text_input(
                            "End Date",
                            key=f"end_date_{idx}",
                            value=exp.get('end_date', ''),
                            placeholder="Present"
                        )
    
                    exp['description'] = st.text_area(
                        "Role Overview",
                        key=f"desc_{idx}",
                        value=exp.get('description', ''),
                        height=80,
                        placeholder="Brief overview of your role and main responsibilities...",
                        help="Describe your overall role and its impact"
                    )
    
                    # Responsibilities
                    st.markdown("** Key Responsibilities**")
                    resp_text = st.text_area(
                        "Enter responsibilities (one per line)",
                        key=f"resp_{idx}",
                        value='\n'.join(exp.get('responsibilities', [])),
                        height=100,
                        placeholder="Led development of...\nManaged team of 5 engineers...",
                        help="List your main duties and responsibilities"
                    )
                    exp['responsibilities'] = [r.strip() for r in resp_text.split('\n') if r.strip()]
    
                    # Achievements
                    st.markdown("** Key Achievements**")
                    achv_text = st.text_area(
                        "Enter achievements (one per line)",
                        key=f"achv_{idx}",
                        value='\n'.join(exp.get('achievements', [])),
                        height=100,
                        placeholder="Increased efficiency by 40%...\nReduced costs by $50K annually...",
                        help="List measurable achievements and impacts"
                    )
                    exp['achievements'] = [a.strip() for a in achv_text.split('\n') if a.strip()]
    
                    if st.button(" Remove Experience", key=f"remove_exp_{idx}", type="secondary"):
                        st.session_state.form_data['experiences'].pop(idx)
                        st.rerun()
    
        # RIGHT COLUMN - Education
        with col_edu:
            st.markdown("###  Education")
            if 'education' not in st.session_state.form_data:
                st.session_state.form_data['education'] = []
    
            if st.button(" Add Education", use_container_width=True):
                st.session_state.form_data['education'].append({
                    'school': '',
                    'degree': '',
                    'field': '',
                    'graduation_date': '',
                    'gpa': '',
                    'achievements': []
                })
                st.rerun()
    
            for idx, edu in enumerate(st.session_state.form_data['education']):
                with st.expander(f"📌 Education {idx + 1}: {edu.get('school', 'New School')}", expanded=True):
                    edu['school'] = st.text_input(
                        "School/University",
                        key=f"school_{idx}",
                        value=edu.get('school', ''),
                        placeholder="Harvard University"
                    )
                    edu['degree'] = st.text_input(
                        "Degree",
                        key=f"degree_{idx}",
                        value=edu.get('degree', ''),
                        placeholder="Bachelor of Science"
                    )
                    edu['field'] = st.text_input(
                        "Field of Study",
                        key=f"field_{idx}",
                        value=edu.get('field', ''),
                        placeholder="Computer Science"
                    )
                    edu['graduation_date'] = st.text_input(
                        "Graduation Date",
                        key=f"grad_date_{idx}",
                        value=edu.get('graduation_date', ''),
                        placeholder="May 2020"
                    )
                    edu['gpa'] = st.text_input(
                        "GPA (optional)",
                        key=f"gpa_{idx}",
                        value=edu.get('gpa', ''),
                        placeholder="7.8/10.0"
                    )
    
                    # Educational Achievements
                    st.markdown("** Achievements & Activities**")
                    edu_achv_text = st.text_area(
                        "Enter achievements (one per line)",
                        key=f"edu_achv_{idx}",
                        value='\n'.join(edu.get('achievements', [])),
                        height=100,
                        placeholder="Dean's List all semesters...\nPresident of Computer Science Club...",
                        help="List academic honors, activities, and relevant coursework"
                    )
                    edu['achievements'] = [a.strip() for a in edu_achv_text.split('\n') if a.strip()]
    
                    if st.button(" Remove Education", key=f"remove_edu_{idx}", type="secondary"):
                        st.session_state.form_data['education'].pop(idx)
                        st.rerun()

        # ====================
        # END OF 2 COLUMN LAYOUT
        # ====================

        st.markdown("---")
        st.markdown("###  Projects")
        if 'projects' not in st.session_state.form_data:
            st.session_state.form_data['projects'] = []
    
        if st.button("➕ Add Project", use_container_width=False):
            st.session_state.form_data['projects'].append({
                'name': '',
                'technologies': '',
                'description': '',
                'responsibilities': [],
                'achievements': [],
                'link': ''
            })
            st.rerun()
    
        for idx, proj in enumerate(st.session_state.form_data['projects']):
            with st.expander(f"📌 Project {idx + 1}: {proj.get('name', 'New Project')}", expanded=True):
                proj['name'] = st.text_input(
                    "Project Name",
                    key=f"proj_name_{idx}",
                    value=proj.get('name', ''),
                    placeholder="E-commerce Platform"
                )
                proj['technologies'] = st.text_input(
                    "Technologies Used",
                    key=f"proj_tech_{idx}",
                    value=proj.get('technologies', ''),
                    placeholder="React, Node.js, MongoDB, AWS",
                    help="List the main technologies, frameworks, and tools used"
                )
    
                proj['description'] = st.text_area(
                    "Project Overview",
                    key=f"proj_desc_{idx}",
                    value=proj.get('description', ''),
                    height=80,
                    placeholder="Built a full-stack e-commerce platform that...",
                    help="Brief overview of the project and its purpose"
                )
    
                # Project Responsibilities
                st.markdown("**🎯 Key Responsibilities**")
                proj_resp_text = st.text_area(
                    "Enter responsibilities (one per line)",
                    key=f"proj_resp_{idx}",
                    value='\n'.join(proj.get('responsibilities', [])),
                    height=100,
                    placeholder="Designed and implemented frontend architecture...\nIntegrated payment gateway...",
                    help="List your main responsibilities in the project"
                )
                proj['responsibilities'] = [r.strip() for r in proj_resp_text.split('\n') if r.strip()]
    
                # Project Achievements
                st.markdown("**🏆 Key Achievements**")
                proj_achv_text = st.text_area(
                    "Enter achievements (one per line)",
                    key=f"proj_achv_{idx}",
                    value='\n'.join(proj.get('achievements', [])),
                    height=100,
                    placeholder="Achieved 10,000+ active users in first month...\nReduced page load time by 60%...",
                    help="List measurable outcomes and project impact"
                )
                proj['achievements'] = [a.strip() for a in proj_achv_text.split('\n') if a.strip()]
    
                proj['link'] = st.text_input(
                    "Project Link (optional)",
                    key=f"proj_link_{idx}",
                    value=proj.get('link', ''),
                    placeholder="https://github.com/username/project",
                    help="Link to GitHub, live demo, or documentation"
                )
    
                if st.button("🗑️ Remove Project", key=f"remove_proj_{idx}", type="secondary"):
                    st.session_state.form_data['projects'].pop(idx)
                    st.rerun()

        # Skills Section
        st.markdown("---")
        st.markdown("### Skills")
        if 'skills_categories' not in st.session_state.form_data:
            st.session_state.form_data['skills_categories'] = {
                'technical': [],
                'soft': [],
                'languages': [],
                'tools': []
            }
    
        col1, col2 = st.columns(2)
        with col1:
            tech_skills = st.text_area(
                "💻 Technical Skills (one per line)",
                value='\n'.join(st.session_state.form_data['skills_categories']['technical']),
                height=120,
                placeholder="Python\nJavaScript\nMachine Learning\nSQL",
                help="Programming languages, frameworks, and technical competencies"
            )
            st.session_state.form_data['skills_categories']['technical'] = [
                s.strip() for s in tech_skills.split('\n') if s.strip()
            ]
    
            soft_skills = st.text_area(
                "🤝 Soft Skills (one per line)",
                value='\n'.join(st.session_state.form_data['skills_categories']['soft']),
                height=120,
                placeholder="Leadership\nTeam Collaboration\nProblem Solving\nCommunication",
                help="Interpersonal and professional skills"
            )
            st.session_state.form_data['skills_categories']['soft'] = [
                s.strip() for s in soft_skills.split('\n') if s.strip()
            ]
    
        with col2:
            languages = st.text_area(
                "🌐 Languages (one per line)",
                value='\n'.join(st.session_state.form_data['skills_categories']['languages']),
                height=120,
                placeholder="English (Native)\nSpanish (Fluent)\nFrench (Intermediate)",
                help="Spoken languages with proficiency level"
            )
            st.session_state.form_data['skills_categories']['languages'] = [
                l.strip() for l in languages.split('\n') if l.strip()
            ]
    
            tools = st.text_area(
                "🛠️ Tools & Technologies (one per line)",
                value='\n'.join(st.session_state.form_data['skills_categories']['tools']),
                height=120,
                placeholder="Git\nDocker\nJira\nFigma",
                help="Software tools, platforms, and technologies"
            )
            st.session_state.form_data['skills_categories']['tools'] = [
                t.strip() for t in tools.split('\n') if t.strip()
            ]
    
        # Update form data in session state
        st.session_state.form_data.update({
            'summary': summary
        })
        
        # Custom Sections
        st.markdown("---")
        st.markdown("### ➕ Custom Sections (Optional)")
        st.info("💡 Add additional sections like Certifications, Awards, Volunteer Work, Publications, etc.")
        
        if 'custom_sections' not in st.session_state.form_data:
            st.session_state.form_data['custom_sections'] = []
        
        if st.button("➕ Add Custom Section", use_container_width=False):
            st.session_state.form_data['custom_sections'].append({
                'section_name': '',
                'items': []
            })
            st.rerun()
        
        for section_idx, custom_section in enumerate(st.session_state.form_data['custom_sections']):
            with st.expander(f"📌 {custom_section.get('section_name', f'Custom Section {section_idx + 1}')}", expanded=True):
                # Section name
                custom_section['section_name'] = st.text_input(
                    "Section Name",
                    key=f"custom_section_name_{section_idx}",
                    value=custom_section.get('section_name', ''),
                    placeholder="Certifications / Awards / Volunteer Work",
                    help="e.g., Certifications, Awards, Volunteer Work, Publications"
                )
                
                # Initialize items if not exists
                if 'items' not in custom_section:
                    custom_section['items'] = []
                
                # Add item button
                if st.button(f"➕ Add Item", key=f"add_item_{section_idx}", use_container_width=False):
                    custom_section['items'].append({
                        'title': '',
                        'details': '',
                        'date': '',
                        'description': ''
                    })
                    st.rerun()
                
                # Display items
                for item_idx, item in enumerate(custom_section['items']):
                    st.markdown(f"**Item {item_idx + 1}**")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        item['title'] = st.text_input(
                            "Title/Name",
                            key=f"custom_item_title_{section_idx}_{item_idx}",
                            value=item.get('title', ''),
                            placeholder="AWS Certified Solutions Architect",
                            help="Certificate name, Award title, Organization name, etc."
                        )
                    with col2:
                        item['date'] = st.text_input(
                            "Date (optional)",
                            key=f"custom_item_date_{section_idx}_{item_idx}",
                            value=item.get('date', ''),
                            placeholder="Jan 2023",
                            help="When you received or completed this"
                        )
                    
                    item['details'] = st.text_input(
                        "Details/Organization",
                        key=f"custom_item_details_{section_idx}_{item_idx}",
                        value=item.get('details', ''),
                        placeholder="Amazon Web Services",
                        help="Issuing organization, location, or additional details"
                    )
                    
                    item['description'] = st.text_area(
                        "Description (optional)",
                        key=f"custom_item_desc_{section_idx}_{item_idx}",
                        value=item.get('description', ''),
                        height=80,
                        placeholder="Brief description of the achievement or certification...",
                        help="Brief description of the achievement, work, or certification"
                    )
                    
                    if st.button(f"🗑️ Remove Item", key=f"remove_custom_item_{section_idx}_{item_idx}", type="secondary"):
                        custom_section['items'].pop(item_idx)
                        st.rerun()
                    
                    st.divider()
                
                if st.button(f"🗑️ Remove Section", key=f"remove_custom_section_{section_idx}", type="secondary"):
                    st.session_state.form_data['custom_sections'].pop(section_idx)
                    st.rerun()
                
                st.markdown("---")

                
                

        # Generate Resume button
        if st.columns([1,2,1])[1].button("📄 Generate Resume", type="primary", use_container_width=True):
            print("Validating form data...")
            print(f"Session state form data: {st.session_state.form_data}")
            print(
    f"Email input value: {
        st.session_state.get(
            'email_input',
             '')}")

            # Get the current values from form
            current_name = st.session_state.form_data['personal_info']['full_name'].strip(
            )
            current_email = st.session_state.email_input if 'email_input' in st.session_state else ''

            print(f"Current name: {current_name}")
            print(f"Current email: {current_email}")

            # Validate required fields
            if not current_name:
                st.error("⚠️ Please enter your full name.")
                return

            if not current_email:
                st.error("⚠️ Please enter your email address.")
                return

            # Update email in form data one final time
            st.session_state.form_data['personal_info']['email'] = current_email

            try:
                print("Preparing resume data...")
                # Prepare resume data with current form values
                resume_data = {
                    "personal_info": st.session_state.form_data['personal_info'],
                    "summary": st.session_state.form_data.get('summary', '').strip(),
                    "experience": st.session_state.form_data.get('experiences', []),
                    "education": st.session_state.form_data.get('education', []),
                    "projects": st.session_state.form_data.get('projects', []),
                    "skills": st.session_state.form_data.get('skills_categories', {
                        'technical': [],
                        'soft': [],
                        'languages': [],
                        'tools': []
                    }),
                    "template": selected_template
                }

                print(f"Resume data prepared: {resume_data}")

                try:
                    # Generate resume
                    resume_buffer = self.builder.generate_resume(resume_data)
                    if resume_buffer:
                        try:
                            # Save resume data to database
                            save_resume_data(resume_data)

                            # Offer the resume for download
                            st.success("✅ Resume generated successfully!")

                      
                            st.download_button(
                                label="Download Resume 📥",
                                data=resume_buffer,
                                file_name=f"{
    current_name.replace(
        ' ', '_')}_resume.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            )
                        except Exception as db_error:
                            print(
    f"Warning: Failed to save to database: {
        str(db_error)}")
                            # Still allow download even if database save fails
                            st.warning(
                                "⚠️ Resume generated but couldn't be saved to database")
                            

                            st.download_button(
                                label="Download Resume 📥",
                                data=resume_buffer,
                                file_name=f"{
    current_name.replace(
        ' ', '_')}_resume.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            )
                    else:
                        st.error(
                            "❌ Failed to generate resume. Please try again.")
                        print("Resume buffer was None")
                except Exception as gen_error:
                    print(f"Error during resume generation: {str(gen_error)}")
                    print(f"Full traceback: {traceback.format_exc()}")
                    st.error(f"❌ Error generating resume: {str(gen_error)}")

            except Exception as e:
                print(f"Error preparing resume data: {str(e)}")
                print(f"Full traceback: {traceback.format_exc()}")
                st.error(f"❌ Error preparing resume data: {str(e)}")

    # Add this method to your ResumeApp class in app.py

    def render_portfolio_builder(self):
        
        self.add_back_to_home_button()
   
        page_header("Portfolio Builder", "Create stunning portfolios with professional templates")
        
        
        # Initialize session state for portfolio data
        if 'portfolio_data' not in st.session_state:
            st.session_state.portfolio_data = {
                'personal_info': {
                    'name': 'John Doe',
                    'tagline': 'Full-Stack Developer & UI/UX Enthusiast',
                    'email': 'john@example.com',
                    'phone': '+1 (555) 123-4567',
                    'linkedin': 'linkedin.com/in/johndoe',
                    'github': 'github.com/johndoe',
                    'twitter': 'twitter.com/johndoe',
                    'website': 'johndoe.com'
                },
                'about': 'Passionate full-stack developer with 5+ years of experience building scalable web applications. Specialized in React, Node.js, and cloud technologies. Love turning complex problems into elegant solutions.',
                'skills': {
                    'Frontend': ['React', 'Vue.js', 'TypeScript', 'Tailwind CSS'],
                    'Backend': ['Node.js', 'Python', 'Django', 'PostgreSQL'],
                    'Tools': ['Git', 'Docker', 'AWS', 'CI/CD'],
                    'Soft Skills': ['Leadership', 'Communication', 'Problem Solving']
                },
                'projects': [
                    {
                        'title': 'E-Commerce Platform',
                        'tech_stack': 'React, Node.js, MongoDB, Stripe',
                        'description': 'Built a fully-featured e-commerce platform with payment integration, inventory management, and real-time analytics.',
                        'link': 'https://example.com'
                    },
                    {
                        'title': 'AI Content Generator',
                        'tech_stack': 'Python, FastAPI, OpenAI, React',
                        'description': 'Developed an AI-powered content generation tool that helps marketers create engaging content.',
                        'link': 'https://example.com'
                    }
                ],
                'experience': [
                    {
                        'role': 'Senior Full Stack Developer',
                        'company': 'Tech Corp Inc.',
                        'duration': 'Jan 2022 - Present',
                        'description': 'Leading a team of 5 developers in building scalable web applications. Implemented CI/CD pipelines reducing deployment time by 60%.'
                    }
                ],
                'education': [
                    {
                        'degree': 'B.Tech in Computer Science',
                        'college': 'MIT University',
                        'cgpa': '8.5/10',
                        'duration': '2015 - 2019'
                    }
                ],
                'certifications': [
                    {
                        'name': 'AWS Certified Solutions Architect',
                        'issuer': 'Amazon Web Services'
                    },
                    {
                        'name': 'Google Cloud Professional Developer',
                        'issuer': 'Google Cloud'
                    }
                ],
                'achievements': [
                    'Won Best Innovation Award at TechHack 2023',
                    'Published research paper on Machine Learning in IEEE',
                    'Mentored 50+ students in web development'
                ]
            }
        
        
        # Template Selection Section (Main Area)
        # st.markdown("##  Choose Template")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("**Select Template Style**")
            template_name = st.selectbox(
                "template_select",
                ["Designer Portfolio", "Dark Modern Portfolio", "Neon Cyberpunk", "Elegant Minimalist"],
                label_visibility="collapsed"
            )
        
        with col2:
            template_info = {
                "Designer Portfolio": ("Selected: Designer Portfolio", "🎨 Creative layout with navigation and vibrant colors"),
                "Dark Modern Portfolio": ("Selected: Dark Modern Portfolio", "🌙 Sleek dark theme with glassmorphism effects"),
                "Neon Cyberpunk": ("Selected: Neon Cyberpunk", "⚡ Futuristic neon design with cyber aesthetics"),
                "Elegant Minimalist": ("Selected: Elegant Minimalist", "✨ Clean and sophisticated minimalist design")
            }
            
            selected_title, selected_desc = template_info[template_name]
            st.info(f"**{selected_title}**\n\n{selected_desc}")
        
        # st.markdown("---")
        st.markdown("""
            <style>
             .stTabs [data-baseweb="tab-list"] {
                 justify-content: center;
                 margin-top: 20px;
                 margin-bottom: 20px;
                 gap: 10px;
             }
         
             /* Base style for each tab */
             .stTabs [data-baseweb="tab"] {
                 background-color: #f0f0f0;
                 border: 1px solid #ddd;
                 border-radius: 8px;
                 padding: 10px 24px;
                 font-size: 16px;
                 font-weight: 600;
                 color: #333;
                 transition: all 0.2s ease-in-out;
             }
         
             /* Hover effect */
             .stTabs [data-baseweb="tab"]:hover {
                 background-color: #e0f5ec;
                 border-color: #00bfa5;
                 color: #111;
                 transform: translateY(-2px);
                 cursor: pointer;
             }
         
             /* Selected/active tab style */
             .stTabs [aria-selected="true"] {
                 background-color: #00bfa5 !important;
                 color: white !important;
                 border: 1px solid #00bfa5;
                 font-weight: 700;
                 box-shadow: 0px 4px 12px rgba(0, 191, 165, 0.2);
             }
             </style>
         """, unsafe_allow_html=True)
        # Create tabs
        tab1, tab2, tab3 = st.tabs(["📝 Edit Portfolio", "👁 Live Preview", "⬇️ Download & Share"])
        
        # TAB 1: Edit Content
        with tab1:                
                
                # Personal Information
                with st.expander("👤 Personal Information", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        name = st.text_input("Full Name *", st.session_state.portfolio_data['personal_info']['name'], key="port_name")
                        email = st.text_input("Email *", st.session_state.portfolio_data['personal_info']['email'], key="port_email")
                        phone = st.text_input("Phone", st.session_state.portfolio_data['personal_info']['phone'], key="port_phone")
                    with col2:
                        tagline = st.text_input("Professional Tagline *", st.session_state.portfolio_data['personal_info']['tagline'], key="port_tagline")
                        linkedin = st.text_input("LinkedIn", st.session_state.portfolio_data['personal_info']['linkedin'], key="port_linkedin")
                        github = st.text_input("GitHub", st.session_state.portfolio_data['personal_info']['github'], key="port_github")
                    
                    col3, col4 = st.columns(2)
                    with col3:
                        website = st.text_input("Website", st.session_state.portfolio_data['personal_info'].get('website', ''), key="port_website")
                    with col4:
                        twitter = st.text_input("Twitter", st.session_state.portfolio_data['personal_info'].get('twitter', ''), key="port_twitter")
                
                # About Me
                with st.expander("📝 About Me", expanded=True):
                    about = st.text_area(
                        "Tell your story",
                        st.session_state.portfolio_data['about'],
                        height=120,
                        help="Write 2-3 sentences about your background and expertise",
                        key="port_about"
                    )
                
                # Skills
                with st.expander("🎯 Skills & Expertise", expanded=True):
                    st.markdown("Add your skills by category (comma-separated)")
                    col1, col2 = st.columns(2)
                    
                    default_skills = st.session_state.portfolio_data['skills']
                    
                    with col1:
                        frontend = st.text_area("Frontend Technologies", 
                            ', '.join(default_skills.get('Frontend', [])), 
                            help="e.g., React, Vue.js, TypeScript",
                            key="port_frontend")
                        backend = st.text_area("Backend Technologies", 
                            ', '.join(default_skills.get('Backend', [])),
                            key="port_backend")
                    with col2:
                        tools = st.text_area("Tools & Platforms", 
                            ', '.join(default_skills.get('Tools', [])),
                            key="port_tools")
                        soft_skills = st.text_area("Soft Skills", 
                            ', '.join(default_skills.get('Soft Skills', [])),
                            key="port_soft")
                
                # Projects
                with st.expander("💼 Projects", expanded=True):
                    num_projects = st.number_input("Number of Projects", 1, 10, len(st.session_state.portfolio_data['projects']), key="port_num_projects")
                    projects = []
                    for i in range(num_projects):
                        st.markdown(f"#### 🚀 Project {i+1}")
                        col1, col2 = st.columns(2)
                        
                        default_proj = st.session_state.portfolio_data['projects'][i] if i < len(st.session_state.portfolio_data['projects']) else {}
                        
                        with col1:
                            title = st.text_input(f"Project Title *", default_proj.get('title', f'Project {i+1}'), key=f"proj_title_{i}")
                            tech = st.text_input(f"Tech Stack", default_proj.get('tech_stack', ''), key=f"proj_tech_{i}")
                        with col2:
                            desc = st.text_area(f"Description", default_proj.get('description', ''), key=f"proj_desc_{i}", height=100)
                            link = st.text_input(f"Project Link", default_proj.get('link', ''), key=f"proj_link_{i}")
                        
                        projects.append({'title': title, 'tech_stack': tech, 'description': desc, 'link': link})
                        if i < num_projects - 1:
                            st.divider()
                
                # Experience
                with st.expander("💼 Work Experience", expanded=False):
                    num_exp = st.number_input("Number of Experiences", 0, 10, len(st.session_state.portfolio_data.get('experience', [])), key="port_num_exp")
                    experience = []
                    for i in range(num_exp):
                        st.markdown(f"#### Experience {i+1}")
                        col1, col2 = st.columns(2)
                        
                        default_exp = st.session_state.portfolio_data['experience'][i] if i < len(st.session_state.portfolio_data.get('experience', [])) else {}
                        
                        with col1:
                            role = st.text_input("Job Title", default_exp.get('role', ''), key=f"exp_role_{i}")
                            company = st.text_input("Company", default_exp.get('company', ''), key=f"exp_company_{i}")
                        with col2:
                            duration = st.text_input("Duration", default_exp.get('duration', ''), key=f"exp_duration_{i}")
                        
                        description = st.text_area("Description", default_exp.get('description', ''), key=f"exp_desc_{i}", height=100)
                        
                        experience.append({'role': role, 'company': company, 'duration': duration, 'description': description})
                        if i < num_exp - 1:
                            st.divider()
                
                # Education
                with st.expander("🎓 Education", expanded=False):
                    num_edu = st.number_input("Number of Degrees", 0, 5, len(st.session_state.portfolio_data.get('education', [])), key="port_num_edu")
                    education = []
                    for i in range(num_edu):
                        st.markdown(f"#### Education {i+1}")
                        col1, col2 = st.columns(2)
                        
                        default_edu = st.session_state.portfolio_data['education'][i] if i < len(st.session_state.portfolio_data.get('education', [])) else {}
                        
                        with col1:
                            degree = st.text_input("Degree", default_edu.get('degree', ''), key=f"edu_degree_{i}")
                            college = st.text_input("Institution", default_edu.get('college', ''), key=f"edu_college_{i}")
                        with col2:
                            cgpa = st.text_input("CGPA/Grade", default_edu.get('cgpa', ''), key=f"edu_cgpa_{i}")
                            duration = st.text_input("Duration", default_edu.get('duration', ''), key=f"edu_duration_{i}")
                        
                        education.append({'degree': degree, 'college': college, 'cgpa': cgpa, 'duration': duration})
                        if i < num_edu - 1:
                            st.divider()
                
                # Certifications
                with st.expander("📜 Certifications", expanded=False):
                    num_certs = st.number_input("Number of Certifications", 0, 10, len(st.session_state.portfolio_data.get('certifications', [])), key="port_num_certs")
                    certifications = []
                    for i in range(num_certs):
                        col1, col2 = st.columns(2)
                        
                        default_cert = st.session_state.portfolio_data['certifications'][i] if i < len(st.session_state.portfolio_data.get('certifications', [])) else {}
                        
                        with col1:
                            cert_name = st.text_input(f"Certification {i+1}", default_cert.get('name', ''), key=f"cert_name_{i}")
                        with col2:
                            cert_issuer = st.text_input(f"Issuer {i+1}", default_cert.get('issuer', ''), key=f"cert_issuer_{i}")
                        
                        certifications.append({'name': cert_name, 'issuer': cert_issuer})
                
                # Achievements
                with st.expander("🏆 Achievements", expanded=False):
                    num_achievements = st.number_input("Number of Achievements", 0, 10, len(st.session_state.portfolio_data.get('achievements', [])), key="port_num_achievements")
                    achievements = []
                    for i in range(num_achievements):
                        default_achievement = st.session_state.portfolio_data['achievements'][i] if i < len(st.session_state.portfolio_data.get('achievements', [])) else ''
                        achievement = st.text_input(f"Achievement {i+1}", default_achievement, key=f"achievement_{i}")
                        if achievement:
                            achievements.append(achievement)
                
                # Update session state
                st.session_state.portfolio_data = {
                    'personal_info': {
                        'name': name,
                        'tagline': tagline,
                        'email': email,
                        'phone': phone,
                        'website': website,
                        'github': github,
                        'linkedin': linkedin,
                        'twitter': twitter
                    },
                    'about': about,
                    'skills': {
                        'Frontend': [s.strip() for s in frontend.split(',') if s.strip()],
                        'Backend': [s.strip() for s in backend.split(',') if s.strip()],
                        'Tools': [s.strip() for s in tools.split(',') if s.strip()],
                        'Soft Skills': [s.strip() for s in soft_skills.split(',') if s.strip()]
                    },
                    'projects': projects,
                    'experience': experience,
                    'education': education,
                    'certifications': certifications,
                    'achievements': achievements
                }
                
                if st.button("💾 Save Changes", type="primary", use_container_width=True):
                    st.success("✅ Portfolio data saved successfully!")
                    st.balloons()
        
        # TAB 2: Live Preview
        with tab2:
                st.markdown("### 👁️ Live Preview")
                # st.info("💡 This is how your portfolio will look. Scroll to see the full design!")
                
                photo_base64 = st.session_state.get('portfolio_photo', None)
                preview_html = self.generate_portfolio_preview(st.session_state.portfolio_data, template_name)
                st.components.v1.html(preview_html, height=1800, scrolling=True)
        
        # TAB 3: Download
        with tab3:
                # st.markdown("### ⬇️ Download Your Portfolio")
                
                # Calculate Portfolio Completeness Score
                data = st.session_state.portfolio_data
                score = 0
                max_score = 100
                feedback = []
                
                # Store individual scores for breakdown
                scores = {}
                
                # Personal Info (20 points)
                personal_score = 0
                if data['personal_info'].get('name'): personal_score += 5
                if data['personal_info'].get('email'): personal_score += 5
                if data['personal_info'].get('tagline'): personal_score += 5
                if data['personal_info'].get('github'): 
                    personal_score += 5
                else:
                    feedback.append("❌ Add GitHub profile link")
                scores['Personal Info'] = personal_score
                score += personal_score
                
                # About Section (10 points)
                about_score = 0
                if data.get('about') and len(data['about']) > 100:
                    about_score = 10
                else:
                    feedback.append("❌ Write a detailed About Me (100+ characters)")
                scores['About Section'] = about_score
                score += about_score
                
                # Projects (30 points total)
                project_score = 0
                project_count = len(data.get('projects', []))
                
                # Project count (15 points)
                if project_count >= 3:
                    project_score += 15
                elif project_count >= 2:
                    project_score += 10
                    feedback.append("⚠️ Add at least 3 projects (currently: {})".format(project_count))
                elif project_count >= 1:
                    project_score += 5
                    feedback.append("❌ Add at least 3 projects (currently: {})".format(project_count))
                else:
                    feedback.append("❌ Add at least 3 projects (currently: 0)")
                
                # Check project details (15 points - 5 each for tech/links/desc)
                if project_count > 0:
                    projects_with_tech = sum(1 for p in data.get('projects', []) if p.get('tech_stack'))
                    projects_with_links = sum(1 for p in data.get('projects', []) if p.get('link'))
                    projects_with_desc = sum(1 for p in data.get('projects', []) if p.get('description') and len(p['description']) > 50)
                    
                    if projects_with_tech >= project_count * 0.8:
                        project_score += 5
                    else:
                        feedback.append("⚠️ Add tech stack to all projects ({}/{})".format(projects_with_tech, project_count))
                    
                    if projects_with_links >= project_count * 0.6:
                        project_score += 5
                    else:
                        feedback.append("⚠️ Add live demo/GitHub links to projects ({}/{})".format(projects_with_links, project_count))
                    
                    if projects_with_desc >= project_count * 0.8:
                        project_score += 5
                    else:
                        feedback.append("⚠️ Write detailed descriptions for all projects")
                
                scores['Projects'] = project_score
                score += project_score
                
                # Skills (15 points)
                skills_score = 0
                skill_categories = len([v for v in data.get('skills', {}).values() if v])
                total_skills = sum(len(v) for v in data.get('skills', {}).values())
                
                if skill_categories >= 4:
                    skills_score += 8
                elif skill_categories >= 3:
                    skills_score += 5
                    feedback.append("⚠️ Add more skill categories")
                else:
                    feedback.append("❌ Add at least 3 skill categories")
                
                if total_skills >= 12:
                    skills_score += 7
                elif total_skills >= 8:
                    skills_score += 4
                    feedback.append("⚠️ Add more skills (currently: {})".format(total_skills))
                else:
                    feedback.append("❌ Add at least 12 skills across categories")
                
                scores['Skills'] = skills_score
                score += skills_score
                
                # Experience (10 points)
                exp_count = len(data.get('experience', []))
                exp_score = 10 if exp_count >= 1 else 0
                if exp_count == 0:
                    feedback.append("❌ Add at least 1 work experience")
                scores['Experience'] = exp_score
                score += exp_score
                
                # Education (5 points)
                edu_count = len(data.get('education', []))
                edu_score = 5 if edu_count >= 1 else 0
                if edu_count == 0:
                    feedback.append("❌ Add your education details")
                scores['Education'] = edu_score
                score += edu_score
                
                # Certifications (5 points)
                cert_count = len(data.get('certifications', []))
                cert_score = 0
                if cert_count >= 2:
                    cert_score = 5
                elif cert_count >= 1:
                    cert_score = 3
                    feedback.append("⚠️ Add more certifications")
                else:
                    feedback.append("⚠️ Add certifications (optional but recommended)")
                scores['Certifications'] = cert_score
                score += cert_score
                
                # Achievements (5 points)
                achievement_count = len(data.get('achievements', []))
                achievement_score = 0
                if achievement_count >= 2:
                    achievement_score = 5
                elif achievement_count >= 1:
                    achievement_score = 3
                    feedback.append("⚠️ Add more achievements")
                else:
                    feedback.append("⚠️ Add notable achievements (optional)")
                scores['Achievements'] = achievement_score
                score += achievement_score
                
                # Display Score
                score_color = "green" if score >= 80 else "orange" if score >= 60 else "red"
                score_emoji = "🎉" if score >= 80 else "⚡" if score >= 60 else "⚠️"
                
                col_score1, col_score2 = st.columns([2, 3])
                
                with col_score1:
                    # Determine score rating and color
                    if score >= 80:
                        rating = "EXCELLENT"
                        rating_color = "#10b981"
                    elif score >= 70:
                        rating = "GOOD"
                        rating_color = "#4169e1"  # Royal blue like in image
                    elif score >= 50:
                        rating = "AVERAGE"
                        rating_color = "#f59e0b"
                    else:
                        rating = "NEEDS WORK"
                        rating_color = "#ef4444"
                    
                    # Calculate circle animation values
                    circumference = 565.48
                    offset = circumference - (score / 100) * circumference
                    
                    st.markdown(f"""
                    <style>
                    @keyframes progressCircle {{
                        from {{
                            stroke-dashoffset: {circumference};
                        }}
                        to {{
                            stroke-dashoffset: {offset};
                        }}
                    }}
                    
                    .circular-container {{
                        background: white;
                        padding: 40px;
                        border-radius: 15px;
                        text-align: center;
                        height: 100%;
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                        align-items: center;
                        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
                    }}
                    
                    .circular-progress {{
                        position: relative;
                        width: 220px;
                        height: 220px;
                        margin: 20px auto;
                    }}
                    
                    .circular-progress svg {{
                        transform: rotate(-90deg);
                        width: 100%;
                        height: 100%;
                    }}
                    
                    .circle-bg {{
                        fill: none;
                        stroke: #f0f0f5;
                        stroke-width: 16;
                    }}
                    
                    .circle-progress {{
                        fill: none;
                        stroke: {rating_color};
                        stroke-width: 16;
                        stroke-linecap: round;
                        stroke-dasharray: {circumference};
                        stroke-dashoffset: {circumference};
                        animation: progressCircle 1.5s ease-out forwards;
                    }}
                    
                    .score-text {{
                        position: absolute;
                        top: 50%;
                        left: 50%;
                        transform: translate(-50%, -50%);
                        text-align: center;
                    }}
                    
                    .score-number {{
                        font-size: 4rem;
                        font-weight: 900;
                        color: #1f2937;
                        line-height: 1;
                        margin: 0;
                    }}
                    
                    .score-label {{
                        font-size: 0.95rem;
                        font-weight: 600;
                        color: #9ca3af;
                        text-transform: uppercase;
                        letter-spacing: 1px;
                        margin-top: 5px;
                    }}
                    
                    .score-subtitle {{
                        background: #f8f9fc;
                        padding: 15px 20px;
                        border-radius: 10px;
                        margin-top: 20px;
                        width: 100%;
                    }}
                    
                    .score-subtitle-text {{
                        font-size: 0.9rem;
                        font-weight: 600;
                        color: #4169e1;
                        margin: 0;
                        line-height: 1.4;
                    }}
                    </style>
                    
                    <div class="circular-container">
                        <div class="circular-progress">
                            <svg>
                                <circle class="circle-bg" cx="110" cy="110" r="90"></circle>
                                <circle class="circle-progress" cx="110" cy="110" r="90"></circle>
                            </svg>
                            <div class="score-text">
                                <div class="score-number">{score}</div>
                                <div class="score-label">{rating}</div>
                            </div>
                        </div>
                        
                 </div>
                    """, unsafe_allow_html=True)
                                    
                    with col_score2:
                        st.markdown("""
                        <style>
                        .checklist-container {
                            background: white;
                            padding: 30px;
                            border-radius: 15px;
                            height: 100%;
                            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
                        }
                        
                        .checklist-header {
                            display: flex;
                            align-items: center;
                            gap: 12px;
                            margin-bottom: 25px;
                            padding-bottom: 15px;
                            border-bottom: 3px solid #e5e7eb;
                        }
                        
                        .checklist-icon {
                            font-size: 1.8rem;
                        }
                        
                        .checklist-title {
                            font-size: 1.3rem;
                            font-weight: 700;
                            color: #000000;
                            margin: 0;
                        }
                        
                        .checklist-items {
                            display: flex;
                            flex-direction: column;
                            gap: 12px;
                        }
                        
                        .checklist-item {
                            background: #f8f9fa;
                            padding: 16px;
                            border-radius: 10px;
                            border-left: 4px solid #3b82f6;
                            transition: all 0.3s ease;
                            display: flex;
                            align-items: flex-start;
                            gap: 15px;
                            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
                        }
                        
                        .checklist-item:hover {
                            transform: translateX(5px);
                            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
                            border-left-color: #2563eb;
                            background: #eff6ff;
                        }
                        
                        .checklist-checkbox {
                            width: 22px;
                            height: 22px;
                            border: 2px solid #cbd5e1;
                            border-radius: 5px;
                            flex-shrink: 0;
                            margin-top: 2px;
                            background: white;
                            position: relative;
                            cursor: pointer;
                        }
                        
                        .checklist-checkbox::after {
                            content: '✓';
                            position: absolute;
                            top: 50%;
                            left: 50%;
                            transform: translate(-50%, -50%);
                            color: #3b82f6;
                            font-weight: bold;
                            font-size: 14px;
                            opacity: 0;
                            transition: opacity 0.2s ease;
                        }
                        
                        .checklist-item:hover .checklist-checkbox {
                            border-color: #3b82f6;
                            background: #eff6ff;
                        }
                        
                        .checklist-item:hover .checklist-checkbox::after {
                            opacity: 1;
                        }
                        
                        .checklist-text {
                            color: #1f2937;
                            font-size: 0.95rem;
                            line-height: 1.6;
                            flex: 1;
                            font-weight: 500;
                        }
                        
                        .checklist-warning-icon {
                            color: #f59e0b;
                            font-size: 1.2rem;
                            flex-shrink: 0;
                            margin-top: 2px;
                        }
                        
                        .no-feedback {
                            text-align: center;
                            padding: 50px 20px;
                            background: linear-gradient(135deg, #ecfdf5, #d1fae5);
                            border-radius: 12px;
                        }
                        
                        .no-feedback-icon {
                            font-size: 4.5rem;
                            margin-bottom: 20px;
                            animation: bounce 2s infinite;
                        }
                        
                        @keyframes bounce {
                            0%, 100% { transform: translateY(0); }
                            50% { transform: translateY(-10px); }
                        }
                        
                        .no-feedback-text {
                            font-size: 1.4rem;
                            font-weight: 700;
                            margin-bottom: 10px;
                            color: #059669;
                        }
                        
                        .no-feedback-subtext {
                            font-size: 1rem;
                            color: #047857;
                        }
                        
                        .feedback-count {
                            background: #3b82f6;
                            color: white;
                            padding: 4px 12px;
                            border-radius: 20px;
                            font-size: 0.85rem;
                            font-weight: 600;
                            margin-left: auto;
                        }
                        </style>
                        
                        <div class="checklist-container">
                            <div class="checklist-header">
                                <span class="checklist-icon">📋</span>
                                <h3 style="font-size: 1.3rem; font-weight: 700;color:#000000 ;  margin: 0;">Improvement Checklist</h3>
                        """, unsafe_allow_html=True)
                        
                        # Check if feedback exists and has items
                        if feedback and len(feedback) > 0:
                            st.markdown(f'<span class="feedback-count">{len(feedback)} items</span>', unsafe_allow_html=True)
                            st.markdown('</div><div class="checklist-items">', unsafe_allow_html=True)
                            
                            for item in feedback:
                                # Remove any existing bullet points or checkmarks
                                clean_item = item.strip().lstrip('•-✓✗❌✅ ')
                                
                                st.markdown(f"""
                                <div class="checklist-item">
                                    <div class="checklist-checkbox"></div>
                                    <span class="checklist-warning-icon">⚠️</span>
                                    <div class="checklist-text">{clean_item}</div>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                        else:
                            st.markdown('</div>', unsafe_allow_html=True)
                            # Show message when no feedback
                            st.markdown("""
                            <div class="no-feedback">
                                <div class="no-feedback-icon">🎉</div>
                                <div class="no-feedback-text">Excellent Work!</div>
                                <div class="no-feedback-subtext">Your resume looks great. No major improvements needed.</div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                 
                st.markdown("<br>", unsafe_allow_html=True)
                
                
                st.markdown("### Choose your preferred format")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("#### 📄 DOCX Format")
                    if st.button("Generate DOCX", type="primary", use_container_width=True):
                        with st.spinner("Creating document..."):
                            buffer = self.portfolio_builder.generate_portfolio(st.session_state.portfolio_data, template_name)
                            st.download_button(
                                "⬇️ Download DOCX",
                                data=buffer,
                                file_name=f"portfolio_{template_name.lower().replace(' ', '_')}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                use_container_width=True
                            )
                
                with col2:
                    st.markdown("#### 🌐 HTML Format")
                    if st.button("Generate HTML", type="primary", use_container_width=True):
                        with st.spinner("Creating HTML..."):
                            html_content = self.generate_portfolio_preview(st.session_state.portfolio_data, template_name)
                            st.download_button(
                                "⬇️ Download HTML",
                                data=html_content,
                                file_name=f"portfolio_{template_name.lower().replace(' ', '_')}.html",
                                mime="text/html",
                                use_container_width=True
                            )
                
                with col3:
                    st.markdown("#### 📋 JSON Format")
                    if st.button("Generate JSON", type="secondary", use_container_width=True):
                        import json
                        json_data = json.dumps(st.session_state.portfolio_data, indent=2)
                        st.download_button(
                            "⬇️ Download JSON",
                            data=json_data,
                            file_name="portfolio_data.json",
                            mime="application/json",
                            use_container_width=True
                        )
            
        st.markdown("---")
        st.success("💡 **Pro Tip:** Download HTML for instant web deployment!")
        st.markdown("""
            **What you can do with the files:**
            - 📄 **DOCX**: Edit in Microsoft Word or Google Docs
            - 🌐 **HTML**: Host on GitHub Pages, Netlify, or Vercel
            - 📋 **JSON**: Import your data later or share with others
            """)
    
    def generate_portfolio_preview(self, data, template_name):
        """Generate HTML preview of portfolio with all 4 templates - ALL SECTIONS INCLUDED"""
        
        # Get initials for Elegant Minimalist template
        name = data['personal_info'].get('name', 'JD')
        initials = ''.join([word[0].upper() for word in name.split()[:2]]) if name else 'JD'
        
        # Format ALL sections based on template
        projects_html = ""
        for i, proj in enumerate(data.get('projects', []), 1):
            if proj.get('title'):
                if template_name == "Designer Portfolio":
                    projects_html += f"""
                    <div class="project-card">
                        <div class="project-header">
                            <h3 class="project-title">{proj['title']}</h3>
                        </div>
                        <div class="project-body">
                            <div style="color: #ff6b6b; font-weight: 600; margin-bottom: 15px;">{proj.get('tech_stack', '')}</div>
                            <p style="color: #555; line-height: 1.8; margin-bottom: 20px;">{proj['description']}</p>
                            {f'<a href="{proj["link"]}" style="color: #ff6b6b; font-weight: 600; text-decoration: none;">View Project →</a>' if proj.get('link') else ''}
                        </div>
                    </div>
                    """
                elif template_name == "Dark Modern Portfolio":
                    projects_html += f"""
                    <div class="project-card">
                        <div style="color: #667eea; font-size: 1em; margin-bottom: 15px; font-weight: 700;">PROJECT {i:02d}</div>
                        <h3 class="project-title">{proj['title']}</h3>
                        <div style="background: rgba(102, 126, 234, 0.2); color: #667eea; padding: 8px 20px; border-radius: 50px; display: inline-block; margin-bottom: 20px; font-size: 0.9em; font-weight: 600;">{proj.get('tech_stack', '')}</div>
                        <p style="color: #a0aec0; line-height: 1.8; font-size: 1.1em; margin-bottom: 25px;">{proj.get('description', '')}</p>
                        {f'<a href="{proj["link"]}" style="color: #667eea; font-weight: 600; text-decoration: none;" target="_blank">View Project →</a>' if proj.get('link') else ''}
                    </div>
                    """
                elif template_name == "Neon Cyberpunk":
                    projects_html += f"""
                    <div class="cyber-card">
                        <div style="color: #00ffff; font-size: 1.2em; margin-bottom: 15px;">PROJECT {i:02d}</div>
                        <h3 class="card-title">{proj['title']}</h3>
                        <div style="background: rgba(255, 0, 255, 0.2); border: 1px solid #ff00ff; color: #ff00ff; padding: 8px 20px; display: inline-block; margin-bottom: 20px;">{proj.get('tech_stack', '')}</div>
                        <p style="color: #cccccc; line-height: 1.8; margin-bottom: 20px;">{proj.get('description', '')}</p>
                        {f'<a href="{proj["link"]}" style="color: #00ffff; text-decoration: none; font-weight: 700;" target="_blank">VIEW PROJECT →</a>' if proj.get('link') else ''}
                    </div>
                    """
                else:  # Elegant Minimalist
                    projects_html += f"""
                    <div class="work-item">
                        <h3 class="work-title">{proj['title']}</h3>
                        <div style="color: #999; font-size: 0.95em; margin-bottom: 20px; letter-spacing: 1px; text-transform: uppercase;">{proj.get('tech_stack', '')}</div>
                        <p style="color: #666; line-height: 1.9; font-size: 1.05em; margin-bottom: 25px;">{proj.get('description', '')}</p>
                        {f'<a href="{proj["link"]}" style="color: #2c2c2c; text-decoration: none; font-weight: 700; border-bottom: 2px solid #2c2c2c; padding-bottom: 2px;" target="_blank">VIEW PROJECT</a>' if proj.get('link') else ''}
                    </div>
                    """
        
        # Format experience based on template
        experience_html = ""
        for exp in data.get('experience', []):
            if exp.get('role'):
                if template_name == "Designer Portfolio":
                    experience_html += f"""
                    <div class="exp-item">
                        <div class="exp-role">{exp['role']}</div>
                        <div class="exp-company">{exp.get('company', '')}</div>
                        <div class="exp-duration">{exp.get('duration', '')}</div>
                        <p class="exp-desc">{exp.get('description', '')}</p>
                    </div>
                    """
                elif template_name == "Dark Modern Portfolio":
                    experience_html += f"""
                    <div class="exp-item">
                        <div class="exp-role">{exp['role']}</div>
                        <div class="exp-company">{exp.get('company', '')}</div>
                        <div class="exp-duration">{exp.get('duration', '')}</div>
                        <p class="exp-desc">{exp.get('description', '')}</p>
                    </div>
                    """
                elif template_name == "Neon Cyberpunk":
                    experience_html += f"""
                    <div class="cyber-card">
                        <div style="color: #ff00ff; font-size: 0.9em; margin-bottom: 10px;">{exp.get('duration', '')}</div>
                        <h3 class="card-title">{exp['role']}</h3>
                        <div style="color: #00ffff; font-weight: 600; margin-bottom: 15px;">{exp.get('company', '')}</div>
                        <p style="color: #cccccc; line-height: 1.8;">{exp.get('description', '')}</p>
                    </div>
                    """
                else:  # Elegant Minimalist
                    experience_html += f"""
                    <div class="work-item">
                        <h3 class="work-title">{exp['role']}</h3>
                        <div style="color: #999; font-size: 0.95em; margin-bottom: 10px; letter-spacing: 1px;">{exp.get('company', '')} • {exp.get('duration', '')}</div>
                        <p style="color: #666; line-height: 1.9; font-size: 1.05em;">{exp.get('description', '')}</p>
                    </div>
                    """
        
        # Format education based on template
        education_html = ""
        for edu in data.get('education', []):
            if edu.get('degree'):
                if template_name == "Designer Portfolio":
                    education_html += f"""
                    <div class="edu-card">
                        <div class="edu-degree">{edu['degree']}</div>
                        <div class="edu-college">{edu.get('college', '')}</div>
                        <div class="edu-details">
                            <span>{edu.get('cgpa', '')}</span>
                            <span>{edu.get('duration', '')}</span>
                        </div>
                    </div>
                    """
                elif template_name == "Dark Modern Portfolio":
                    education_html += f"""
                    <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; margin-bottom: 20px;">
                        <div style="font-size: 1.4em; font-weight: 700; margin-bottom: 10px;">{edu['degree']}</div>
                        <div style="color: #667eea; font-weight: 600; margin-bottom: 10px;">{edu.get('college', '')}</div>
                        <div style="color: #777; font-size: 0.9em;">{edu.get('cgpa', '')} • {edu.get('duration', '')}</div>
                    </div>
                    """
                elif template_name == "Neon Cyberpunk":
                    education_html += f"""
                    <div class="cyber-card">
                        <div style="color: #00ffff; font-size: 0.9em; margin-bottom: 10px;">{edu.get('duration', '')}</div>
                        <h3 class="card-title">{edu['degree']}</h3>
                        <div style="color: #ff00ff; font-weight: 600; margin-bottom: 10px;">{edu.get('college', '')}</div>
                        <div style="color: #cccccc;">CGPA: {edu.get('cgpa', '')}</div>
                    </div>
                    """
                else:  # Elegant Minimalist
                    education_html += f"""
                    <div style="padding: 30px 0; border-bottom: 1px solid #e8e8e8; margin-bottom: 30px;">
                        <h3 style="font-family: 'Cormorant Garamond', serif; font-size: 1.8em; margin-bottom: 10px;">{edu['degree']}</h3>
                        <div style="color: #999; font-size: 0.95em; margin-bottom: 10px; letter-spacing: 1px;">{edu.get('college', '')}</div>
                        <div style="color: #666;">{edu.get('cgpa', '')} • {edu.get('duration', '')}</div>
                    </div>
                    """
        
        # Format certifications based on template
        certifications_html = ""
        for cert in data.get('certifications', []):
            if cert.get('name'):
                if template_name == "Designer Portfolio":
                    certifications_html += f"""
                    <div class="cert-item">
                        <div class="cert-name">{cert['name']}</div>
                        <div class="cert-issuer">{cert.get('issuer', '')}</div>
                    </div>
                    """
                elif template_name == "Dark Modern Portfolio":
                    certifications_html += f"""
                    <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); padding: 25px; border-radius: 12px; border-left: 4px solid #667eea; margin-bottom: 15px;">
                        <div style="font-weight: 700; margin-bottom: 8px;">{cert['name']}</div>
                        <div style="color: #667eea; font-size: 0.9em;">{cert.get('issuer', '')}</div>
                    </div>
                    """
                elif template_name == "Neon Cyberpunk":
                    certifications_html += f"""
                    <div style="background: rgba(0, 0, 0, 0.8); border: 2px solid #00ffff; padding: 20px; margin-bottom: 15px;">
                        <div style="color: #00ffff; font-weight: 700; margin-bottom: 5px;">{cert['name']}</div>
                        <div style="color: #ff00ff; font-size: 0.9em;">{cert.get('issuer', '')}</div>
                    </div>
                    """
                else:  # Elegant Minimalist
                    certifications_html += f"""
                    <div style="padding: 20px 0; border-bottom: 1px solid #e8e8e8;">
                        <div style="font-weight: 700; margin-bottom: 5px;">{cert['name']}</div>
                        <div style="color: #999; font-size: 0.9em;">{cert.get('issuer', '')}</div>
                    </div>
                    """
        
        # Format achievements based on template
        achievements_html = ""
        for achievement in data.get('achievements', []):
            if achievement:
                if template_name == "Designer Portfolio":
                    achievements_html += f'<div class="achievement-item">• {achievement}</div>'
                elif template_name == "Dark Modern Portfolio":
                    achievements_html += f'<div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); padding: 25px 30px; border-radius: 12px; margin-bottom: 20px; color: #a0aec0; font-size: 1.05em; line-height: 1.8;">• {achievement}</div>'
                elif template_name == "Neon Cyberpunk":
                    achievements_html += f'<div style="background: rgba(0, 0, 0, 0.8); border: 2px solid #ff00ff; padding: 20px 25px; margin-bottom: 15px; color: #cccccc;">▸ {achievement}</div>'
                else:  # Elegant Minimalist
                    achievements_html += f'<div style="padding: 20px 0; border-bottom: 1px solid #e8e8e8; color: #666; line-height: 1.9;">• {achievement}</div>'
        
        # Format skills based on template
        skills_html = ""
        for cat, skills_list in data.get('skills', {}).items():
            if skills_list:
                if template_name == "Designer Portfolio":
                    skills_html += f'<div class="skill-card"><div class="skill-category">{cat}</div><div class="skill-list">{", ".join(skills_list)}</div></div>'
                elif template_name == "Dark Modern Portfolio":
                    skills_html += f'<div class="skill-card"><div class="skill-category">{cat}</div><div class="skill-list">{", ".join(skills_list)}</div></div>'
                elif template_name == "Neon Cyberpunk":
                    skills_html += f'<div style="background: rgba(0, 0, 0, 0.8); border: 2px solid #ff00ff; padding: 30px;"><div style="font-family: Orbitron, sans-serif; font-size: 1.3em; color: #ff00ff; margin-bottom: 15px;">{cat}</div><div style="color: #00ffff; line-height: 2;">{", ".join(skills_list)}</div></div>'
                else:  # Elegant Minimalist
                    skills_html += f'<div><div style="font-family: Cormorant Garamond, serif; font-size: 1.5em; font-weight: 700; margin-bottom: 15px;">{cat}</div><div style="color: #666; line-height: 2;">{", ".join(skills_list)}</div></div>'
        
        templates_html = {
            "Designer Portfolio": f"""
            <!DOCTYPE html>
            <html><head><meta charset="UTF-8">
            <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700;900&display=swap" rel="stylesheet">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ font-family: 'Poppins', sans-serif; background: #ffffff; }}
                nav {{ background: white; padding: 25px 60px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 20px rgba(0,0,0,0.08); position: sticky; top: 0; z-index: 1000; }}
                .logo {{ font-size: 1.8em; font-weight: 900; background: linear-gradient(135deg, #ff6b6b 0%, #feca57 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
                .nav-links {{ display: flex; gap: 40px; list-style: none; align-items: center; }}
                .nav-links a {{ color: #333; text-decoration: none; font-weight: 600; transition: color 0.3s; }}
                .nav-links a:hover {{ color: #ff6b6b; }}
                .cta-btn {{ background: linear-gradient(135deg, #ff6b6b 0%, #feca57 100%); color: white; padding: 12px 30px; border-radius: 50px; text-decoration: none; font-weight: 600; box-shadow: 0 5px 20px rgba(255, 107, 107, 0.3); }}
                .hero {{ background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%); padding: 120px 80px; text-align: center; }}
                .hero-tag {{ color: #ff6b6b; font-size: 1em; text-transform: uppercase; letter-spacing: 3px; font-weight: 700; margin-bottom: 25px; }}
                .hero h1 {{ font-size: 4.5em; color: #1a1a2e; margin-bottom: 30px; line-height: 1.1; font-weight: 900; }}
                .hero-desc {{ color: #666; line-height: 2; font-size: 1.2em; margin-bottom: 30px; max-width: 800px; margin-left: auto; margin-right: auto; }}
                .section {{ padding: 100px 80px; }}
                .section-alt {{ background: #f8f9fa; }}
                .section-title {{ text-align: center; font-size: 3.5em; color: #1a1a2e; margin-bottom: 70px; font-weight: 900; }}
                .section-title::after {{ content: ''; display: block; width: 100px; height: 5px; background: linear-gradient(135deg, #ff6b6b 0%, #feca57 100%); margin: 20px auto 0; border-radius: 3px; }}
                .skills-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 30px; max-width: 1200px; margin: 0 auto; }}
                .skill-card {{ background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); }}
                .skill-category {{ font-size: 1.3em; font-weight: 700; color: #ff6b6b; margin-bottom: 15px; }}
                .skill-list {{ color: #666; line-height: 2; }}
                .projects-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 40px; max-width: 1400px; margin: 0 auto; }}
                .project-card {{ background: white; border-radius: 20px; overflow: hidden; box-shadow: 0 10px 40px rgba(0,0,0,0.1); transition: all 0.3s; }}
                .project-card:hover {{ transform: translateY(-10px); box-shadow: 0 20px 60px rgba(0,0,0,0.15); }}
                .project-header {{ background: linear-gradient(135deg, #ff6b6b 0%, #feca57 100%); padding: 30px; color: white; }}
                .project-title {{ font-size: 1.8em; font-weight: 700; margin-bottom: 10px; }}
                .project-body {{ padding: 30px; }}
                .exp-item {{ background: white; padding: 35px; border-radius: 15px; box-shadow: 0 5px 20px rgba(0,0,0,0.08); margin-bottom: 30px; border-left: 5px solid #ff6b6b; max-width: 900px; margin-left: auto; margin-right: auto; }}
                .exp-role {{ font-size: 1.6em; font-weight: 700; color: #1a1a2e; margin-bottom: 10px; }}
                .exp-company {{ color: #ff6b6b; font-weight: 600; margin-bottom: 5px; }}
                .exp-duration {{ color: #999; font-size: 0.9em; margin-bottom: 15px; }}
                .exp-desc {{ color: #666; line-height: 1.8; }}
                .edu-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 30px; max-width: 1200px; margin: 0 auto; }}
                .edu-card {{ background: white; padding: 35px; border-radius: 15px; box-shadow: 0 5px 20px rgba(0,0,0,0.08); border-top: 4px solid #feca57; }}
                .edu-degree {{ font-size: 1.4em; font-weight: 700; color: #1a1a2e; margin-bottom: 10px; }}
                .edu-college {{ color: #666; margin-bottom: 10px; }}
                .edu-details {{ display: flex; gap: 20px; color: #999; font-size: 0.95em; }}
                .cert-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 25px; max-width: 1200px; margin: 0 auto; }}
                .cert-item {{ background: white; padding: 25px; border-radius: 12px; box-shadow: 0 5px 15px rgba(0,0,0,0.08); border-left: 4px solid #ff6b6b; }}
                .cert-name {{ font-weight: 700; color: #1a1a2e; margin-bottom: 8px; }}
                .cert-issuer {{ color: #ff6b6b; font-size: 0.9em; }}
                .achievement-item {{ background: white; padding: 25px 30px; border-radius: 12px; box-shadow: 0 5px 15px rgba(0,0,0,0.08); margin-bottom: 20px; color: #555; font-size: 1.05em; line-height: 1.8; max-width: 900px; margin-left: auto; margin-right: auto; }}
                .contact-section {{ background: linear-gradient(135deg, #1a1a2e 0%, #2d3561 100%); color: white; text-align: center; }}
                .contact-grid {{ display: flex; justify-content: center; gap: 40px; margin-top: 50px; flex-wrap: wrap; }}
                .contact-item {{ background: rgba(255,255,255,0.1); padding: 25px 35px; border-radius: 12px; }}
                .contact-label {{ font-size: 0.9em; opacity: 0.8; margin-bottom: 8px; }}
                .contact-value {{ font-weight: 600; font-size: 1.1em; }}
            </style></head><body>
                <nav>
                    <div class="logo">PORTFOLIO</div>
                    <ul class="nav-links">
                        <li><a href="#about">About</a></li>
                        <li><a href="#skills">Skills</a></li>
                        <li><a href="#projects">Projects</a></li>
                        <li><a href="#experience">Experience</a></li>
                        <li><a href="#contact">Contact</a></li>
                    </ul>
                    <a href="mailto:{data['personal_info']['email']}" class="cta-btn">Get In Touch</a>
                </nav>
                
                <section class="hero" id="about">
                    <div class="hero-tag">WELCOME TO MY PORTFOLIO</div>
                    <h1>{data['personal_info']['name']}</h1>
                    <p style="font-size: 1.5em; color: #ff6b6b; margin-bottom: 30px;">{data['personal_info']['tagline']}</p>
                    <p class="hero-desc">{data['about']}</p>
                </section>
                
                {f'<section class="section section-alt" id="skills"><h2 class="section-title">Skills & Expertise</h2><div class="skills-grid">{skills_html}</div></section>' if skills_html else ''}
                
                {f'<section class="section" id="projects"><h2 class="section-title">Featured Projects</h2><div class="projects-grid">{projects_html}</div></section>' if projects_html else ''}
                
                {f'<section class="section section-alt" id="experience"><h2 class="section-title">Experience</h2>{experience_html}</section>' if experience_html else ''}
                
                {f'<section class="section" id="education"><h2 class="section-title">Education</h2><div class="edu-grid">{education_html}</div></section>' if education_html else ''}
                
                {f'<section class="section section-alt" id="certifications"><h2 class="section-title">Certifications</h2><div class="cert-grid">{certifications_html}</div></section>' if certifications_html else ''}
                
                {f'<section class="section" id="achievements"><h2 class="section-title">Achievements</h2>{achievements_html}</section>' if achievements_html else ''}
                
                <section class="section contact-section" id="contact">
                    <h2 class="section-title" style="color: white;">Get In Touch</h2>
                    <div class="contact-grid">
                        <div class="contact-item"><div class="contact-label">Email</div><div class="contact-value">{data['personal_info'].get('email', '')}</div></div>
                        {f'<div class="contact-item"><div class="contact-label">LinkedIn</div><div class="contact-value">{data["personal_info"].get("linkedin", "")}</div></div>' if data['personal_info'].get('linkedin') else ''}
                        {f'<div class="contact-item"><div class="contact-label">GitHub</div><div class="contact-value">{data["personal_info"].get("github", "")}</div></div>' if data['personal_info'].get('github') else ''}
                    </div>
                </section>
            </body></html>
            """,
            
            "Dark Modern Portfolio": f"""
            <!DOCTYPE html>
            <html><head><meta charset="UTF-8">
            <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;600;700&display=swap" rel="stylesheet">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ font-family: 'Space Grotesk', sans-serif; background: #0a0a0a; color: white; }}
                header {{ padding: 120px 60px; text-align: center; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); }}
                .header-title {{ font-size: 5em; font-weight: 900; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
                .hero {{ max-width: 1200px; margin: 80px auto; padding: 0 60px; text-align: center; }}
                .hero-heading {{ font-size: 3.8em; margin-bottom: 30px; font-weight: 900; }}
                .section {{ max-width: 1400px; margin: 100px auto; padding: 0 60px; }}
                .section-title {{ font-size: 3em; font-weight: 700; margin-bottom: 60px; text-align: center; }}
                .projects-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(450px, 1fr)); gap: 40px; }}
                .project-card {{ background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 25px; padding: 45px; }}
                .project-title {{ font-size: 2em; font-weight: 700; margin-bottom: 20px; }}
                .skills-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 30px; }}
                .skill-card {{ background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; }}
                .skill-category {{ font-size: 1.3em; font-weight: 700; color: #667eea; margin-bottom: 15px; }}
                .skill-list {{ color: #a0aec0; line-height: 2; }}
                .exp-item {{ background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); padding: 35px; border-radius: 15px; margin-bottom: 30px; }}
                .exp-role {{ font-size: 1.6em; font-weight: 700; margin-bottom: 10px; }}
                .exp-company {{ color: #667eea; font-weight: 600; margin-bottom: 5px; }}
                .exp-duration {{ color: #777; font-size: 0.9em; margin-bottom: 15px; }}
                .exp-desc {{ color: #a0aec0; line-height: 1.8; }}
                .contact-section {{ background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); padding: 80px 60px; text-align: center; margin: 100px auto; max-width: 1400px; }}
            </style></head><body>
                <header>
                    <div class="header-title">{data['personal_info']['tagline']}</div>
                </header>
                <div class="hero">
                    <h1 class="hero-heading">Hello! I Am<br>{data['personal_info']['name']}</h1>
                    <p style="color: #a0aec0; line-height: 2; font-size: 1.2em; max-width: 800px; margin: 0 auto;">{data['about']}</p>
                </div>
                {f'<div class="section"><h2 class="section-title">Skills</h2><div class="skills-grid">{skills_html}</div></div>' if skills_html else ''}
                {f'<div class="section"><h2 class="section-title">Projects</h2><div class="projects-grid">{projects_html}</div></div>' if projects_html else ''}
                {f'<div class="section"><h2 class="section-title">Experience</h2>{experience_html}</div>' if experience_html else ''}
                {f'<div class="section"><h2 class="section-title">Education</h2>{education_html}</div>' if education_html else ''}
                {f'<div class="section"><h2 class="section-title">Certifications</h2>{certifications_html}</div>' if certifications_html else ''}
                {f'<div class="section"><h2 class="section-title">Achievements</h2>{achievements_html}</div>' if achievements_html else ''}
                <div class="contact-section">
                    <h2 class="section-title">Get In Touch</h2>
                    <p style="color: #a0aec0; font-size: 1.1em; margin-bottom: 30px;">Email: {data['personal_info'].get('email', '')}</p>
                </div>
            </body></html>
            """,
            
            "Neon Cyberpunk": f"""
            <!DOCTYPE html>
            <html><head><meta charset="UTF-8">
            <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;600&display=swap" rel="stylesheet">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ font-family: 'Rajdhani', sans-serif; background: #000000; color: #00ffff; }}
                .top-bar {{ background: rgba(0, 0, 0, 0.9); border-bottom: 2px solid #00ffff; padding: 20px 60px; }}
                .logo-cyber {{ font-family: 'Orbitron', sans-serif; font-size: 2em; font-weight: 900; color: #00ffff; text-shadow: 0 0 20px #00ffff; }}
                .cyber-hero {{ padding: 150px 80px; background: radial-gradient(circle at 50% 50%, #1a0033 0%, #000000 100%); text-align: center; }}
                .glitch-text {{ font-family: 'Orbitron', sans-serif; font-size: 6em; font-weight: 900; color: #00ffff; text-shadow: 0 0 20px #00ffff; }}
                .section {{ padding: 100px 80px; }}
                .section-title {{ font-family: 'Orbitron', sans-serif; font-size: 3em; color: #00ffff; text-align: center; margin-bottom: 60px; text-shadow: 0 0 20px #00ffff; }}
                .cyber-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(450px, 1fr)); gap: 50px; }}
                .cyber-card {{ background: rgba(0, 0, 0, 0.8); border: 2px solid #00ffff; padding: 40px; }}
                .card-title {{ font-family: 'Orbitron', sans-serif; font-size: 2.2em; color: #ffffff; margin-bottom: 20px; }}
                .skills-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 30px; }}
            </style></head><body>
                <div class="top-bar"><div class="logo-cyber">CYBER_PORT</div></div>
                <section class="cyber-hero">
                    <h1 class="glitch-text">{data['personal_info']['name']}</h1>
                    <p style="font-size: 2em; color: #ff00ff; margin: 20px 0;">{data['personal_info']['tagline']}</p>
                    <p style="color: #ffffff; line-height: 1.9; max-width: 800px; margin: 40px auto; font-size: 1.2em;">{data['about']}</p>
                </section>
                {f'<section class="section"><h2 class="section-title">SKILLS</h2><div class="skills-grid">{skills_html}</div></section>' if skills_html else ''}
                {f'<section class="section"><h2 class="section-title">PROJECTS</h2><div class="cyber-grid">{projects_html}</div></section>' if projects_html else ''}
                {f'<section class="section"><h2 class="section-title">EXPERIENCE</h2><div class="cyber-grid">{experience_html}</div></section>' if experience_html else ''}
                {f'<section class="section"><h2 class="section-title">EDUCATION</h2><div class="cyber-grid">{education_html}</div></section>' if education_html else ''}
                {f'<section class="section"><h2 class="section-title">CERTIFICATIONS</h2>{certifications_html}</section>' if certifications_html else ''}
                {f'<section class="section"><h2 class="section-title">ACHIEVEMENTS</h2>{achievements_html}</section>' if achievements_html else ''}
                <section class="section" style="text-align: center;">
                    <h2 class="section-title">CONTACT</h2>
                    <p style="font-size: 1.3em; color: #ff00ff;">Email: {data['personal_info'].get('email', '')}</p>
                </section>
            </body></html>
            """,
            
            "Elegant Minimalist": f"""
            <!DOCTYPE html>
            <html><head><meta charset="UTF-8">
            <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;600;700&family=Lato:wght@300;400&display=swap" rel="stylesheet">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ font-family: 'Lato', sans-serif; background: #fafafa; color: #2c2c2c; }}
                header {{ padding: 40px 60px; background: white; border-bottom: 1px solid #e0e0e0; }}
                .initials {{ font-family: 'Cormorant Garamond', serif; font-size: 2.5em; font-weight: 700; }}
                .hero-minimal {{ padding: 120px 60px 80px; background: white; text-align: center; }}
                .hero-name {{ font-family: 'Cormorant Garamond', serif; font-size: 5em; font-weight: 300; margin-bottom: 20px; }}
                .divider {{ width: 60px; height: 2px; background: #2c2c2c; margin: 50px auto; }}
                .section {{ padding: 100px 60px; background: white; max-width: 1000px; margin: 0 auto; }}
                .section-heading {{ font-family: 'Cormorant Garamond', serif; font-size: 3.5em; text-align: center; margin-bottom: 80px; }}
                .work-grid {{ display: grid; gap: 80px; }}
                .work-item {{ padding: 50px 0; border-bottom: 1px solid #e8e8e8; }}
                .work-title {{ font-family: 'Cormorant Garamond', serif; font-size: 2.5em; margin-bottom: 15px; }}
                .skills-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 40px; margin-top: 60px; }}
            </style></head><body>
                <header><div class="initials">{initials}</div></header>
                <section class="hero-minimal">
                    <h1 class="hero-name">{data['personal_info']['name']}</h1>
                    <p style="font-size: 1.3em; color: #666; margin-bottom: 50px;">{data['personal_info']['tagline']}</p>
                    <div class="divider"></div>
                    <p style="max-width: 700px; margin: 0 auto; font-size: 1.15em; line-height: 2; color: #555;">{data['about']}</p>
                </section>
                {f'<section class="section"><h2 class="section-heading">Skills</h2><div class="skills-grid">{skills_html}</div></section>' if skills_html else ''}
                {f'<section class="section"><h2 class="section-heading">Selected Works</h2><div class="work-grid">{projects_html}</div></section>' if projects_html else ''}
                {f'<section class="section"><h2 class="section-heading">Experience</h2><div class="work-grid">{experience_html}</div></section>' if experience_html else ''}
                {f'<section class="section"><h2 class="section-heading">Education</h2>{education_html}</section>' if education_html else ''}
                {f'<section class="section"><h2 class="section-heading">Certifications</h2>{certifications_html}</section>' if certifications_html else ''}
                {f'<section class="section"><h2 class="section-heading">Achievements</h2>{achievements_html}</section>' if achievements_html else ''}
                <section class="section" style="text-align: center;">
                    <h2 class="section-heading">Contact</h2>
                    <p style="font-size: 1.2em; color: #666;">Email: {data['personal_info'].get('email', '')}</p>
                </section>
            </body></html>
            """
        }
        
        return templates_html.get(template_name, templates_html["Designer Portfolio"])
        
    def render_analyzer(self):
         """Render the resume analyzer page"""
         apply_modern_styles()
         self.add_back_to_home_button()
     
         # Page Header
         page_header(
             "Resume Analyzer",
             "Get instant AI-powered feedback to optimize your resume"
         )
         st.markdown("""
            <style>
             .stTabs [data-baseweb="tab-list"] {
                 justify-content: center;
                 margin-top: 20px;
                 margin-bottom: 20px;
                 gap: 10px;
             }
         
             /* Base style for each tab */
             .stTabs [data-baseweb="tab"] {
                 background-color: #f0f0f0;
                 border: 1px solid #ddd;
                 border-radius: 8px;
                 padding: 10px 24px;
                 font-size: 16px;
                 font-weight: 600;
                 color: #333;
                 transition: all 0.2s ease-in-out;
             }
         
             /* Hover effect */
             .stTabs [data-baseweb="tab"]:hover {
                 background-color: #e0f5ec;
                 border-color: #00bfa5;
                 color: #111;
                 transform: translateY(-2px);
                 cursor: pointer;
             }
         
             /* Selected/active tab style */
             .stTabs [aria-selected="true"] {
                 background-color: #00bfa5 !important;
                 color: white !important;
                 border: 1px solid #00bfa5;
                 font-weight: 700;
                 box-shadow: 0px 4px 12px rgba(0, 191, 165, 0.2);
             }
             </style>
         """, unsafe_allow_html=True)
         # Create tabs for Normal Analyzer, AI Analyzer, and Multi-Resume Analyzer
         analyzer_tabs = st.tabs(["Standard Analyzer", "AI Analyzer", "Multi-Resume Analyzer"])
     
         with analyzer_tabs[0]:
            # Job Role Selection
            categories = list(self.job_roles.keys())
            selected_category = st.selectbox(
    "Job Category", categories, key="standard_category")

            roles = list(self.job_roles[selected_category].keys())
            selected_role = st.selectbox(
    "Specific Role", roles, key="standard_role")

            role_info = self.job_roles[selected_category][selected_role]

            # Display role information
            st.markdown(f"""
            <div style='background-color: #1e1e1e; padding: 20px; border-radius: 10px; margin: 10px 0;'>
                <h3>{selected_role}</h3>
                <p>{role_info['description']}</p>
                <h4>Required Skills:</h4>
                <p>{', '.join(role_info['required_skills'])}</p>
            </div>
            """, unsafe_allow_html=True)

            # File Upload
            uploaded_file = st.file_uploader(
    "Upload your resume", type=[
        'pdf', 'docx'], key="standard_file")

            if not uploaded_file:
                # Display empty state with a prominent upload button
                st.markdown(
                    self.render_empty_state(
                    "fas fa-cloud-upload-alt",
                    "Upload your resume to get started with standard analysis"
                    ),
                    unsafe_allow_html=True
                )
                # Add a prominent upload button
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.markdown("""
                    <style>
                    .upload-button {
                        background: linear-gradient(90deg, #4b6cb7, #182848);
                        color: white;
                        border: none;
                        border-radius: 10px;
                        padding: 15px 25px;
                        font-size: 18px;
                        font-weight: bold;
                        cursor: pointer;
                        width: 100%;
                        text-align: center;
                        margin: 20px 0;
                        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
                        transition: all 0.3s ease;
                    }
                    .upload-button:hover {
                        transform: translateY(-3px);
                        box-shadow: 0 6px 15px rgba(0,0,0,0.3);
                    }

                    """, unsafe_allow_html=True)

            if uploaded_file:
                # Add a prominent analyze button
                analyze_standard = st.button("🔍 Analyze My Resume",
                                    type="primary",
                                    use_container_width=True,
                                    key="analyze_standard_button")

                if analyze_standard:
                    with st.spinner("Analyzing your document..."):
                        # Get file content
                        text = ""
                        try:
                            if uploaded_file.type == "application/pdf":
                                try:
                                    text = self.analyzer.extract_text_from_pdf(uploaded_file)
                                except Exception as pdf_error:
                                    st.error(f"PDF extraction failed: {str(pdf_error)}")
                                    st.info("Trying alternative PDF extraction method...")
                                    # Try AI analyzer as backup
                                    try:
                                        text = self.ai_analyzer.extract_text_from_pdf(uploaded_file)
                                    except Exception as backup_error:
                                        st.error(f"All PDF extraction methods failed: {str(backup_error)}")
                                        return
                            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                                try:
                                    text = self.analyzer.extract_text_from_docx(uploaded_file)
                                except Exception as docx_error:
                                    st.error(f"DOCX extraction failed: {str(docx_error)}")
                                    # Try AI analyzer as backup
                                    try:
                                        text = self.ai_analyzer.extract_text_from_docx(uploaded_file)
                                    except Exception as backup_error:
                                        st.error(f"All DOCX extraction methods failed: {str(backup_error)}")
                                        return
                            else:
                                text = uploaded_file.getvalue().decode()
                                
                            if not text or text.strip() == "":
                                st.error("Could not extract any text from the uploaded file. Please try a different file.")
                                return
                        except Exception as e:
                            st.error(f"Error reading file: {str(e)}")
                            return

                        # Analyze the document
                        analysis = self.analyzer.analyze_resume({'raw_text': text}, role_info)
                        
                        # Check if analysis returned an error
                        if 'error' in analysis:
                            st.error(analysis['error'])
                            return


                        # Save resume data to database
                        resume_data = {
                            'personal_info': {
                                'name': analysis.get('name', ''),
                                'email': analysis.get('email', ''),
                                'phone': analysis.get('phone', ''),
                                'linkedin': analysis.get('linkedin', ''),
                                'github': analysis.get('github', ''),
                                'portfolio': analysis.get('portfolio', '')
                            },
                            'summary': analysis.get('summary', ''),
                            'target_role': selected_role,
                            'target_category': selected_category,
                            'education': analysis.get('education', []),
                            'experience': analysis.get('experience', []),
                            'projects': analysis.get('projects', []),
                            'skills': analysis.get('skills', []),
                            'template': ''
                        }

                        # Save to database
                        try:
                            resume_id = save_resume_data(resume_data)

                            # Save analysis data
                            analysis_data = {
                                'resume_id': resume_id,
                                'ats_score': analysis['ats_score'],
                                'keyword_match_score': analysis['keyword_match']['score'],
                                'format_score': analysis['format_score'],
                                'section_score': analysis['section_score'],
                                'missing_skills': ','.join(analysis['keyword_match']['missing_skills']),
                                'recommendations': ','.join(analysis['suggestions'])
                            }
                            save_analysis_data(resume_id, analysis_data)
                            st.success("Resume data saved successfully!")
                        except Exception as e:
                            st.error(f"Error saving to database: {str(e)}")
                            print(f"Database error: {e}")

                        # Show results based on document type
                        if analysis.get('document_type') != 'resume':
                            st.error(
    f"⚠️ This appears to be a {
        analysis['document_type']} document, not a resume!")
                            st.warning(
                                "Please upload a proper resume for ATS analysis.")
                            return
                     
                    st.markdown("---")
                    st.markdown("## 📊 Analysis Results")
                    
                    # === TOP METRICS ROW ===
                    metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
                    
                    with metrics_col1:
                        # ATS Score with color coding
                        ats_score = analysis['ats_score']
                        score_color = '#4CAF50' if ats_score >= 80 else '#FFA500' if ats_score >= 60 else '#FF4444'
                        status = 'Excellent' if ats_score >= 80 else 'Good' if ats_score >= 60 else 'Needs Improvement'
                        
                        st.markdown(f"""
                        <div class="metric-card" style="text-align: center; padding: 20px; background: linear-gradient(135deg, #1e1e1e, #2a2a2a); border-radius: 15px; margin: 10px 0; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
                            <h3 style="color: #fff; margin-bottom: 15px;">🎯 ATS Score</h3>
                            <div style="font-size: 2.5em; font-weight: bold; color: {score_color};">{ats_score}</div>
                            <div style="color: {score_color}; font-weight: bold; margin-top: 5px;">{status}</div>
                        </div>
                        """, unsafe_allow_html=True)
            
                    with metrics_col2:
                        keyword_score = int(analysis.get('keyword_match', {}).get('score', 0))
                        st.markdown(f"""
                        <div class="metric-card" style="text-align: center; padding: 20px; background: linear-gradient(135deg, #1e1e1e, #2a2a2a); border-radius: 15px; margin: 10px 0; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
                            <h3 style="color: #fff; margin-bottom: 15px;">🔍 Keywords</h3>
                            <div style="font-size: 2.5em; font-weight: bold; color: #64B5F6;">{keyword_score}%</div>
                            <div style="color: #64B5F6; font-weight: bold; margin-top: 5px;">Match Rate</div>
                        </div>
                        """, unsafe_allow_html=True)
            
                    with metrics_col3:
                        format_score = int(analysis.get('format_score', 0))
                        st.markdown(f"""
                        <div class="metric-card" style="text-align: center; padding: 20px; background: linear-gradient(135deg, #1e1e1e, #2a2a2a); border-radius: 15px; margin: 10px 0; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
                            <h3 style="color: #fff; margin-bottom: 15px;">📄 Format</h3>
                            <div style="font-size: 2.5em; font-weight: bold; color: #81C784;">{format_score}%</div>
                            <div style="color: #81C784; font-weight: bold; margin-top: 5px;">Structure</div>
                        </div>
                        """, unsafe_allow_html=True)
            
                    with metrics_col4:
                        section_score = int(analysis.get('section_score', 0))
                        st.markdown(f"""
                        <div class="metric-card" style="text-align: center; padding: 20px; background: linear-gradient(135deg, #1e1e1e, #2a2a2a); border-radius: 15px; margin: 10px 0; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
                            <h3 style="color: #fff; margin-bottom: 15px;">📋 Sections</h3>
                            <div style="font-size: 2.5em; font-weight: bold; color: #FFB74D;">{section_score}%</div>
                            <div style="color: #FFB74D; font-weight: bold; margin-top: 5px;">Complete</div>
                        </div>
                        """, unsafe_allow_html=True)
            
                    st.markdown("<br>", unsafe_allow_html=True)
            
            
                    # Main Feature Card Container
                    
                    st.markdown("## 📋 Resume Improvement Suggestions")
                    # Enhanced helper function to render each suggestion section
                    def render_section(title, suggestions, bullet_icon="✓", nested_items=None):
                        """
                        Render a suggestion section with optional nested items
                        """
                        if suggestions or nested_items:
                            st.markdown(f"""
                            <div style='
                                background-color: #1e1e1e;
                                padding: 5px;
                                border-radius: 12px;
                                margin-bottom: 5px;
                                border-left: 4px solid #4CAF50;
                            '>
                                <h3 style='color: #4CAF50; margin-bottom: 15px;'>{title}</h3>
                            """, unsafe_allow_html=True)
                            
                            # Main suggestions
                            if suggestions:
                                st.markdown("<ul style='list-style-type: none; padding-left: 0;'>", unsafe_allow_html=True)
                                for item in suggestions:
                                    st.markdown(f"""
                                        <li style='margin-bottom: 10px; color: #e0e0e0;'>
                                            <span style='color: #4CAF50; margin-right: 8px;'>{bullet_icon}</span>{item}
                                        </li>
                                    """, unsafe_allow_html=True)
                                st.markdown("</ul>", unsafe_allow_html=True)
                            
                            # Nested items (for missing skills)
                            if nested_items:
                                
                                for skill in nested_items:
                                    st.markdown(f"""
                                        <li style='margin-bottom: 6px; margin-left: 15px; color: #ccc;'>
                                            <span style='color: #66BB6A; margin-right: 8px;'>•</span>{skill}
                                        </li>
                                    """, unsafe_allow_html=True)
                                st.markdown("</ul></div>", unsafe_allow_html=True)
                            
                            st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Render Each Section
                    render_section("📞 Contact Information", analysis.get('contact_suggestions', []))
                    render_section("📝 Professional Summary", analysis.get('summary_suggestions', []))
                    
                    # Skills section with nested missing skills
                    skills_suggestions = analysis.get('skills_suggestions', [])
                    missing_skills = analysis.get('keyword_match', {}).get('missing_skills', [])
                    render_section("🎯 Skills", skills_suggestions, nested_items=missing_skills)
                    
                    render_section("💼 Work Experience", analysis.get('experience_suggestions', []))
                    render_section("🎓 Education", analysis.get('education_suggestions', []))
                    render_section("📄 Formatting", analysis.get('format_suggestions', []))
                    
                    # Close main container
                    st.markdown("</div>", unsafe_allow_html=True)
                        # Course Recommendations
                    st.markdown("## 📚 Recommended Courses ")
                    

                        # Get courses based on role and category
                    courses = get_courses_for_role(selected_role)
                    if not courses:
                            category = get_category_for_role(selected_role)
                            courses = COURSES_BY_CATEGORY.get(
                                category, {}).get(selected_role, [])

                        # Display courses in a grid
                    cols = st.columns(2)
                    for i, course in enumerate(
                        courses[:6]):  # Show top 6 courses
                            with cols[i % 2]:
                                st.markdown(f"""
                                <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                                    <h4>{course[0]}</h4>
                                    <a href='{course[1]}' target='_blank'>View Course</a>
                                </div>
                                """, unsafe_allow_html=True)

                    st.markdown("</div>", unsafe_allow_html=True)

                        # Learning Resources
                    st.markdown("## 📺 Helpful Videos")
                            

                    tab1, tab2 = st.tabs(["Resume Tips", "Interview Tips"])

                    with tab1:
                            # Resume Videos
                            for category, videos in RESUME_VIDEOS.items():
                                st.subheader(category)
                                cols = st.columns(2)
                                for i, video in enumerate(videos):
                                    with cols[i % 2]:
                                        st.video(video[1])

                    with tab2:
                            # Interview Videos
                            for category, videos in INTERVIEW_VIDEOS.items():
                                st.subheader(category)
                                cols = st.columns(2)
                                for i, video in enumerate(videos):
                                    with cols[i % 2]:
                                        st.video(video[1])

                    st.markdown("</div>", unsafe_allow_html=True)

         with analyzer_tabs[1]:
              st.markdown("""
              <div style='background-color: #1e1e1e; padding: 20px; border-radius: 10px; margin: 10px 0;'>
                  <h3>🚀 ATS Resume Optimizer</h3>
                  <p>Transform your resume into an ATS-friendly format that passes automated screening systems.</p>
                  <p><strong>Upload your resume and optionally provide a job description for targeted optimization.</strong></p>
              </div>
              """, unsafe_allow_html=True)
              
              # Initialize the optimizer
              if 'ats_optimizer' not in st.session_state:
                  st.session_state.ats_optimizer = self.ai_analyzer  # Use existing analyzer
              
              optimizer = st.session_state.ats_optimizer
              
              # Create two columns for better layout
              col_left, col_right = st.columns([1, 1])
              
              with col_left:
                  st.subheader("📄 Upload Resume")
                  
                  # File upload
                  uploaded_file = st.file_uploader(
                      "Choose your resume file",
                      type=['pdf', 'docx'],
                      help="Upload your current resume in PDF or DOCX format",
                      key="ats_file_upload"
                  )
                  
                  if uploaded_file:
                      st.success(f"✅ Uploaded: {uploaded_file.name}")
                      
                      # Extract text silently (no display)
                      with st.spinner("📖 Processing resume..."):
                          if uploaded_file.name.endswith('.pdf'):
                              resume_text = optimizer.extract_text_from_pdf(uploaded_file)
                          else:
                              resume_text = optimizer.extract_text_from_docx(uploaded_file)
                      
                      if resume_text:
                          # Store in session state (no display)
                          st.session_state['ats_resume_text'] = resume_text
                      else:
                          st.error("❌ Failed to extract text from resume")
              
              with col_right:
                  st.subheader("🎯 Optimization Settings")
                  
                  # Job role input
                  job_role = st.text_input(
                      "Target Job Role (Optional)",
                      placeholder="e.g., Senior Software Engineer, Data Scientist",
                      help="Specify the job role to optimize your resume with relevant keywords",
                      key="ats_job_role"
                  )
                  
                  # Job description input
                  use_job_desc = st.checkbox(
                      "Add Job Description for Better Optimization",
                      value=False,
                      help="Paste the actual job description to tailor your resume specifically",
                      key="ats_use_job_desc"
                  )
                  
                  job_description = ""
                  if use_job_desc:
                      job_description = st.text_area(
                          "Paste Job Description Here",
                          placeholder="Copy and paste the full job description from the posting...",
                          height=200,
                          help="The AI will optimize your resume to match this specific job",
                          key="ats_job_desc"
                      )
                      
                      if job_description:
                          st.info("💡 **Tip**: Including the job description significantly improves keyword matching and ATS compatibility!")
              
              # Optimize button (full width)
              st.markdown("<br>", unsafe_allow_html=True)
              optimize_col1, optimize_col2, optimize_col3 = st.columns([1, 2, 1])
              
              with optimize_col2:
                  optimize_button = st.button(
                      " Optimize Resume for ATS",
                      type="primary",
                      use_container_width=True,
                      key="ats_optimize_btn"
                  )
              
              # Process optimization
              if optimize_button:
                  if not uploaded_file:
                      st.error("⚠️ Please upload a resume first")
                  elif 'ats_resume_text' not in st.session_state or not st.session_state['ats_resume_text']:
                      st.error("⚠️ Could not extract text from resume. Please try a different file.")
                  else:
                      with st.spinner("🔄 Optimizing your resume for ATS... This may take a moment..."):
                          # Show progress
                          progress_bar = st.progress(0)
                          progress_bar.progress(20)
                          
                          result = optimizer.optimize_resume_with_gemini(
                              st.session_state['ats_resume_text'],
                              job_description=job_description if job_description else None,
                              job_role=job_role if job_role else None
                          )
                          
                          progress_bar.progress(100)
                      
                      if "error" in result:
                          st.error(f"❌ {result['error']}")
                      elif result.get("success"):
                          optimized_text = result.get("optimized_resume", "")
                          
                          # Store in session state
                          st.session_state['ats_optimized_text'] = optimized_text
                          
                          st.success("✅ Resume optimization complete!")
                          
                          # Show success message with features
                          st.markdown("""
                          <div style='background-color: #1e3c72; padding: 20px; border-radius: 10px; margin: 20px 0; text-align: center;'>
                              <h3 style='color: white; margin-bottom: 15px;'>✨ Your Resume Has Been Optimized!</h3>
                              <div style='display: flex; justify-content: space-around; flex-wrap: wrap; gap: 15px;'>
                                  <div style='flex: 1; min-width: 200px;'>
                                      <div style='font-size: 40px; margin-bottom: 10px;'>✓</div>
                                      <p style='color: white; margin: 0;'><strong>ATS-Friendly Format</strong></p>
                                  </div>
                                  <div style='flex: 1; min-width: 200px;'>
                                      <div style='font-size: 40px; margin-bottom: 10px;'>🔑</div>
                                      <p style='color: white; margin: 0;'><strong>Keyword Optimized</strong></p>
                                  </div>
                                  <div style='flex: 1; min-width: 200px;'>
                                      <div style='font-size: 40px; margin-bottom: 10px;'>📄</div>
                                      <p style='color: white; margin: 0;'><strong>Professional Layout</strong></p>
                                  </div>
                                  <div style='flex: 1; min-width: 200px;'>
                                      <div style='font-size: 40px; margin-bottom: 10px;'>🚀</div>
                                      <p style='color: white; margin: 0;'><strong>Ready to Use</strong></p>
                                  </div>
                              </div>
                          </div>
                          """, unsafe_allow_html=True)
                          
                          # Download buttons
                          st.markdown("### 📥 Download Your Optimized Resume")
                          
                          download_col1, download_col2, download_col3 = st.columns(3)
                          
                          with download_col1:
                              # Download as TXT
                              st.download_button(
                                  label="📝 Download as TXT",
                                  data=optimized_text,
                                  file_name="ats_optimized_resume.txt",
                                  mime="text/plain",
                                  use_container_width=True,
                                  key="download_txt"
                              )
                          
                          with download_col2:
                              # Create and download as DOCX
                              with st.spinner("Creating DOCX..."):
                                  docx_buffer = optimizer.create_docx_resume(
                                      optimized_text,
                                      candidate_name="ATS Optimized Resume"
                                  )
                              
                              if docx_buffer:
                                  st.download_button(
                                      label="📄 Download as DOCX",
                                      data=docx_buffer,
                                      file_name="ats_optimized_resume.docx",
                                      mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                      use_container_width=True,
                                      key="download_docx"
                                  )
                          
                        #   with download_col3:
                        #       # Clear button
                        #       if st.button("🔄 Start Over", use_container_width=True, key="clear_btn"):
                        #           if 'ats_resume_text' in st.session_state:
                        #               del st.session_state['ats_resume_text']
                        #           if 'ats_optimized_text' in st.session_state:
                        #               del st.session_state['ats_optimized_text']
                        #           st.rerun()
                          
                          # Show optimization tips
                          with st.expander("💡 What Changed? ATS Optimization Details", expanded=False):
                              st.markdown("""
                              ### ✅ Your Resume Has Been Optimized With:
                              
                              **Formatting Improvements:**
                              - 🎯 Clear section headers (Professional Summary, Skills, Experience, Education)
                              - 📊 Consistent formatting throughout
                              - 🔤 ATS-friendly fonts and structure
                              - 📝 Proper bullet point usage
                              
                              **Content Enhancements:**
                              - 🔑 Relevant keywords for your target role
                              - 💪 Strong action verbs (Led, Developed, Achieved, Implemented)
                              - 📈 Quantified achievements with metrics
                              - 🎓 Highlighted technical and soft skills
                              
                              **ATS Compatibility:**
                              - ✅ No complex tables or graphics
                              - ✅ Standard section naming
                              - ✅ Keyword-rich content
                              - ✅ Parseable format for automated systems
                              
                              ### 📌 Next Steps:
                              1. **Review** the optimized content carefully
                              2. **Customize** any sections to match your personal voice
                              3. **Download** in your preferred format (DOCX recommended)
                              4. **Apply** with confidence knowing your resume will pass ATS screening!
                              
                              ### ⚠️ Important Reminders:
                              - Always proofread before submitting
                              - Ensure all dates and information are accurate
                              - Tailor further for each specific job application
                              - Keep a master copy for future updates
                              """)
                          
                          # Show keyword analysis (if job description was provided)
                          if job_description:
                              with st.expander("🔍 Keyword Match Analysis", expanded=False):
                                  st.markdown("""
                                  **Keywords from Job Description:**
                                  
                                  Your resume has been optimized to include relevant keywords from the provided job description.
                                  This significantly increases your chances of passing ATS screening!
                                  
                                  💡 **Pro Tip**: The more specific the job description, the better the optimization!
                                  """)
              
              
     
         with analyzer_tabs[2]:  # Multi-Resume Analyzer Tab
             st.markdown("""
             <div style='background-color: #1e1e1e; padding: 20px; border-radius: 10px; margin: 10px 0;'>
                 <h3>🚀 Multi-Resume Analyzer</h3>
                 <p>Upload multiple resumes to compare and find the best one for your target role!</p>
             </div>
             """, unsafe_allow_html=True)
     
             # Job Role Selection for Multi-Resume
             categories = list(self.job_roles.keys())
             selected_category_multi = st.selectbox(
                 "Job Category", categories, key="multi_category")
     
             roles = list(self.job_roles[selected_category_multi].keys())
             selected_role_multi = st.selectbox(
                 "Specific Role", roles, key="multi_role")
     
             role_info_multi = self.job_roles[selected_category_multi][selected_role_multi]
     
             # Display role information
             st.markdown(f"""
             <div style='background-color: #1e1e1e; padding: 20px; border-radius: 10px; margin: 10px 0;'>
                 <h3>{selected_role_multi}</h3>
                 <p>{role_info_multi['description']}</p>
                 <h4>Required Skills:</h4>
                 <p>{', '.join(role_info_multi['required_skills'])}</p>
             </div>
             """, unsafe_allow_html=True)
             
             # Multiple File Upload
             uploaded_files = st.file_uploader(
                 "Upload multiple resumes for comparison",
                 type=['pdf', 'docx'],
                 accept_multiple_files=True,
                 key="multi_files",
                 help="Upload 2-10 resumes to compare and find the best one"
             )
             
             # ---- EMPTY STATE REMOVED HERE ----
             # You said to remove the full st.markdown empty state block
             
             if not uploaded_files:
                 pass  # Do nothing when no files uploaded
             
             elif len(uploaded_files) < 2:
                 st.warning("⚠️ Please upload at least 2 resumes for comparison.")
             
             elif len(uploaded_files) > 10:
                 st.error("❌ Maximum 10 resumes allowed for comparison.")
             
             else:
                 st.success(f"✅ {len(uploaded_files)} resumes uploaded successfully!")
             
                 # Display uploaded files
                 st.markdown("### Uploaded Resumes:")
                 cols = st.columns(min(3, len(uploaded_files)))
             
                 for i, file in enumerate(uploaded_files):
                     with cols[i % 3]:
                         st.markdown(f"""
                         <div style='background-color: #2d2d2d; padding: 15px; border-radius: 10px; margin: 5px 0; text-align: center;'>
                             <i class='fas fa-file-alt' style='font-size: 2em; color: #4b6cb7; margin-bottom: 10px;'></i>
                             <p style='margin: 0; font-weight: bold;'>{file.name}</p>
                             <p style='margin: 0; color: #888; font-size: 0.9em;'>{file.type.split('/')[-1].upper()}</p>
                         </div>
                         """, unsafe_allow_html=True)
             
                  
                 # Analyze Multiple Resumes Button
                 analyze_multiple = st.button(
                     "🚀 Analyze & Compare All Resumes",
                     type="primary",
                     use_container_width=True,
                     key="analyze_multiple_button"
                 )
     
                 if analyze_multiple:
                     self._analyze_multiple_resumes(uploaded_files, role_info_multi, selected_role_multi, selected_category_multi)
     
    def _analyze_single_resume(self, uploaded_file, role_info, selected_role, selected_category):
         """Analyze a single resume (existing functionality)"""
         with st.spinner("Analyzing your document..."):
             # Get file content
             text = ""
             try:
                 if uploaded_file.type == "application/pdf":
                     try:
                         text = self.analyzer.extract_text_from_pdf(uploaded_file)
                     except Exception as pdf_error:
                         st.error(f"PDF extraction failed: {str(pdf_error)}")
                         st.info("Trying alternative PDF extraction method...")
                         # Try AI analyzer as backup
                         try:
                             text = self.ai_analyzer.extract_text_from_pdf(uploaded_file)
                         except Exception as backup_error:
                             st.error(f"All PDF extraction methods failed: {str(backup_error)}")
                             return
                 elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                     try:
                         text = self.analyzer.extract_text_from_docx(uploaded_file)
                     except Exception as docx_error:
                         st.error(f"DOCX extraction failed: {str(docx_error)}")
                         # Try AI analyzer as backup
                         try:
                             text = self.ai_analyzer.extract_text_from_docx(uploaded_file)
                         except Exception as backup_error:
                             st.error(f"All DOCX extraction methods failed: {str(backup_error)}")
                             return
                 else:
                     text = uploaded_file.getvalue().decode()
                     
                 if not text or text.strip() == "":
                     st.error("Could not extract any text from the uploaded file. Please try a different file.")
                     return
             except Exception as e:
                 st.error(f"Error reading file: {str(e)}")
                 return
     
             # Analyze the document
             analysis = self.analyzer.analyze_resume({'raw_text': text}, role_info)
             
             # Check if analysis returned an error
             if 'error' in analysis:
                 st.error(analysis['error'])
                 return
     
             # Show snowflake effect
             st.snow()
     
             # Save resume data to database
             resume_data = {
                 'personal_info': {
                     'name': analysis.get('name', ''),
                     'email': analysis.get('email', ''),
                     'phone': analysis.get('phone', ''),
                     'linkedin': analysis.get('linkedin', ''),
                     'github': analysis.get('github', ''),
                     'portfolio': analysis.get('portfolio', '')
                 },
                 'summary': analysis.get('summary', ''),
                 'target_role': selected_role,
                 'target_category': selected_category,
                 'education': analysis.get('education', []),
                 'experience': analysis.get('experience', []),
                 'projects': analysis.get('projects', []),
                 'skills': analysis.get('skills', []),
                 'template': ''
             }
     
             # Save to database
             try:
                 resume_id = save_resume_data(resume_data)
     
                 # Save analysis data
                 analysis_data = {
                     'resume_id': resume_id,
                     'ats_score': analysis['ats_score'],
                     'keyword_match_score': analysis['keyword_match']['score'],
                     'format_score': analysis['format_score'],
                     'section_score': analysis['section_score'],
                     'missing_skills': ','.join(analysis['keyword_match']['missing_skills']),
                     'recommendations': ','.join(analysis['suggestions'])
                 }
                 save_analysis_data(resume_id, analysis_data)
                 st.success("Resume data saved successfully!")
             except Exception as e:
                 st.error(f"Error saving to database: {str(e)}")
                 print(f"Database error: {e}")
     
             # Show results based on document type
             if analysis.get('document_type') != 'resume':
                 st.error(
     f"⚠️ This appears to be a {
         analysis['document_type']} document, not a resume!")
                 st.warning(
                     "Please upload a proper resume for ATS analysis.")
                 return
                 
             # Display single resume analysis results
             self._display_single_resume_results(analysis, selected_role, selected_category)
     
    def _analyze_multiple_resumes(self, uploaded_files, role_info, selected_role, selected_category):
         """Analyze multiple resumes and compare them"""
         with st.spinner(f"Analyzing {len(uploaded_files)} resumes... This may take a moment."):
             resume_analyses = []
             
             progress_bar = st.progress(0)
             status_text = st.empty()
             
             for i, uploaded_file in enumerate(uploaded_files):
                 status_text.text(f"Analyzing {uploaded_file.name}... ({i+1}/{len(uploaded_files)})")
                 progress_bar.progress((i + 1) / len(uploaded_files))
                 
                 # Extract text from file
                 text = ""
                 try:
                     if uploaded_file.type == "application/pdf":
                         try:
                             text = self.analyzer.extract_text_from_pdf(uploaded_file)
                         except Exception:
                             try:
                                 text = self.ai_analyzer.extract_text_from_pdf(uploaded_file)
                             except Exception as e:
                                 st.warning(f"Failed to extract text from {uploaded_file.name}: {str(e)}")
                                 continue
                     elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                         try:
                             text = self.analyzer.extract_text_from_docx(uploaded_file)
                         except Exception:
                             try:
                                 text = self.ai_analyzer.extract_text_from_docx(uploaded_file)
                             except Exception as e:
                                 st.warning(f"Failed to extract text from {uploaded_file.name}: {str(e)}")
                                 continue
                     else:
                         text = uploaded_file.getvalue().decode()
                         
                     if not text or text.strip() == "":
                         st.warning(f"Could not extract text from {uploaded_file.name}")
                         continue
                         
                 except Exception as e:
                     st.warning(f"Error reading {uploaded_file.name}: {str(e)}")
                     continue
                 
                 # Analyze the resume
                 analysis = self.analyzer.analyze_resume({'raw_text': text}, role_info)
                 
                 if 'error' not in analysis and analysis.get('document_type') == 'resume':
                     analysis['filename'] = uploaded_file.name
                     resume_analyses.append(analysis)
                 else:
                     st.warning(f"{uploaded_file.name} appears to be invalid or not a resume")
             
             status_text.empty()
             progress_bar.empty()
             
             if not resume_analyses:
                 st.error("❌ No valid resumes could be analyzed. Please check your files and try again.")
                 return
             
             if len(resume_analyses) < len(uploaded_files):
                 st.warning(f"⚠️ Only {len(resume_analyses)} out of {len(uploaded_files)} files were successfully analyzed.")
             
            
             # Display comparison results
             self._display_multiple_resume_results(resume_analyses, selected_role, selected_category)
     
    def _display_multiple_resume_results(self, resume_analyses, selected_role, selected_category):
         """Display results for multiple resume comparison"""
         
         # Sort resumes by ATS score
         resume_analyses.sort(key=lambda x: x['ats_score'], reverse=True)
         best_resume = resume_analyses[0]
         
         # Header with best resume highlight
         st.markdown("""
         <div style='background: linear-gradient(90deg, #4CAF50, #45a049); padding: 25px; border-radius: 15px; margin: 20px 0; text-align: center;'>
             <h2 style='color: white; margin: 0;'>🏆 Analysis Complete!</h2>
             <p style='color: white; margin: 10px 0 0 0; font-size: 1.2em;'>Best Resume: <strong>{}</strong></p>
         </div>
         """.format(best_resume['filename']), unsafe_allow_html=True)
         
         # Comparison Table
         st.markdown("### 📊 Resume Comparison Overview")
         
         comparison_data = []
         for i, analysis in enumerate(resume_analyses):
             rank_emoji = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
             comparison_data.append({
                 'Rank': rank_emoji,
                 'Resume': analysis['filename'][:30] + "..." if len(analysis['filename']) > 30 else analysis['filename'],
                 'ATS Score': f"{analysis['ats_score']}%",
                 'Skills Match': f"{int(analysis.get('keyword_match', {}).get('score', 0))}%",
                 'Format Score': f"{int(analysis.get('format_score', 0))}%",
                 'Section Score': f"{int(analysis.get('section_score', 0))}%"
             })
         
         st.dataframe(comparison_data, use_container_width=True)
         
         # Detailed Analysis Tabs
         st.markdown("### 🔍 Detailed Analysis")
         
         # Create tabs for each resume
         tab_names = [f"{'🏆 ' if i == 0 else ''}{analysis['filename'][:20]}{'...' if len(analysis['filename']) > 20 else ''}" 
                      for i, analysis in enumerate(resume_analyses)]
         
         resume_tabs = st.tabs(tab_names)
         
         for i, (tab, analysis) in enumerate(zip(resume_tabs, resume_analyses)):
             with tab:
                 is_best = i == 0
                 
                 if is_best:
                     st.markdown("""
                     <div style='background: linear-gradient(45deg, #4CAF50, #45a049); padding: 15px; border-radius: 10px; margin-bottom: 20px; text-align: center;'>
                         <h3 style='color: white; margin: 0;'>🏆 BEST RESUME</h3>
                         <p style='color: white; margin: 5px 0 0 0;'>This resume scored highest for the selected role!</p>
                     </div>
                     """, unsafe_allow_html=True)
                 
                 # Display detailed results for this resume
                 self._display_detailed_resume_analysis(analysis, selected_role, selected_category, is_best)
         
         # Summary and Recommendations
         st.markdown("### 💡 Key Insights & Recommendations")
         
         col1, col2 = st.columns(2)
         
         with col1:
             st.markdown("""
             <div class="feature-card">
                 <h3>📈 Score Distribution</h3>
             """, unsafe_allow_html=True)
             
             # Create score distribution chart data
             scores = [analysis['ats_score'] for analysis in resume_analyses]
             filenames = [analysis['filename'][:15] + "..." if len(analysis['filename']) > 15 else analysis['filename'] 
                         for analysis in resume_analyses]
             
             # Display scores as metrics
             for filename, score in zip(filenames, scores):
                 color = "#4CAF50" if score >= 80 else "#FFA500" if score >= 60 else "#FF4444"
                 st.markdown(f"""
                 <div style='display: flex; justify-content: space-between; align-items: center; padding: 10px; margin: 5px 0; background-color: #2d2d2d; border-radius: 8px;'>
                     <span>{filename}</span>
                     <span style='color: {color}; font-weight: bold; font-size: 1.2em;'>{score}%</span>
                 </div>
                 """, unsafe_allow_html=True)
             
             st.markdown("</div>", unsafe_allow_html=True)
         
         with col2:
             st.markdown("""
             <div class="feature-card">
                 <h3>🎯 Optimization Tips</h3>
             """, unsafe_allow_html=True)
             
             # Provide general optimization tips
             optimization_tips = [
                 f"The best resume ({best_resume['filename']}) scored {best_resume['ats_score']}%",
                 f"Average score across all resumes: {sum(scores)/len(scores):.1f}%",
                 f"Score range: {min(scores)}% - {max(scores)}%"
             ]
             
             # Add specific recommendations based on best resume's missing skills
             if best_resume.get('keyword_match', {}).get('missing_skills'):
                 optimization_tips.append("Even the best resume could benefit from adding these skills:")
                 for skill in best_resume['keyword_match']['missing_skills'][:3]:
                     optimization_tips.append(f"  • {skill}")
             
             for tip in optimization_tips:
                 if tip.startswith("  •"):
                     st.markdown(f"<div style='margin-left: 20px; color: #cccccc;'>{tip}</div>", unsafe_allow_html=True)
                 else:
                     st.markdown(f"<div style='margin: 8px 0; color: #ffffff;'>✓ {tip}</div>", unsafe_allow_html=True)
             
             st.markdown("</div>", unsafe_allow_html=True)
     
    def _display_detailed_resume_analysis(self, analysis, selected_role, selected_category, is_best=False):
        """Display detailed analysis for a single resume with four metric cards"""
        
        # Calculate metrics
        ats_score = analysis.get('ats_score', 0)
        keyword_match = analysis.get('keyword_match', {}).get('score', 0)
        format_score = analysis.get('format_score', 0)
        section_score = analysis.get('section_score', 0)
        
        # Determine rating text for ATS Score
        if ats_score >= 80:
            rating = "Excellent"
            rating_color = "#4CAF50"
        elif ats_score >= 60:
            rating = "Good"
            rating_color = "#FFA500"
        else:
            rating = "Needs Improvement"
            rating_color = "#FF4444"
        
        # Create four columns for the metric cards
        st.markdown("""
        <style>
        .metric-card {
            background: #2a2a2a;
            border-radius: 16px;
            padding: 30px 20px;
            text-align: center;
            border: 2px solid #3a3a3a;
            transition: all 0.3s ease;
        }
        .metric-card:hover {
            border-color: #4b6cb7;
            transform: translateY(-2px);
        }
        .metric-icon {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .metric-title {
            color: #888;
            font-size: 0.9em;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .metric-value {
            font-size: 3em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .metric-label {
            font-size: 1em;
            font-weight: 600;
        }
        </style>
        """, unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card" style="border-color: #4b6cb7;">
                <div class="metric-icon">🎯</div>
                <div class="metric-title">ATS Score</div>
                <div class="metric-value" style="color: {rating_color};">{int(ats_score)}</div>
                <div class="metric-label" style="color: {rating_color};">{rating}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">🔍</div>
                <div class="metric-title">Keywords</div>
                <div class="metric-value" style="color: #6DB3F2;">{int(keyword_match)}%</div>
                <div class="metric-label" style="color: #6DB3F2;">Match Rate</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">📄</div>
                <div class="metric-title">Format</div>
                <div class="metric-value" style="color: #90C695;">{int(format_score)}%</div>
                <div class="metric-label" style="color: #90C695;">Structure</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">📋</div>
                <div class="metric-title">Sections</div>
                <div class="metric-value" style="color: #F5A962;">{int(section_score)}%</div>
                <div class="metric-label" style="color: #F5A962;">Complete</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Detailed Analysis Section
        st.markdown("""
        <div style="background: #2a2a2a; border-radius: 12px; padding: 20px; border: 1px solid #3a3a3a;">
            <h3 style="margin-top: 0;">🎯 Skills Analysis(Missing Skills:)</h3>
        """, unsafe_allow_html=True)
        
        if analysis.get('keyword_match', {}).get('missing_skills'):
            # st.markdown("**Missing Skills:**")
            
            # Display skills in columns for better layout
            missing_skills = analysis['keyword_match']['missing_skills']
            
            # Determine number of columns based on number of skills
            num_skills = len(missing_skills)
            if num_skills <= 5:
                num_cols = 2
            elif num_skills <= 10:
                num_cols = 3
            else:
                num_cols = 4
            
            # Create columns for skills
            cols = st.columns(num_cols)
            
            for idx, skill in enumerate(missing_skills):
                col_idx = idx % num_cols
                with cols[col_idx]:
                    st.markdown(f"• {skill}")
        else:
            st.success("All key skills present!")
        
        st.markdown("</div>", unsafe_allow_html=True)
     
    def _display_single_resume_results(self, analysis, selected_role, selected_category):
         """Display results for single resume analysis (existing functionality)"""
         # Display results in a modern card layout
         col1, col2 = st.columns(2)
     
         with col1:
             # ATS Score Card with circular progress
             st.markdown("""
             <div class="feature-card">
                 <h2>ATS Score</h2>
                 <div style="position: relative; width: 150px; height: 150px; margin: 0 auto;">
                     <div style="
                         position: absolute;
                         width: 150px;
                         height: 150px;
                         border-radius: 50%;
                         background: conic-gradient(
                             #4CAF50 0% {score}%,
                             #2c2c2c {score}% 100%
                         );
                         display: flex;
                         align-items: center;
                         justify-content: center;
                     ">
                         <div style="
                             width: 120px;
                             height: 120px;
                             background: #1a1a1a;
                             border-radius: 50%;
                             display: flex;
                             align-items: center;
                             justify-content: center;
                             font-size: 24px;
                             font-weight: bold;
                             color: {color};
                         ">
                             {score}
                         </div>
                     </div>
                 </div>
                 <div style="text-align: center; margin-top: 10px;">
                     <span style="
                         font-size: 1.2em;
                         color: {color};
                         font-weight: bold;
                     ">
                         {status}
                     </span>
                 </div>
             """.format(
                 score=analysis['ats_score'],
                 color='#4CAF50' if analysis['ats_score'] >= 80 else '#FFA500' if analysis[
                     'ats_score'] >= 60 else '#FF4444',
                 status='Excellent' if analysis['ats_score'] >= 80 else 'Good' if analysis[
                     'ats_score'] >= 60 else 'Needs Improvement'
             ), unsafe_allow_html=True)
     
             st.markdown("</div>", unsafe_allow_html=True)
     
             # Skills Match Card
             st.markdown("""
             <div class="feature-card">
                 <h2>Skills Match</h2>
             """, unsafe_allow_html=True)
     
             st.metric(
                 "Keyword Match", f"{int(analysis.get('keyword_match', {}).get('score', 0))}%")
     
             if analysis['keyword_match']['missing_skills']:
                 st.markdown("#### Missing Skills:")
                 for skill in analysis['keyword_match']['missing_skills']:
                     st.markdown(f"- {skill}")
     
             st.markdown("</div>", unsafe_allow_html=True)
     
         with col2:
             # Format Score Card
             st.markdown("""
             <div class="feature-card">
                 <h2>Format Analysis</h2>
             """, unsafe_allow_html=True)
     
             st.metric("Format Score",
                       f"{int(analysis.get('format_score', 0))}%")
             st.metric("Section Score",
                       f"{int(analysis.get('section_score', 0))}%")
     
             st.markdown("</div>", unsafe_allow_html=True)
     
     
                        
     
     
    
    def render_job_search(self):
        """Render the job search page"""
        apply_modern_styles()
        self.add_back_to_home_button()
     
         # Page Header
        page_header(
             "Smart Job Search",
             "Find Your Dream Job Across Multiple Platforms"
         )
        render_job_search()

    

    def render_feedback_page(self):
        """Render the feedback page"""
        apply_modern_styles()
        self.add_back_to_home_button()
        
        # Page Header
        page_header(
            "Feedback & Suggestions",
            "Help us improve by sharing your thoughts"
        )
        
        # Initialize feedback manager
        feedback_manager = FeedbackManager()
        st.markdown("""
                    <style>
                    /* Center align and style tab container */
                    .stTabs [data-baseweb="tab-list"] {
                        justify-content: center;
                        margin-top: 20px;
                        margin-bottom: 20px;
                        gap: 10px;
                    }
                
                    /* Base style for each tab */
                    .stTabs [data-baseweb="tab"] {
                        background-color: #f0f0f0;
                        border: 1px solid #ddd;
                        border-radius: 8px;
                        padding: 10px 24px;
                        font-size: 16px;
                        font-weight: 600;
                        color: #333;
                        transition: all 0.2s ease-in-out;
                    }
                
                    /* Hover effect */
                    .stTabs [data-baseweb="tab"]:hover {
                        background-color: #e0f5ec;
                        border-color: #00bfa5;
                        color: #111;
                        transform: translateY(-2px);
                        cursor: pointer;
                    }
                
                    /* Selected/active tab style */
                    .stTabs [aria-selected="true"] {
                        background-color: #00bfa5 !important;
                        color: white !important;
                        border: 1px solid #00bfa5;
                        font-weight: 700;
                        box-shadow: 0px 4px 12px rgba(0, 191, 165, 0.2);
                    }
                    </style>
                """, unsafe_allow_html=True)
        # Create tabs for form and stats
        form_tab, stats_tab = st.tabs(["Submit Feedback", "Feedback Stats"])
        
        with form_tab:
            feedback_manager.render_feedback_form()
            
        with stats_tab:
            feedback_manager.render_feedback_stats()
            
            
        
    # def render_header(self):
    #     """Render navigation header with scrolling announcements"""
    #     st.markdown("""
    #     <style>
    #     header[data-testid="stHeader"] { display: none; }
    #     footer { display: none; }
        
    #     .block-container {
    #         padding-top: 0rem !important;
    #     }
        
    #     .custom-header {
    #         position: fixed;
    #         top: 0;
    #         left: 0;
    #         width: 100%;
    #         height: 80px;
    #         background: linear-gradient(90deg, #050510, #0b0f2a);
    #         display: flex;
    #         align-items: center;
    #         justify-content: space-between;
    #         padding: 0 60px;
    #         z-index: 100000;
    #         box-shadow: 0 2px 20px rgba(0,0,0,0.5);
    #     }
        
    #     .header-spacer {
    #         height: 90px;
    #     }
        
    #     .logo {
    #         color: white;
    #         font-size: 30px;
    #         font-weight: bold;
    #         cursor: pointer;
    #     }
        
    #     .nav-links {
    #         display: flex;
    #         gap: 30px;
    #     }
        
    #     .nav-links a {
    #         color: white;
    #         text-decoration: none;
    #         font-size: 16px;
    #         transition: color 0.3s;
    #         cursor: pointer;
    #     }
        
    #     .nav-links a:hover {
    #         color: #4dabf7;
    #     }
        
    #     .nav-links a.active {
    #         color: #00bfa5;
    #         font-weight: 600;
    #     }
        
    #     /* Scrolling Announcement Bar */
    #     .announcement-bar {
    #         flex: 1;
    #         height: 50px;
    #         background: linear-gradient(90deg, #1a1a2e, #16213e);
    #         overflow: hidden;
    #         border-radius: 10px;
    #         margin-left: 30px;
    #     }
        
    #     .announcement-content {
    #         display: flex;
    #         align-items: center;
    #         height: 100%;
    #         animation: scroll-left 40s linear infinite;
    #         white-space: nowrap;
    #     }
        
    #     .announcement-item {
    #         display: inline-flex;
    #         align-items: center;
    #         padding: 0 50px;
    #         color: white;
    #         font-size: 16px;
    #         font-weight: 500;
    #     }
        
    #     .announcement-item::after {
    #         content: "•";
    #         margin-left: 50px;
    #         color: #00bfa5;
    #         font-size: 20px;
    #     }
        
    #     @keyframes scroll-left {
    #         0% {
    #             transform: translateX(0);
    #         }
    #         100% {
    #             transform: translateX(-50%);
    #         }
    #     }
        
    #     .announcement-bar:hover .announcement-content {
    #         animation-play-state: paused;
    #     }
    #     </style>
        
    #     <div class="custom-header">
    #         <div class="logo" onclick="window.location.href='?page=home'">
    #             📈 <span>CareerIQ</span>
    #         </div>
    #         <div class="announcement-bar">
    #             <div class="announcement-content">
    #                 <span class="announcement-item">
    #                     🚀 Welcome to CareerIQ — an AI-powered career platform for resume building, ATS optimization, job search, portfolio creation, mock interviews, smart quizzes, and career insights.
    #                 </span>
    #                 <span class="announcement-item">
    #                     🚀 Welcome to CareerIQ — an AI-powered career platform for resume building, ATS optimization, job search, portfolio creation, mock interviews, smart quizzes, and career insights.
    #                 </span>
    #             </div>
    #         </div>
    #     </div>
        
    #     <div class="header-spacer"></div>
        
    #     """, unsafe_allow_html=True)

    
    def render_home(self):
        """Home page with 8 feature buttons in 2 rows"""
        # self.render_header()
        # self.render_header()
        apply_modern_styles()
            
        # Add custom styling
        st.markdown("""
        <style>
        /* Feature card styling */
        .feature-card-container {
            background: linear-gradient(145deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
            border-radius: 20px;
            padding: 40px 30px;
            text-align: center;
            border: 2px solid rgba(255,255,255,0.1);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            height: 100%;
            position: relative;
            overflow: hidden;
            margin-bottom: 10px;
        }
        
        .feature-card-container::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(0, 191, 165, 0.2), transparent);
            transition: left 0.6s;
        }
        
        .feature-card-container:hover::before {
            left: 100%;
        }
        
        .feature-card-container:hover {
            transform: translateY(-10px);
            border-color: rgba(0, 191, 165, 0.6);
            box-shadow: 0 20px 40px rgba(0, 191, 165, 0.3);
            background: linear-gradient(145deg, rgba(0, 191, 165, 0.1), rgba(0, 191, 165, 0.05));
        }
        
        .feature-icon {
            font-size: 4em;
            margin-bottom: 20px;
            display: inline-block;
            transition: all 0.4s ease;
        }
        
        .feature-card-container:hover .feature-icon {
            transform: scale(1.2) rotate(5deg);
        }
        
        .feature-title {
            font-size: 1.4em;
            font-weight: 700;
            margin-bottom: 15px;
            color: #00bfa5;
            letter-spacing: 1px;
        }
        
        .feature-desc {
            color: rgba(255, 255, 255, 0.7);
            font-size: 0.95em;
            line-height: 1.6;
        }
        
        /* Team card styling */
        .team-card {
            background: linear-gradient(145deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
            border-radius: 20px;
            padding: 25px 30px;
            text-align: left;
            border: 2px solid rgba(255,255,255,0.1);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            min-height: 140px;
            max-height: 140px;
            position: relative;
            overflow: hidden;
            display: flex;
            align-items: center;
            gap: 25px;
        }
        
        .team-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(102, 126, 234, 0.2), transparent);
            transition: left 0.6s;
        }
        
        .team-card:hover::before {
            left: 100%;
        }
        
        .team-card:hover {
            transform: translateY(-10px);
            border-color: rgba(102, 126, 234, 0.6);
            box-shadow: 0 20px 40px rgba(102, 126, 234, 0.3);
            background: linear-gradient(145deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.05));
        }
        
        .team-avatar {
            width: 90px;
            height: 90px;
            border-radius: 50%;
            margin: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.8em;
            font-weight: 700;
            color: white;
            transition: all 0.4s ease;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            flex-shrink: 0;
        }
        
        .team-card:hover .team-avatar {
            transform: scale(1.1) rotate(5deg);
        }
        
        .avatar-purple {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        .avatar-blue {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }
        
        .avatar-pink {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        
        .avatar-teal {
            background: linear-gradient(135deg, #00bfa5 0%, #00d9c5 100%);
        }
        
        .team-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 5px;
        }
        
        .team-name {
            font-size: 1.3em;
            font-weight: 700;
            margin: 0;
            color: white;
            letter-spacing: 0.5px;
        }
        
        .team-role {
            color: #667eea;
            font-size: 0.95em;
            margin: 0;
            font-weight: 500;
        }
        
        .github-btn {
            color: white;
        }
        
        /* Floating Help Button */
        .floating-help {
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.5);
            cursor: pointer;
            transition: all 0.3s ease;
            z-index: 1000;
            animation: pulse 2s infinite;
        }
        
        .floating-help:hover {
            transform: scale(1.1);
            box-shadow: 0 15px 40px rgba(102, 126, 234, 0.7);
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        
        @keyframes gradientAnimation {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        </style>
        """, unsafe_allow_html=True)
        # st.markdown("<br><br>", unsafe_allow_html=True)

        # Hero Section
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem 0rem;
            border-radius: 20px;
            text-align: center;
            margin-bottom: 3rem;
            box-shadow: 0 20px 40px rgba(0,0,0,0.15);
        ">    
            <h1 style="
                font-size: 3.5rem; 
                margin-bottom: 1rem; 
                font-weight: 700;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                background: linear-gradient(90deg, #ff6ec4, #7873f5, #4ade80, #facc15, #f43f5e);
                background-size: 300% 300%;
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                animation: gradientAnimation 6s ease infinite;
            ">CareerIQ</h1>
            <p style="
                color: rgba(255,255,255,0.9); 
                font-size: 1.3rem; 
                max-width: 600px; 
                margin: 0 auto;
                line-height: 1.6;
            ">Transform your career with an all-in-one AI-powered platform. Build resumes, ace interviews, explore opportunities, and track your growth seamlessly.</p>
        </div>
        """, unsafe_allow_html=True)
        
    

        st.markdown("""
<div style="text-align:center; margin: 30px 0;">
    <h2 style="
        font-size: 2.5rem;
        font-weight: 700;
        color: #00bfa5;
        margin-bottom: 10px;
    ">
        Choose Your Tool
    </h2>
    <div style="
        width: 80px;
        height: 4px;
        background-color: #00bfa5;
        margin: 0 auto;
        border-radius: 10px;
    "></div>
</div>
""", unsafe_allow_html=True)
        
        # Define all 8 features
        features = [
            {
                "icon": "🎨",
                "title": "RESUME BUILDER",
                "desc": "Create professional resumes with AI-powered templates",
                "page": "resume_builder"
            },
            {
                "icon": "🔍",
                "title": "RESUME ANALYZER",
                "desc": "Get instant AI-powered feedback on your resume",
                "page": "resume_analyzer"
            },
            {
                "icon": "📁",
                "title": "PORTFOLIO BUILDER",
                "desc": "Build stunning portfolios with templates",
                "page": "portfolio_builder"
            },
            {
                "icon": "🧩",
                "title": "SMARTPREP AI",
                "desc": "Prepare for interviews with AI mock tests",
                "page": "smartprep_ai_"
            },
            {
                "icon": "🎤",
                "title": "MOCK INTERVIEW",  
                "desc": "AI-powered voice mock interviews with real-time feedback",
                "page": "mock_interview"
            },
            {
                "icon": "🎯",
                "title": "JOB SEARCH",
                "desc": "Find your dream job across platforms",
                "page": "job_search"
            },
            {
                "icon": "📊",
                "title": "DASHBOARD",
                "desc": "Track your career progress and analytics",
                "page": "dashboard"
            },
            {
                "icon": "💬",
                "title": "FEEDBACK",
                "desc": "Share your thoughts and help us improve",
                "page": "feedback"
            }
        ]
        
        # First Row - 4 buttons
        st.markdown("### ")
        col1, col2, col3, col4 = st.columns(4, gap="large")
        
        columns_row1 = [col1, col2, col3, col4]
        for idx, col in enumerate(columns_row1):
            with col:
                feature = features[idx]
                
                # Visual card
                st.markdown(f"""
                <div class="feature-card-container">
                    <div class="feature-icon">{feature['icon']}</div>
                    <div class="feature-title">{feature['title']}</div>
                    <div class="feature-desc">{feature['desc']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Button below card
                if st.button(feature['title'], key=f"btn_{feature['page']}_{idx}", use_container_width=True):
                    st.session_state.page = feature['page']
                    st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Second Row - 4 buttons
        col5, col6, col7, col8 = st.columns(4, gap="large")
        
        columns_row2 = [col5, col6, col7, col8]
        for idx, col in enumerate(columns_row2):
            with col:
                feature = features[idx + 4]
                
                # Visual card
                st.markdown(f"""
                <div class="feature-card-container">
                    <div class="feature-icon">{feature['icon']}</div>
                    <div class="feature-title">{feature['title']}</div>
                    <div class="feature-desc">{feature['desc']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Button below card
                if st.button(feature['title'], key=f"btn_{feature['page']}_{idx+4}", use_container_width=True):
                    st.session_state.page = feature['page']
                    st.rerun()
                    
        st.markdown("<br>", unsafe_allow_html=True)

        # Testimonials Section
        st.markdown("""
        <div style="
            background: linear-gradient(145deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
            border-radius: 20px;
            padding: 3rem 2rem;
            margin: 3rem 0;
            border: 2px solid rgba(255,255,255,0.1);
        ">
            <h2 style="text-align: center; color: #00bfa5; margin-bottom: 2rem; font-size: 2.5rem;">What Our Users Say</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem;">
                <div style="background: rgba(102, 126, 234, 0.1); padding: 2rem; border-radius: 15px; border-left: 4px solid #667eea;">
                    <div style="color: #facc15; margin-bottom: 1rem; font-size: 1.2rem;">⭐⭐⭐⭐⭐</div>
                    <p style="color: rgba(255,255,255,0.9); line-height: 1.6; margin-bottom: 1rem;">
                        "CareerIQ helped me land my dream job! The resume builder and mock interviews were game-changers."
                    </p>
                    <div style="color: #667eea; font-weight: 600;">- Sarah M., Software Engineer</div>
                </div>
                <div style="background: rgba(0, 191, 165, 0.1); padding: 2rem; border-radius: 15px; border-left: 4px solid #00bfa5;">
                    <div style="color: #facc15; margin-bottom: 1rem; font-size: 1.2rem;">⭐⭐⭐⭐⭐</div>
                    <p style="color: rgba(255,255,255,0.9); line-height: 1.6; margin-bottom: 1rem;">
                        "The AI feedback on my resume was incredibly detailed. Got 3 interview calls within a week!"
                    </p>
                    <div style="color: #00bfa5; font-weight: 600;">- Raj K., Data Analyst</div>
                </div>
                <div style="background: rgba(245, 87, 108, 0.1); padding: 2rem; border-radius: 15px; border-left: 4px solid #f5576c;">
                    <div style="color: #facc15; margin-bottom: 1rem; font-size: 1.2rem;">⭐⭐⭐⭐⭐</div>
                    <p style="color: rgba(255,255,255,0.9); line-height: 1.6; margin-bottom: 1rem;">
                        "Portfolio builder is amazing! Created a stunning portfolio in just 30 minutes."
                    </p>
                    <div style="color: #f5576c; font-weight: 600;">- Priya S., Designer</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        

        # MEET OUR TEAM SECTION
        st.markdown("<br>", unsafe_allow_html=True)
    
        st.markdown("""
<div style="text-align:center; margin: 30px 0;">
    <h2 style="
        font-size: 2.5rem;
        font-weight: 700;
        color: #00bfa5;
        margin-bottom: 10px;
    ">
        Meet Our Team
    </h2>
    <div style="
        width: 80px;
        height: 4px;
        background-color: #00bfa5;
        margin: 0 auto;
        border-radius: 10px;
    "></div>
</div>
""", unsafe_allow_html=True)

        # Team Members Data
        team_members = [
            {
                "name": "Aksh Patel",
                "initials": "AP",
                "role": "Software Developer",
                "avatar_class": "avatar-purple",
                "github": "#"
            },
            {
                "name": "Ayush Patel",
                "initials": "AP",
                "role": "Software Developer",
                "avatar_class": "avatar-blue",
                "github": "#"
            },
            { 
                "name": "Prinsi Patel",
                "initials": "PP",
                "role": "AI Developer",
                "avatar_class": "avatar-purple",
                "github": "#"
            },
            {
                "name": "Prerna Patel",
                "initials": "PP",
                "role": "Technical Support",
                "avatar_class": "avatar-pink",
                "github": "#"
            }
        ]
        
        # First Row - 2 members
        col1, col2 = st.columns(2, gap="large")
        
        with col1:
            member = team_members[0]
            st.markdown(f"""
            <div class="team-card">
                <div class="team-avatar {member['avatar_class']}">{member['initials']}</div>
                <div class="team-content">
                    <div class="team-name">{member['name']}</div>
                    <div class="team-role">{member['role']}</div>
                    <a href="{member['github']}" class="github-btn" target="_blank">GitHub</a>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            member = team_members[1]
            st.markdown(f"""
            <div class="team-card">
                <div class="team-avatar {member['avatar_class']}">{member['initials']}</div>
                <div class="team-content">
                    <div class="team-name">{member['name']}</div>
                    <div class="team-role">{member['role']}</div>
                    <a href="{member['github']}" class="github-btn" target="_blank">GitHub</a>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Second Row - 2 members
        col3, col4 = st.columns(2, gap="large")
        
        with col3:
            member = team_members[2]
            st.markdown(f"""
            <div class="team-card">
                <div class="team-avatar {member['avatar_class']}">{member['initials']}</div>
                <div class="team-content">
                    <div class="team-name">{member['name']}</div>
                    <div class="team-role">{member['role']}</div>
                    <a href="{member['github']}" class="github-btn" target="_blank">GitHub</a>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            member = team_members[3]
            st.markdown(f"""
            <div class="team-card">
                <div class="team-avatar {member['avatar_class']}">{member['initials']}</div>
                <div class="team-content">
                    <div class="team-name">{member['name']}</div>
                    <div class="team-role">{member['role']}</div>
                    <a href="{member['github']}" class="github-btn" target="_blank">GitHub</a>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Call to Action
        st.markdown("""
        <div style="
            text-align: center;
            margin: 4rem 0 2rem 0;
            padding: 3rem 2rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 20px;
            box-shadow: 0 15px 35px rgba(102, 126, 234, 0.3);
        ">
            <h3 style="
                color: white;
                font-size: 2.2rem;
                margin-bottom: 1rem;
                font-weight: 600;
            ">Ready to Launch Your Dream Career?</h3>
            <p style="
                color: rgba(255,255,255,0.9);
                font-size: 1.2rem;
                max-width: 600px;
                margin: 0 auto;
            ">Join thousands of professionals transforming their careers with AI!</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🚀 Start Your Journey Now!", key="get_started_btn", 
                        help="Click to start analyzing your resume with AI magic",
                        type="primary",
                        use_container_width=True):
                cleaned_name = "RESUME BUILDER".lower().replace(" ", "_").replace("📝", "").strip()
                st.session_state.page = cleaned_name
                st.rerun()
        
    
        # Add some spacing at the bottom
        st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)
        
        
        
    def add_back_to_home_button(self):
        """Add a floating back to home button on the left side"""
        
        apply_modern_styles()

        st.markdown("""
        <style>
        .back-to-home-btn {
            position: fixed;
            top: 20px;
            left: 20px;
            z-index: 9999;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 14px;
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
    
    
    def main(self):
        """Main application without sidebar"""
        self.apply_global_styles()
    
        # Force home page on first load
        if 'initial_load' not in st.session_state:
            st.session_state.initial_load = True
            st.session_state.page = 'home'
        
        # Get current page and render
        current_page = st.session_state.get('page', 'home')
        
        # Create page mapping
        page_mapping = {
            'home': '🏠 HOME',
            'resume_builder': '📝 RESUME BUILDER',
            'resume_analyzer': '🔍 RESUME ANALYZER',
            'portfolio_builder': '📁 PORTFOLIO BUILDER',
            'smartprep_ai_': '🧩 SmartPrep AI ',
            'mock_interview': '🎤 MOCK INTERVIEW',  # ← આ add કરો
            'job_search': '🎯 JOB SEARCH',
            'dashboard': '📊 DASHBOARD',
            'feedback': '💬 FEEDBACK',
        }
        
        # Handle mock_interview page separately (કારણ કે તે pages dict માં નથી)
        if current_page == 'mock_interview':
            self.render_mock_interview()  # ← નવું method call
        # Render the appropriate page
        elif current_page in page_mapping:
            page_name = page_mapping[current_page]
            if page_name in self.pages:
                self.pages[page_name]()
            else:
                self.render_home()
        else:
            self.render_home()
        
        # Add footer
        self.add_footer()
    
    
    def render_mock_interview(self):
        """Render mock interview page"""
        try:
            # API key લો secrets માંથી
            groq_api_key = st.secrets.get("GROQ_API_KEY", "")
            
            # જો secrets માં નથી તો user input લો
            if not groq_api_key:
                st.title("🎤 AI Mock Interview")
                st.markdown("**Configure your interview settings**")
                st.markdown("---")
                
                groq_api_key = st.text_input(
                    "🔑 Enter Groq API Key:", 
                    type="password",
                    help="Get your free API key from https://console.groq.com"
                )
                
                st.info("💡 **Tip:** Add your API key to `.streamlit/secrets.toml` to avoid entering it every time")
            
            # જો API key છે તો interview શરૂ કરો
            if groq_api_key:
                from SmartQuiz.aimockinterview import MockInterviewSystem
                mock_system = MockInterviewSystem(groq_api_key)
                mock_system.run()
            else:
                st.warning("⚠️ Please enter your Groq API key to use Mock Interview feature")
                
                col1, col2, col3 = st.columns([1, 1, 1])
                with col2:
                    if st.button("⬅️ Back to Home", use_container_width=True):
                        st.session_state.page = 'home'
                        st.rerun()
        
        except Exception as e:
            st.error(f"❌ Error loading Mock Interview: {str(e)}")
            if st.button("⬅️ Back to Home"):
                st.session_state.page = 'home'
                st.rerun()
    
    
if __name__ == "__main__":
    app = ResumeApp()
    app.main()