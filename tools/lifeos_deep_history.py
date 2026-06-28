"""Curated long-form history lessons for the LifeOS learning feed."""
from __future__ import annotations

from typing import Any


DEEP_LESSONS: list[dict[str, Any]] = [
    {
        "id": "deep-socrates-athens",
        "emoji": "🏛️",
        "accent": "#b87935",
        "title": "Socrates and the City That Put Him on Trial",
        "subtitle": "How one irritating Athenian turned philosophy into a way of living, then died for it.",
        "minutes": 16,
        "hero_article": "Socrates",
        "track": "deep-history",
        "difficulty_level": "undergrad",
        "lead": (
            "Socrates did not write books, lead armies, found a school, or claim to have a doctrine. "
            "He walked around Athens asking people to explain themselves. That sounds harmless until "
            "you remember what Athens had just lived through: war, plague, civil terror, political "
            "collapse, and a humiliating defeat by Sparta. In that tense city, questions could feel "
            "like sabotage."
        ),
        "sections": [
            (
                "Page 1: Athens was brilliant, wounded, and suspicious",
                "<p>Classical Athens was not just a pretty marble postcard. It was a restless democracy "
                "where ordinary male citizens could debate, vote, serve on juries, and shape public life. "
                "The same city produced tragedy, comedy, architecture, naval power, and political argument "
                "at a level that still feels modern.</p><p>But by the late fifth century BCE, Athens had "
                "been crushed by the Peloponnesian War. The plague had killed thousands. The empire had "
                "collapsed. A pro-Spartan oligarchy called the Thirty Tyrants briefly seized power and "
                "murdered opponents. When democracy returned, the city was trying to rebuild trust. That "
                "background matters because Socrates was not judged in a calm classroom. He was judged by "
                "a traumatized political community looking for reasons its world had broken.</p>",
                "Classical Athens",
            ),
            (
                "Page 2: The Socratic method was not a quiz",
                "<p>Socrates became famous for elenchus, the method of testing a claim by asking for a "
                "definition, finding a contradiction, and forcing the speaker to refine or abandon the "
                "idea. If someone claimed courage was obvious, Socrates asked what courage was. If someone "
                "said justice meant helping friends and harming enemies, he pressed until the claim began "
                "to crack.</p><p>The point was not trivia. It was moral pressure. Socrates treated vague "
                "confidence as dangerous. He believed people should not run a city, raise children, chase "
                "money, or command armies while being unable to explain what goodness, justice, courage, "
                "or wisdom actually meant. His method turned public conversation into a stress test for "
                "the soul.</p>",
                "Socratic method",
            ),
            (
                "Page 3: Why young Athenians loved him and elders hated him",
                "<p>Young elite men followed Socrates because he made powerful people look foolish in "
                "public. That was thrilling if you were twenty and bored by respectable speeches. It was "
                "less thrilling if you were one of the generals, poets, craftsmen, and politicians being "
                "examined in front of an audience.</p><p>His social circle also hurt him. Alcibiades, one "
                "of Athens' most brilliant and destructive figures, had been close to Socrates and later "
                "betrayed Athens. Critias, a leader among the Thirty Tyrants, had also known him. Socrates "
                "was not responsible for their crimes, but politics rarely works by clean logic. To many "
                "citizens, he looked like the teacher of dangerous aristocratic men who despised democracy.</p>",
                "Alcibiades",
            ),
            (
                "Page 4: The trial was about religion, politics, and public trust",
                "<p>In 399 BCE Socrates was charged with impiety and corrupting the youth. Impiety did not "
                "mean private doubt in the modern sense. Athens tied religion to civic life: festivals, "
                "oaths, temples, sacrifices, and the favor of the gods were woven into the survival of the "
                "city. A man accused of introducing strange divine matters could be seen as attacking the "
                "shared order.</p><p>Plato's <i>Apology</i> presents Socrates as refusing to flatter the "
                "jury. Instead of begging, he argues that Athens should reward him for waking the city up. "
                "That might be morally brave, but it was legally terrible. A large jury convicted him, and "
                "after a second vote sentenced him to death. His defense was consistent with his life: he "
                "would rather lose than pretend to know what he did not know.</p>",
                "Trial of Socrates",
            ),
            (
                "Page 5: Hemlock turned a local case into a civilizational event",
                "<p>Socrates could probably have escaped. His friends had money and plans. In Plato's "
                "<i>Crito</i>, he refuses because he believes he has lived under Athenian law and cannot "
                "reject it only when it hurts him. Whether Plato idealized the scene or not, the image is "
                "powerful: a philosopher calmly drinks hemlock because integrity matters more than survival.</p>"
                "<p>The death of Socrates created a wound in Western thought. It raised a question that "
                "never went away: what should a society do with people who expose its contradictions? Kill "
                "the critic, ignore him, absorb him, or let him transform the culture? Plato spent the rest "
                "of his life answering that question.</p>",
                "The Death of Socrates",
            ),
            (
                "Page 6: The real lesson is intellectual courage",
                "<p>Socrates matters because he made philosophy personal. He did not treat wisdom as "
                "information stored in the head. He treated it as a way of living under examination. To "
                "learn from him is not to memorize his biography. It is to notice where you are confident "
                "without understanding.</p><p>That is why he belongs in a LifeOS learning graph. Every "
                "serious subject eventually asks for the same Socratic move: define the thing, test the "
                "definition, find the contradiction, and improve your model. That works in ethics, startups, "
                "science, politics, and self-management.</p>",
                None,
            ),
        ],
        "ideas": [
            ("Elenchus", "Socrates' cross-examination method: define, test, expose contradiction, refine."),
            ("Athenian democracy", "A direct citizen democracy that was creative, intense, and politically fragile."),
            ("Impiety", "A civic-religious charge, not merely private disbelief."),
            ("Examined life", "The claim that living well requires testing your beliefs and motives."),
        ],
        "game": {
            "type": "order",
            "prompt": "Rebuild the pressure chain that led from Athenian glory to Socrates' death.",
            "items": [
                ("s1", "Athens becomes a democratic and cultural power"),
                ("s2", "War, plague, defeat, and oligarchic terror damage civic trust"),
                ("s3", "Socrates publicly tests respected people and attracts elite youth"),
                ("s4", "He is charged with impiety and corrupting the youth"),
                ("s5", "He refuses to flatter the jury and accepts death by hemlock"),
            ],
            "explain": (
                "The trial makes more sense when you see the chain: a brilliant democracy becomes wounded, "
                "then a public critic starts looking less like a teacher and more like a threat."
            ),
        },
        "did_you_know": (
            "The famous phrase about the unexamined life comes from Plato's account of the trial, not from "
            "a book Socrates wrote. Socrates left no writings of his own."
        ),
        "source": ("Internet Encyclopedia of Philosophy - Socrates", "https://iep.utm.edu/socrates/"),
        "sources": [
            {"title": "Internet Encyclopedia of Philosophy - Socrates", "url": "https://iep.utm.edu/socrates/", "note": "Biography, method, trial, and philosophical context."},
            {"title": "Stanford Encyclopedia of Philosophy - Socrates", "url": "https://plato.stanford.edu/entries/socrates/", "note": "Source-critical overview of Socrates and the Socratic problem."},
            {"title": "Plato, Apology - Internet Classics Archive", "url": "https://classics.mit.edu/Plato/apology.html", "note": "Primary-source account of Socrates' defense, via Plato."},
        ],
        "next": "Next: Plato turns the shock of Socrates' death into a school, a theory of reality, and a political dream.",
    },
    {
        "id": "deep-plato-academy",
        "emoji": "📜",
        "accent": "#5d6fc9",
        "title": "Plato: The Student Who Built a School for Reality",
        "subtitle": "From Socrates' death to the Academy, the cave, the Forms, and the dream of philosopher-rulers.",
        "minutes": 17,
        "hero_article": "Plato",
        "track": "deep-history",
        "difficulty_level": "undergrad",
        "lead": (
            "Plato is what happens when a brilliant student watches his teacher get executed by a democracy. "
            "He never stopped asking the basic question: if public opinion can kill the wisest man in the "
            "city, what kind of knowledge should rule human life?"
        ),
        "sections": [
            (
                "Page 1: Plato inherited a trauma",
                "<p>Plato was born into an aristocratic Athenian family around 428 BCE. He saw the "
                "Peloponnesian War, the collapse of Athens, the violence of the Thirty Tyrants, and the "
                "restoration of democracy. Then he saw Socrates condemned in 399 BCE. Those events gave his "
                "philosophy its emotional engine.</p><p>Plato did not simply ask abstract questions. He "
                "asked why cities are so easily ruled by appetite, fear, ambition, and appearance. He wanted "
                "a kind of knowledge stronger than rhetoric. If Socrates showed that most people do not know "
                "what they think they know, Plato asked what real knowing would have to be.</p>",
                "Peloponnesian War",
            ),
            (
                "Page 2: Dialogues are thinking machines",
                "<p>Plato wrote dialogues rather than textbooks. That matters. A dialogue lets an idea move, "
                "fail, recover, and collide with another mind. Socrates usually appears as the central "
                "questioner, but the reader has to do work. You are not handed a finished doctrine as much "
                "as placed inside a live argument.</p><p>This format also protects Plato from easy summary. "
                "Sometimes Socrates refutes others without giving a final answer. Sometimes myths appear "
                "where proof runs out. Sometimes the conversation ends in aporia, a productive state of "
                "puzzlement. Plato's writing trains the reader to experience philosophy as disciplined "
                "confusion becoming clearer.</p>",
                "Platonic dialogue",
            ),
            (
                "Page 3: The Forms are Plato's answer to change",
                "<p>The world you see is unstable. Beautiful bodies age, just actions are disputed, and "
                "triangles drawn in sand are imperfect. Yet you still understand beauty, justice, and "
                "triangularity. Plato's theory of Forms says that the visible world participates in deeper, "
                "intelligible realities that are more stable than physical things.</p><p>You do not need to "
                "accept the theory literally to feel its force. Plato is asking why knowledge seems to reach "
                "beyond sensory examples. Mathematics is the cleanest case: no one has seen a perfect circle, "
                "but the mind can reason about one. For Plato, philosophy is the ascent from shifting "
                "appearances toward what is real, ordered, and knowable.</p>",
                "Theory of forms",
            ),
            (
                "Page 4: The cave is about education, not just illusion",
                "<p>In the allegory of the cave, prisoners mistake shadows for reality because shadows are "
                "all they have ever seen. One prisoner is freed, painfully adjusts to the light, sees the "
                "world outside, and eventually sees the sun. When he returns, the others think he is ruined "
                "or insane.</p><p>The usual cheap reading is that the cave means people are fooled by fake "
                "images. The stronger reading is about education. Real learning is not comfortable content "
                "delivery. It turns the whole soul around. It also creates a social problem: the person who "
                "has seen more clearly may become harder for the group to understand.</p>",
                "Allegory of the cave",
            ),
            (
                "Page 5: The Republic is a psychology disguised as politics",
                "<p><i>The Republic</i> asks what justice is by imagining a city. But the city is also a "
                "magnified soul. Plato divides the soul into reason, spirit, and appetite. A just person is "
                "one whose rational part governs, whose spirited part supports what is noble, and whose "
                "appetites do not seize the throne.</p><p>This is why the philosopher-ruler appears. Plato "
                "does not merely want smart politicians. He wants rulers whose desires have been trained by "
                "mathematics, dialectic, discipline, and exposure to the Good. The proposal is dangerous and "
                "elitist, but the diagnosis is hard to dismiss: cities decay when the worst part of human "
                "nature becomes politically dominant.</p>",
                "Republic (Plato)",
            ),
            (
                "Page 6: The Academy made philosophy institutional",
                "<p>Plato founded the Academy in Athens, often described as one of the earliest long-running "
                "institutions of higher learning in the Greek world. It was not a modern university, but it "
                "created a durable space for mathematics, metaphysics, ethics, and political inquiry.</p>"
                "<p>Aristotle studied there for about twenty years before founding his own school. That one "
                "connection alone makes the Academy one of the most consequential intellectual institutions "
                "ever built. Socrates made philosophy a life. Plato made it a tradition that could outlive "
                "the original questioner.</p>",
                "Platonic Academy",
            ),
        ],
        "ideas": [
            ("Dialogue", "A philosophical form that makes the reader participate in the argument."),
            ("Forms", "Stable intelligible realities that explain knowledge beyond changing examples."),
            ("Allegory of the cave", "A model of education as painful reorientation toward reality."),
            ("Academy", "Plato's institution for sustained philosophical and mathematical inquiry."),
        ],
        "game": {
            "type": "ponder",
            "prompt": (
                "You are designing a city after watching Socrates die. Do you trust majority opinion, "
                "expert rule, written law, or philosophical education most? Pick one and argue the tradeoff."
            ),
            "reveal": (
                "Plato's answer leans toward philosophical education and expert rule, but the tension never "
                "goes away. Majority rule can be ignorant; expert rule can become tyranny; written law can "
                "be rigid; education is slow. The hard move is seeing why no option is clean."
            ),
        },
        "did_you_know": (
            "The Academy lasted in different forms for centuries. Plato's biggest invention may not be one "
            "argument, but the idea that serious thinking needs an institution around it."
        ),
        "source": ("Stanford Encyclopedia of Philosophy - Plato", "https://plato.stanford.edu/entries/plato/"),
        "sources": [
            {"title": "Stanford Encyclopedia of Philosophy - Plato", "url": "https://plato.stanford.edu/entries/plato/", "note": "Core philosophical and biographical reference."},
            {"title": "Internet Encyclopedia of Philosophy - Plato", "url": "https://iep.utm.edu/plato/", "note": "Accessible overview of Plato's life, dialogues, Forms, and politics."},
            {"title": "Plato, Republic - Internet Classics Archive", "url": "https://classics.mit.edu/Plato/republic.html", "note": "Primary text for the cave, justice, and philosopher-rule themes."},
        ],
        "next": "Next: Alexandria tries to scale the Academy's dream into a world-memory project.",
    },
    {
        "id": "deep-library-alexandria",
        "emoji": "🔥",
        "accent": "#c4533d",
        "title": "The Library of Alexandria: How a World-Memory Disappeared",
        "subtitle": "The famous burning was not one simple fire. It was a long institutional death.",
        "minutes": 18,
        "hero_article": "Library of Alexandria",
        "track": "deep-history",
        "difficulty_level": "undergrad",
        "lead": (
            "The Library of Alexandria is usually told as a tragedy about one fire destroying ancient wisdom. "
            "That version is dramatic, but too simple. The better story is about how knowledge institutions "
            "are built, funded, politicized, neglected, damaged, mythologized, and slowly lost."
        ),
        "sections": [
            (
                "Page 1: Alexandria was a planned capital of knowledge",
                "<p>After Alexander the Great's conquests, Egypt came under the Ptolemies, a Macedonian Greek "
                "dynasty. Their capital, Alexandria, was designed to be a Mediterranean powerhouse: port, "
                "palace city, royal display, trade hub, and intellectual magnet. The famous lighthouse showed "
                "ships where to land. The library and Mouseion showed scholars where to think.</p><p>The "
                "Mouseion was not just a room full of scrolls. It was a research community supported by royal "
                "money. Scholars received food, status, and time. That matters because knowledge at scale is "
                "not just genius. It is infrastructure: salaries, copying, cataloging, buildings, politics, "
                "and a culture that thinks preserving texts is worth the cost.</p>",
                "Alexandria",
            ),
            (
                "Page 2: The library tried to collect the world",
                "<p>The Ptolemies wanted prestige through collection. Ancient sources describe aggressive "
                "book gathering: buying manuscripts, copying texts from ships, and competing with other "
                "centers of learning. The goal was not a casual bookshelf. It was a universal library, a "
                "claim that Alexandria could gather Greek literature, science, medicine, mathematics, "
                "geography, and foreign knowledge under one royal roof.</p><p>Scroll culture made this hard. "
                "Texts had to be copied by hand. Titles varied. Authors were disputed. A damaged scroll could "
                "erase a work. Cataloging became an intellectual achievement in itself. The library was a "
                "machine for turning fragile manuscripts into organized memory.</p>",
                "Callimachus",
            ),
            (
                "Page 3: What scholars actually did there",
                "<p>Alexandrian scholarship was not passive storage. Euclid is associated with Alexandria's "
                "mathematical world. Eratosthenes estimated Earth's circumference with impressive accuracy. "
                "Aristarchus proposed a heliocentric model. Editors compared versions of Homer and tried to "
                "produce reliable texts. Grammarians, physicians, astronomers, mathematicians, and poets all "
                "worked in a culture of criticism and comparison.</p><p>This is why the library matters. It "
                "represents a shift from wisdom as scattered tradition to knowledge as an organized project. "
                "You can see a line from the Academy to Alexandria: create a place where inquiry has memory, "
                "standards, and continuity.</p>",
                "Eratosthenes",
            ),
            (
                "Page 4: Julius Caesar's fire damaged something, but not everything",
                "<p>During Caesar's Alexandrian War in 48 BCE, fires connected to the harbor fighting likely "
                "destroyed ships, warehouses, and some books. Ancient reports differ on what burned and how "
                "many scrolls were lost. The tempting story says the whole library vanished in one night. The "
                "evidence is messier.</p><p>The key lesson is uncertainty. Some collections were likely "
                "damaged. But Alexandria's scholarly life did not instantly end. Later writers still refer "
                "to learning in the city. So Caesar's fire was probably one major wound in a longer decline, "
                "not the clean single cause of disappearance.</p>",
                "Alexandrian War",
            ),
            (
                "Page 5: Institutions die when funding, politics, and culture change",
                "<p>Over centuries, the Ptolemaic royal system fell under Roman control. Civil wars, changing "
                "patronage, religious conflict, economic pressure, and political instability all weakened "
                "the conditions that had sustained the library. A research institution needs more than books. "
                "It needs a protected ecosystem.</p><p>The Serapeum, a temple complex that may have housed a "
                "daughter collection, was destroyed in 391 CE amid Christian-pagan conflict under Theophilus. "
                "That event is often folded into the library myth. Later stories blamed Muslim conquerors in "
                "the seventh century, but many historians treat that account with skepticism. The honest "
                "answer is not one villain. It is cumulative institutional failure.</p>",
                "Serapeum of Alexandria",
            ),
            (
                "Page 6: The myth survives because the fear is real",
                "<p>People love the burning-library story because it gives a clean image to a real fear: "
                "civilization can forget. A text can vanish because no one copies it. A discipline can decay "
                "because patrons stop paying. A society can lose technical knowledge because institutions "
                "break faster than students can be trained.</p><p>That is why Alexandria belongs in a "
                "personal knowledge graph. It is not only ancient history. It is a warning about your own "
                "learning system. Notes, books, agents, images, games, and review loops are not decorative. "
                "They are how fragile ideas become durable.</p>",
                None,
            ),
        ],
        "ideas": [
            ("Mouseion", "A royal research community attached to the library, not just a storage room."),
            ("Universal library", "The ambition to collect, copy, organize, and compare the known textual world."),
            ("Caesar's fire", "A damaging event in 48 BCE, but probably not the single total destruction."),
            ("Institutional decline", "The slower loss of funding, protection, continuity, and cultural priority."),
        ],
        "game": {
            "type": "order",
            "prompt": "Put the Library of Alexandria story in the less-mythical order.",
            "items": [
                ("a1", "Ptolemaic rulers build Alexandria as a prestige capital"),
                ("a2", "The Mouseion and library attract scholars and collect scrolls"),
                ("a3", "Caesar's Alexandrian War causes fire damage near the harbor"),
                ("a4", "Roman rule and later conflicts weaken old scholarly institutions"),
                ("a5", "The Serapeum is destroyed amid late antique religious conflict"),
                ("a6", "Later generations compress centuries of loss into one burning-library myth"),
            ],
            "explain": (
                "The key correction is that Alexandria was not simply one fire. It was a knowledge system "
                "that suffered damage, lost patronage, and became a myth after its world changed."
            ),
        },
        "did_you_know": (
            "Eratosthenes estimated Earth's circumference using shadows in Alexandria and Syene. The library "
            "was not just preserving old books; it was producing new models of the world."
        ),
        "source": ("World History Encyclopedia - Library of Alexandria", "https://www.worldhistory.org/Library_of_Alexandria/"),
        "sources": [
            {"title": "World History Encyclopedia - Library of Alexandria", "url": "https://www.worldhistory.org/Library_of_Alexandria/", "note": "Overview of the library, Mouseion, collection aims, and destruction debates."},
            {"title": "World History Encyclopedia - Library of Alexandria", "url": "https://www.worldhistory.org/Library_of_Alexandria/", "note": "Readable historical account of Alexandria's library, scholars, and later decline."},
            {"title": "World History Encyclopedia - The Destruction of the Great Library of Alexandria", "url": "https://www.worldhistory.org/article/207/what-happened-to-the-great-library-at-alexandria/", "note": "Focused discussion of the competing destruction narratives and uncertainty."},
        ],
        "next": "Next: compare Alexandria with modern knowledge systems like universities, Wikipedia, Obsidian, and LifeOS.",
    },
]


