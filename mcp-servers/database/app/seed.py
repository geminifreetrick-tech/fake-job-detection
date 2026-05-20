"""Seed awareness module content (articles + quizzes) on first startup."""
from __future__ import annotations

import logging

from sqlalchemy import select

from .db import SessionLocal
from .models import Article, Quiz

logger = logging.getLogger("db-mcp.seed")


_ARTICLES: list[dict] = [
    {
        "slug": "spotting-fake-job-postings",
        "title": "How to spot a fake job posting in 60 seconds",
        "summary": (
            "Five red flags that should make you walk away from any job advert — "
            "unrealistic pay, payment requests, off-platform contact, and more."
        ),
        "tags": ["basics", "red-flags"],
        "body_md": (
            "# How to spot a fake job posting in 60 seconds\n\n"
            "Job scammers follow a small set of recognizable patterns. Train your eye on these "
            "and you can dismiss most fraudulent postings before you finish reading.\n\n"
            "## 1. Pay that's wildly above market\n"
            "If a no-experience-required role pays $5,000/week, it's almost certainly not real. "
            "Salaries above 2× the market rate for the seniority should be treated as a strong "
            "warning sign — especially when paired with vague responsibilities.\n\n"
            "## 2. They ask you to pay them\n"
            "Legitimate employers never charge for training, equipment, a background check, "
            "or 'registration'. Any request for money — even 'refundable' fees — is a scam.\n\n"
            "## 3. The conversation moves to Telegram / WhatsApp\n"
            "Real recruiters use corporate email. If the very first message redirects you to a "
            "personal messaging app, it's a strong indicator the company doesn't want a paper trail.\n\n"
            "## 4. The job description is grammatically poor or full of CAPS\n"
            "Combined with urgency cues ('HIRE NOW!!!'), poor English suggests a copy-pasted scam "
            "template rather than a real listing reviewed by a hiring team.\n\n"
            "## 5. The domain doesn't quite match the brand\n"
            "Lookalike domains — `amazn-careers.xyz`, `microsoft-hiring.top` — are designed to "
            "trick you. Always verify the official careers page yourself before sending any data.\n\n"
            "> If two or more of these red flags are present, walk away.\n"
        ),
    },
    {
        "slug": "money-mule-jobs-explained",
        "title": "Money mule jobs: how 'easy remote work' becomes a crime",
        "summary": (
            "Reshipping, payment forwarding, and crypto 'assistant' roles are nearly always "
            "money-laundering schemes that put you at legal risk."
        ),
        "tags": ["money-mule", "high-risk"],
        "body_md": (
            "# Money mule jobs: how 'easy remote work' becomes a crime\n\n"
            "A money mule is someone who moves illicit funds on behalf of criminals — usually "
            "without realizing it. Job postings that recruit mules are dressed up as legitimate "
            "remote work, but they all share the same structure:\n\n"
            "- **Receive money or packages** at your home or via your personal bank account.\n"
            "- **Forward them** to a third party (often overseas) after taking a small cut.\n"
            "- **Use your real identity** so the criminals stay anonymous.\n\n"
            "## Typical job titles\n"
            "- 'Payment processor / financial assistant'\n"
            "- 'Package re-shipping agent'\n"
            "- 'Cryptocurrency trading assistant'\n"
            "- 'Personal logistics coordinator'\n\n"
            "## Why it's a problem for you\n"
            "Even if you had no idea, courts in most countries can convict you of money "
            "laundering or wire fraud. Your bank account is frozen, your credit is destroyed, "
            "and you may face prison time.\n\n"
            "## What real remote work looks like\n"
            "Real remote roles never ask you to receive funds in your personal account or "
            "re-ship packages. They give you a payroll-managed paycheck, a corporate device, "
            "and a normal onboarding process.\n"
        ),
    },
    {
        "slug": "what-to-do-after-falling-for-a-scam",
        "title": "What to do if you already shared info with a fake recruiter",
        "summary": (
            "A quick triage checklist: revoke access, freeze accounts, file reports, and "
            "monitor for identity theft."
        ),
        "tags": ["recovery", "victims"],
        "body_md": (
            "# What to do if you already shared info with a fake recruiter\n\n"
            "Acting in the first 24 hours dramatically reduces the damage from a job-recruitment "
            "scam. Run through this list in order:\n\n"
            "## 1. Stop all further contact\n"
            "Don't try to confront the scammer or 'get your money back' — it almost always makes "
            "things worse. Block, mute, and move on.\n\n"
            "## 2. Change passwords and enable 2FA everywhere\n"
            "Especially on email, bank, and any account where you reused the password you "
            "shared with the scammer.\n\n"
            "## 3. Contact your bank\n"
            "If you sent money or shared bank details, call the bank's fraud line (the number "
            "on the back of your card). They can reverse charges, freeze accounts, and reissue "
            "a card.\n\n"
            "## 4. File reports\n"
            "- In the US: report to the FBI's IC3 (ic3.gov) and the FTC (reportfraud.ftc.gov).\n"
            "- In the UK: Action Fraud (actionfraud.police.uk).\n"
            "- In the EU: your national consumer protection authority.\n\n"
            "## 5. Monitor for identity theft\n"
            "Freeze your credit at all three major bureaus. Set up free credit monitoring. "
            "Watch for unexpected accounts or hard inquiries for the next 12 months.\n"
        ),
    },
]


