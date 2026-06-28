"""Fixture external content pack for curriculum CLI validation only — not runtime app content."""

CURRICULUM_TRACKS = [
    {
        "id": "fixture-thinking-basics",
        "name": "Fixture Thinking Basics",
        "domain": "thinking",
        "author": "LifeOS validation fixture",
        "collection": "External pack sample",
        "units": [
            {
                "id": "fixture-thinking-observe",
                "title": "Observe Before You Conclude",
                "subtitle": "Separate what happened from the story you tell about it.",
                "emoji": "👁️",
                "accent": "#d79d3f",
                "minutes": 10,
                "hero_article": "Observation",
                "prerequisites": [],
                "sections": [
                    {
                        "heading": "Page 1: Facts vs interpretations",
                        "body": (
                            "<p>A <b>fact</b> is what a camera would record; an <b>interpretation</b> "
                            "is the meaning you assign. Mixing them early makes debugging harder — in code "
                            "and in life.</p>"
                        ),
                        "image_article": None,
                    },
                    {
                        "heading": "Page 2: Write observations first",
                        "body": (
                            "<p>Before proposing a fix, list neutral observations: timestamps, error "
                            "messages, who was affected. Delay judgment until the list is complete.</p>"
                        ),
                        "image_article": None,
                    },
                    {
                        "heading": "Page 3: Check for missing data",
                        "body": (
                            "<p>Ask what you did not see. Absence of evidence is not evidence of absence "
                            "— but it should trigger more looking, not more certainty.</p>"
                        ),
                        "image_article": None,
                    },
                    {
                        "heading": "Page 4: One sentence per claim",
                        "body": (
                            "<p>Split compound stories into atomic claims. Each claim should be "
                            "testable on its own before you chain them into a narrative.</p>"
                        ),
                        "image_article": None,
                    },
                    {
                        "heading": "Page 5: Pause before the label",
                        "body": (
                            "<p>Labels like 'lazy', 'broken', or 'impossible' are interpretations. "
                            "Use them only after observations survive a second read.</p>"
                        ),
                        "image_article": None,
                    },
                ],
                "ideas": [
                    ("Observation", "A neutral record of what occurred without embedded judgment."),
                    ("Interpretation", "The meaning or explanation assigned to observations."),
                ],
                "thinking_questions": [
                    "What is one recent bug where you skipped straight to a fix without listing observations?",
                    "Which words in your last post-mortem were facts, and which were interpretations?",
                ],
                "practice_prompt": "Rewrite a recent incident note: facts only, then interpretations in a separate section.",
                "source": {
                    "label": "LifeOS fixture — observation drill",
                    "url": "https://example.com/lifeos/fixture/observe",
                },
                "did_you_know": "Fixture content for external-pack validation; not served by the app.",
                "next": "Next: infer carefully from incomplete evidence.",
            },
            {
                "id": "fixture-thinking-infer",
                "title": "Infer Carefully From Evidence",
                "subtitle": "Build conclusions as chains — each link should hold weight on its own.",
                "emoji": "🔗",
                "accent": "#b8860b",
                "minutes": 11,
                "hero_article": "Inference",
                "prerequisites": ["fixture-thinking-observe"],
                "sections": [
                    {
                        "heading": "Page 1: Inference is not proof",
                        "body": (
                            "<p>An <b>inference</b> is the best available conclusion given current "
                            "evidence. It can be overturned by new data — that is a feature, not a flaw.</p>"
                        ),
                        "image_article": None,
                    },
                    {
                        "heading": "Page 2: State confidence explicitly",
                        "body": (
                            "<p>Use language that matches evidence: 'likely', 'possible', 'ruled out'. "
                            "Hidden certainty breeds brittle decisions.</p>"
                        ),
                        "image_article": None,
                    },
                    {
                        "heading": "Page 3: Look for disconfirming evidence",
                        "body": (
                            "<p>Ask what observation would prove you wrong. If nothing would, you are "
                            "not inferring — you are asserting.</p>"
                        ),
                        "image_article": None,
                    },
                    {
                        "heading": "Page 4: Prefer simpler explanations",
                        "body": (
                            "<p>When two stories fit the facts, the one with fewer moving parts is a "
                            "better default — not because it is always true, but because it is cheaper to test.</p>"
                        ),
                        "image_article": None,
                    },
                    {
                        "heading": "Page 5: Update when data arrives",
                        "body": (
                            "<p>Good thinkers treat conclusions as provisional. New observations from "
                            "the prior unit should trigger revision, not defensiveness.</p>"
                        ),
                        "image_article": None,
                    },
                ],
                "ideas": [
                    ("Inference", "A conclusion supported by evidence but not directly observed."),
                    ("Confidence", "How strongly current evidence supports a claim."),
                ],
                "thinking_questions": [
                    "What single observation would most reduce your confidence in your top hypothesis?",
                    "Where did you last treat an inference as if it were a direct observation?",
                ],
                "practice_prompt": "Take one open question and write three competing inferences with explicit confidence levels.",
                "source": {
                    "label": "LifeOS fixture — inference drill",
                    "url": "https://example.com/lifeos/fixture/infer",
                },
                "did_you_know": "This unit depends on fixture-thinking-observe — tests prerequisite edges.",
                "next": "Fixture track complete.",
            },
        ],
    },
]