DEEP_GRAPH: dict[str, Any] = {
    "domains": [
        {"id": "history", "name": "History", "color": "#c4892d"},
        {"id": "thinking", "name": "Thinking", "color": "#1f9d78"},
        {"id": "culture", "name": "Culture", "color": "#d86b8a"},
    ],
    "nodes": [
        {
            "id": "deep-socrates-athens",
            "domain": "history",
            "title": "Socrates and Athens",
            "kind": "article",
            "xp": 150,
            "url": "/output/learn/deep-socrates-athens.html",
            "summary": "Why wounded democratic Athens put Socrates on trial.",
            "x": 20,
            "y": 58,
        },
        {
            "id": "deep-plato-academy",
            "domain": "thinking",
            "title": "Plato and the Academy",
            "kind": "article",
            "xp": 160,
            "url": "/output/learn/deep-plato-academy.html",
            "summary": "Forms, the cave, the Republic, and philosophy as an institution.",
            "x": 32,
            "y": 70,
        },
        {
            "id": "deep-library-alexandria",
            "domain": "culture",
            "title": "Library of Alexandria",
            "kind": "article",
            "xp": 170,
            "url": "/output/learn/deep-library-alexandria.html",
            "summary": "How a world-memory project was built, damaged, and mythologized.",
            "x": 45,
            "y": 58,
        },
    ],
    "edges": [
        {"from": "story-of-civilization", "to": "deep-socrates-athens", "relation": "prerequisite"},
        {"from": "deep-socrates-athens", "to": "deep-plato-academy", "relation": "prerequisite"},
        {"from": "deep-plato-academy", "to": "deep-library-alexandria", "relation": "application"},
        {"from": "story-of-civilization", "to": "deep-library-alexandria", "relation": "application"},
    ],
}
