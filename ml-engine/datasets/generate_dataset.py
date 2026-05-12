#!/usr/bin/env python3
"""Generate a synthetic labeled dataset (sample_jobs.csv) for training.

Run directly to regenerate the bundled dataset:
    python datasets/generate_dataset.py

Output: datasets/sample_jobs.csv
"""
from __future__ import annotations

import csv
import random
from pathlib import Path

random.seed(42)

OUT_PATH = Path(__file__).resolve().parent / "sample_jobs.csv"
N_LEGIT = 600
N_FRAUD = 400

LEGIT_TITLES = [
    "Software Engineer", "Data Analyst", "Product Manager", "UX Designer",
    "Marketing Coordinator", "Accountant", "Nurse", "Teacher",
    "HR Specialist", "DevOps Engineer", "QA Engineer", "Sales Executive",
    "Customer Success Manager", "Backend Developer", "Frontend Developer",
    "Machine Learning Engineer", "Technical Writer", "Graphic Designer",
    "Financial Analyst", "Operations Manager",
]
FRAUD_TITLES = [
    "Urgent – Work From Home Agent", "Easy Online Income!", "Immediate Hire – Data Entry",
    "Make $5000/Week – No Experience", "Secret Shopper Needed!!!",
    "Home-Based Customer Service Rep", "Crypto Trading Assistant",
    "Remote Payment Processor", "Package Handler (Reshipping)",
    "Survey Taker – Earn $$$", "Admin Assistant – Immediate Start",
    "Online Ad Evaluator – $100/day!", "Virtual Assistant – Start Today!",
    "Social Media Evaluator $$", "Hiring Now – Unlimited Earnings!",
    "Work From Home – No Interview", "Personal Assistant to CEO",
    "Financial Freedom Coach", "Bitcoin Investment Manager",
    "Commission Agent – High Earnings",
]
COMPANIES_LEGIT = [
    "Acme Inc.", "TechNova Ltd.", "HealthPlus Corp.", "GreenLeaf Partners",
    "BlueWave Systems", "Stellar Analytics", "ClearPath Inc.", "NovaBridge Corp.",
    "Vanguard Solutions", "Skyline Technologies",
]
COMPANIES_FRAUD = [
    "Global Innovations LLC", "", "TrustWork Group",
    "EarnMaxx", "TopDollar Inc.", "QuickHire LLC", "AlphaPayments",
    "HomeBiz Pro", "CashFlow Systems", "EliteCommission Corp.",
]
LEGIT_SNIPPETS = [
    "We are looking for a motivated {title} to join our growing team in {loc}.",
    "{company} is hiring a {title}. Minimum 3 years of experience required.",
    "As a {title} you will collaborate with cross-functional teams to deliver high-quality products.",
    "Requirements: bachelor's degree in a related field, strong {skill} skills.",
    "Competitive salary and comprehensive benefits package including 401(k) and health insurance.",
    "You will report to the VP of Engineering and lead a team of 5.",
    "Responsibilities include designing, developing, and maintaining scalable systems.",
    "We offer flexible work arrangements, PTO, and professional development stipends.",
]
FRAUD_SNIPPETS = [
    "No experience needed!!! Start earning from day one!",
    "Make money fast – earn $5000/week from home!!!",
    "GUARANTEED INCOME – ACT NOW before positions fill up!",
    "Send your resume via WhatsApp to +1-555-0199.",
    "Contact our hiring manager on Telegram @quickhire.",
    "We require a small registration fee of $49.99 to process your application.",
    "Training fee: $99 – fully refundable after first paycheck.",
    "Use your personal bank account to receive and forward payments.",
    "This is a limited time offer – APPLY NOW!",
    "Congratulations! You have been selected for this exclusive opportunity!",
    "Binary option trading assistant – earn commission on every trade!",
    "Click here to apply: http://j0bs-apply.xyz/start",
    "Visit http://amazn-careers.tk/apply to get started",
    "Work from home, be your own boss, achieve financial freedom!",
    "100% FREE to join – no investment required (processing fee applies).",
    "Earn $100 per day doing simple online surveys!!!",
    "URGENT HIRING – We need 50 people TODAY!",
    "Weekly salary paid via crypto – provide your Bitcoin wallet.",
    "Easy money – reshipping packages from our warehouse.",
    "Multi level marketing opportunity – build your downline!",
]
LOCATIONS = [
    "New York, NY", "San Francisco, CA", "Remote", "Chicago, IL",
    "Austin, TX", "Seattle, WA", "Boston, MA", "Denver, CO",
    "London, UK", "Toronto, Canada",
]
SKILLS = [
    "Python", "JavaScript", "SQL", "communication", "project management",
    "data analysis", "design", "leadership", "Excel", "Java",
]
LEGIT_SALARIES = [
    "$65,000 - $85,000/year", "$90,000 - $130,000 per year",
    "Competitive salary based on experience", "$45/hour",
    "$70K – $110K annually",
]
FRAUD_SALARIES = [
    "$5,000/week", "$800/day", "EARN $10,000 MONTHLY",
    "$200k+ guaranteed", "$3000 weekly from home",
    "Unlimited earning potential", "$100/day no cap",
]


def _random_legit() -> dict:
    title = random.choice(LEGIT_TITLES)
    company = random.choice(COMPANIES_LEGIT)
    loc = random.choice(LOCATIONS)
    skill = random.choice(SKILLS)
    paragraphs = random.sample(LEGIT_SNIPPETS, k=random.randint(2, 5))
    text = " ".join(p.format(title=title, company=company, loc=loc, skill=skill) for p in paragraphs)
    salary_info = random.choice(LEGIT_SALARIES) if random.random() < 0.7 else ""
    if salary_info:
        text += f" Salary: {salary_info}."
    return {"title": title, "company": company, "text": text, "label": 0}


def _random_fraud() -> dict:
    title = random.choice(FRAUD_TITLES)
    company = random.choice(COMPANIES_FRAUD) if random.random() < 0.6 else ""
    paragraphs = random.sample(FRAUD_SNIPPETS, k=random.randint(2, 6))
    text = " ".join(paragraphs)
    salary_info = random.choice(FRAUD_SALARIES) if random.random() < 0.8 else ""
    if salary_info:
        text += f" Salary: {salary_info}."
    return {"title": title, "company": company, "text": text, "label": 1}


def main() -> None:
    rows: list[dict] = []
    for _ in range(N_LEGIT):
        rows.append(_random_legit())
    for _ in range(N_FRAUD):
        rows.append(_random_fraud())
    random.shuffle(rows)
    with open(OUT_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "company", "text", "label"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Generated {len(rows)} rows → {OUT_PATH}")


if __name__ == "__main__":
    main()
