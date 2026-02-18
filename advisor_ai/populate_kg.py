"""
Populate KG — Load courses, categories, prerequisites into Neo4j.
Run once: python -m advisor_ai.populate_kg
Safe to re-run (uses MERGE).
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# ── Neo4j Connection ────────────────────────────────────────────────

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


# ── Programs ────────────────────────────────────────────────────────

PROGRAMS = [
    {"name": "Artificial Intelligence", "total_hours": 144},
    {"name": "Cybersecurity", "total_hours": 144},
]


# ── Categories with Required Hours ──────────────────────────────────
#
# required_hours = how many hours a student MUST complete from this category
# type = "compulsory" (must take all) or "elective" (choose subset)
#
# AI:  39 + 10 + 2 + 21 + 3 + 48 + 21 = 144
# CB:  39 + 10 + 2 + 21 + 3 + 48 + 21 = 144

CATEGORIES = {
    # ── Shared Categories (both programs) ───────────────────────────
    "Basic Computer Science": {
        "required_hours": 39,
        "type": "compulsory",
        "programs": ["Artificial Intelligence", "Cybersecurity"],
    },
    "University Requirements (Compulsory)": {
        "required_hours": 10,
        "type": "compulsory",
        "programs": ["Artificial Intelligence", "Cybersecurity"],
    },
    "University Requirements (Elective)": {
        "required_hours": 2,
        "type": "elective",
        "programs": ["Artificial Intelligence", "Cybersecurity"],
    },
    "Math & Basic Science": {
        "required_hours": 21,
        "type": "compulsory",
        "programs": ["Artificial Intelligence", "Cybersecurity"],
    },
    "Math & Basic Science (Elective)": {
        "required_hours": 3,
        "type": "elective",
        "programs": ["Artificial Intelligence", "Cybersecurity"],
    },

    # ── AI-only Categories ──────────────────────────────────────────
    "AI Major Requirements": {
        "required_hours": 48,
        "type": "compulsory",
        "programs": ["Artificial Intelligence"],
    },
    "AI Major Electives": {
        "required_hours": 21,
        "type": "elective",
        "programs": ["Artificial Intelligence"],
    },

    # ── Cybersecurity-only Categories ───────────────────────────────
    "Cybersecurity Major Requirements": {
        "required_hours": 48,
        "type": "compulsory",
        "programs": ["Cybersecurity"],
    },
    "Cybersecurity Major Electives": {
        "required_hours": 21,
        "type": "elective",
        "programs": ["Cybersecurity"],
    },
}


# ── Courses ─────────────────────────────────────────────────────────
# (code, name, credit_hours, level, category)

COURSES = [
    # ═══════════════════════════════════════════════════════════════
    # SHARED — Basic Computer Science (39 hours)
    # ═══════════════════════════════════════════════════════════════
    ("CS101", "Introduction to Computer Science", 3, 1, "Basic Computer Science"),
    ("CS102", "Structured Programming", 3, 1, "Basic Computer Science"),
    ("CS103", "Discrete Structure", 3, 1, "Basic Computer Science"),
    ("CS201", "Object Oriented Programming", 3, 2, "Basic Computer Science"),
    ("CS202", "Signal and System", 3, 2, "Basic Computer Science"),
    ("CS203", "Data Structures", 3, 2, "Basic Computer Science"),
    ("CS204", "Operating Systems", 3, 2, "Basic Computer Science"),
    ("CS205", "Algorithms", 3, 2, "Basic Computer Science"),
    ("IS101", "Fundamentals of Information Systems", 3, 1, "Basic Computer Science"),
    ("IS201", "Database Systems", 3, 2, "Basic Computer Science"),
    ("IS202", "System Analysis and Design", 3, 2, "Basic Computer Science"),
    ("SW201", "Software Engineering", 3, 2, "Basic Computer Science"),
    ("AI201", "Introduction to Artificial Intelligence", 3, 2, "Basic Computer Science"),

    # ═══════════════════════════════════════════════════════════════
    # SHARED — University Requirements Compulsory (10 hours)
    # ═══════════════════════════════════════════════════════════════
    ("HM001", "English Language 1", 2, 1, "University Requirements (Compulsory)"),
    ("HM002", "English Language 2", 2, 1, "University Requirements (Compulsory)"),
    ("HM003", "Human Rights & Anticorruption", 2, 2, "University Requirements (Compulsory)"),
    ("HM004", "Russian Language 1", 2, 2, "University Requirements (Compulsory)"),
    ("HM005", "Russian Language 2", 2, 2, "University Requirements (Compulsory)"),

    # ═══════════════════════════════════════════════════════════════
    # SHARED — University Requirements Elective (pick 2 hours)
    # ═══════════════════════════════════════════════════════════════
    ("HM006", "Scientific Thinking", 2, 3, "University Requirements (Elective)"),
    ("HM007", "Technical Writing", 1, 3, "University Requirements (Elective)"),
    ("HM008", "Scientific Research Methodology", 2, 3, "University Requirements (Elective)"),
    ("HM009", "Scientific Research Methodology 2", 2, 3, "University Requirements (Elective)"),
    ("HM010", "Russian Language 3", 2, 3, "University Requirements (Elective)"),

    # ═══════════════════════════════════════════════════════════════
    # SHARED — Math & Basic Science (21 hours)
    # ═══════════════════════════════════════════════════════════════
    ("ELC101", "Electronics", 3, 1, "Math & Basic Science"),
    ("ELC201", "Logic Design", 3, 2, "Math & Basic Science"),
    ("MTH101", "Mathematics 1", 3, 1, "Math & Basic Science"),
    ("MTH102", "Linear Algebra", 3, 1, "Math & Basic Science"),
    ("MTH103", "Mathematics 2", 3, 1, "Math & Basic Science"),
    ("MTH104", "Probability and Statistics 1", 3, 1, "Math & Basic Science"),
    ("PH101", "Physics", 3, 1, "Math & Basic Science"),

    # ═══════════════════════════════════════════════════════════════
    # SHARED — Math & Basic Science Elective (pick 3 hours = 1 course)
    # ═══════════════════════════════════════════════════════════════
    ("MTH201", "Mathematics 3", 3, 2, "Math & Basic Science (Elective)"),
    ("MTH202", "Probability and Statistics 2", 3, 2, "Math & Basic Science (Elective)"),
    ("MTH203", "Numerical Analysis", 3, 2, "Math & Basic Science (Elective)"),

    # ═══════════════════════════════════════════════════════════════
    # AI — Major Requirements (48 hours, all compulsory)
    # ═══════════════════════════════════════════════════════════════
    ("AI301", "Machine Learning", 3, 3, "AI Major Requirements"),
    ("AI302", "Natural Language Processing", 3, 3, "AI Major Requirements"),
    ("AI303", "Speech Recognition", 3, 3, "AI Major Requirements"),
    ("AI304", "Computer Vision", 3, 3, "AI Major Requirements"),
    ("AI305", "Pattern Recognition", 3, 3, "AI Major Requirements"),
    ("AI306", "Computational Perception", 3, 3, "AI Major Requirements"),
    ("AI401", "Intelligent Algorithms", 3, 4, "AI Major Requirements"),
    ("AI402", "Computational Cognitive Systems", 3, 4, "AI Major Requirements"),
    ("AI403", "Deep Learning", 3, 4, "AI Major Requirements"),
    ("AI404", "Graduation Project 1", 3, 4, "AI Major Requirements"),
    ("AI405", "Multi Agent Systems", 3, 4, "AI Major Requirements"),
    ("AI406", "AI Applications", 3, 4, "AI Major Requirements"),
    ("AI407", "Graduation Project 2", 3, 4, "AI Major Requirements"),
    ("CS302", "Computer Architecture and Organization", 3, 3, "AI Major Requirements"),
    ("DS307", "Cloud Computing", 3, 3, "AI Major Requirements"),
    ("SW303", "User Interface Design", 3, 3, "AI Major Requirements"),

    # ═══════════════════════════════════════════════════════════════
    # AI — Major Electives (pick 21 hours = 7 courses)
    # ═══════════════════════════════════════════════════════════════
    ("AI307", "Computational Learning Theory", 3, 3, "AI Major Electives"),
    ("AI308", "Language Modeling", 3, 3, "AI Major Electives"),
    ("AI309", "User Models", 3, 3, "AI Major Electives"),
    ("AI310", "Handwriting Recognition", 3, 3, "AI Major Electives"),
    ("AI311", "Expert Systems", 3, 3, "AI Major Electives"),
    ("AI312", "Architecture of Intelligence", 3, 3, "AI Major Electives"),
    ("AI314", "Artificial Intelligence in Games", 3, 3, "AI Major Electives"),
    ("AI408", "Cognitive Modeling", 3, 4, "AI Major Electives"),
    ("AI409", "Cognitive Engineering", 3, 4, "AI Major Electives"),
    ("AI410", "Cognitive Natural Networks", 3, 4, "AI Major Electives"),
    ("AI411", "Language and Speech Technology", 3, 4, "AI Major Electives"),
    ("AI412", "Statistical Language Modeling", 3, 4, "AI Major Electives"),
    ("AI413", "AI for Robotics", 3, 4, "AI Major Electives"),
    ("AI415", "Selected Topic in AI 1", 3, 4, "AI Major Electives"),
    ("AI416", "Selected Topic in AI 2", 3, 4, "AI Major Electives"),
    ("CS301", "Operations Research", 3, 3, "AI Major Electives"),
    ("CS303", "Image Processing", 3, 3, "AI Major Electives"),
    ("CS307", "Computer Graphics", 3, 3, "AI Major Electives"),
    ("CS309", "Embedded Systems", 3, 3, "AI Major Electives"),
    ("CS403", "Advanced Knowledge Representation and Reasoning", 3, 4, "AI Major Electives"),
    ("ROB302", "Fundamental of Cognitive Interaction with Robots", 3, 3, "AI Major Electives"),
    ("SW305", "Software Development for Mobile Devices", 3, 3, "AI Major Electives"),
    ("SW401", "Software Testing & Quality Assurance", 3, 4, "AI Major Electives"),

    # ═══════════════════════════════════════════════════════════════
    # CYBERSECURITY — Major Requirements (48 hours, all compulsory)
    # ═══════════════════════════════════════════════════════════════
    ("CB301", "Computer Networks", 3, 3, "Cybersecurity Major Requirements"),
    ("CB302", "Computer Architecture", 3, 3, "Cybersecurity Major Requirements"),
    ("CB303", "Cryptography", 3, 3, "Cybersecurity Major Requirements"),
    ("CB304", "Introduction to Cyber-Security", 3, 3, "Cybersecurity Major Requirements"),
    ("CB305", "Network Security", 3, 3, "Cybersecurity Major Requirements"),
    ("CB306", "Software Security", 3, 3, "Cybersecurity Major Requirements"),
    ("CB307", "Introduction to Cyber Attacks", 3, 3, "Cybersecurity Major Requirements"),
    ("CB308", "Real-Time Auditing & Defense", 3, 3, "Cybersecurity Major Requirements"),
    ("CB309", "Hardware Security", 3, 3, "Cybersecurity Major Requirements"),
    ("CB401", "Cyber Attack Countermeasures", 3, 4, "Cybersecurity Major Requirements"),
    ("CB402", "Digital Forensics", 3, 4, "Cybersecurity Major Requirements"),
    ("CB403", "Advanced Cryptography", 3, 4, "Cybersecurity Major Requirements"),
    ("CB404", "Ethical Hacking", 3, 4, "Cybersecurity Major Requirements"),
    ("CB405", "Penetration Testing & Vulnerabilities Discovery", 3, 4, "Cybersecurity Major Requirements"),
    ("CB406", "Graduation Project 1", 3, 4, "Cybersecurity Major Requirements"),
    ("CB407", "Graduation Project 2", 3, 4, "Cybersecurity Major Requirements"),

    # ═══════════════════════════════════════════════════════════════
    # CYBERSECURITY — Major Electives (pick 21 hours = 7 courses)
    # ═══════════════════════════════════════════════════════════════
    ("CB310", "Usable Security", 3, 3, "Cybersecurity Major Electives"),
    ("CB311", "Blockchain & Cryptocurrencies", 3, 3, "Cybersecurity Major Electives"),
    ("CB312", "Cyber Security for Internet of Things", 3, 3, "Cybersecurity Major Electives"),
    ("CB313", "Reverse Engineering & Disassemblers", 3, 3, "Cybersecurity Major Electives"),
    ("CB314", "Threat Detection and Mitigation", 3, 3, "Cybersecurity Major Electives"),
    ("CB408", "Firewalls and Web Application Firewall", 3, 4, "Cybersecurity Major Electives"),
    ("CB409", "Cybercrime Investigator", 3, 4, "Cybersecurity Major Electives"),
    ("CB410", "Cryptanalysis", 3, 4, "Cybersecurity Major Electives"),
    ("CB411", "Selected Topic in Networks 1", 3, 4, "Cybersecurity Major Electives"),
    ("CB412", "Selected Topic in Networks 2", 3, 4, "Cybersecurity Major Electives"),
    ("CB413", "Computer Networks Defense", 3, 4, "Cybersecurity Major Electives"),
    ("CB414", "Information Security", 3, 4, "Cybersecurity Major Electives"),
    ("CS402", "Theory of Computation", 3, 4, "Cybersecurity Major Electives"),
    ("DS301", "Data Mining & Big Data Analysis", 3, 3, "Cybersecurity Major Electives"),
    # DS307 Cloud Computing already defined above (AI Major Req), link via OFFERS
    ("IS306", "Internet of Things", 3, 3, "Cybersecurity Major Electives"),
    ("STA301", "Operations Research", 3, 3, "Cybersecurity Major Electives"),
]


# ── Prerequisites ───────────────────────────────────────────────────
# (course_code, prerequisite_code)
# Inferred from course levels and academic logic

PREREQUISITES = [
    # CS chain
    ("CS102", "CS101"),       # Structured Programming needs Intro CS
    ("CS201", "CS102"),       # OOP needs Structured Programming
    ("CS203", "CS201"),       # Data Structures needs OOP
    ("CS204", "CS201"),       # OS needs OOP
    ("CS205", "CS203"),       # Algorithms needs Data Structures
    ("CS302", "CS204"),       # Computer Architecture needs OS

    # IS chain
    ("IS201", "IS101"),       # Database needs Fundamentals
    ("IS201", "CS102"),       # Database needs Programming
    ("IS202", "IS201"),       # System Analysis needs Database

    # Math chain
    ("MTH103", "MTH101"),     # Math 2 needs Math 1
    ("MTH201", "MTH103"),     # Math 3 needs Math 2
    ("MTH202", "MTH104"),     # Stats 2 needs Stats 1
    ("MTH203", "MTH103"),     # Numerical Analysis needs Math 2
    ("ELC201", "ELC101"),     # Logic Design needs Electronics

    # Language chain
    ("HM002", "HM001"),       # English 2 needs English 1
    ("HM005", "HM004"),       # Russian 2 needs Russian 1
    ("HM010", "HM005"),       # Russian 3 needs Russian 2

    # AI chain
    ("AI201", "CS102"),       # Intro AI needs Programming
    ("AI301", "AI201"),       # Machine Learning needs Intro AI
    ("AI301", "MTH104"),      # Machine Learning needs Stats
    ("AI302", "AI301"),       # NLP needs Machine Learning
    ("AI303", "AI302"),       # Speech Recognition needs NLP
    ("AI304", "AI301"),       # Computer Vision needs ML
    ("AI305", "AI301"),       # Pattern Recognition needs ML
    ("AI306", "AI304"),       # Computational Perception needs CV
    ("AI401", "CS205"),       # Intelligent Algorithms needs Algorithms
    ("AI401", "AI301"),       # Intelligent Algorithms needs ML
    ("AI403", "AI301"),       # Deep Learning needs ML
    ("AI404", "AI301"),       # Graduation Project 1 needs ML
    ("AI405", "AI301"),       # Multi Agent Systems needs ML
    ("AI407", "AI404"),       # Graduation Project 2 needs Project 1

    # AI Electives
    ("AI307", "AI301"),       # Computational Learning Theory needs ML
    ("AI308", "AI302"),       # Language Modeling needs NLP
    ("AI310", "AI304"),       # Handwriting Recognition needs CV
    ("AI311", "AI201"),       # Expert Systems needs Intro AI
    ("AI408", "AI301"),       # Cognitive Modeling needs ML
    ("AI410", "AI403"),       # Cognitive Neural Networks needs DL
    ("AI411", "AI302"),       # Language & Speech Tech needs NLP
    ("AI412", "AI302"),       # Statistical Language Modeling needs NLP
    ("AI413", "AI301"),       # AI for Robotics needs ML
    ("CS303", "CS202"),       # Image Processing needs Signal
    ("CS307", "CS201"),       # Computer Graphics needs OOP
    ("CS403", "AI201"),       # Advanced Knowledge Rep needs Intro AI
    ("SW201", "CS201"),       # Software Engineering needs OOP
    ("SW303", "SW201"),       # UI Design needs Software Eng
    ("SW305", "CS201"),       # Mobile Dev needs OOP
    ("SW401", "SW201"),       # Software Testing needs Software Eng

    # Cybersecurity chain
    ("CB301", "CS201"),       # Computer Networks needs OOP
    ("CB303", "MTH102"),      # Cryptography needs Linear Algebra
    ("CB304", "CB301"),       # Intro Cybersecurity needs Networks
    ("CB305", "CB301"),       # Network Security needs Networks
    ("CB305", "CB304"),       # Network Security needs Intro Cyber
    ("CB306", "CS201"),       # Software Security needs OOP
    ("CB306", "CB304"),       # Software Security needs Intro Cyber
    ("CB307", "CB304"),       # Intro Cyber Attacks needs Intro Cyber
    ("CB308", "CB305"),       # Real-Time Auditing needs Network Security
    ("CB309", "ELC201"),      # Hardware Security needs Logic Design
    ("CB401", "CB307"),       # Countermeasures needs Cyber Attacks
    ("CB402", "CB304"),       # Digital Forensics needs Intro Cyber
    ("CB403", "CB303"),       # Advanced Crypto needs Cryptography
    ("CB404", "CB307"),       # Ethical Hacking needs Cyber Attacks
    ("CB405", "CB404"),       # Pen Testing needs Ethical Hacking
    ("CB406", "CB304"),       # Graduation Project 1 needs Intro Cyber
    ("CB407", "CB406"),       # Graduation Project 2 needs Project 1
    ("CB310", "CB304"),       # Usable Security needs Intro Cyber
    ("CB311", "CB303"),       # Blockchain needs Cryptography
    ("CB312", "CB301"),       # IoT Security needs Networks
    ("CB313", "CB304"),       # Reverse Engineering needs Intro Cyber
    ("CB314", "CB305"),       # Threat Detection needs Network Security
    ("CB408", "CB305"),       # Firewalls needs Network Security
    ("CB410", "CB303"),       # Cryptanalysis needs Cryptography
    ("CB413", "CB305"),       # Network Defense needs Network Security
    ("CB414", "CB304"),       # Info Security needs Intro Cyber
]


# ═══════════════════════════════════════════════════════════════════
# Population Functions
# ═══════════════════════════════════════════════════════════════════

def clear_database(session):
    """Wipe all data (optional — for clean re-runs)."""
    session.run("MATCH (n) DETACH DELETE n")
    print("[KG] Database cleared")


def create_programs(session):
    """Create Program nodes."""
    for prog in PROGRAMS:
        session.run(
            "MERGE (p:Program {name: $name}) SET p.total_hours = $hours",
            name=prog["name"],
            hours=prog["total_hours"],
        )
    print(f"[KG] Created {len(PROGRAMS)} programs")


def create_categories(session):
    """Create Category nodes with required_hours and type."""
    for cat_name, cat_data in CATEGORIES.items():
        session.run(
            """
            MERGE (cat:Category {name: $name})
            SET cat.required_hours = $hours, cat.type = $type
            """,
            name=cat_name,
            hours=cat_data["required_hours"],
            type=cat_data["type"],
        )
        # Link to programs
        for prog_name in cat_data["programs"]:
            session.run(
                """
                MATCH (p:Program {name: $prog}), (cat:Category {name: $cat})
                MERGE (p)-[:HAS_CATEGORY]->(cat)
                """,
                prog=prog_name,
                cat=cat_name,
            )
    print(f"[KG] Created {len(CATEGORIES)} categories with required hours")


def create_courses(session):
    """Create Course nodes and link to categories and programs."""
    for code, name, ch, level, category in COURSES:
        # Create course
        session.run(
            """
            MERGE (c:Course {code: $code})
            SET c.name = $name, c.credit_hours = $ch, c.level = $level
            """,
            code=code, name=name, ch=ch, level=level,
        )
        # Link to category
        session.run(
            """
            MATCH (c:Course {code: $code}), (cat:Category {name: $cat})
            MERGE (c)-[:BELONGS_TO]->(cat)
            """,
            code=code, cat=category,
        )
        # Link to the program(s) that this category belongs to
        for prog_name in CATEGORIES[category]["programs"]:
            session.run(
                """
                MATCH (p:Program {name: $prog}), (c:Course {code: $code})
                MERGE (p)-[:OFFERS]->(c)
                """,
                prog=prog_name, code=code,
            )
    print(f"[KG] Created {len(COURSES)} courses")


def create_prerequisites(session):
    """Create REQUIRES relationships between courses."""
    created = 0
    for course_code, prereq_code in PREREQUISITES:
        result = session.run(
            """
            MATCH (c:Course {code: $course}), (p:Course {code: $prereq})
            MERGE (c)-[:REQUIRES]->(p)
            RETURN c.code AS c, p.code AS p
            """,
            course=course_code, prereq=prereq_code,
        )
        if result.single():
            created += 1
    print(f"[KG] Created {created} prerequisite relationships")


def print_stats(session):
    """Print summary statistics."""
    result = session.run("""
        MATCH (p:Program) WITH count(p) AS programs
        MATCH (cat:Category) WITH programs, count(cat) AS categories
        MATCH (c:Course) WITH programs, categories, count(c) AS courses
        MATCH ()-[r:REQUIRES]->() WITH programs, categories, courses, count(r) AS prereqs
        RETURN programs, categories, courses, prereqs
    """)
    r = result.single()
    print(f"\n[KG] === Database Stats ===")
    print(f"  Programs:      {r['programs']}")
    print(f"  Categories:    {r['categories']}")
    print(f"  Courses:       {r['courses']}")
    print(f"  Prerequisites: {r['prereqs']}")


# ═══════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"[KG] Connecting to Neo4j at {URI}...")
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

    try:
        driver.verify_connectivity()
        print("[KG] Connected!")

        with driver.session() as session:
            clear_database(session)
            create_programs(session)
            create_categories(session)
            create_courses(session)
            create_prerequisites(session)
            print_stats(session)

        print("\n[KG] ✅ Knowledge Graph populated successfully!")
    except Exception as e:
        print(f"\n[KG] ❌ Error: {e}")
    finally:
        driver.close()