_QUIZZES: list[dict] = [
    {
        "slug": "intro-fake-job-detection",
        "title": "Intro: Can you spot a fake job?",
        "description": (
            "Five quick scenarios. Pick the option that best describes the red flag — "
            "and we'll explain why."
        ),
        "questions": [
            {
                "id": "q1",
                "prompt": (
                    "A job ad promises $5,000/week for entry-level remote data entry, "
                    "no experience required. What's the biggest red flag?"
                ),
                "choices": [
                    "The salary is wildly above market for the role",
                    "Data entry is a boring job",
                    "Remote work is suspicious",
                    "No experience required",
                ],
                "correct_index": 0,
                "explanation": (
                    "Pay that's far above market for the seniority is one of the strongest "
                    "indicators of fraud — real employers don't overpay by 5–10×."
                ),
            },
            {
                "id": "q2",
                "prompt": (
                    "After applying, the recruiter says you must pay $99 for a "
                    "'refundable training kit'. What should you do?"
                ),
                "choices": [
                    "Pay quickly so you don't lose the job",
                    "Negotiate the fee down",
                    "Refuse — legitimate employers never charge applicants",
                    "Ask for a payment plan",
                ],
                "correct_index": 2,
                "explanation": (
                    "Any request for money — even framed as 'refundable' — is a scam. "
                    "Real employers pay you, never the other way round."
                ),
            },
            {
                "id": "q3",
                "prompt": (
                    "The recruiter immediately moves the conversation to Telegram and "
                    "uses a Gmail address. What does that tell you?"
                ),
                "choices": [
                    "They're a forward-thinking modern company",
                    "It's normal for tech companies",
                    "They want to avoid a paper trail — likely a scam",
                    "Telegram is more secure than email",
                ],
                "correct_index": 2,
                "explanation": (
                    "Real recruiters use corporate email and platforms that keep audit logs. "
                    "Personal messaging apps and free email domains are a strong scam signal."
                ),
            },
            {
                "id": "q4",
                "prompt": (
                    "You're asked to receive packages at home and forward them overseas "
                    "for a flat $200/package. This is:"
                ),
                "choices": [
                    "A legitimate logistics job",
                    "A reshipping scam / money-mule recruitment",
                    "An entry-level supply chain role",
                    "A normal warehouse position",
                ],
                "correct_index": 1,
                "explanation": (
                    "Receiving and forwarding packages is a classic reshipping scam, which "
                    "is illegal in most jurisdictions even if you didn't know."
                ),
            },
            {
                "id": "q5",
                "prompt": (
                    "The apply link is `amazn-careers.xyz/apply`. What's wrong?"
                ),
                "choices": [
                    "Nothing — `.xyz` is fine",
                    "It's a lookalike domain impersonating Amazon",
                    "Amazon doesn't have a careers page",
                    "The site is too slow",
                ],
                "correct_index": 1,
                "explanation": (
                    "Lookalike domains drop characters or use unusual TLDs to impersonate a "
                    "real brand. Always navigate to the company's official careers site yourself."
                ),
            },
        ],
    },
]


async def seed_all() -> None:
    async with SessionLocal() as session:
        for a in _ARTICLES:
            res = await session.execute(select(Article).where(Article.slug == a["slug"]))
            if res.scalar_one_or_none() is None:
                session.add(Article(**a))
        for q in _QUIZZES:
            res = await session.execute(select(Quiz).where(Quiz.slug == q["slug"]))
            if res.scalar_one_or_none() is None:
                session.add(Quiz(**q))
        await session.commit()
    logger.info("seeded %d articles, %d quizzes", len(_ARTICLES), len(_QUIZZES))
