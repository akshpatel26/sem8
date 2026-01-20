# ============================================================================
# File 1: smartQuiz/debug_paths.py
# ============================================================================
"""
Run this first to see where files are located
"""

import os
from pathlib import Path
import json

print("="*70)
print("🔍 DEBUGGING FILE PATHS")
print("="*70)

# Get current directory
current_dir = Path.cwd()
print(f"\n📂 Current Directory: {current_dir}")

# Check for smartQuiz folder
smartquiz_dir = current_dir / "smartQuiz"
if smartquiz_dir.exists():
    print(f"✅ smartQuiz folder found at: {smartquiz_dir}")
else:
    print(f"❌ smartQuiz folder NOT found")
    smartquiz_dir = current_dir
    print(f"   Using current directory: {smartquiz_dir}")

# Check for ml_models folder
ml_models_dir = smartquiz_dir / "ml_models"
print(f"\n📁 Looking for ml_models at: {ml_models_dir}")
print(f"   Exists: {ml_models_dir.exists()}")

if ml_models_dir.exists():
    files = list(ml_models_dir.iterdir())
    print(f"   Files in ml_models: {len(files)}")
    for f in files:
        print(f"      - {f.name}")

# Check for content_db.json
db_path = ml_models_dir / "content_db.json"
print(f"\n📄 Looking for content_db.json at: {db_path}")
print(f"   Exists: {db_path.exists()}")

if db_path.exists():
    try:
        with open(db_path, 'r') as f:
            data = json.load(f)
        print(f"   ✅ Database loaded successfully!")
        print(f"   Semesters in database: {list(data.keys())}")
        for sem, subjects in data.items():
            print(f"      {sem}: {list(subjects.keys())}")
    except Exception as e:
        print(f"   ❌ Error loading database: {e}")

# Check for semester_pdfs
pdf_dir = smartquiz_dir / "semester_pdfs"
print(f"\n📚 Looking for semester_pdfs at: {pdf_dir}")
print(f"   Exists: {pdf_dir.exists()}")

if pdf_dir.exists():
    sem_folders = [d for d in pdf_dir.iterdir() if d.is_dir()]
    print(f"   Semester folders: {len(sem_folders)}")
    for sem in sorted(sem_folders):
        pdfs = list(sem.glob("*.pdf"))
        print(f"      {sem.name}: {len(pdfs)} PDFs")

print("\n" + "="*70)
print("💡 RECOMMENDATIONS:")
print("="*70)

if not db_path.exists():
    print("❌ Database not found. Run the setup script in the correct directory.")
    print(f"   Navigate to: {smartquiz_dir}")
    print(f"   Then run: python setup_complete_database.py")
else:
    print("✅ Database exists. The issue might be in ml_model.py path resolution.")
    print("   Run the fixed ml_model.py provided below.")

print("="*70)


# ============================================================================
# File 2: smartQuiz/ml_model.py (FIXED VERSION)
# ============================================================================
"""
FIXED ml_model.py with better path handling
REPLACE your existing ml_model.py with this
"""

import os
import json
import pickle
import re
from pathlib import Path
import PyPDF2

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

