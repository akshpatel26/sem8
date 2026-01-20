"""
UPDATED ml_model.py with Difficulty Level Support
"""

import json
import os
from pathlib import Path
import random

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("⚠️ Anthropic library not available. Using fallback generation.")

class MLQuizGenerator:
    def __init__(self):
        """Initialize the quiz generator with proper path handling"""
        self.base_dir = self._find_base_dir()
        self.pdf_folder = self.base_dir / "semester_pdfs"
        self.model_folder = self.base_dir / "ml_models"
        
        self.model_folder.mkdir(exist_ok=True, parents=True)
        self.pdf_folder.mkdir(exist_ok=True, parents=True)
        
        print(f"🔍 MLQuizGenerator initialized:")
        print(f"   Base: {self.base_dir}")
        print(f"   Models: {self.model_folder}")
        print(f"   PDFs: {self.pdf_folder}")
        
        self.content_db = self.load_content_database()
        
        if self.content_db:
            print(f"✅ Loaded {len(self.content_db)} semesters")
        else:
            print("❌ Failed to load database")
    
    def _find_base_dir(self):
        """Find the correct base directory"""
        current = Path.cwd()
        
        if current.name == "smartQuiz":
            return current
        
        if (current / "smartQuiz").exists():
            return current / "smartQuiz"
        
        for parent in [current] + list(current.parents):
            if (parent / "ml_models").exists() or (parent / "smartQuiz").exists():
                return parent / "smartQuiz" if (parent / "smartQuiz").exists() else parent
        
        return current
    
    def load_content_database(self):
        """Load the content database"""
        db_path = self.model_folder / "content_db.json"
        
        print(f"📄 Loading database from: {db_path}")
        
        if not db_path.exists():
            print("❌ Database file not found!")
            return {}
        
        try:
            with open(db_path, 'r', encoding='utf-8') as f:
                database = json.load(f)
            
            print(f"✅ Database loaded successfully")
            return database
            
        except Exception as e:
            print(f"❌ Error loading database: {e}")
            return {}
    
    def get_subjects(self, semester):
        """Get list of subjects for a semester"""
        if semester not in self.content_db:
            return []
        
        subjects = list(self.content_db[semester].keys())
        return subjects
    
    def get_topics(self, semester, subject):
        """Get topics for a subject"""
        try:
            topics = self.content_db[semester][subject]['topics']
            return topics
        except KeyError:
            return []
    
    def get_content_for_topics(self, semester, subject, topics):
        """Get content excerpts for selected topics"""
        try:
            content_pages = self.content_db[semester][subject]['content']
            return [page['text'] for page in content_pages[:5]]
        except KeyError:
            return ["General content about " + subject]
    
    def generate_questions(self, semester, subject, topics, difficulty="Medium"):
        """Generate quiz questions based on difficulty level"""
        print(f"\n🤖 Generating questions:")
        print(f"   Semester: {semester}")
        print(f"   Subject: {subject}")
        print(f"   Topics: {len(topics)}")
        print(f"   Difficulty: {difficulty}")
        
        content = self.get_content_for_topics(semester, subject, topics)
        
        # Try AI generation first
        if ANTHROPIC_AVAILABLE and os.getenv("ANTHROPIC_API_KEY"):
            print("   Attempting AI generation...")
            try:
                questions = self.generate_with_claude(content, topics, subject, difficulty)
                if questions and len(questions) > 0:
                    print(f"✅ Generated {len(questions)} questions with AI")
                    return questions
            except Exception as e:
                print(f"⚠️ AI generation failed: {e}")
        
        # Fallback to template-based generation
        print("   Using template-based generation...")
        return self.generate_fallback_questions(topics, subject, difficulty)
    
    def generate_with_claude(self, content, topics, subject, difficulty):
        """Generate questions using Claude AI with difficulty level"""
        if not ANTHROPIC_API_KEY:
            return None
            
        combined_content = "\n\n".join(content[:3])[:3000]
        topic_list = ', '.join(topics[:10])
        
        # Difficulty-specific prompts
        difficulty_instructions = {
            "Easy": """
- Focus on definitions, basic concepts, and recall
- Questions should test memorization and understanding
- Use straightforward language
- Correct answers should be clearly identifiable
- Examples: "What is...", "Define...", "Which of the following is..."
            """,
            "Medium": """
- Focus on application and analysis
- Questions should require understanding and reasoning
- Include scenario-based questions
- Distractors should be more challenging
- Examples: "How would you...", "What happens when...", "Compare..."
            """,
            "Hard": """
- Focus on evaluation, synthesis, and complex problem-solving
- Questions should require deep analysis and critical thinking
- Include multi-step reasoning and edge cases
- Distractors should be very plausible
- Examples: "Analyze...", "Design a solution for...", "What would be the impact..."
            """
        }
        
        prompt = f"""Generate {min(len(topics), 15)} multiple-choice questions for {subject} at {difficulty.upper()} difficulty level.

Topics to cover: {topic_list}

Context: {combined_content}

DIFFICULTY LEVEL: {difficulty}
{difficulty_instructions.get(difficulty, difficulty_instructions["Medium"])}

Create diverse questions in JSON format:
[
  {{
    "question": "Clear question text?",
    "topic": "Specific topic name",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "Option A",
    "explanation": "Detailed explanation of why this is correct and why others are wrong."
  }}
]

Requirements:
- ALL questions must match the {difficulty} difficulty level
- Mix question types appropriate for this difficulty
- Make distractors realistic and relevant
- Provide comprehensive explanations
- Return ONLY the JSON array, no other text"""

        try:
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
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
                return questions[:15]
            
            return None
            
        except Exception as e:
            print(f"Claude API error: {e}")
            return None
    
    def generate_fallback_questions(self, topics, subject, difficulty):
        """Generate questions using templates based on difficulty"""
        
        # Easy Level Templates
        easy_templates = [
            {
                "template": "What is {topic}?",
                "options_gen": lambda t: [
                    f"A fundamental concept in {subject}",
                    f"An advanced technique",
                    f"A deprecated method",
                    f"A programming language"
                ],
                "answer_idx": 0
            },
            {
                "template": "Which statement correctly defines {topic}?",
                "options_gen": lambda t: [
                    f"{t} is a key concept used in {subject}",
                    f"{t} is rarely used in practice",
                    f"{t} was invented last year",
                    f"{t} is only theoretical"
                ],
                "answer_idx": 0
            },
            {
                "template": "{topic} is primarily used for:",
                "options_gen": lambda t: [
                    f"Implementing core functionality",
                    f"Decorative purposes only",
                    f"Historical reference",
                    f"Testing purposes only"
                ],
                "answer_idx": 0
            }
        ]
        
        # Medium Level Templates
        medium_templates = [
            {
                "template": "How does {topic} improve system performance?",
                "options_gen": lambda t: [
                    f"By optimizing resource utilization and processing efficiency",
                    f"By increasing hardware requirements",
                    f"By reducing functionality",
                    f"By limiting user access"
                ],
                "answer_idx": 0
            },
            {
                "template": "When implementing {topic}, what is the main consideration?",
                "options_gen": lambda t: [
                    f"Ensuring proper integration with existing systems",
                    f"Making it visually appealing",
                    f"Avoiding all modern practices",
                    f"Using the oldest available method"
                ],
                "answer_idx": 0
            },
            {
                "template": "Compare {topic} with traditional approaches:",
                "options_gen": lambda t: [
                    f"{t} offers better scalability and efficiency",
                    f"{t} is always slower",
                    f"{t} requires more manual work",
                    f"{t} has no practical advantages"
                ],
                "answer_idx": 0
            }
        ]
        
        # Hard Level Templates
        hard_templates = [
            {
                "template": "Analyze the impact of {topic} on system architecture when dealing with high-volume concurrent requests:",
                "options_gen": lambda t: [
                    f"It provides distributed processing capabilities with load balancing and fault tolerance mechanisms",
                    f"It simply increases server count without optimization",
                    f"It has no effect on concurrent processing",
                    f"It requires complete system redesign for minimal benefit"
                ],
                "answer_idx": 0
            },
            {
                "template": "In a scenario where {topic} conflicts with legacy systems, what is the optimal resolution strategy?",
                "options_gen": lambda t: [
                    f"Implement an adapter pattern with incremental migration and backward compatibility",
                    f"Completely abandon the new approach",
                    f"Force immediate replacement regardless of dependencies",
                    f"Maintain both systems indefinitely without integration"
                ],
                "answer_idx": 0
            },
            {
                "template": "Evaluate the trade-offs of implementing {topic} in a distributed microservices environment:",
                "options_gen": lambda t: [
                    f"Increased complexity and latency vs improved scalability and fault isolation",
                    f"No trade-offs exist; it's always beneficial",
                    f"Only disadvantages with no benefits",
                    f"It's incompatible with microservices architecture"
                ],
                "answer_idx": 0
            }
        ]
        
        # Select templates based on difficulty
        if difficulty == "Easy":
            templates = easy_templates
        elif difficulty == "Hard":
            templates = hard_templates
        else:
            templates = medium_templates
        
        questions = []
        
        for i, topic in enumerate(topics[:15]):
            template = templates[i % len(templates)]
            
            question_text = template["template"].format(topic=topic, subject=subject)
            options = template["options_gen"](topic)
            correct_answer = options[template["answer_idx"]]
            
            # Shuffle options
            random.shuffle(options)
            
            # Create explanation based on difficulty
            if difficulty == "Easy":
                explanation = f"This is a basic question about {topic}. The correct answer defines the fundamental purpose of {topic} in {subject}."
            elif difficulty == "Hard":
                explanation = f"This advanced question tests your deep understanding of {topic}. The correct answer considers multiple factors including scalability, architecture, and real-world implementation challenges in {subject}."
            else:
                explanation = f"This question tests your practical understanding of {topic}. The correct answer demonstrates how {topic} is applied effectively in {subject} scenarios."
            
            questions.append({
                'question': question_text,
                'topic': topic,
                'options': options,
                'correct_answer': correct_answer,
                'explanation': explanation
            })
        
        return questions
    
    def retrain_model(self):
        """Reload the database"""
        self.content_db = self.load_content_database()
        return len(self.content_db) > 0


if __name__ == "__main__":
    print("="*70)
    print("TESTING ML QUIZ GENERATOR WITH DIFFICULTY LEVELS")
    print("="*70)
    
    gen = MLQuizGenerator()
    
    if gen.content_db:
        subjects = gen.get_subjects("Sem 3")
        if subjects:
            test_subject = subjects[0]
            topics = gen.get_topics("Sem 3", test_subject)
            
            if len(topics) >= 10:
                for difficulty in ["Easy", "Medium", "Hard"]:
                    print(f"\n🎯 Testing {difficulty} difficulty:")
                    questions = gen.generate_questions("Sem 3", test_subject, topics[:5], difficulty)
                    print(f"   Generated {len(questions)} questions")
                    if questions:
                        print(f"   Sample: {questions[0]['question'][:60]}...")