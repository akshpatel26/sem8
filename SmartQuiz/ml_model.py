"""
FIXED ml_model.py - Works on Streamlit Cloud
This version ensures the database is always available
"""

import json
import os
from pathlib import Path
import random

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("⚠️ Anthropic library not available. Using fallback generation.")

class MLQuizGenerator:
    def __init__(self):
        """Initialize with embedded database - works everywhere"""
        self.base_dir = self._find_base_dir()
        self.pdf_folder = self.base_dir / "semester_pdfs"
        self.model_folder = self.base_dir / "ml_models"
        
        # Create directories
        self.model_folder.mkdir(exist_ok=True, parents=True)
        self.pdf_folder.mkdir(exist_ok=True, parents=True)
        
        print(f"🔍 MLQuizGenerator initialized:")
        print(f"   Base: {self.base_dir}")
        print(f"   Models: {self.model_folder}")
        
        # Load or create database
        self.content_db = self.load_or_create_database()
        
        if self.content_db:
            print(f"✅ Database ready with {len(self.content_db)} semesters")
        else:
            print("❌ Database initialization failed")
    
    def _find_base_dir(self):
        """Find the correct base directory"""
        current = Path.cwd()
        
        # Check various locations
        if current.name == "smartQuiz":
            return current
        if (current / "smartQuiz").exists():
            return current / "smartQuiz"
        
        # Default to current directory
        return current
    
    def get_embedded_database(self):
        """Return the complete embedded database - always works"""
        return {
            "Sem 1": {
            "Mathematics I": {
                "topics": [
                    "Calculus Fundamentals", "Linear Algebra", "Differential Equations",
                    "Integration", "Vector Spaces", "Matrix Operations", "Limits",
                    "Derivatives", "Series", "Complex Numbers", "Eigenvalues",
                    "Taylor Series", "Fourier Series", "Partial Derivatives", "Applications"
                ],
                "content": [{"page": 1, "text": "Mathematics I covers fundamental concepts in calculus and algebra."}],
                "pdf_path": "semester_pdfs/Sem 1/Mathematics-I.pdf"
            },
            "Physics": {
                "topics": [
                    "Mechanics", "Thermodynamics", "Electromagnetism", "Optics",
                    "Modern Physics", "Waves", "Newton's Laws", "Energy",
                    "Momentum", "Rotational Motion", "Gravitation", "Fluid Mechanics",
                    "Heat Transfer", "Electromagnetic Waves", "Quantum Basics"
                ],
                "content": [{"page": 1, "text": "Physics explores the fundamental laws of nature."}],
                "pdf_path": "semester_pdfs/Sem 1/Physics.pdf"
            },
            "Chemistry": {
                "topics": [
                    "Atomic Structure", "Chemical Bonding", "Thermochemistry",
                    "Chemical Kinetics", "Equilibrium", "Acids and Bases",
                    "Electrochemistry", "Organic Chemistry", "Periodic Table",
                    "Stoichiometry", "States of Matter", "Solutions", "Redox",
                    "Nuclear Chemistry", "Coordination Compounds"
                ],
                "content": [{"page": 1, "text": "Chemistry studies matter and its transformations."}],
                "pdf_path": "semester_pdfs/Sem 1/Chemistry.pdf"
            },
            "Programming Fundamentals": {
                "topics": [
                    "Introduction to Programming", "Variables and Data Types", "Control Structures",
                    "Loops", "Functions", "Arrays", "Strings", "Pointers",
                    "Structures", "File Handling", "Debugging", "Algorithm Design",
                    "Problem Solving", "Programming Paradigms", "Memory Management"
                ],
                "content": [{"page": 1, "text": "Programming fundamentals teach basic coding concepts."}],
                "pdf_path": "semester_pdfs/Sem 1/Programming.pdf"
            }
        },
        
        "Sem 2": {
            "Mathematics II": {
                "topics": [
                    "Advanced Calculus", "Multivariable Calculus", "Differential Equations",
                    "Laplace Transforms", "Z-Transforms", "Probability",
                    "Statistics", "Vector Calculus", "Partial Derivatives",
                    "Multiple Integrals", "Green's Theorem", "Stokes Theorem",
                    "Divergence Theorem", "Line Integrals", "Surface Integrals"
                ],
                "content": [{"page": 1, "text": "Advanced mathematics for engineering applications."}],
                "pdf_path": "semester_pdfs/Sem 2/Mathematics-II.pdf"
            },
            
            "Digital Electronics": {
                "topics": [
                    "Number Systems", "Boolean Algebra", "Logic Gates", "Combinational Circuits",
                    "Sequential Circuits", "Flip-Flops", "Registers", "Counters",
                    "Memory Elements", "Multiplexers", "Decoders", "Encoders",
                    "Adders and Subtractors", "State Machines", "Digital Design"
                ],
                "content": [{"page": 1, "text": "Digital electronics works with discrete signals."}],
                "pdf_path": "semester_pdfs/Sem 2/DigitalElectronics.pdf"
            }
        },
        
        "Sem 3": {
                "Database Management Systems": {
                "topics": [
                    "Introduction to DBMS", "Relational Model", "SQL Fundamentals",
                    "Normalization", "ER Diagrams", "Transactions", "ACID Properties",
                    "Indexing", "Query Optimization", "Joins", "Views and Triggers",
                    "Stored Procedures", "Database Design", "Concurrency Control", "Recovery"
                ],
                "content": [{"page": 1, "text": "DBMS manages structured data efficiently."}],
                "pdf_path": "semester_pdfs/Sem 3/DBMS.pdf"
            },
             "Discrete Mathematics": {
                "topics": [
                  "Set Operations and Laws",
                  "Relations and Their Properties",
                  "Functions and Compositions",
                  "Equivalence and Partial Order Relations",
                  "Lattices and Hasse Diagrams",
                  "Boolean Algebra and Identities",
                  "Propositional Logic and Truth Tables",
                  "Rules of Inference",
                  "Proof Techniques",
                  "Groups, Rings, and Fields",
                  "Homomorphisms",
                  "Graph Terminology and Properties",
                  "Eulerian and Hamiltonian Graphs",
                  "Trees and Spanning Trees",
                  "Shortest Path Algorithms"
                ],
                "content": [
                  {
                    "page": 1,
                    "text": "Discrete Mathematics focuses on logic, algebraic structures, graphs, and set theory."
                  }
                ],
                "pdf_path": "semester_pdfs/Sem 3/DiscreteMathematics.pdf"
                
              }, " IT Workshop ": {
                "topics": [
                  "WWW Protocols and Programs",
                  "Secure Connections",
                  "Web Browsers and Server Configuration",
                  "Web Design Principles",
                  "Website Planning and Navigation",
                  "FTP and Web Hosting",
                  "HTML5 and Basic Tags",
                  "HTML Forms and Website Structure",
                  "XHTML and XML Basics",
                  "CSS Syntax, Structure, and Properties",
                  "CSS3: Layout, Fonts, Colors, Positioning",
                  "JavaScript Basics: Variables, Functions, Conditions, Loops",
                  "JavaScript Objects and DOM",
                  "Form Validation and AJAX Alternatives",
                  "Introduction to jQuery",
                  "DHTML (HTML + CSS + JS)",
                  "AJAX: Concepts, Advantages, Disadvantages",
                  "PHP Basics and Server-side Scripting",
                  "PHP Arrays, Functions, Forms",
                  "MySQL Database Operations with PHP",
                  "PHPMyAdmin and Debugging",
                  "SciLab Basics and Programming"
                ],
                "content": [
                  {
                    "page": 1,
                    "text": "Web Technology includes WWW, HTML, CSS, JavaScript, AJAX, PHP, MySQL, and SciLab."
                  }
                ],
                "pdf_path": "semester_pdfs/Sem 3/ IT Workshop .pdf"
              },
                         
            "Data Structures": {
                "topics": [
                    "Arrays and Linked Lists", "Stacks and Queues", "Trees", "Graphs",
                    "Sorting Algorithms", "Searching Algorithms", "Hashing",
                    "Binary Search Trees", "AVL Trees", "B-Trees", "Graph Traversal",
                    "Dynamic Programming", "Greedy Algorithms", "Recursion", "Complexity Analysis"
                ],
                "content": [{"page": 1, "text": "Data structures organize data efficiently."}],
                "pdf_path": "semester_pdfs/Sem 3/DataStructures.pdf"
            },
            "Digital Electronics": {
                "topics": [
                    "Number Systems", "Boolean Algebra", "Logic Gates", "Combinational Circuits",
                    "Sequential Circuits", "Flip-Flops", "Registers", "Counters",
                    "Memory Elements", "Multiplexers", "Decoders", "Encoders",
                    "Adders and Subtractors", "State Machines", "Digital Design"
                ],
                "content": [{"page": 1, "text": "Digital electronics works with discrete signals."}],
                "pdf_path": "semester_pdfs/Sem 3/DigitalElectronics.pdf"
            },
            "Object Oriented Programming": {
                "topics": [
                    "OOP Concepts", "Classes and Objects", "Inheritance", "Polymorphism",
                    "Encapsulation", "Abstraction", "Interfaces", "Exception Handling",
                    "File I/O", "Collections Framework", "Generics", "Multithreading",
                    "Design Patterns", "SOLID Principles", "UML Diagrams"
                ],
                "content": [{"page": 1, "text": "OOP organizes code around objects and classes."}],
                "pdf_path": "semester_pdfs/Sem 3/OOP.pdf"
            },
           
        },
        
        "Sem 4": {
    "Principles of Management": {
        "topics": [
            "Introduction to Management", "Functions of Management",
            "Planning", "Organizing", "Staffing", "Directing",
            "Controlling", "Decision Making", "Motivation",
            "Leadership", "Communication", "Business Ethics",
            "Corporate Social Responsibility", "Strategic Management",
            "Change Management"
        ],
        "content": [
            { "page": 1, "text": "Principles of Management deals with planning, organizing, directing, and controlling organizational activities." }
        ],
        "pdf_path": "semester_pdfs/Sem 4/POM.pdf"
    },

    "Probability, Statistics and Numerical Methods": {
        "topics": [
            "Probability", "Random Variables", "Distributions",
            "Sampling", "Estimation", "Hypothesis Testing",
            "Correlation", "Regression", "Curve Fitting",
            "Interpolation", "Numerical Differentiation",
            "Numerical Integration", "Numerical Solutions of Equations",
            "Matrices", "Error Analysis"
        ],
        "content": [
            { "page": 1, "text": "Probability and statistics involve data analysis, while numerical methods provide approximations to mathematical problems." }
        ],
        "pdf_path": "semester_pdfs/Sem 4/PSNM.pdf"
    },

    "Computer Organization & Architecture": {
        "topics": [
            "Basic Computer Organization", "Number Systems",
            "Digital Logic Circuits", "Memory Organization",
            "Instruction Set Architecture", "Control Unit",
            "ALU", "Pipeline Processing", "I/O Organization",
            "Cache Memory", "Multiprocessors", "RISC & CISC",
            "Microprogramming", "Bus Structure", "Performance Metrics"
        ],
        "content": [
            { "page": 1, "text": "Computer Organization explains hardware components and architecture defines their design." }
        ],
        "pdf_path": "semester_pdfs/Sem 4/COA.pdf"
    },

    "Operating Systems": {
        "topics": [
            "Introduction to OS", "Process Management", "Threads",
            "CPU Scheduling", "Synchronization", "Deadlocks",
            "Memory Management", "Virtual Memory", "Paging & Segmentation",
            "File Systems", "I/O Systems", "Security", "Protection",
            "Distributed Systems", "Case Studies"
        ],
        "content": [
            { "page": 1, "text": "Operating Systems manage hardware resources and provide services to applications." }
        ],
        "pdf_path": "semester_pdfs/Sem 4/OS.pdf"
    },

    "Object Oriented Programming using Java": {
        "topics": [
            "Basics of Java", "OOP Concepts", "Classes and Objects",
            "Constructors", "Inheritance", "Polymorphism",
            "Abstraction", "Interfaces", "Exception Handling",
            "Collections", "Multithreading", "File Handling",
            "Packages", "JVM Architecture", "GUI Basics"
        ],
        "content": [
            { "page": 1, "text": "Java is an object-oriented programming language widely used for application development." }
        ],
        "pdf_path": "semester_pdfs/Sem 4/Java.pdf"
    }
},
        

        
  "Sem 5": {
    "Software Engineering": {
      "topics": [
        "Introduction to Software Engineering",
        "Software Development Life Cycle",
        "Agile Model",
        "Waterfall Model",
        "Requirement Engineering",
        "SRS Documentation",
        "System Design",
        "UML Diagrams",
        "Software Testing",
        "White-box Testing",
        "Black-box Testing",
        "Software Maintenance",
        "Software Project Management",
        "Risk Management",
        "Quality Assurance"
      ],
      "content": [
        { "page": 1, "text": "Software Engineering is the systematic approach to the development, operation, and maintenance of software." },
        { "page": 2, "text": "The Software Development Life Cycle includes phases like planning, analysis, design, implementation, and testing." }
      ],
      "pdf_path": "semester_pdfs/Sem 5/SoftwareEngineering.pdf"
    },

    "Microprocessor Architecture and Programming": {
      "topics": [
        "Introduction to Microprocessors",
        "8085 Architecture",
        "Registers & Flags",
        "Instruction Set",
        "Addressing Modes",
        "8086 Architecture",
        "Memory Segmentation",
        "Assembly Language Programming",
        "Interrupts",
        "Timing and Control",
        "ALP for Arithmetic Operations",
        "Stack and Subroutines",
        "DMA Controller",
        "Peripheral Devices",
        "Serial & Parallel Communication"
      ],
      "content": [
        { "page": 1, "text": "Microprocessors are programmable digital circuits used for data processing and control." },
        { "page": 2, "text": "The 8085 microprocessor is an 8-bit processor with 16-bit address lines and features like interrupts and flags." }
      ],
      "pdf_path": "semester_pdfs/Sem 5/Microprocessor.pdf"
    },

    "Theory of Computation": {
      "topics": [
        "Introduction to Automata",
        "Finite Automata",
        "DFA & NFA",
        "Regular Expressions",
        "Regular Languages",
        "Pumping Lemma",
        "Context-Free Grammar",
        "Pushdown Automata",
        "Turing Machines",
        "Chomsky Hierarchy",
        "Decidability",
        "Undecidability",
        "Church-Turing Thesis",
        "Computational Complexity",
        "NP-complete Problems"
      ],
      "content": [
        { "page": 1, "text": "Theory of Computation studies computational models such as automata, grammars, and Turing machines." },
        { "page": 2, "text": "Finite automata are abstract machines used to recognize regular languages." }
      ],
      "pdf_path": "semester_pdfs/Sem 5/TOC.pdf"
    },

    "Design and Analysis of Algorithms": {
      "topics": [
        "Introduction to Algorithms",
        "Time Complexity",
        "Space Complexity",
        "Divide and Conquer",
        "Greedy Algorithms",
        "Dynamic Programming",
        "Graph Algorithms",
        "Shortest Path Algorithms",
        "Minimum Spanning Trees",
        "Backtracking",
        "Branch and Bound",
        "Sorting Algorithms",
        "Searching Algorithms",
        "NP-Hard Problems",
        "Approximation Algorithms"
      ],
      "content": [
        { "page": 1, "text": "Algorithm design involves creating efficient solutions using techniques like divide and conquer and dynamic programming." },
        { "page": 2, "text": "Time complexity determines how the runtime of an algorithm grows with input size." }
      ],
      "pdf_path": "semester_pdfs/Sem 5/DAA.pdf"
    },

    "Computer Networks": {
      "topics": [
        "Introduction to Networks",
        "OSI Model",
        "TCP/IP Model",
        "Physical Layer",
        "Data Link Layer",
        "Network Layer",
        "Transport Layer",
        "Application Layer",
        "Routing Algorithms",
        "IP Addressing",
        "Subnetting",
        "Ethernet",
        "Wireless Networks",
        "Network Security Basics",
        "Congestion Control"
      ],
      "content": [
        { "page": 1, "text": "Computer Networks allow devices to exchange data using communication channels and protocols." },
        { "page": 2, "text": "The OSI model has seven layers, each responsible for different network functions." }
      ],
      "pdf_path": "semester_pdfs/Sem 5/ComputerNetworks.pdf"
    },

    "Advanced Java Programming": {
      "topics": [
        "JDBC",
        "Servlets",
        "JSP",
        "JSTL",
        "MVC Architecture",
        "Networking in Java",
        "RMI",
        "Multithreading",
        "Lambda Expressions",
        "Collections Framework",
        "Streams API",
        "Web Services",
        "JPA",
        "Spring Basics",
        "Hibernate Basics"
      ],
      "content": [
        { "page": 1, "text": "Advanced Java focuses on enterprise-level technology such as Servlets, JSP, and JDBC for web applications." },
        { "page": 2, "text": "The MVC pattern separates application logic, UI, and data for cleaner design." }
      ],
      "pdf_path": "semester_pdfs/Sem 5/AdvancedJava.pdf"
    },

    "Dot Net Technology": {
      "topics": [
        ".NET Framework",
        "C# Basics",
        "OOP in C#",
        "Delegates & Events",
        "Collections",
        "LINQ",
        "ADO.NET",
        "ASP.NET",
        "MVC Framework",
        "Web Services",
        "Entity Framework",
        "Windows Forms",
        "Exception Handling",
        "Garbage Collection",
        "Deployment"
      ],
      "content": [
        { "page": 1, "text": ".NET technology supports building web and desktop applications using the C# language." },
        { "page": 2, "text": "ASP.NET enables dynamic web applications with server-side programming capabilities." }
      ],
      "pdf_path": "semester_pdfs/Sem 5/DotNet.pdf"
    }
  },
       "Sem 6": {
    "Artificial Intelligence": {
        "topics": [
            "Introduction to AI", "Search Techniques", "Heuristic Search",
            "Knowledge Representation", "Propositional Logic",
            "Predicate Logic", "Expert Systems", "Machine Learning Basics",
            "NLP Basics", "Computer Vision Basics", "Reasoning",
            "Planning", "Fuzzy Logic", "Genetic Algorithms", "AI Ethics"
        ],
        "content": [
            { "page": 1, "text": "Artificial Intelligence aims to create intelligent systems capable of reasoning and learning." }
        ],
        "pdf_path": "semester_pdfs/Sem 6/AI.pdf"
    },

    "Python Programming": {
        "topics": [
    "String Values, Operations & Slicing",
    "Control Flow (if, loops, break/continue)",
    "Operators",
    "Lists, Tuples, Sets & Dictionaries",
    "Functions (parameters, scope, lambda, arguments)",
    "Object-Oriented Programming (classes, objects, methods,Inheritance,Polymorphism)",
    "Inheritance & Polymorphism",
    "Exception Handling (model, multiple exceptions)",
    "File Handling (read/write, directories, metadata)",
    "Modules & Packages (sys, math, I/O)",
    "Dynamic Typing & Type Conversions",
    "Built-in Functions",
    "Searching Algorithms",
    "Sorting Algorithms",
    "Hash Tables",
    "Custom Exceptions & Error Handling Basics"
        ],
        "content": [
            { "page": 1, "text": "Python is a versatile high-level programming language used for scripting, automation, and data science." }
        ],
        "pdf_path": "semester_pdfs/Sem 6/Python.pdf"
    },

    "Cryptography and Network Security": {
        "topics": [
            "Introduction to Cryptography", "Classical Ciphers",
            "Symmetric Key Encryption", "Asymmetric Encryption",
            "RSA", "Hash Functions", "Digital Signatures",
            "Key Management", "Network Security", "Firewalls",
            "Intrusion Detection", "Web Security", "VPN",
            "Transport Layer Security", "Cyber Attacks"
        ],
        "content": [
            { "page": 1, "text": "Cryptography ensures secure communication through encryption and network security mechanisms." }
        ],
        "pdf_path": "semester_pdfs/Sem 6/CNS.pdf"
    },

    "Machine Learning": {
        "topics": [
            "Introduction to ML", "Supervised Learning", "Unsupervised Learning",
            "Regression", "Classification", "Clustering",
            "Decision Trees", "Random Forest", "SVM",
            "K-Means", "PCA", "Neural Networks",
            "Feature Engineering", "Model Evaluation", "Cross Validation"
        ],
        "content": [
            { "page": 1, "text": "Machine learning enables systems to learn from data without being explicitly programmed." }
        ],
        "pdf_path": "semester_pdfs/Sem 6/ML.pdf"
    },

    "Android Programming": {
        "topics": [
            "Android Basics", "Activities & Intents", "Layouts & UI",
            "RecyclerView", "Fragments", "Data Storage",
            "SQLite", "Room Database", "Networking",
            "API Integration", "Multithreading", "Services",
            "Notifications", "Material Design", "App Deployment"
        ],
        "content": [
            { "page": 1, "text": "Android programming focuses on developing mobile applications using Java or Kotlin." }
        ],
        "pdf_path": "semester_pdfs/Sem 6/Android.pdf"
    },

    "Soft Computing": {
      "topics": [
        "Introduction to Soft Computing",
        "Neural Networks Basics",
        "Perceptron Model",
        "Backpropagation Algorithm",
        "Fuzzy Logic",
        "Fuzzy Inference System",
        "Genetic Algorithms",
        "Evolutionary Computing",
        "Swarm Intelligence",
        "ANN Architecture",
        "Defuzzification Methods",
        "Hybrid Systems",
        "Neuro-Fuzzy Systems",
        "Optimization Techniques",
        "Soft Computing Applications"
      ],
      "content": [
        { "page": 1, "text": "Soft computing combines neural networks, fuzzy systems, and evolutionary algorithms to solve real-world problems." },
        { "page": 2, "text": "Artificial Neural Networks mimic biological neurons and are used for classification and prediction tasks." }
      ],
      "pdf_path": "semester_pdfs/Sem 6/SoftComputing.pdf"
    },

    "Advanced Computer Network": {
      "topics": [
        "Advanced Networking Concepts",
        "TCP Congestion Control",
        "Quality of Service",
        "Advanced Routing Algorithms",
        "Multicast Routing",
        "Software Defined Networking",
        "Network Virtualization",
        "MPLS",
        "Mobile IP",
        "Wireless Sensor Networks",
        "Network Security Enhancements",
        "IPv6",
        "Transport Protocol Enhancements",
        "Cloud Networking",
        "Datacenter Networks"
      ],
      "content": [
        { "page": 1, "text": "Advanced Computer Networks explore high-performance, scalable, and secure communication systems." },
        { "page": 2, "text": "Software Defined Networking provides centralized control to manage dynamic network behavior." }
      ],
      "pdf_path": "semester_pdfs/Sem 6/AdvancedNetworks.pdf"
    },

    "Internet of Things": {
      "topics": [
        "Introduction to IoT",
        "IoT Architecture",
        "Sensors & Actuators",
        "Embedded Systems",
        "Microcontrollers",
        "IoT Communication Protocols",
        "MQTT",
        "CoAP",
        "IoT Cloud Platforms",
        "Edge Computing",
        "IoT Security",
        "Smart Home Applications",
        "Wearable Devices",
        "Industrial IoT",
        "IoT Data Analytics"
      ],
      "content": [
        { "page": 1, "text": "The Internet of Things connects everyday physical devices to the internet for data sharing and automation." },
        { "page": 2, "text": "IoT architectures include sensing, network, and application layers that together enable smart systems." }
      ],
      "pdf_path": "semester_pdfs/Sem 6/IoT.pdf"
    }
    
},
       
    
  "Sem 7": {
    "Compiler Design": {
      "topics": [
        "Introduction to Compilers",
        "Compiler Phases",
        "Lexical Analysis",
        "Syntax Analysis",
        "Parsing Techniques",
        "Semantic Analysis",
        "Syntax Directed Translation",
        "Intermediate Code Generation",
        "Code Optimization",
        "Code Generation",
        "Symbol Tables",
        "Runtime Environments",
        "Error Detection & Recovery",
        "LR & LL Parsing",
        "Garbage Collection"
      ],
      "content": [
        { "page": 1, "text": "Compiler Design focuses on transforming source code into optimized machine code." }
      ],
      "pdf_path": "semester_pdfs/Sem 7/CompilerDesign.pdf"
    },

    "Cyber Security": {
      "topics": [
        "Introduction to Cyber Security",
        "Types of Cyber Attacks",
        "Malware & Vulnerabilities",
        "Network Security",
        "Cryptographic Techniques",
        "Security Policies",
        "Risk Management",
        "Penetration Testing",
        "Web Security",
        "Incident Response",
        "Firewalls",
        "IDS & IPS",
        "Authentication Mechanisms",
        "Cloud Security",
        "Digital Forensics"
      ],
      "content": [
        { "page": 1, "text": "Cyber Security deals with protecting systems, networks, and data from digital attacks." }
      ],
      "pdf_path": "semester_pdfs/Sem 7/CyberSecurity.pdf"
    },

    "Natural Language Processing": {
      "topics": [
        "Introduction to NLP",
        "Text Preprocessing",
        "Tokenization",
        "Stemming & Lemmatization",
        "Bag of Words",
        "TF-IDF",
        "Language Models",
        "POS Tagging",
        "Named Entity Recognition",
        "Syntax Parsing",
        "Word Embeddings",
        "RNN & LSTM Basics",
        "Text Classification",
        "Speech Processing",
        "Machine Translation"
      ],
      "content": [
        { "page": 1, "text": "NLP enables machines to understand, interpret, and generate human language." }
      ],
      "pdf_path": "semester_pdfs/Sem 7/NLP.pdf"
    },

    "Blockchain Technology": {
      "topics": [
        "Introduction to Blockchain",
        "Distributed Ledger Technology",
        "Cryptographic Hashing",
        "Consensus Mechanisms",
        "Mining & Blockchain Structure",
        "Smart Contracts",
        "Ethereum Basics",
        "Blockchain Security",
        "Tokens & Cryptocurrency",
        "Public vs Private Chains",
        "Hyperledger Fabric",
        "Blockchain Scalability",
        "Decentralized Apps",
        "Blockchain Applications",
        "Future Trends"
      ],
      "content": [
        { "page": 1, "text": "Blockchain Technology offers decentralized and tamper-proof ledgers for secure transactions." }
      ],
      "pdf_path": "semester_pdfs/Sem 7/Blockchain.pdf"
    },

    "Distributed Systems": {
      "topics": [
        "Introduction to Distributed Systems",
        "Communication Models",
        "Clock Synchronization",
        "Distributed Algorithms",
        "Mutual Exclusion",
        "Deadlock Handling",
        "Distributed File Systems",
        "Fault Tolerance",
        "Consistency Models",
        "Replication",
        "Naming Services",
        "Load Balancing",
        "MapReduce",
        "Cloud Distributed Systems",
        "Distributed Security"
      ],
      "content": [
        { "page": 1, "text": "Distributed Systems enable multiple computers to work together as a unified system." }
      ],
      "pdf_path": "semester_pdfs/Sem 7/DistributedSystems.pdf"
    },

    "Image Processing": {
      "topics": [
        "Introduction to Image Processing",
        "Image Formation",
        "Color Models",
        "Image Enhancement",
        "Filtering Techniques",
        "Image Restoration",
        "Edge Detection",
        "Segmentation",
        "Morphological Operations",
        "Feature Extraction",
        "Image Compression",
        "Image Representation",
        "Pattern Recognition",
        "Object Detection",
        "Image Applications"
      ],
      "content": [
        { "page": 1, "text": "Image Processing involves manipulating digital images to extract useful information." }
      ],
      "pdf_path": "semester_pdfs/Sem 7/ImageProcessing.pdf"
    }
  },

         "Sem 8": {
    "Next Generation Networks": {
      "topics": [
        "Introduction to NGN",
        "Network Evolution",
        "IP Multimedia Subsystems",
        "VoIP Technologies",
        "4G and LTE",
        "5G Architecture",
        "Quality of Service",
        "Network Virtualization",
        "SDN & NFV",
        "Optical Networks",
        "Wireless Broadband",
        "Network Management",
        "Cloud Networking",
        "IoT Connectivity",
        "Future Internet Technologies"
      ],
      "content": [
        { "page": 1, "text": "Next Generation Networks integrate voice, data, and multimedia over advanced IP-based architectures." }
      ],
      "pdf_path": "semester_pdfs/Sem 8/NGN.pdf"
    },

    "Neural Network and Deep Learning": {
      "topics": [
        "Introduction to Neural Networks",
        "Perceptron Model",
        "Activation Functions",
        "Feedforward Networks",
        "Backpropagation",
        "Optimization Techniques",
        "CNN Architecture",
        "RNN & LSTM",
        "Autoencoders",
        "GANs",
        "Transfer Learning",
        "Regularization Techniques",
        "Hyperparameter Tuning",
        "Deep Learning Frameworks",
        "Applications of Deep Learning"
      ],
      "content": [
        { "page": 1, "text": "Deep Learning enables machines to learn complex patterns using neural network architectures." }
      ],
      "pdf_path": "semester_pdfs/Sem 8/DeepLearning.pdf"
    },

    "Web Data Management": {
      "topics": [
        "Web Data Basics",
        "HTML & XML Data",
        "Web Mining",
        "Data Extraction",
        "Scraping Techniques",
        "Web Databases",
        "Semi-Structured Data",
        "JSON & NoSQL",
        "Information Retrieval",
        "Data Integration",
        "Semantic Web",
        "Ontology Management",
        "Search Engines",
        "Web Data Analytics",
        "Web Data Applications"
      ],
      "content": [
        { "page": 1, "text": "Web Data Management focuses on organizing, storing, and analyzing data generated from the web." }
      ],
      "pdf_path": "semester_pdfs/Sem 8/WebDataManagement.pdf"
    },

    "Big Data Analytics": {
      "topics": [
        "Introduction to Big Data",
        "Hadoop Ecosystem",
        "HDFS Architecture",
        "MapReduce",
        "YARN",
        "NoSQL Databases",
        "Data Warehousing",
        "Spark Architecture",
        "Spark RDD & DataFrames",
        "Data Mining Techniques",
        "Distributed Databases",
        "Real-Time Analytics",
        "Visualization Tools",
        "Data Pipelines",
        "Big Data Applications"
      ],
      "content": [
        { "page": 1, "text": "Big Data Analytics deals with processing and analyzing extremely large datasets for insights." }
      ],
      "pdf_path": "semester_pdfs/Sem 8/BigDataAnalytics.pdf"
    }
  }
            }
        
    
    def load_or_create_database(self):
        """Load database from file or use embedded version"""
        db_path = self.model_folder / "content_db.json"
        
        # Try to load existing database
        if db_path.exists():
            try:
                with open(db_path, 'r', encoding='utf-8') as f:
                    database = json.load(f)
                print(f"✅ Loaded database from file")
                return database
            except Exception as e:
                print(f"⚠️ Error loading file database: {e}")
        
        # Use embedded database
        print("📦 Using embedded database")
        database = self.get_embedded_database()
        
        # Try to save it for next time
        try:
            with open(db_path, 'w', encoding='utf-8') as f:
                json.dump(database, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved database to: {db_path}")
        except Exception as e:
            print(f"⚠️ Could not save database: {e}")
            print("   (This is OK - using embedded version)")
        
        return database
    
    def get_subjects(self, semester):
        """Get list of subjects for a semester"""
        if semester not in self.content_db:
            print(f"❌ Semester '{semester}' not found")
            return []
        
        subjects = list(self.content_db[semester].keys())
        print(f"📚 Found {len(subjects)} subjects for {semester}")
        return subjects
    
    def get_topics(self, semester, subject):
        """Get topics for a subject"""
        try:
            topics = self.content_db[semester][subject]['topics']
            print(f"📝 Found {len(topics)} topics for {subject}")
            return topics
        except KeyError as e:
            print(f"❌ Error getting topics: {e}")
            return []
    
    def get_content_for_topics(self, semester, subject, topics):
        """Get content excerpts for selected topics"""
        try:
            content_pages = self.content_db[semester][subject]['content']
            return [page['text'] for page in content_pages[:5]]
        except KeyError:
            return [f"Content about {subject}"]
    
    def generate_questions(self, semester, subject, topics, difficulty="Medium"):
        """Generate quiz questions based on difficulty level"""
        print(f"\n🤖 Generating {difficulty} questions for {subject}")
        
        content = self.get_content_for_topics(semester, subject, topics)
        
        # Try AI generation if available
        if ANTHROPIC_AVAILABLE and os.getenv("ANTHROPIC_API_KEY"):
            try:
                questions = self.generate_with_claude(content, topics, subject, difficulty)
                if questions and len(questions) > 0:
                    print(f"✅ Generated {len(questions)} AI questions")
                    return questions
            except Exception as e:
                print(f"⚠️ AI generation failed: {e}")
        
        # Fallback generation
        print("📝 Using template-based generation")
        return self.generate_fallback_questions(topics, subject, difficulty)
    
    def generate_with_claude(self, content, topics, subject, difficulty):
        """Generate questions using Claude AI"""
        # Implementation here (same as before)
        pass
    
    def generate_fallback_questions(self, topics, subject, difficulty):
        """Generate template-based questions"""
        templates = {
            "Easy": [
                ("What is {topic}?", [
                    f"A fundamental concept in {subject}",
                    "An advanced technique",
                    "A deprecated method",
                    "A programming language"
                ], 0)
            ],
            "Medium": [
                ("How does {topic} improve system performance?", [
                    "By optimizing resource utilization",
                    "By increasing hardware requirements",
                    "By reducing functionality",
                    "By limiting user access"
                ], 0)
            ],
            "Hard": [
                ("Analyze the impact of {topic} in distributed systems:", [
                    "Provides scalability with fault tolerance",
                    "Simply increases server count",
                    "Has no effect on performance",
                    "Requires complete redesign"
                ], 0)
            ]
        }
        
        questions = []
        template_list = templates.get(difficulty, templates["Medium"])
        
        for i, topic in enumerate(topics[:15]):
            template = template_list[i % len(template_list)]
            question_text = template[0].format(topic=topic, subject=subject)
            options = template[1].copy()
            random.shuffle(options)
            correct_answer = template[1][template[2]]
            
            explanation = f"This tests understanding of {topic} at {difficulty} level."
            
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
        self.content_db = self.load_or_create_database()
        return len(self.content_db) > 0


# Test the generator
if __name__ == "__main__":
    print("="*70)
    print("TESTING ML QUIZ GENERATOR")
    print("="*70)
    
    gen = MLQuizGenerator()
    
    if gen.content_db:
        print("\n✅ Generator initialized successfully")
        print(f"📊 Available semesters: {list(gen.content_db.keys())}")
        
        # Test getting subjects
        subjects = gen.get_subjects("Sem 3")
        print(f"\n📚 Sem 3 subjects: {subjects}")
        
        if subjects:
            # Test getting topics
            topics = gen.get_topics("Sem 3", subjects[0])
            print(f"\n📝 Topics for {subjects[0]}: {len(topics)} topics")
            
            # Test generating questions
            if len(topics) >= 5:
                questions = gen.generate_questions("Sem 3", subjects[0], topics[:5], "Medium")
                print(f"\n✅ Generated {len(questions)} questions")
    else:
        print("\n❌ Generator initialization failed")