class MLQuizGenerator:
    def __init__(self):
        # Fix path resolution - check multiple locations
        self.base_dir = self._find_base_dir()
        
        self.pdf_folder = self.base_dir / "semester_pdfs"
        self.model_folder = self.base_dir / "ml_models"
        
        # Create directories if they don't exist
        self.model_folder.mkdir(exist_ok=True, parents=True)
        self.pdf_folder.mkdir(exist_ok=True, parents=True)
        
        print(f"🔍 Base directory: {self.base_dir}")
        print(f"📁 PDF folder: {self.pdf_folder}")
        print(f"📁 Model folder: {self.model_folder}")
        
        self.content_db = self.load_content_database()
        print(f"📊 Loaded {len(self.content_db)} semesters from database")
    
    def _find_base_dir(self):
        """Find the correct base directory for the project"""
        current = Path.cwd()
        
        # Check if we're already in smartQuiz
        if current.name == "smartQuiz":
            return current
        
        # Check if smartQuiz exists as subfolder
        smartquiz = current / "smartQuiz"
        if smartquiz.exists():
            return smartquiz
        
        # Check parent directories
        for parent in current.parents:
            smartquiz = parent / "smartQuiz"
            if smartquiz.exists():
                return smartquiz
        
        # Default to current directory
        return current
    
    def load_content_database(self):
        """Load or create content database"""
        db_path = self.model_folder / "content_db.json"
        
        print(f"📄 Looking for database at: {db_path}")
        print(f"   Exists: {db_path.exists()}")
        
        if db_path.exists():
            try:
                with open(db_path, 'r', encoding='utf-8') as f:
                    db = json.load(f)
                print(f"✅ Database loaded: {len(db)} semesters")
                return db
            except Exception as e:
                print(f"❌ Error loading database: {e}")
                return self.create_default_database()
        else:
            print("⚠️ Database not found, creating default...")
            return self.create_default_database()
    
    def create_default_database(self):
        """Create a default database with all semesters"""
        print("🔨 Creating default database...")
        
        database = {}
        
        # Define subjects for each semester
        semester_subjects = {
            "Sem 1": ["Mathematics I", "Physics", "Chemistry", "Programming Fundamentals"],
            "Sem 2": ["Mathematics II", "Data Structures", "Digital Electronics"],
            "Sem 3": ["Database Management Systems", "Object Oriented Programming", "Computer Networks", "Operating Systems"],
            "Sem 4": ["Design and Analysis of Algorithms", "Software Engineering", "Web Technologies"],
            "Sem 5": ["Machine Learning", "Artificial Intelligence", "Compiler Design"],
            "Sem 6": ["Cloud Computing", "Information Security", "Big Data Analytics"],
            "Sem 7": ["Deep Learning", "Blockchain Technology", "Internet of Things"],
            "Sem 8": ["Advanced Machine Learning", "Natural Language Processing", "Computer Vision", "Project Management"]
        }
        
        # Generic topics template
        topic_templates = [
            "Introduction to {subject}",
            "Fundamentals of {subject}",
            "Basic Concepts",
            "Advanced Techniques",
            "Applications and Use Cases",
            "Theory and Principles",
            "Practical Implementation",
            "Case Studies",
            "Problem Solving Approaches",
            "Analysis and Design",
            "Best Practices",
            "Tools and Technologies",
            "Standards and Methodologies",
            "Architecture and Framework",
            "Optimization Techniques"
        ]
        
        for sem, subjects in semester_subjects.items():
            database[sem] = {}
            
            for subject in subjects:
                topics = [t.format(subject=subject) if "{subject}" in t else f"{t} in {subject}" 
                         for t in topic_templates]
                
                database[sem][subject] = {
                    'topics': topics,
                    'content': [
                        {
                            'page': 1,
                            'text': f"{subject} is an important subject covering various concepts and applications in computer science and engineering."
                        }
                    ],
                    'pdf_path': f"semester_pdfs/{sem}/{subject.replace(' ', '-')}.pdf"
                }
        
        # Save database
        db_path = self.model_folder / "content_db.json"
        try:
            with open(db_path, 'w', encoding='utf-8') as f:
                json.dump(database, f, indent=2, ensure_ascii=False)
            print(f"✅ Database created at: {db_path}")
        except Exception as e:
            print(f"❌ Error saving database: {e}")
        
        return database
    
    def get_subjects(self, semester):
        """Get subjects for a semester"""
        subjects = list(self.content_db.get(semester, {}).keys())
        print(f"📚 Getting subjects for {semester}: {subjects}")
        return subjects
    
    def get_topics(self, semester, subject):
        """Get topics for a subject"""
        try:
            topics = self.content_db[semester][subject]['topics']
            print(f"📝 Getting topics for {semester}/{subject}: {len(topics)} topics")
            return topics
        except KeyError as e:
            print(f"❌ Error getting topics: {e}")
            return []
    
    def get_content_for_topics(self, semester, subject, topics):
        """Get content related to selected topics"""
        try:
            all_content = self.content_db[semester][subject]['content']
            return [page['text'] for page in all_content[:5]]
        except KeyError:
            return []
    
    def generate_questions(self, semester, subject, topics):
        """Generate questions using Claude AI or fallback"""
        print(f"🤖 Generating questions for {len(topics)} topics...")
        
        # Get relevant content
        content = self.get_content_for_topics(semester, subject, topics)
        
        # Try to generate with AI
        if ANTHROPIC_AVAILABLE:
            try:
                questions = self.generate_with_claude(content, topics, subject)
                if questions and len(questions) > 0:
                    print(f"✅ Generated {len(questions)} questions with AI")
                    return questions
            except Exception as e:
                print(f"⚠️ AI generation failed: {e}")
        
        # Fallback to rule-based generation
        print("📝 Using fallback question generation...")
        return self.generate_fallback_questions(topics, subject)
    
    def generate_with_claude(self, content, topics, subject):
        """Generate questions using Claude API"""
        combined_content = "\n\n".join(content[:3])[:3000]
        
        prompt = f"""Generate {min(len(topics), 15)} multiple-choice questions for {subject}.

Topics: {', '.join(topics[:10])}

Create questions in JSON format:
[
  {{
    "question": "Question text?",
    "topic": "Topic name",
    "options": ["A", "B", "C", "D"],
    "correct_answer": "A",
    "explanation": "Why A is correct."
  }}
]

Return ONLY the JSON array."""

        try:
            client = anthropic.Anthropic()
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                questions = json.loads(response_text[json_start:json_end])
                return questions
            
            return None
        except Exception as e:
            print(f"Claude API error: {e}")
            return None
    
    def generate_fallback_questions(self, topics, subject):
        """Generate fallback questions"""
        questions = []
        
        templates = [
            "What is the primary purpose of {topic}?",
            "Which best describes {topic}?",
            "What is a key characteristic of {topic}?",
            "In {subject}, {topic} is used for?",
            "What is the main advantage of {topic}?"
        ]
        
        for i, topic in enumerate(topics[:15]):
            template = templates[i % len(templates)]
            
            questions.append({
                'question': template.format(topic=topic, subject=subject),
                'topic': topic,
                'options': [
                    f"It provides the framework for {topic}",
                    f"It serves as an alternative to {topic}",
                    f"It represents a specialized form of {topic}",
                    f"It offers a theoretical view of {topic}"
                ],
                'correct_answer': f"It provides the framework for {topic}",
                'explanation': f"This tests your understanding of {topic} in {subject}. The correct answer highlights the fundamental role of this concept."
            })
        
        return questions
    
    def retrain_model(self):
        """Retrain the model"""
        self.content_db = self.create_default_database()
        return len(self.content_db) > 0


# ============================================================================
# File 3: smartQuiz/force_create_db.py
# ============================================================================
"""
Run this to forcefully create the database in the right location
"""

import json
from pathlib import Path

# Get the directory where this script is located
script_dir = Path(__file__).parent
ml_models_dir = script_dir / "ml_models"
ml_models_dir.mkdir(exist_ok=True, parents=True)

database = {
    "Sem 1": {
        "Mathematics I": {"topics": ["Calculus", "Algebra", "Geometry", "Trigonometry", "Statistics", "Probability", "Number Theory", "Set Theory", "Logic", "Discrete Math", "Linear Algebra", "Differential Equations", "Integration", "Series", "Complex Numbers"], "content": [{"page": 1, "text": "Mathematics content"}], "pdf_path": "sem1/math.pdf"},
        "Physics": {"topics": ["Mechanics", "Thermodynamics", "Optics", "Electromagnetism", "Modern Physics", "Waves", "Acoustics", "Quantum", "Relativity", "Nuclear", "Atomic Structure", "Motion", "Energy", "Force", "Work"], "content": [{"page": 1, "text": "Physics content"}], "pdf_path": "sem1/physics.pdf"},
        "Chemistry": {"topics": ["Organic", "Inorganic", "Physical Chemistry", "Analytical", "Biochemistry", "Electrochemistry", "Thermochemistry", "Kinetics", "Equilibrium", "Acids Bases", "Redox", "Periodic Table", "Bonding", "States of Matter", "Solutions"], "content": [{"page": 1, "text": "Chemistry content"}], "pdf_path": "sem1/chem.pdf"},
        "Programming": {"topics": ["Variables", "Data Types", "Control Flow", "Loops", "Functions", "Arrays", "Pointers", "Structures", "File IO", "Algorithms", "Debugging", "OOP Basics", "Recursion", "Memory", "Syntax"], "content": [{"page": 1, "text": "Programming content"}], "pdf_path": "sem1/prog.pdf"}
    },
    "Sem 2": {
        "Data Structures": {"topics": ["Arrays", "Linked Lists", "Stacks", "Queues", "Trees", "Graphs", "Hashing", "Sorting", "Searching", "Recursion", "Dynamic Programming", "Greedy", "Backtracking", "Complexity", "Memory Management"], "content": [{"page": 1, "text": "DS content"}], "pdf_path": "sem2/ds.pdf"},
        "Digital Electronics": {"topics": ["Logic Gates", "Boolean Algebra", "Combinational Circuits", "Sequential Circuits", "Flip Flops", "Counters", "Registers", "Memory", "ALU", "Multiplexers", "Decoders", "Encoders", "Adders", "State Machines", "Digital Design"], "content": [{"page": 1, "text": "DE content"}], "pdf_path": "sem2/de.pdf"}
    },
    "Sem 3": {
        "Database Management Systems": {"topics": ["Relational Model", "SQL", "Normalization", "ER Diagrams", "Transactions", "ACID", "Indexing", "Query Optimization", "Joins", "Views", "Triggers", "Stored Procedures", "Database Design", "Concurrency", "Recovery"], "content": [{"page": 1, "text": "DBMS content"}], "pdf_path": "sem3/dbms.pdf"},
        "Object Oriented Programming": {"topics": ["Classes", "Objects", "Inheritance", "Polymorphism", "Encapsulation", "Abstraction", "Interfaces", "Exception Handling", "File IO", "Collections", "Generics", "Multithreading", "Design Patterns", "SOLID", "UML"], "content": [{"page": 1, "text": "OOP content"}], "pdf_path": "sem3/oop.pdf"},
        "Computer Networks": {"topics": ["OSI Model", "TCP IP", "Data Link", "Network Layer", "Transport Layer", "Application Layer", "IP Addressing", "Subnetting", "Routing", "Network Security", "DNS", "HTTP", "Network Devices", "Wireless", "Protocols"], "content": [{"page": 1, "text": "Networks content"}], "pdf_path": "sem3/networks.pdf"},
        "Operating Systems": {"topics": ["Process Management", "Threads", "CPU Scheduling", "Synchronization", "Deadlocks", "Memory Management", "Virtual Memory", "File Systems", "IO Systems", "Disk Scheduling", "Protection", "Security", "System Calls", "IPC", "Linux Commands"], "content": [{"page": 1, "text": "OS content"}], "pdf_path": "sem3/os.pdf"}
    },
    "Sem 4": {
        "Algorithms": {"topics": ["Analysis", "Divide Conquer", "Dynamic Programming", "Greedy", "Backtracking", "Branch Bound", "Graph Algorithms", "Sorting Advanced", "String Matching", "NP Complete", "Approximation", "Randomized", "Amortized", "Network Flow", "Algorithm Design"], "content": [{"page": 1, "text": "Algorithms"}], "pdf_path": "sem4/algo.pdf"},
        "Software Engineering": {"topics": ["SDLC", "Requirements", "Design", "Architecture", "Patterns", "Testing", "QA", "Project Management", "Agile", "Version Control", "CI CD", "Metrics", "Risk", "Maintenance", "Documentation"], "content": [{"page": 1, "text": "SE"}], "pdf_path": "sem4/se.pdf"}
    },
    "Sem 5": {
        "Machine Learning": {"topics": ["Supervised", "Unsupervised", "Regression", "Classification", "Clustering", "Neural Networks", "Decision Trees", "Random Forests", "SVM", "K-Means", "PCA", "Feature Engineering", "Model Evaluation", "Overfitting", "Cross Validation"], "content": [{"page": 1, "text": "ML"}], "pdf_path": "sem5/ml.pdf"},
        "AI": {"topics": ["Search", "Heuristics", "Knowledge Representation", "Expert Systems", "NLP", "Computer Vision", "Planning", "Reasoning", "Fuzzy Logic", "Genetic Algorithms", "Neural Nets", "Deep Learning", "Reinforcement", "Ethics", "Applications"], "content": [{"page": 1, "text": "AI"}], "pdf_path": "sem5/ai.pdf"}
    },
    "Sem 6": {
        "Cloud Computing": {"topics": ["Fundamentals", "Service Models", "Deployment", "Virtualization", "Containers", "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Security", "Serverless", "Microservices", "Load Balancing", "Scaling"], "content": [{"page": 1, "text": "Cloud"}], "pdf_path": "sem6/cloud.pdf"},
        "Security": {"topics": ["Cryptography", "Encryption", "Authentication", "Authorization", "Network Security", "Web Security", "Firewalls", "IDS", "Protocols", "Ethical Hacking", "Pen Testing", "Policies", "PKI", "Digital Signatures", "Cyber Threats"], "content": [{"page": 1, "text": "Security"}], "pdf_path": "sem6/security.pdf"}
    },
    "Sem 7": {
        "Deep Learning": {"topics": ["Neural Networks", "CNN", "RNN", "LSTM", "GRU", "Autoencoders", "GANs", "Transfer Learning", "Activation", "Optimization", "Regularization", "Batch Norm", "Dropout", "Image Recognition", "NLP Deep"], "content": [{"page": 1, "text": "DL"}], "pdf_path": "sem7/dl.pdf"},
        "Blockchain": {"topics": ["Basics", "Distributed Ledger", "Consensus", "Proof of Work", "Proof of Stake", "Smart Contracts", "Ethereum", "Hyperledger", "Cryptocurrency", "Bitcoin", "Mining", "Security", "DApps", "Tokenomics", "Applications"], "content": [{"page": 1, "text": "Blockchain"}], "pdf_path": "sem7/blockchain.pdf"}
    },
    "Sem 8": {
        "NLP": {"topics": ["Text Processing", "Tokenization", "POS", "NER", "Sentiment", "Classification", "Language Models", "Embeddings", "Word2Vec", "GloVe", "BERT", "Transformers", "QA", "Translation", "Text Generation"], "content": [{"page": 1, "text": "NLP"}], "pdf_path": "sem8/nlp.pdf"},
        "Computer Vision": {"topics": ["Image Processing", "Classification", "Object Detection", "Segmentation", "Face Recognition", "OCR", "Video Analysis", "3D Vision", "YOLO", "RCNN", "Mask RCNN", "Augmentation", "Features", "Vision Transformers", "GANs Images"], "content": [{"page": 1, "text": "CV"}], "pdf_path": "sem8/cv.pdf"}
    }
}

db_path = ml_models_dir / "content_db.json"
with open(db_path, 'w', encoding='utf-8') as f:
    json.dump(database, f, indent=2)

print("="*70)
print("✅ DATABASE CREATED SUCCESSFULLY!")
print("="*70)
print(f"📁 Location: {db_path.absolute()}")
print(f"📊 Semesters: {len(database)}")
for sem, subjects in database.items():
    print(f"   {sem}: {', '.join(subjects.keys())}")
print("="*70)
print("🚀 Now run: streamlit run app.py")
print("="*70)