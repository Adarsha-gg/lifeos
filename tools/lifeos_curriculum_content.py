#!/usr/bin/env python3
"""Structured LifeOS mastery curriculum content.

This module is intentionally data-first. Renderers or schedulers can import
``CURRICULUM_TRACKS`` and treat each unit as a graph node:

    track["units"][i]["id"]                 stable node id
    track["units"][i]["prerequisites"]      prerequisite unit ids
    track["units"][i]["sections"]           lesson pages/sections
    track["units"][i]["thinking_questions"] retrieval and transfer prompts
    track["units"][i]["application_prompt"] daily practice/application task

The maps are original standard curricula, not copied from Math Academy,
Physics Academy, or any proprietary source. They use public learning-system
principles: granular prerequisite graphs, mastery ordering, daily lessons,
retrieval practice, spaced review, and interleaving.
"""
from __future__ import annotations

import json
import os
import ast
import html as html_lib
from pathlib import Path
from typing import Any

try:
    from lifeos_paths import VAULT_ROOT as LIFEOS_VAULT_ROOT
except Exception:
    LIFEOS_VAULT_ROOT = None


Source = dict[str, str]
Section = dict[str, str]
Unit = dict[str, Any]

APP_ROOT = Path(__file__).resolve().parents[1]
VAULT_ROOT = Path(
    os.environ.get(
        "LIFEOS_VAULT",
        str(LIFEOS_VAULT_ROOT) if LIFEOS_VAULT_ROOT is not None else str(APP_ROOT / ".tmp-lifeos-vault"),
    )
).expanduser()
PG_JSON = VAULT_ROOT / "output" / "learn" / "paul-graham-essays.json"
PG_REFRESH_SCRIPT = Path(__file__).resolve().with_name("lifeos_paul_graham.py")

PG_INDEX_SOURCE: Source = {
    "title": "Paul Graham Essays",
    "url": "https://www.paulgraham.com/articles.html",
}


OPEN_MATH_SOURCES: list[Source] = [
    {"title": "OpenStax Algebra and Trigonometry", "url": "https://openstax.org/details/books/algebra-and-trigonometry"},
    {"title": "OpenStax Calculus", "url": "https://openstax.org/details/books/calculus-volume-1"},
    {"title": "MIT OpenCourseWare Mathematics", "url": "https://ocw.mit.edu/search/?d=Mathematics"},
]

OPEN_PHYSICS_SOURCES: list[Source] = [
    {"title": "OpenStax University Physics", "url": "https://openstax.org/details/books/university-physics-volume-1"},
    {"title": "Physics LibreTexts University Physics", "url": "https://phys.libretexts.org/Bookshelves/University_Physics"},
    {"title": "MIT OpenCourseWare Physics", "url": "https://ocw.mit.edu/search/?d=Physics"},
]

OPEN_HISTORY_SOURCES: list[Source] = [
    {"title": "World History Encyclopedia", "url": "https://www.worldhistory.org/"},
    {"title": "OpenStax World History", "url": "https://openstax.org/details/books/world-history-volume-1"},
    {"title": "Internet History Sourcebooks", "url": "https://sourcebooks.fordham.edu/"},
]


def slug(text: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in text.lower()).strip("-").replace("--", "-")


def section(title: str, body: str) -> Section:
    return {"title": title, "body": body}


def primary_source(sources: list[Source], order: int = 1) -> Source:
    if not sources:
        return {"label": "LifeOS original curriculum", "url": "https://lifeos.local/curriculum"}
    raw = sources[(order - 1) % len(sources)]
    label = raw.get("label") or raw.get("title") or "Open learning source"
    return {"label": label, "url": raw["url"]}


def ensure_five_sections(sections: list[Section], title: str, focus: str) -> list[Section]:
    out = list(sections)
    additions = [
        section("Prerequisite check", f"Before studying {title}, restate the prerequisite ideas and identify which one controls the first step."),
        section("Transfer test", f"Apply {title} to a new situation where {focus} appears in a disguised form, then explain why the method still fits."),
        section("Error audit", f"List two mistakes a learner would make with {title}, then write the cue that would catch each mistake early."),
        section("Mastery review", f"Close the unit by recalling the main idea, solving one cold example, and linking {title} back to an older unit."),
    ]
    for extra in additions:
        if len(out) >= 5:
            break
        out.append(extra)
    return out


def compact_unit(
    track_id: str,
    title: str,
    order: int,
    level: str,
    prerequisites: list[str],
    sources: list[Source],
    focus: str,
) -> Unit:
    unit_id = f"{track_id}-{slug(title)}"
    return {
        "id": unit_id,
        "title": title,
        "subtitle": f"{level}: {focus}",
        "summary": f"Build usable mastery of {title} by turning {focus} into definitions, examples, transfer checks, and review prompts.",
        "kind": "compact",
        "level": level,
        "order": order,
        "minutes": 18,
        "prerequisites": prerequisites,
        "source": primary_source(sources, order),
        "objectives": [
            f"State the central idea of {title} without looking it up.",
            f"Solve or explain one fresh example involving {focus}.",
            "Name the most common error pattern and how to catch it.",
        ],
        "sections": [
            section("Core move", f"Learn the one move that makes {title} useful: translate the situation into {focus}, then check the result against common sense."),
            section("Worked contrast", f"Compare a clean example with a near-miss. The goal is not pattern matching; it is knowing which assumption lets the method apply."),
            section("Representation switch", f"Express {focus} in at least two forms: words, symbols, diagrams, tables, timelines, or physical intuition depending on the domain."),
            section("Failure mode", f"Name the assumption that would make {title} fail, and use it as a quick test before applying a memorized method."),
            section("Review hook", "Schedule a short retrieval pass tomorrow, then mix this idea with two older units so fluency survives context changes."),
        ],
        "thinking_questions": [
            f"What would make {title} the wrong tool for a problem?",
            f"Invent a small example where {focus} is visible but not obvious.",
            "How would you teach the idea using a drawing, table, or physical analogy?",
        ],
        "application_prompt": f"Spend ten minutes creating one original problem about {focus}, solve it, then write the fastest way to detect a wrong answer.",
        "review_prompts": [
            "Recall the definition or law from memory.",
            "Solve one tiny example cold.",
            "Explain how this unit depends on its prerequisites.",
        ],
        "sources": sources,
    }


def substantial_unit(
    track_id: str,
    title: str,
    order: int,
    level: str,
    prerequisites: list[str],
    sources: list[Source],
    sections: list[Section],
    thinking_questions: list[str],
    application_prompt: str,
    objectives: list[str],
) -> Unit:
    return {
        "id": f"{track_id}-{slug(title)}",
        "title": title,
        "subtitle": f"{level} substantial unit",
        "summary": objectives[0] if objectives else f"Develop durable understanding of {title} through explanation, examples, transfer, and review.",
        "kind": "substantial",
        "level": level,
        "order": order,
        "minutes": 45,
        "prerequisites": prerequisites,
        "source": primary_source(sources, order),
        "objectives": objectives,
        "sections": ensure_five_sections(sections, title, level),
        "thinking_questions": thinking_questions,
        "application_prompt": application_prompt,
        "review_prompts": [
            "One-day recall: rewrite the map from memory.",
            "Three-day transfer: solve a problem with numbers or names changed.",
            "Seven-day interleave: mix this with a non-adjacent unit and explain which tool applies.",
        ],
        "sources": sources,
    }


def previous_id(track_id: str, title: str) -> str:
    return f"{track_id}-{slug(title)}"


MATH_TOPICS: list[tuple[str, str, str]] = [
    ("Whole Numbers and Place Value", "arithmetic", "base-ten quantity"),
    ("Mental Arithmetic and Estimation", "arithmetic", "bounds and approximate size"),
    ("Factors, Multiples, and Divisibility", "arithmetic", "multiplicative structure"),
    ("Fractions as Numbers", "arithmetic", "part-whole and number-line reasoning"),
    ("Decimal and Percent Reasoning", "arithmetic", "equivalent representations"),
    ("Ratios, Rates, and Proportions", "prealgebra", "multiplicative comparison"),
    ("Negative Numbers and Absolute Value", "prealgebra", "signed distance"),
    ("Exponents and Scientific Notation", "prealgebra", "repeated scaling"),
    ("Variables and Expressions", "prealgebra", "symbolic placeholders"),
    ("Linear Equations", "algebra", "balancing operations"),
    ("Inequalities and Intervals", "algebra", "solution sets"),
    ("Coordinate Plane and Slope", "algebra", "change over change"),
    ("Systems of Linear Equations", "algebra", "simultaneous constraints"),
    ("Polynomials and Factoring", "algebra", "algebraic structure"),
    ("Quadratic Equations", "algebra", "second-degree change"),
    ("Functions as Machines", "functions", "input-output rules"),
    ("Function Transformations", "functions", "shifts, stretches, and symmetry"),
    ("Exponential and Logarithmic Functions", "functions", "inverse growth scales"),
    ("Sequences and Series", "functions", "ordered accumulation"),
    ("Euclidean Geometry Foundations", "geometry", "definitions and proof from axioms"),
    ("Triangles and Congruence", "geometry", "rigid structure"),
    ("Similarity and Scale", "geometry", "shape-preserving transformation"),
    ("Circles and Angle Theorems", "geometry", "locus and angle relationships"),
    ("Area, Volume, and Cavalieri Reasoning", "geometry", "measure by decomposition"),
    ("Right Triangle Trigonometry", "trigonometry", "ratios in triangles"),
    ("Unit Circle and Radian Measure", "trigonometry", "rotation as number"),
    ("Trig Identities and Equations", "trigonometry", "equivalent periodic expressions"),
    ("Vectors in the Plane", "precalculus", "magnitude and direction"),
    ("Complex Numbers", "precalculus", "two-dimensional arithmetic"),
    ("Limits and Continuity", "calculus", "local behavior through approach"),
    ("Derivative as Rate of Change", "calculus", "instantaneous change"),
    ("Derivative Rules and Implicit Differentiation", "calculus", "local linearization"),
    ("Applications of Derivatives", "calculus", "optimization and shape"),
    ("Integral as Accumulation", "calculus", "area and total change"),
    ("Fundamental Theorem of Calculus", "calculus", "inverse relationship of rate and accumulation"),
    ("Techniques of Integration", "calculus", "recognizing accumulated structure"),
    ("Infinite Series and Taylor Approximation", "calculus", "functions as polynomials"),
    ("Multivariable Functions", "calculus", "surfaces and partial change"),
    ("Vectors and Matrices", "linear-algebra", "organized linear data"),
    ("Matrix Multiplication and Linear Maps", "linear-algebra", "composition of transformations"),
    ("Gaussian Elimination", "linear-algebra", "systematic constraint solving"),
    ("Vector Spaces and Subspaces", "linear-algebra", "closure and structure"),
    ("Eigenvalues and Eigenvectors", "linear-algebra", "directions preserved by a map"),
    ("Orthogonality and Least Squares", "linear-algebra", "projection and best fit"),
    ("Counting Principles", "probability-statistics", "structured enumeration"),
    ("Probability Models", "probability-statistics", "sample spaces and events"),
    ("Conditional Probability and Bayes", "probability-statistics", "updating under evidence"),
    ("Random Variables and Expectation", "probability-statistics", "weighted averages of outcomes"),
    ("Distributions and the Central Limit Theorem", "probability-statistics", "aggregate regularity"),
    ("Statistical Inference", "probability-statistics", "estimation under uncertainty"),
    ("Logic and Quantifiers", "discrete-proofs", "precise mathematical language"),
    ("Proof Methods", "discrete-proofs", "direct, contrapositive, contradiction, induction"),
    ("Sets, Relations, and Functions", "discrete-proofs", "membership and mapping structure"),
    ("Graph Theory Basics", "discrete-proofs", "nodes, edges, and connectivity"),
    ("Recurrence Relations", "discrete-proofs", "self-referential structure"),
    ("Differential Equations Models", "advanced", "change equations over time"),
    ("First Order Differential Equations", "advanced", "separable and linear dynamics"),
    ("Second Order Linear Systems", "advanced", "oscillation and forcing"),
    ("Optimization with Constraints", "advanced", "best feasible choice"),
    ("Gradient Descent and Convexity", "advanced", "iterative improvement"),
    ("Linear Algebra for Machine Learning", "advanced", "features, parameters, and projections"),
    ("Probability for Machine Learning", "advanced", "uncertainty in prediction"),
    ("Calculus for Neural Networks", "advanced", "chain rule over computation graphs"),
]


MATH_SUBSTANTIAL: dict[str, dict[str, Any]] = {
    "Fractions as Numbers": {
        "sections": [
            section("Fractions are points, not pizza slices", "Treat a fraction first as a location on the number line. Area models are useful, but the number-line view prevents the common mistake of thinking larger denominators automatically mean larger values."),
            section("Equivalent fractions preserve value", "Multiplying numerator and denominator by the same nonzero number changes the name, not the point. This is the first serious encounter with invariance under transformation."),
            section("Addition needs a shared unit", "You cannot add thirds and fifths until the unit pieces agree. Common denominators are not a ritual; they manufacture a shared measuring stick."),
            section("Multiplication rescales", "Multiplying by a fraction asks for a fraction of a quantity. The result can shrink, stay equal, or grow depending on whether the multiplier is below, equal to, or above one."),
            section("Division asks how many fit", "Dividing by 3/4 means asking how many three-quarter chunks fit in the original amount. The reciprocal algorithm is a compressed answer to that measurement question."),
        ],
        "questions": [
            "Why is 7/9 greater than 3/5 without converting to decimals?",
            "What exactly is preserved when 4/6 becomes 2/3?",
            "Invent a situation where 1/2 + 1/3 is not obviously 5/6 until units are aligned.",
            "Why can multiplying by 2/3 make a number smaller?",
            "Explain fraction division without saying 'flip and multiply.'",
            "What visual model fails for negative fractions, and what model still works?",
        ],
        "application": "Create three fraction comparison problems that can be solved by benchmarks rather than common denominators, then explain the benchmark used.",
        "objectives": ["Place, compare, add, multiply, and divide fractions as numbers.", "Explain every fraction algorithm as a statement about units or scaling.", "Use benchmark reasoning before calculation."],
    },
    "Linear Equations": {
        "sections": [
            section("An equation is a constraint", "A linear equation does not describe a procedure; it describes a condition that some values satisfy. Solving means finding the values that keep the statement true."),
            section("Balance is an invariant", "Adding, subtracting, multiplying, or dividing both sides by the same allowed quantity preserves the solution set. The equation changes appearance while the hidden answer stays fixed."),
            section("Structure before steps", "The fastest solvers inspect where the variable appears, which operations trap it, and which inverse operation releases it with the least collateral algebra."),
            section("Parameters change the family", "Equations like ax + b = c are not one problem. They are a family whose behavior changes when a is zero, when b equals c, or when values make constraints impossible."),
            section("Word problems are translation tests", "The hard part is deciding what quantity is unknown and how the story constrains it. The algebra is the bookkeeping after the model is chosen."),
        ],
        "questions": [
            "What operation would change an equation's solution set?",
            "Why is dividing by a variable dangerous before checking whether it could be zero?",
            "Create a word problem whose answer is negative and explain why that is sensible.",
            "When does ax + b = c have no solution?",
            "How can you check a solved equation without trusting your algebra?",
        ],
        "application": "Take one recurring personal quantity, such as monthly savings or training time, and model a target as a one-variable linear equation.",
        "objectives": ["Solve one-variable linear equations fluently.", "Describe solution-preserving transformations.", "Translate short real situations into equations."],
    },
    "Functions as Machines": {
        "sections": [
            section("A function is a rule with discipline", "Each allowed input gets exactly one output. The rule may be a formula, table, graph, algorithm, or verbal description, but the single-output discipline is non-negotiable."),
            section("Domain is part of the object", "A formula without a domain is incomplete. The same expression can define different functions when the allowed inputs change."),
            section("Graphs show whole behavior", "A graph makes trends, intercepts, symmetry, and local change visible at once. It is not a picture after the algebra; it is another representation of the same object."),
            section("Composition builds pipelines", "f(g(x)) means the output of one function becomes the input of another. This is the mathematical skeleton of data pipelines and programs."),
            section("Inverse functions reverse information", "An inverse exists when outputs remember enough to recover inputs. If two inputs collapse to one output, information has been lost and a global inverse is impossible."),
        ],
        "questions": [
            "Can a vertical line hit a function graph twice? Why does that test work?",
            "How can two functions use the same formula but be different?",
            "Give an example of composition outside math class.",
            "What information is lost when f(x) = x^2 accepts all real inputs?",
            "Why does restricting a domain sometimes create an inverse?",
        ],
        "application": "Model a habit loop or app workflow as composed functions: input, transformation, output, and feedback.",
        "objectives": ["Move between formula, graph, table, and verbal function descriptions.", "Use domain and range precisely.", "Analyze composition and inverse behavior."],
    },
    "Euclidean Geometry Foundations": {
        "sections": [
            section("Definitions do heavy lifting", "Geometry starts by deciding what words mean: point, line, segment, angle, circle, parallel. Sloppy definitions make impossible proofs."),
            section("Axioms are starting permissions", "An axiom is not proved inside the system; it is a rule of the game. Euclidean geometry shows how far reasoning can go from a small starting set."),
            section("Diagrams help but do not prove", "A drawing suggests relationships, but proof must rely on stated properties. The picture can lie by looking more special than the problem says."),
            section("Congruence transfers facts", "When two figures are congruent, measurements and incidences can move from one to the other. This is the engine behind many early proofs."),
            section("Proof is controlled attention", "A proof is a chain where each step is licensed by a definition, axiom, theorem, or previous result. The discipline is learning what you are allowed to notice."),
        ],
        "questions": [
            "What hidden assumption does a typical geometry diagram tempt you to make?",
            "Why can a definition be judged useful even though it is not true or false?",
            "How does congruence differ from equality?",
            "Write a two-column proof as a paragraph. What becomes clearer or harder?",
            "Why did non-Euclidean geometry matter historically?",
        ],
        "application": "Choose a simple theorem about parallel lines or triangle angles and annotate every step with the permission that justifies it.",
        "objectives": ["Use definitions, postulates, and theorems distinctly.", "Separate visual evidence from proof.", "Write short valid geometric arguments."],
    },
    "Derivative as Rate of Change": {
        "sections": [
            section("Average rate becomes instantaneous rate", "The derivative starts with a secant slope over an interval and asks what happens as the interval shrinks around a point."),
            section("Limits make the impossible legal", "Instantaneous change sounds like change over zero time. Limits avoid division by zero by studying a sequence of ordinary divisions that approach the target."),
            section("The derivative is local linearity", "Near a differentiable point, a curve behaves like its tangent line. This turns curved behavior into a local linear approximation."),
            section("Units reveal meaning", "If position is meters and time is seconds, the derivative is meters per second. Units often expose wrong derivatives before algebra does."),
            section("Non-smooth points are honest failures", "Corners, jumps, and vertical tangents show that not every graph has a derivative everywhere. Failure cases teach the definition."),
        ],
        "questions": [
            "What does the derivative of a constant function mean physically?",
            "Why is the derivative a function, not just a number?",
            "How can a graph be continuous but not differentiable?",
            "What units would the derivative of revenue with respect to price have?",
            "Why does local linearity make approximation possible?",
        ],
        "application": "Track any changing quantity for a week and estimate both average rates and plausible instantaneous rates from your data.",
        "objectives": ["Define the derivative from a limit.", "Interpret derivatives as rates, slopes, and local linear approximations.", "Identify common non-differentiability cases."],
    },
    "Integral as Accumulation": {
        "sections": [
            section("Area is the first model, not the whole idea", "The integral measures accumulated quantity. Area under a curve is the geometric case; total distance, total charge, and total probability use the same structure."),
            section("Sums become integrals", "Riemann sums chop a changing quantity into tiny pieces, approximate each piece, and pass to a limit as the pieces shrink."),
            section("Signed accumulation matters", "Area above and below an axis can cancel because integrals track signed contribution. This is essential for displacement, net work, and error."),
            section("Antiderivatives compress accumulation", "When you can find a function whose derivative is the rate, total accumulation becomes endpoint subtraction."),
            section("Numerical integration is a legitimate tool", "Many real integrals have no simple antiderivative. Trapezoids, Simpson's rule, and computation are not second-class math; they are practical accumulation."),
        ],
        "questions": [
            "When should area below the axis count as negative?",
            "What quantity is accumulated when integrating velocity?",
            "Why does making rectangles thinner improve a Riemann sum?",
            "What does an antiderivative know that a raw rate graph does not?",
            "Give an example where numerical integration is more realistic than symbolic integration.",
        ],
        "application": "Use a step counter, speed estimate, or energy reading to approximate a total by summing small intervals, then describe the limiting ideal.",
        "objectives": ["Interpret definite integrals as accumulation.", "Connect Riemann sums to limiting totals.", "Use signed area and antiderivatives appropriately."],
    },
    "Matrix Multiplication and Linear Maps": {
        "sections": [
            section("Matrices encode transformations", "A matrix is not just a box of numbers. In linear algebra, it is often a machine that moves vectors while preserving addition and scalar multiplication."),
            section("Columns tell the story", "The columns of a matrix show where basis vectors go. From those images, every other vector's image follows by linearity."),
            section("Multiplication means composition", "AB means do B, then A. The order matters because transformations usually do not commute."),
            section("Shape constraints are semantic", "Matrix dimensions are not bookkeeping trivia. They say which outputs can feed into which inputs."),
            section("Linear maps are local models", "Even nonlinear systems often use matrices as best local approximations. This is why linear algebra appears inside calculus, graphics, statistics, and machine learning."),
        ],
        "questions": [
            "Why does matrix multiplication use rows against columns?",
            "Give two transformations where order changes the result.",
            "What do the columns of a 2 by 2 matrix mean geometrically?",
            "Why is dimension mismatch a meaningful error?",
            "How can a nonlinear process use a linear approximation?",
        ],
        "application": "Pick a simple 2D shape, apply two 2 by 2 transformations in both orders, and sketch why the outputs differ.",
        "objectives": ["Interpret matrices as linear maps.", "Compute and reason about matrix products.", "Use columns and dimensions to explain transformations."],
    },
    "Conditional Probability and Bayes": {
        "sections": [
            section("Conditioning changes the universe", "P(A|B) means the sample space has been restricted to cases where B happened. Many mistakes come from using the old universe after new information arrives."),
            section("Base rates are stubborn", "Evidence matters, but rare events remain rare unless the evidence is strong enough to overcome the base rate."),
            section("Bayes is bookkeeping for belief updates", "Bayes' rule converts likelihoods into posterior probabilities by combining prior probability with how diagnostic the evidence is."),
            section("Natural frequencies beat naked percentages", "Thinking in counts, such as 10 out of 1000, often makes Bayesian problems clearer than abstract percentages."),
            section("Independence is a strong claim", "If A and B are independent, learning B does not change the probability of A. That is rarer in real systems than students expect."),
        ],
        "questions": [
            "How does the sample space change after conditioning?",
            "Why can a test with high accuracy still produce many false positives?",
            "Convert a medical-test percentage problem into natural frequencies.",
            "What would prove two events are not independent?",
            "Where do base rates get ignored in everyday decisions?",
        ],
        "application": "Analyze one personal decision involving evidence, such as a recommendation or warning sign, using explicit prior, likelihood, and posterior language.",
        "objectives": ["Compute and interpret conditional probabilities.", "Use Bayes' rule with base rates.", "Recognize independence and dependence."],
    },
    "Proof Methods": {
        "sections": [
            section("Proof is not decoration", "A proof explains why a claim must be true under stated assumptions. It is the difference between confidence from examples and certainty from structure."),
            section("Direct proof follows the grain", "Start from assumptions, unpack definitions, and move toward the conclusion. This is the default when the implication's structure is straightforward."),
            section("Contrapositive changes the target", "To prove if P then Q, prove if not Q then not P. This often turns a hard positive claim into an easier impossibility claim."),
            section("Contradiction traps inconsistency", "Assume the claim is false and show that this breaks something already accepted. The method is powerful but should reveal the actual conflict."),
            section("Induction handles infinite ladders", "Prove the first rung, then prove every rung pulls up the next. The result covers infinitely many cases without checking them one by one."),
        ],
        "questions": [
            "When is a counterexample stronger than many examples?",
            "Why are definitions often the first move in a proof?",
            "Give a claim whose contrapositive is easier than the original.",
            "What makes an induction step insufficient?",
            "How can a proof be valid but unilluminating?",
        ],
        "application": "Write one small direct proof, one contrapositive proof, and one induction proof about integers or divisibility.",
        "objectives": ["Choose among major proof strategies.", "Use definitions and quantifiers precisely.", "Write short rigorous arguments."],
    },
    "Gradient Descent and Convexity": {
        "sections": [
            section("Optimization asks for the best feasible point", "A loss function ranks choices. Gradient descent is one method for moving through those choices toward lower loss."),
            section("The gradient points uphill", "The negative gradient gives the steepest local decrease for small moves. It is local advice, not a global guarantee."),
            section("Step size controls learning", "Too small and progress crawls; too large and the method overshoots or diverges. Much of practical optimization is step-size judgment."),
            section("Convexity makes local information trustworthy", "In convex problems, any local minimum is global. This turns gradient descent from heuristic into a method with strong guarantees."),
            section("Machine learning uses imperfect landscapes", "Neural networks are usually nonconvex, but gradient methods still work surprisingly well because high-dimensional landscapes often contain many useful descent paths."),
        ],
        "questions": [
            "Why does the negative gradient decrease a function locally?",
            "What happens when a learning rate is too large?",
            "Why is convexity such a valuable assumption?",
            "How can local information fail in a nonconvex landscape?",
            "What is the analogy between gradient descent and habit improvement?",
        ],
        "application": "Minimize a simple quadratic by hand for five gradient-descent steps with two different step sizes and compare behavior.",
        "objectives": ["Explain gradient descent geometrically.", "Analyze the role of step size.", "State why convexity changes optimization guarantees."],
    },
}


PHYSICS_TOPICS: list[tuple[str, str, str]] = [
    ("Measurement, Units, and Dimensional Analysis", "measurement", "units as physical meaning"),
    ("Vectors and Coordinate Systems", "measurement", "magnitude, direction, and components"),
    ("Motion in One Dimension", "kinematics", "position, velocity, acceleration"),
    ("Motion in Two Dimensions", "kinematics", "component-wise motion"),
    ("Projectile Motion", "kinematics", "independent horizontal and vertical motion"),
    ("Newton's First and Second Laws", "newton", "force and acceleration"),
    ("Free Body Diagrams", "newton", "isolating interactions"),
    ("Friction, Drag, and Contact Forces", "newton", "surface and fluid resistance"),
    ("Newton's Third Law and Systems", "newton", "paired interactions"),
    ("Work and Kinetic Energy", "energy", "force through distance"),
    ("Potential Energy and Conservation", "energy", "stored interaction energy"),
    ("Power and Efficiency", "energy", "rate of energy transfer"),
    ("Momentum and Impulse", "momentum", "force over time"),
    ("Collisions and Center of Mass", "momentum", "system-level motion"),
    ("Rotational Kinematics", "rotation", "angular position, velocity, acceleration"),
    ("Torque and Rotational Dynamics", "rotation", "turning effect of force"),
    ("Angular Momentum", "rotation", "rotational inertia in motion"),
    ("Static Equilibrium", "rotation", "balanced forces and torques"),
    ("Simple Harmonic Motion", "oscillations", "restoring force and cycles"),
    ("Wave Properties", "waves", "amplitude, wavelength, frequency, speed"),
    ("Sound, Interference, and Beats", "waves", "superposition in air pressure"),
    ("Temperature and Heat", "thermodynamics", "thermal energy transfer"),
    ("Ideal Gas Law and Kinetic Theory", "thermodynamics", "particles behind pressure"),
    ("First Law of Thermodynamics", "thermodynamics", "energy accounting"),
    ("Second Law and Entropy", "thermodynamics", "direction and dispersal"),
    ("Electric Charge and Coulomb's Law", "electricity", "electric interaction"),
    ("Electric Fields", "electricity", "force per charge"),
    ("Electric Potential and Voltage", "electricity", "energy per charge"),
    ("Capacitors and Dielectrics", "electricity", "stored electric field energy"),
    ("Current, Resistance, and Ohm's Law", "circuits", "charge flow and opposition"),
    ("DC Circuit Analysis", "circuits", "Kirchhoff constraints"),
    ("RC and RL Transients", "circuits", "time-dependent circuits"),
    ("Magnetic Fields and Forces", "magnetism", "moving charge interactions"),
    ("Electromagnetic Induction", "magnetism", "changing flux creates emf"),
    ("Maxwell's Equations Concept Map", "magnetism", "unified electromagnetism"),
    ("Geometric Optics", "optics", "rays, lenses, and mirrors"),
    ("Wave Optics and Diffraction", "optics", "interference of light"),
    ("Special Relativity Postulates", "relativity", "invariant light speed"),
    ("Time Dilation and Length Contraction", "relativity", "spacetime intervals"),
    ("Relativistic Energy and Momentum", "relativity", "mass-energy relation"),
    ("Quantum Evidence and Photons", "quantum", "discrete light-matter interaction"),
    ("Wavefunctions and Probability", "quantum", "state and measurement"),
    ("Atoms and Spectra", "quantum", "quantized energy levels"),
    ("Nuclear Structure and Radioactivity", "nuclear", "unstable nuclei"),
    ("Fission, Fusion, and Binding Energy", "nuclear", "nuclear energy accounting"),
    ("Particle Physics Overview", "particle", "fields, particles, and interactions"),
    ("Fluids: Pressure and Buoyancy", "fluids", "force through fluid depth"),
    ("Fluid Flow and Bernoulli's Principle", "fluids", "continuity and energy in flow"),
    ("Gravity and Orbits", "astro", "inverse-square attraction"),
    ("Stars and Stellar Evolution", "astro", "gravity against pressure"),
    ("Cosmology and the Expanding Universe", "astro", "large-scale spacetime history"),
]


PHYSICS_SUBSTANTIAL: dict[str, dict[str, Any]] = {
    "Vectors and Coordinate Systems": {
        "sections": [
            section("Physics needs directed quantities", "Displacement, velocity, acceleration, force, and fields need both size and direction. Treating them as ordinary signed numbers hides part of the physical situation."),
            section("Components trade geometry for arithmetic", "A vector can be decomposed along axes. The components are not separate realities; they are a coordinate-dependent way to calculate with one directed quantity."),
            section("Coordinate choice is strategy", "Good axes make a problem simpler by aligning with motion, slopes, or symmetry. A bad axis choice is legal but expensive."),
            section("Vector addition is physical combination", "Adding vectors means combining effects: two displacements, two forces, or two field contributions. The parallelogram rule and component method say the same thing."),
            section("Dot products measure alignment", "The dot product extracts the part of one vector along another. Work, projection, and flux all depend on this idea."),
        ],
        "questions": [
            "Why is speed not a vector but velocity is?",
            "How can the same vector have different components in different coordinate systems?",
            "When would tilted axes be better than horizontal and vertical axes?",
            "What does a zero dot product mean physically?",
            "How does vector addition explain equilibrium?",
        ],
        "application": "Draw a sloped-surface force problem twice: once with ordinary axes and once with axes parallel/perpendicular to the surface. Compare the equations.",
        "objectives": ["Resolve and combine vectors.", "Choose useful coordinate systems.", "Use dot products as alignment measurements."],
    },
    "Newton's First and Second Laws": {
        "sections": [
            section("Inertia is the default", "Newton's first law says motion does not need a cause; changes in motion do. This reverses the everyday intuition that continuous motion requires continuous pushing."),
            section("Net force controls acceleration", "The second law connects the vector sum of forces to acceleration. Individual forces matter through their sum, not through moral labels like 'the applied force wins.'"),
            section("Mass measures resistance to acceleration", "For the same net force, larger mass accelerates less. Mass is not weight; weight is the gravitational force on mass."),
            section("Forces are interactions", "A force is not a property an object carries. It is an interaction with another object or field, which is why identifying forces starts by identifying the environment."),
            section("Zero net force does not mean zero motion", "An object with zero net force can be at rest or move at constant velocity. Equilibrium is about acceleration, not speed."),
        ],
        "questions": [
            "Why does a puck keep sliding on nearly frictionless ice?",
            "What is wrong with saying a moving object has a force in its direction of motion?",
            "How can something move upward while accelerating downward?",
            "What forces act on a book resting on a table?",
            "Why is weight different on the Moon but mass is not?",
        ],
        "application": "Record three everyday motions and identify whether each has zero, constant, or changing acceleration. Then infer the net-force direction.",
        "objectives": ["Apply Newton's laws as vector statements.", "Distinguish force from velocity.", "Connect net force, mass, and acceleration."],
    },
    "Potential Energy and Conservation": {
        "sections": [
            section("Energy tracks capacity for change", "Energy is a bookkeeping quantity that lets physics follow transformations across motion, height, compression, heat, and fields."),
            section("Conservative forces store recoverable energy", "Gravity and ideal springs can trade kinetic energy for potential energy and back. The path does not matter, only the starting and ending configurations."),
            section("Systems define what is conserved", "Energy conservation applies to a chosen system. If energy seems lost, ask whether it crossed the boundary as heat, sound, work, or radiation."),
            section("Potential energy needs a reference", "Only differences in potential energy affect motion. Choosing zero at the floor, table, or infinity is a convenience as long as differences remain consistent."),
            section("Dissipation changes usefulness, not total energy", "Friction converts organized mechanical energy into thermal energy. Total energy remains, but the ability to do macroscopic work declines."),
        ],
        "questions": [
            "Why can potential energy be negative?",
            "When does path matter for work?",
            "What system boundary makes a falling-object problem easiest?",
            "Where does mechanical energy go when brakes heat up?",
            "Why is conservation more powerful than force analysis in some problems?",
        ],
        "application": "Analyze a playground swing or elevator ride using energy transfers instead of forces first; then check the force picture.",
        "objectives": ["Use conservation of mechanical energy.", "Choose system boundaries.", "Distinguish conservative and nonconservative work."],
    },
    "Momentum and Impulse": {
        "sections": [
            section("Momentum belongs to moving mass", "Momentum combines mass and velocity into a vector quantity that is especially powerful for collisions and explosions."),
            section("Impulse changes momentum", "A force applied over time changes momentum. A small force for a long time and a large force for a short time can produce the same impulse."),
            section("Systems conserve momentum internally", "When external impulse is negligible, total system momentum stays constant even while objects exchange enormous forces internally."),
            section("Center of mass reveals system motion", "The center of mass moves as if all external force acted on total mass there. Internal chaos cannot move the center by itself."),
            section("Energy and momentum answer different questions", "Momentum may be conserved in a collision while kinetic energy is not. The missing kinetic energy usually becomes heat, sound, deformation, or internal energy."),
        ],
        "questions": [
            "Why do airbags reduce injury using impulse?",
            "How can two skaters push apart without external force?",
            "What is conserved in a perfectly inelastic collision?",
            "Why does a rocket move forward by throwing mass backward?",
            "How can kinetic energy change while momentum is conserved?",
        ],
        "application": "Estimate the impulse in catching a ball softly versus stiffly, using rough force and time assumptions.",
        "objectives": ["Use impulse-momentum reasoning.", "Analyze isolated systems.", "Separate momentum conservation from kinetic-energy conservation."],
    },
    "Simple Harmonic Motion": {
        "sections": [
            section("Restoring force creates oscillation", "A system oscillates when displacement from equilibrium produces a force back toward equilibrium. Springs and small-angle pendulums are the canonical cases."),
            section("Acceleration points toward equilibrium", "In simple harmonic motion, acceleration is proportional to negative displacement. Speed is largest at equilibrium and zero at turning points."),
            section("Energy swaps forms", "A spring-mass system trades kinetic energy for potential energy continuously. Total mechanical energy stays constant when damping is negligible."),
            section("Period depends on system parameters", "A mass-spring oscillator's period depends on mass and spring stiffness. A simple pendulum's small-angle period depends mainly on length and gravity."),
            section("Resonance amplifies response", "Driving a system near its natural frequency can produce large oscillations. This is useful in instruments and dangerous in bridges or machinery."),
        ],
        "questions": [
            "Where are velocity and acceleration largest in a spring oscillator?",
            "Why does a stiffer spring oscillate faster?",
            "What approximation makes a pendulum simple harmonic?",
            "How does damping change the energy story?",
            "Why can a small periodic push have a large effect?",
        ],
        "application": "Measure a hanging object's oscillation period for different amplitudes and decide where the small-angle or linear approximation breaks down.",
        "objectives": ["Model restoring-force systems.", "Track energy through oscillation.", "Explain natural frequency, damping, and resonance."],
    },
    "Second Law and Entropy": {
        "sections": [
            section("Energy conservation does not choose direction", "The first law permits many processes that never occur spontaneously. The second law explains why heat flows hot to cold and why some transformations are effectively irreversible."),
            section("Entropy counts spreading", "Entropy measures how dispersed energy and microscopic arrangements are. More macrostates correspond to vastly more microscopic possibilities."),
            section("Heat engines need temperature differences", "Engines turn some heat into work by moving energy from hot reservoirs to cold reservoirs. No engine can convert all heat into work in a cycle."),
            section("Irreversibility is statistical", "Microscopic laws may be reversible, but overwhelmingly many particle arrangements correspond to mixed, spread-out states. Direction appears from probability at scale."),
            section("Information and entropy are linked", "Knowing a system's microstate lowers uncertainty. Erasing information has thermodynamic consequences because physical memory is part of the world."),
        ],
        "questions": [
            "Why does perfume spread through a room but not unspread?",
            "What does a refrigerator do to entropy locally and globally?",
            "Why can no heat engine be perfectly efficient?",
            "How is entropy different from ordinary disorder?",
            "What does information have to do with physical states?",
        ],
        "application": "Trace one household energy flow, such as cooking or air conditioning, and identify reservoirs, work, waste heat, and entropy increase.",
        "objectives": ["State the second law in multiple forms.", "Use entropy as energy dispersal and multiplicity.", "Analyze heat engines and irreversibility qualitatively."],
    },
    "DC Circuit Analysis": {
        "sections": [
            section("Circuits impose constraints", "Circuit analysis is not about following electrons one by one. It is about constraints on current and voltage across connected components."),
            section("Kirchhoff's current law conserves charge", "At a junction, current in equals current out. Charge does not pile up indefinitely in ordinary steady circuits."),
            section("Kirchhoff's voltage law conserves energy", "Around a closed loop, voltage rises and drops sum to zero. Each charge returns to its starting energy per charge."),
            section("Equivalent resistance compresses networks", "Series and parallel combinations let you replace a network with a simpler one that behaves the same at its terminals."),
            section("Power reveals physical consequence", "P = IV connects circuit quantities to heating, light, motion, and battery drain. A correct circuit solution should make power sense."),
        ],
        "questions": [
            "Why is current the same through series components?",
            "Why is voltage the same across parallel branches?",
            "What physical conservation law sits behind each Kirchhoff rule?",
            "How can adding a resistor lower total resistance?",
            "Where does power go in a resistor?",
        ],
        "application": "Analyze a two-resistor LED or battery circuit: predict currents, voltages, and power before building or simulating it.",
        "objectives": ["Apply Kirchhoff's laws.", "Simplify series and parallel networks.", "Connect voltage, current, resistance, and power."],
    },
    "Electromagnetic Induction": {
        "sections": [
            section("Changing magnetic flux creates emf", "Induction appears when the magnetic field through a loop changes, the loop area changes, or the loop orientation changes. Flux is the combined measure."),
            section("Lenz's law protects conservation", "The induced effect opposes the change that produced it. This minus sign prevents free energy and encodes energy conservation."),
            section("Generators convert motion to electrical energy", "Moving coils or magnets change flux, inducing voltage. Mechanical work becomes electrical energy through electromagnetic interaction."),
            section("Transformers use changing fields", "An alternating current in one coil creates changing magnetic flux that induces voltage in another coil. The turns ratio controls voltage tradeoffs."),
            section("Fields, not wires, carry the deep story", "Circuit language is useful, but induction reveals that electric and magnetic fields are coupled parts of one electromagnetic system."),
        ],
        "questions": [
            "What are three ways to change magnetic flux?",
            "Why does Lenz's law have a minus sign?",
            "How does a generator become harder to turn under load?",
            "Why do transformers need changing current?",
            "How does induction foreshadow Maxwell's equations?",
        ],
        "application": "Explain a bicycle light generator or wireless charger using flux change, induced emf, and energy conservation.",
        "objectives": ["Calculate and interpret magnetic flux qualitatively.", "Use Faraday's and Lenz's laws.", "Connect induction to generators and transformers."],
    },
    "Wavefunctions and Probability": {
        "sections": [
            section("Quantum states encode probabilities", "A wavefunction is not a tiny classical wave in space. It is a mathematical object whose squared magnitude gives probabilities for measurement outcomes."),
            section("Superposition is real bookkeeping", "Before measurement, a system can be represented as a combination of possible states. Interference shows this is more than ignorance about a hidden classical choice."),
            section("Measurement changes what can be predicted", "A measurement produces an outcome and updates the state used for future predictions. Quantum theory predicts probabilities, not single-event certainty."),
            section("Operators represent observables", "Position, momentum, and energy correspond to mathematical operations on states. Special states of an operator have definite values for that observable."),
            section("The classical world is an approximation", "Large systems interacting with environments lose observable interference rapidly. Classical behavior emerges as a stable approximation, not as a separate set of laws."),
        ],
        "questions": [
            "Why is probability central rather than merely a sign of ignorance?",
            "What experimental behavior makes superposition necessary?",
            "How does measuring position affect later momentum predictions?",
            "What does an energy eigenstate mean?",
            "Why do macroscopic objects look classical?",
        ],
        "application": "Write a two-slit explanation that uses probability amplitudes and interference without imagining electrons as tiny billiard balls.",
        "objectives": ["Interpret wavefunctions probabilistically.", "Explain superposition and measurement.", "Use operators and eigenstates conceptually."],
    },
}


HISTORY_TOPICS: list[tuple[str, str, str]] = [
    ("Foragers, Climate, and the Human Baseline", "prehistory", "mobility and adaptation"),
    ("Agriculture and the Neolithic Transition", "early-civilization", "food production and settlement"),
    ("Mesopotamia: Cities, Temples, and Writing", "early-civilization", "urban institutions"),
    ("Sumerian Kingship and City-States", "early-civilization", "political competition"),
    ("Akkad and the First Empires", "early-civilization", "imperial integration"),
    ("Babylon, Law, and Administration", "early-civilization", "state recordkeeping"),
    ("Egypt: Nile Ecology and Divine Kingship", "egypt", "river civilization"),
    ("Pyramids, Labor, and Old Kingdom Power", "egypt", "monumental organization"),
    ("Indus Valley Urbanism", "indus", "planned cities and trade"),
    ("Early China: Shang, Zhou, and Mandate", "china", "bronze, ritual, legitimacy"),
    ("Warring States and Chinese Philosophy", "china", "order under fragmentation"),
    ("Persian Empire and Imperial Tolerance", "near-east", "roads, satrapies, plural rule"),
    ("Greek Polis and Civic Experiment", "greece", "citizenship and rivalry"),
    ("Athens, Democracy, and Empire", "greece", "participation and domination"),
    ("Socrates and the Examined Life", "greece", "ethical questioning"),
    ("Plato: Forms, Politics, and Education", "greece", "ideal order"),
    ("Aristotle: Causes, Virtue, and Classification", "greece", "empirical system-building"),
    ("Alexander and the Hellenistic World", "hellenistic", "cultural fusion"),
    ("Library of Alexandria: Knowledge Infrastructure", "hellenistic", "collection, scholarship, loss"),
    ("Roman Republic: Mixed Constitution and Expansion", "rome", "institutions under stress"),
    ("Caesar, Augustus, and the Principate", "rome", "republic to empire"),
    ("Roman Law, Roads, and Urban Life", "rome", "durable infrastructure"),
    ("Christianity and Late Antique Transformation", "late-antiquity", "religion and empire"),
    ("Fall of the Western Roman Empire", "late-antiquity", "fragmentation and continuity"),
    ("Byzantium and the Eastern Roman Survival", "late-antiquity", "imperial adaptation"),
    ("Islamic Origins and Caliphates", "islamic", "religion, conquest, governance"),
    ("Islamic Golden Age: Translation and Science", "islamic", "knowledge transmission"),
    ("Medieval Europe: Feudalism, Church, and Towns", "medieval", "localized power"),
    ("Mongol Empire and Eurasian Exchange", "medieval", "connectivity and violence"),
    ("Renaissance Humanism and Patronage", "renaissance", "classical recovery"),
    ("Printing Press and Information Shock", "renaissance", "cheap reproduction"),
    ("Reformation and Confessional Conflict", "early-modern", "authority and conscience"),
    ("Scientific Revolution: Method and Measurement", "science", "experiment and mathematization"),
    ("Enlightenment, Rights, and State Power", "early-modern", "reason and reform"),
    ("Industrialization and Fossil Energy", "industrial", "machines, labor, growth"),
    ("Imperialism, Nationalism, and Modernity", "modern", "global power asymmetry"),
]


HISTORY_SUBSTANTIAL: dict[str, dict[str, Any]] = {
    "Agriculture and the Neolithic Transition": {
        "sections": [
            section("Farming was not an obvious upgrade", "Early agriculture often meant harder labor, narrower diets, disease exposure, and social inequality. Its advantage was demographic and logistical: more calories per acre and stored surplus."),
            section("Climate created windows of possibility", "After the last Ice Age, warmer and more stable conditions made wild grains, herd animals, and settled seasonal camps more reliable in several regions."),
            section("Domestication changed species together", "Humans selected plants and animals for traits useful to settled life. Those species also reshaped human bodies, schedules, settlement patterns, and disease environments."),
            section("Surplus created specialization", "Stored food let some people become potters, builders, priests, traders, scribes, and rulers. This was the social engine of complexity."),
            section("Property and hierarchy hardened", "Fields, herds, irrigation works, and granaries made ownership more durable. Defense, inheritance, taxation, and status became central political problems."),
        ],
        "questions": [
            "Why might farming spread even if individual farmers were less healthy than foragers?",
            "What kinds of authority become possible once food can be stored?",
            "How does domestication change both humans and nonhuman species?",
            "Why is surplus a precondition for many crafts and offices?",
            "What does agriculture make easier to tax?",
            "Which modern institutions still depend on the Neolithic bargain?",
        ],
        "application": "Map one modern routine, such as school, rent, taxes, or work specialization, back to the requirements of settled agricultural life.",
        "objectives": ["Explain the costs and advantages of agriculture.", "Connect surplus to specialization and hierarchy.", "Trace long-run institutional consequences of settlement."],
    },
    "Mesopotamia: Cities, Temples, and Writing": {
        "sections": [
            section("The rivers demanded coordination", "The Tigris and Euphrates offered fertile land but unpredictable water. Irrigation, drainage, and flood response rewarded organized labor and administration."),
            section("The temple was an economic center", "Temples were not only religious sites. They stored grain, employed workers, coordinated offerings, and legitimized authority."),
            section("Cities concentrated strangers", "Uruk and other cities brought together people beyond kinship scale. Walls, offices, measures, seals, and laws helped manage trust among strangers."),
            section("Writing began as administration", "Early cuneiform tracked commodities, labor, and obligations. Literature came later; bureaucracy created the first durable written records."),
            section("Myth and power reinforced each other", "Kingship, divine favor, cosmic order, and military success were narrated together, making political authority feel embedded in the structure of the world."),
        ],
        "questions": [
            "Why did irrigation encourage administration?",
            "How can a temple be both sacred and economic?",
            "Why does city life require more recordkeeping than village life?",
            "What changes when memory moves from people to clay tablets?",
            "How do myths make political power more durable?",
        ],
        "application": "Design a simple clay-tablet accounting system for grain, labor, and debt. Decide what symbols must exist before prose exists.",
        "objectives": ["Describe Mesopotamian urban institutions.", "Explain administrative origins of writing.", "Connect ecology, temples, and kingship."],
    },
    "Egypt: Nile Ecology and Divine Kingship": {
        "sections": [
            section("The Nile made predictability political", "Unlike Mesopotamian rivers, the Nile flooded with relative regularity. This supported a worldview of order, renewal, and centralized coordination."),
            section("Geography favored unity", "Deserts, cataracts, and the river corridor shaped Egypt into a long, connected civilization with defensible boundaries and river transport."),
            section("Pharaoh embodied cosmic order", "Kingship was framed as maintaining ma'at: truth, balance, order, and right relation among gods, people, and nature."),
            section("Monuments were administrative achievements", "Pyramids and temples were not merely architectural feats. They reveal taxation, labor mobilization, craft specialization, logistics, and ideology."),
            section("Death organized life", "Funerary religion, mummification, tomb art, and afterlife beliefs shaped economics and culture because preparing for death required living institutions."),
        ],
        "questions": [
            "How did Nile regularity shape Egyptian ideas of order?",
            "Why might geography encourage political unity?",
            "What does divine kingship solve for a state?",
            "How do monuments reveal administrative capacity?",
            "Why did afterlife beliefs require large earthly institutions?",
        ],
        "application": "Compare the Nile and Mesopotamian river systems, then infer two political differences each ecology would encourage.",
        "objectives": ["Relate Nile ecology to Egyptian institutions.", "Explain divine kingship and ma'at.", "Read monuments as evidence of social organization."],
    },
    "Socrates and the Examined Life": {
        "sections": [
            section("Socrates shifted attention to how to live", "Earlier Greek thinkers often asked about nature and substance. Socrates made ethics, definitions, and self-knowledge central public problems."),
            section("The elenchus tests confidence", "Socratic questioning exposes contradictions in confident claims. The goal is not trivia defeat; it is intellectual humility and clearer definitions."),
            section("Athens was the stage", "Democracy, rhetoric, courts, empire, war, and civic pride made public argument powerful and dangerous. Philosophy was not isolated from politics."),
            section("The trial revealed competing loyalties", "Socrates' defense set obedience to inquiry and divine mission against civic expectations. His death became a permanent image of philosophy under pressure."),
            section("The legacy is a practice, not a doctrine", "Socrates wrote nothing. His influence survives as a method of questioning assumptions and refusing unexamined prestige."),
        ],
        "questions": [
            "Why are definitions morally important for Socrates?",
            "When does questioning become politically threatening?",
            "What is the difference between humility and indecision?",
            "Why might a democracy fear a philosopher?",
            "How does Socrates challenge credentialed confidence today?",
        ],
        "application": "Pick one confident belief about success, justice, or learning. Run five Socratic questions against it and revise the definition.",
        "objectives": ["Explain Socratic questioning.", "Place Socrates in Athenian civic life.", "Use the examined-life method on modern assumptions."],
    },
    "Library of Alexandria: Knowledge Infrastructure": {
        "sections": [
            section("It was a research system, not just a room", "The Library and Mouseion were part of a state-backed scholarly institution that collected texts, supported scholars, edited works, and made Alexandria a knowledge capital."),
            section("Empire made collection possible", "Ptolemaic wealth, trade routes, royal ambition, and Greek administrative culture let Alexandria acquire, copy, classify, and compare texts from across the Mediterranean and Near East."),
            section("Philology was a technology", "Scholars compared manuscripts, corrected corrupt lines, created catalogues, and stabilized inherited texts. This work made later learning possible."),
            section("Its destruction was probably not one clean fire", "The popular story of a single catastrophic burning is too simple. Loss likely accumulated through war damage, funding decline, political change, religious conflict, neglect, and the fragility of manuscript culture."),
            section("Why it mattered", "Alexandria shows that knowledge depends on institutions: money, catalogues, copying labor, scholarly norms, political protection, and material preservation."),
        ],
        "questions": [
            "Why is a library also an infrastructure problem?",
            "What does cataloguing make possible that collecting alone does not?",
            "Why are single-disaster stories attractive but often misleading?",
            "How did imperial power support scholarship?",
            "What modern institutions play the role of Alexandria?",
            "What makes digital knowledge fragile despite easy copying?",
        ],
        "application": "Audit your own knowledge system as if it were Alexandria: acquisition, cataloguing, redundancy, commentary, funding, and failure modes.",
        "objectives": ["Explain the Library and Mouseion as institutions.", "Summarize why the simple-burning myth is inadequate.", "Connect preservation to political and material support."],
    },
    "Roman Republic: Mixed Constitution and Expansion": {
        "sections": [
            section("The Republic balanced social orders", "Consuls, Senate, assemblies, tribunes, and magistracies distributed power across aristocratic leadership and popular participation, at least for citizens."),
            section("Expansion rewarded and strained institutions", "Military success brought land, wealth, slaves, allies, and obligations. Institutions built for a city-state had to govern a Mediterranean empire."),
            section("Citizenship was a tool of integration", "Rome's flexible use of alliances and citizenship helped turn defeated communities into manpower and political partners, though unevenly and often coercively."),
            section("Land and army reforms changed incentives", "As inequality and long campaigns grew, soldiers' loyalty shifted toward commanders who could provide pay, land, and spoils."),
            section("Civil conflict exposed constitutional limits", "The Republic had norms for competition, but repeated emergency politics, violence, and personal armies showed that unwritten restraint could collapse."),
        ],
        "questions": [
            "Why did Rome's constitution work well for a city but struggle with empire?",
            "How did citizenship become a strategic advantage?",
            "Why do military incentives matter for constitutional survival?",
            "What happens when political norms break before laws change?",
            "Was Roman expansion a cause or symptom of Republican crisis?",
        ],
        "application": "Compare one modern institution that scaled beyond its original design. Identify which incentives changed as it grew.",
        "objectives": ["Describe Republican institutions.", "Connect expansion to social and military strain.", "Explain the Republic's transition pressures."],
    },
    "Scientific Revolution: Method and Measurement": {
        "sections": [
            section("Nature became mathematized", "Thinkers increasingly described motion, astronomy, optics, and mechanics with mathematical laws rather than qualitative hierarchies alone."),
            section("Instruments extended observation", "Telescopes, microscopes, clocks, barometers, and improved tables made phenomena visible, comparable, and repeatable in new ways."),
            section("Experiment disciplined speculation", "Controlled tests did not replace theory; they forced theories to risk failure in public, reproducible settings."),
            section("Institutions mattered", "Printing, correspondence networks, academies, patronage, and priority disputes created a social system for checking and spreading claims."),
            section("The revolution was uneven", "Old and new ideas coexisted. Magic, theology, mechanics, craft knowledge, and mathematics overlapped more than clean textbook narratives suggest."),
        ],
        "questions": [
            "Why does measurement change what can count as explanation?",
            "How did instruments alter trust?",
            "What makes an experiment different from an observation?",
            "Why did printing and correspondence matter for science?",
            "Where do older worldviews persist inside scientific change?",
        ],
        "application": "Take one belief you hold about health, productivity, or learning and design a small measurement protocol that could genuinely challenge it.",
        "objectives": ["Explain mathematization and experiment.", "Connect instruments and institutions to scientific change.", "Avoid simplistic lone-genius narratives."],
    },
}


def build_units(track_id: str, topics: list[tuple[str, str, str]], substantial: dict[str, dict[str, Any]], sources: list[Source]) -> list[Unit]:
    units: list[Unit] = []
    prev: list[str] = []
    for order, (title, level, focus) in enumerate(topics, start=1):
        data = substantial.get(title)
        prereqs = prev[-2:]
        if data:
            unit = substantial_unit(
                track_id=track_id,
                title=title,
                order=order,
                level=level,
                prerequisites=prereqs,
                sources=sources,
                sections=data["sections"],
                thinking_questions=data["questions"],
                application_prompt=data["application"],
                objectives=data["objectives"],
            )
        else:
            unit = compact_unit(track_id, title, order, level, prereqs, sources, focus)
        units.append(unit)
        prev.append(unit["id"])
    return units


def pg_tag_profile(tags: list[str]) -> dict[str, str]:
    profiles: dict[str, dict[str, str]] = {
        "startups": {
            "lens": "startup reality",
            "idea": "Treat the essay as a practical test of users, growth, founder behavior, and feedback loops.",
            "prompt": "Apply the essay to one active project and decide what direct user evidence would change this week's plan.",
        },
        "writing": {
            "lens": "clear writing",
            "idea": "Use the essay to study writing as compressed thinking: a way to notice the real claim and remove performance.",
            "prompt": "Rewrite one paragraph so the strongest claim appears first and every sentence earns its place.",
        },
        "thinking": {
            "lens": "independent judgment",
            "idea": "Read for the move from inherited opinion toward a claim that can survive evidence, incentives, and edge cases.",
            "prompt": "Name one belief your group rewards, then list what evidence would change your mind.",
        },
        "work": {
            "lens": "ambitious work",
            "idea": "Study the relation between curiosity, stamina, taste, and direct contact with the problem.",
            "prompt": "Protect one block for work that compounds into ability and inspect what makes it feel worth doing.",
        },
        "programming": {
            "lens": "tools and leverage",
            "idea": "Look for how expressive tools, hacker taste, and small-team leverage change what can be built.",
            "prompt": "Audit one daily tool: decide whether it shortens the important path or only makes the common path familiar.",
        },
        "society": {
            "lens": "institutions and norms",
            "idea": "Ask how norms, institutions, and incentives determine what people can say, build, risk, or become.",
            "prompt": "Pick one norm nearby and ask who benefits, who pays, and what truth it makes harder to say.",
        },
        "wealth": {
            "lens": "wealth creation",
            "idea": "Separate creating new value from merely moving money, then ask what people want at scale.",
            "prompt": "Trace a product or service to the exact place where new value is created.",
        },
        "learning": {
            "lens": "self-education",
            "idea": "Look for the difference between visible ability, direct experience, and credential-shaped substitutes.",
            "prompt": "Convert one credential-shaped goal into a visible skill demonstration someone could inspect.",
        },
    }
    for tag in tags:
        if tag in profiles:
            return profiles[tag]
    return profiles["thinking"]


def infer_pg_tags(title: str, url: str) -> list[str]:
    haystack = f"{title} {url}".lower()
    rules = [
        ("startups", ["startup", "founder", "fundraising", "investor", "users", "growth", "company", "ycombinator"]),
        ("writing", ["write", "writing", "words", "essay", "talk", "read", "usefully", "simply"]),
        ("thinking", ["ideas", "truth", "bias", "disagree", "know", "expert", "heresy", "taste", "smart"]),
        ("work", ["work", "hard", "determination", "procrastination", "ambition", "boss", "love", "project"]),
        ("programming", ["hackers", "lisp", "language", "python", "java", "programmers", "open source", "software"]),
        ("society", ["inequality", "cities", "america", "visa", "kids", "conformism", "privilege", "credibility"]),
        ("wealth", ["rich", "wealth", "money", "economic", "risk", "billionaires"]),
        ("learning", ["learned", "noob", "credentials", "student", "school"]),
    ]
    tags = [tag for tag, words in rules if any(word in haystack for word in words)]
    return tags[:4] or ["thinking"]


def pg_default_digest(title: str, url: str, tags: list[str]) -> dict[str, Any]:
    profile = pg_tag_profile(tags)
    return {
        "summary": (
            f"Original LifeOS digest for Paul Graham's '{title}', focused on {profile['lens']}. "
            "Use the official essay as source text; this curriculum unit stores only a study map."
        ),
        "key_ideas": [
            profile["idea"],
            "Identify the concrete observation Graham starts from, then separate it from the broader rule he draws.",
            "Test the advice against your own incentives, constraints, and a fair objection.",
        ],
        "application_prompt": profile["prompt"],
        "thinking_questions": [
            f"What is the strongest claim in '{title}', stated without Graham's wording?",
            "Which assumption would have to be false for the essay's advice to break?",
            "Where does the essay favor direct evidence over prestige, credentials, or consensus?",
            "What would a critic say is missing, overstated, or too dependent on Graham's context?",
            "What concrete behavior would change this week if you believed the essay?",
        ],
        "official_url": url,
    }


def read_pg_json_units() -> list[dict[str, Any]]:
    if not PG_JSON.exists():
        return []
    try:
        data = json.loads(PG_JSON.read_text(encoding="utf-8"))
    except Exception:
        return []
    units = data.get("units", [])
    return units if isinstance(units, list) else []


def read_pg_fallback_essays() -> list[dict[str, str]]:
    try:
        tree = ast.parse(PG_REFRESH_SCRIPT.read_text(encoding="utf-8"))
    except Exception:
        return []
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "FALLBACK_ESSAYS":
            value = ast.literal_eval(node.value)
            return [item for item in value if isinstance(item, dict) and item.get("title") and item.get("url")]
    return []


def pg_curriculum_unit(raw: dict[str, Any], order: int) -> Unit:
    title = str(raw.get("title") or "Untitled Paul Graham Essay")
    url = str(raw.get("url") or raw.get("official_url") or PG_INDEX_SOURCE["url"])
    tags = [str(tag) for tag in raw.get("tags", [])] or infer_pg_tags(title, url)
    digest = raw.get("digest") if isinstance(raw.get("digest"), dict) else pg_default_digest(title, url, tags)
    summary = str(digest.get("summary") or pg_default_digest(title, url, tags)["summary"])
    key_ideas = [str(item) for item in digest.get("key_ideas", [])][:4]
    if not key_ideas:
        key_ideas = pg_default_digest(title, url, tags)["key_ideas"]
    questions = [str(item) for item in digest.get("thinking_questions", [])]
    if not questions:
        questions = pg_default_digest(title, url, tags)["thinking_questions"]
    application = str(digest.get("application_prompt") or pg_tag_profile(tags)["prompt"])
    unit_id = str(raw.get("id") or f"pg-{slug(Path(url).stem or title)}")
    return {
        "id": unit_id,
        "title": title,
        "subtitle": f"Paul Graham essay digest: {', '.join(tags[:2])}",
        "summary": summary,
        "kind": "essay-digest",
        "level": tags[0],
        "order": int(raw.get("order") or order),
        "minutes": int(raw.get("minutes") or 20),
        "prerequisites": raw.get("prerequisites") if isinstance(raw.get("prerequisites"), list) else [],
        "source": {"label": f"Paul Graham: {title}", "url": url},
        "objectives": [
            "Restate the essay's thesis without copying Graham's wording.",
            "Extract the practical rule and one fair limitation.",
            "Apply the idea to current work, learning, writing, or startup judgment.",
        ],
        "sections": [
            section("Digest", summary),
            section("Key ideas", " ".join(f"{index}. {idea}" for index, idea in enumerate(key_ideas, start=1))),
            section("Application", application),
            section("Question set", " ".join(questions[:4])),
            section("Source practice", "Read the official essay at the source URL, then keep notes as claims, examples, objections, and actions. This unit stores no full essay body."),
        ],
        "thinking_questions": questions,
        "application_prompt": application,
        "review_prompts": [
            "Restate the thesis from memory.",
            "Name one example from your own work where the idea applies.",
            "Find the strongest objection and answer it fairly.",
        ],
        "author": "Paul Graham",
        "tags": tags,
    }


def build_paul_graham_units() -> list[Unit]:
    raw_units = read_pg_json_units()
    if not raw_units:
        raw_units = [
            {
                "id": f"pg-{slug(Path(item['url']).stem or item['title'])}",
                "title": item["title"],
                "url": item["url"],
                "order": index,
                "tags": infer_pg_tags(item["title"], item["url"]),
                "digest": pg_default_digest(item["title"], item["url"], infer_pg_tags(item["title"], item["url"])),
                "prerequisites": [],
            }
            for index, item in enumerate(read_pg_fallback_essays(), start=1)
        ]
    units: list[Unit] = []
    seen: set[str] = set()
    for index, raw in enumerate(raw_units, start=1):
        unit = pg_curriculum_unit(raw, index)
        key = unit["source"]["url"]
        if key in seen:
            continue
        seen.add(key)
        units.append(unit)
    return units


OPEN_STARTUP_STRATEGY_SOURCES: list[Source] = [
    {"title": "Y Combinator Startup Library", "url": "https://www.ycombinator.com/library"},
    {"title": "Startup School Library", "url": "https://www.startupschool.org/library"},
    {"title": "Steve Blank Customer Development", "url": "https://steveblank.com/category/customer-development/"},
]

OPEN_STRATEGIC_MIND_SOURCES: list[Source] = [
    {"title": "Internet History Sourcebooks", "url": "https://sourcebooks.fordham.edu/"},
    {"title": "World History Encyclopedia", "url": "https://www.worldhistory.org/"},
    {"title": "Wikisource History Portal", "url": "https://en.wikisource.org/wiki/Portal:History"},
]

OPEN_ANALYTICAL_MIND_SOURCES: list[Source] = [
    {"title": "MacTutor History of Mathematics", "url": "https://mathshistory.st-andrews.ac.uk/"},
    {"title": "Stanford Encyclopedia of Philosophy", "url": "https://plato.stanford.edu/"},
    {"title": "Nobel Prize Biographical Resources", "url": "https://www.nobelprize.org/prizes/"},
]


TESLA_RESOURCE_CATALOG: dict[str, Source] = {
    "museum-home": {
        "title": "Nikola Tesla Museum — home",
        "url": "https://tesla-museum.org/en/home/",
        "note": "Official Belgrade museum; start for archive context and institutional claims.",
    },
    "museum-archive": {
        "title": "Nikola Tesla Museum — archive",
        "url": "https://tesla-museum.org/en/legacy/archive/",
        "note": "Official overview of Tesla's personal archive and document collections.",
    },
    "museum-repository": {
        "title": "Nikola Tesla Museum — official archive",
        "url": "https://tesla-museum.org/en/legacy/archive/",
        "note": "Searchable official repository; use for documents, letters, drawings, and notes.",
    },
    "unesco-archive": {
        "title": "UNESCO Memory of the World — Nikola Tesla Archive nomination",
        "url": "https://media.unesco.org/sites/default/files/webform/mow001/serbia_nikola_tesla_archive.pdf",
        "note": "Why the archive matters historically, with scale and preservation context.",
    },
    "my-inventions": {
        "title": "My Inventions — Nikola Tesla's autobiography",
        "url": "https://en.wikisource.org/wiki/My_Inventions",
        "note": "Tesla's 1919 autobiographical series; primary source, but still self-presenting.",
    },
    "martin-book": {
        "title": "The Inventions, Researches and Writings of Nikola Tesla — Project Gutenberg",
        "url": "https://archive.org/details/inventionsresear0000mart",
        "note": "Thomas Commerford Martin's 1894 compilation of Tesla lectures, patents, and early work.",
    },
    "high-frequency-book": {
        "title": "Experiments with Alternate Currents of High Potential and High Frequency — Project Gutenberg",
        "url": "https://archive.org/details/experimentswitha13476gut",
        "note": "Tesla's high-frequency lecture material; essential for coils, light, and spectacle.",
    },
    "human-energy": {
        "title": "The Problem of Increasing Human Energy — Tesla Science Center PDF",
        "url": "https://teslauniverse.com/nikola-tesla/articles/problem-increasing-human-energy",
        "note": "Tesla's 1900 philosophical-technical essay on energy, civilization, and invention.",
    },
    "world-system": {
        "title": "Tesla's World System of Wireless — Tesla Universe",
        "url": "https://teslauniverse.com/nikola-tesla/articles/teslas-dream-world-system-wireless-part-1",
        "note": "Gateway for Tesla's wireless-world claims and their later interpretation.",
    },
    "tesla-articles": {
        "title": "Tesla Universe — articles by and about Nikola Tesla",
        "url": "https://teslauniverse.com/nikola-tesla/articles",
        "note": "Useful index for newspaper and magazine material; cross-check dates and provenance.",
    },
    "patents-lab": {
        "title": "Tesla Universe — Nikola Tesla patents",
        "url": "https://teslauniverse.com/nikola-tesla/patents",
        "note": "Patent index; use to inspect claims, drawings, and filing chronology.",
    },
    "patents-universe": {
        "title": "Tesla Universe — Nikola Tesla patents",
        "url": "https://teslauniverse.com/nikola-tesla/patents",
        "note": "Readable patent pages with context and images.",
    },
    "patent-416191": {
        "title": "US416191A — Electro-Magnetic Motor",
        "url": "https://patents.google.com/patent/US416191",
        "note": "Core induction-motor patent; read the claims slowly.",
    },
    "patent-416194": {
        "title": "US416194 — Electric Motor — Tesla Universe",
        "url": "https://teslauniverse.com/nikola-tesla/patents/us-patent-416194-electric-motor",
        "note": "Another key AC motor patent; compare with 416191.",
    },
    "colorado-notes": {
        "title": "Colorado Springs Notes, 1899-1900 — Internet Archive",
        "url": "https://archive.org/details/nikolateslacolor0000niko",
        "note": "Research diary from the Colorado Springs period; technical and messy, not a pop biography.",
    },
    "smithsonian-papers": {
        "title": "Nikola Tesla papers — Smithsonian / Internet Archive",
        "url": "https://archive.org/details/nikolateslapape00tesl",
        "note": "Wardenclyffe-era papers and correspondence material.",
    },
    "wardenclyffe": {
        "title": "Wardenclyffe Tower — Wikipedia",
        "url": "https://en.wikipedia.org/wiki/Wardenclyffe_Tower",
        "note": "Site of Tesla's last standing laboratory; useful for Wardenclyffe context.",
    },
    "ethw": {
        "title": "Engineering and Technology History Wiki — Nikola Tesla",
        "url": "https://ethw.org/Nikola_Tesla",
        "note": "Engineering-history overview with chronology and technical emphasis.",
    },
    "rebus-history-tech": {
        "title": "History of Applied Science and Technology — Nikola Tesla",
        "url": "https://ethw.org/Nikola_Tesla",
        "note": "Open textbook chapter; good for a clean first-pass narrative.",
    },
    "magnet-academy": {
        "title": "National MagLab Magnet Academy — Nikola Tesla",
        "url": "https://nationalmaglab.org/magnet-academy/history-of-electricity-magnetism/pioneers/nikola-tesla/",
        "note": "Accessible electricity-and-magnetism framing.",
    },
    "doe-currents": {
        "title": "U.S. Department of Energy — War of the Currents",
        "url": "https://www.energy.gov/articles/war-currents-ac-vs-dc-power",
        "note": "Concise government explainer on AC vs DC and the current war.",
    },
    "pbs": {
        "title": "PBS American Experience — Tesla",
        "url": "https://www.pbs.org/video/american-experience-tesla/",
        "note": "Documentary overview; useful after primary-source orientation, not before.",
    },
    "carlson": {
        "title": "W. Bernard Carlson — Tesla: Inventor of the Electrical Age",
        "url": "https://press.princeton.edu/books/paperback/9780691165615/tesla",
        "note": "Best serious modern biography to anchor the whole track.",
    },
    "cheney": {
        "title": "Margaret Cheney — Tesla: Man Out of Time",
        "url": "https://books.google.com/books/about/Tesla.html?id=HIuK7iLO9zgC",
        "note": "Readable biography; good for personality, relationships, and narrative texture.",
    },
    "seifer": {
        "title": "Marc J. Seifer — Wizard: The Life and Times of Nikola Tesla",
        "url": "https://books.google.com/books/about/Wizard.html?id=DzMR8x_rbPgC",
        "note": "Large biography with archival ambition; useful, but verify big claims.",
    },
    "munson": {
        "title": "Richard Munson — Tesla: Inventor of the Modern",
        "url": "https://www.richardmunson.com/book/tesla",
        "note": "Modern sympathetic biography; good for broad narrative and impact.",
    },
    "jonnes": {
        "title": "Jill Jonnes — Empires of Light",
        "url": "https://www.penguinrandomhouse.com/books/88630/empires-of-light-by-jill-jonnes/",
        "note": "Context for Edison, Westinghouse, Tesla, and the electrification battle.",
    },
    "oneill": {
        "title": "John J. O'Neill — Prodigal Genius — HathiTrust",
        "url": "https://rastko.rs/istorija/tesla/oniell-tesla.html",
        "note": "Early biography by a journalist who knew Tesla; valuable but myth-amplifying.",
    },
}

TESLA_CORE_SOURCES: list[Source] = list(TESLA_RESOURCE_CATALOG.values())


def source_links_html(keys: list[str]) -> str:
    items: list[str] = []
    for key in keys:
        src = TESLA_RESOURCE_CATALOG[key]
        title = html_lib.escape(src["title"])
        url = html_lib.escape(src["url"], quote=True)
        note = html_lib.escape(src.get("note", ""))
        tail = f" — {note}" if note else ""
        items.append(f"<li><a href='{url}' target='_blank' rel='noopener'>{title}</a>{tail}</li>")
    return "<ul>" + "".join(items) + "</ul>"


TESLA_TOPICS: list[dict[str, Any]] = [
    {"title": "Source Map and Myth Filter", "level": "orientation", "focus": "building a source-backed Tesla dossier instead of memorizing internet mythology", "context": "Tesla is both a documented inventor and a myth magnet. Start by separating primary sources, serious biographies, patents, museum archives, and later folklore.", "model": "source triangulation", "links": ["my-inventions", "martin-book", "carlson", "museum-archive", "patents-lab"]},
    {"title": "Books and Biography Reading Order", "level": "orientation", "focus": "choosing which books answer which Tesla questions", "context": "No single Tesla book is enough. Serious learning needs one technical biography, one narrative biography, one electrification-context book, and direct primary sources.", "model": "bibliography as a toolchain", "links": ["carlson", "cheney", "seifer", "munson", "jonnes", "oneill"]},
    {"title": "Smiljan Origins and Family Formation", "level": "life", "focus": "understanding the family, frontier, religious, and linguistic world that shaped Tesla", "context": "Tesla was born in 1856 in Smiljan, then in the Austrian Empire. His Serbian Orthodox family, brilliant mother, disciplined father, and borderland upbringing mattered.", "model": "early environment and talent formation", "links": ["my-inventions", "carlson", "museum-home"]},
    {"title": "Memory, Visualization, and Inner Models", "level": "mind", "focus": "Tesla's claimed ability to visualize machines before building them", "context": "Tesla repeatedly described intense visual imagination, memory, and mental simulation. Treat this as a cognitive method to analyze, not as magic.", "model": "mental prototyping", "links": ["my-inventions", "carlson", "cheney"]},
    {"title": "Graz, Prague, and Self-Education", "level": "formation", "focus": "tracking Tesla's formal and informal technical education", "context": "Tesla studied engineering and physics but did not complete a degree. The important question is what he actually learned, practiced, and failed to institutionalize.", "model": "self-directed technical apprenticeship", "links": ["ethw", "my-inventions", "carlson"]},
    {"title": "Budapest Insight: Rotating Field Seed", "level": "formation", "focus": "how the rotating magnetic field idea emerged before the famous AC patents", "context": "Tesla later placed a decisive conceptual breakthrough in Budapest. Whether embellished or exact, the episode points to the central model behind his AC system.", "model": "conceptual incubation", "links": ["my-inventions", "carlson", "magnet-academy"], "extra_prerequisites": ["physics-magnetic-fields-and-forces"]},
    {"title": "Paris and Continental Edison Apprenticeship", "level": "career", "focus": "learning practical electrical systems before inventing against them", "context": "Tesla's Continental Edison work gave him exposure to dynamos, lighting, troubleshooting, and engineering practice in Europe.", "model": "apprenticeship before originality", "links": ["ethw", "carlson", "rebus-history-tech"]},
    {"title": "New York Arrival and Edison Machine Works", "level": "career", "focus": "understanding Tesla's first American opportunity and its limits", "context": "Tesla arrived in the United States in 1884 and briefly worked for Edison. The episode is less cartoon rivalry than a clash of systems, incentives, and temperaments.", "model": "institutional mismatch", "links": ["carlson", "jonnes", "ethw"]},
    {"title": "Arc Lighting, Betrayal, and First Company", "level": "career", "focus": "how Tesla learned that invention without control can still lose", "context": "Tesla's early arc-lighting company experience exposed the difference between solving technical problems and owning the business outcome.", "model": "technical success versus equity/control", "links": ["carlson", "cheney", "oneill"]},
    {"title": "The Rotating Magnetic Field", "level": "technical", "focus": "seeing how phase-shifted currents create moving magnetic structure", "context": "The rotating magnetic field is the conceptual heart of Tesla's AC motor work: currents out of phase can make the magnetic field rotate without mechanical commutation.", "model": "field geometry", "links": ["patent-416191", "martin-book", "magnet-academy"], "extra_prerequisites": ["physics-magnetic-fields-and-forces", "physics-electromagnetic-induction"]},
    {"title": "Polyphase AC Theory", "level": "technical", "focus": "understanding why multiple alternating phases changed power engineering", "context": "Polyphase AC made it possible to transmit power efficiently, create rotating fields, and build motors suited to industrial loads.", "model": "phase relationships as infrastructure", "links": ["martin-book", "patent-416191", "doe-currents"], "extra_prerequisites": ["physics-electric-potential-and-voltage", "physics-current-resistance-and-ohm-s-law"]},
    {"title": "Induction Motor Patent 416191", "level": "technical", "focus": "reading the claims and diagrams of a core Tesla motor patent", "context": "US416191A is not just trivia. It lets you see Tesla's invention in legal-technical form: claims, coils, armature, circuits, and the protected idea.", "model": "patent-claim reading", "links": ["patent-416191", "patent-416194", "patents-universe"]},
    {"title": "AC Patents as a System", "level": "technical", "focus": "connecting motors, generators, transformers, transmission, and control into a system", "context": "Tesla's AC contribution was not a single gadget. It was a cluster of patents that fit together as a power architecture.", "model": "invention portfolio", "links": ["patents-lab", "martin-book", "carlson"]},
    {"title": "Westinghouse Deal and Strategic Fit", "level": "business", "focus": "why Tesla needed Westinghouse and Westinghouse needed Tesla", "context": "Westinghouse had industrial capacity, capital, and a strategic need for AC motor technology. Tesla had the patent position and conceptual breakthrough.", "model": "complementary assets", "links": ["carlson", "jonnes", "doe-currents"]},
    {"title": "War of Currents", "level": "history", "focus": "separating AC/DC physics from propaganda, standards, and business competition", "context": "The current war involved safety claims, capital investment, patents, public fear, Edison interests, Westinghouse strategy, and the real engineering advantages of AC transmission.", "model": "technology adoption under conflict", "links": ["doe-currents", "jonnes", "pbs"]},
    {"title": "Chicago World's Columbian Exposition", "level": "history", "focus": "how public demonstration turned AC into spectacle and legitimacy", "context": "The 1893 Chicago fair helped make AC visible as a modern public system, not merely a technical argument among engineers.", "model": "demonstration as persuasion", "links": ["jonnes", "pbs", "carlson"]},
    {"title": "Niagara Falls Power Plant", "level": "history", "focus": "why Niagara became the proof point for large-scale AC power", "context": "Niagara connected natural energy, industrial ambition, Westinghouse engineering, and Tesla's AC system into a symbol of electrified modernity.", "model": "infrastructure proof", "links": ["carlson", "jonnes", "rebus-history-tech"]},
    {"title": "AC Grid Architecture and Transformer Logic", "level": "technical", "focus": "understanding why AC scales across distance better than early DC systems", "context": "The deep win was system architecture: transform voltage up for transmission, down for use, and make motors compatible with the same alternating system.", "model": "system-level engineering", "links": ["doe-currents", "magnet-academy", "martin-book"], "extra_prerequisites": ["physics-electric-potential-and-voltage", "physics-dc-circuit-analysis"]},
    {"title": "High-Frequency Currents", "level": "technical", "focus": "why Tesla moved from power frequency to high-frequency phenomena", "context": "Tesla's high-frequency work opened new effects in lighting, insulation, transformers, wireless experiments, and public demonstrations.", "model": "frequency as design dimension", "links": ["high-frequency-book", "martin-book", "tesla-articles"], "extra_prerequisites": ["physics-wave-properties"]},
    {"title": "Tesla Coil and Resonance", "level": "technical", "focus": "understanding resonant transformers without treating sparks as magic", "context": "The Tesla coil is a resonant transformer system. Its spectacle can distract from the engineering: inductance, capacitance, coupling, insulation, oscillation, and tuning.", "model": "resonant energy transfer", "links": ["high-frequency-book", "martin-book", "colorado-notes"], "extra_prerequisites": ["physics-electromagnetic-induction", "physics-wave-properties"]},
    {"title": "Public Lectures as Technical Theater", "level": "communication", "focus": "how Tesla used lectures, danger, and spectacle to teach and persuade", "context": "Tesla's lectures were technical arguments staged as wonder. They won attention, investors, and reputation, but also encouraged mythologizing.", "model": "demo-driven persuasion", "links": ["high-frequency-book", "martin-book", "pbs"]},
    {"title": "Fluorescent and Gas-Discharge Lighting", "level": "technical", "focus": "placing Tesla's lighting experiments inside the search for efficient illumination", "context": "Tesla explored high-frequency lighting, evacuated tubes, and wireless illumination effects. Some were practical steps; others were demonstrations of phenomena.", "model": "experimental illumination", "links": ["high-frequency-book", "martin-book", "tesla-articles"]},
    {"title": "X-Rays, Radiant Energy, and Experimental Risk", "level": "technical", "focus": "studying Tesla's radiant-matter and X-ray-adjacent work with caution", "context": "Tesla experimented with high-voltage tubes and radiant effects near the early history of X-rays. The lesson is curiosity plus the hazards of poorly understood phenomena.", "model": "frontier experimentation", "links": ["martin-book", "tesla-articles", "carlson"]},
    {"title": "Remote-Control Boat and Teleautomation", "level": "technical", "focus": "why the 1898 radio-controlled boat mattered for robotics and control", "context": "Tesla's remote-control boat demonstrated wireless command, control logic, and the idea of machines acting at a distance under encoded instruction.", "model": "control at a distance", "links": ["patents-lab", "carlson", "rebus-history-tech"]},
    {"title": "Radio: Oscillation, Tuning, and Priority", "level": "technical-history", "focus": "understanding Tesla's real radio contributions without collapsing the story into hero worship", "context": "Radio emerged from many contributors. Tesla's oscillators, tuning ideas, and patents matter, but priority requires precise claims and dates.", "model": "multi-inventor priority", "links": ["patents-lab", "carlson", "tesla-articles"]},
    {"title": "Wireless Signaling Patents", "level": "technical", "focus": "reading Tesla's wireless patents as communication systems", "context": "Wireless patents are where technical imagination, legal claims, and later priority disputes meet. Read them as specific architectures, not slogans.", "model": "communication-system claims", "links": ["patents-universe", "patents-lab", "world-system"]},
    {"title": "Colorado Springs Laboratory", "level": "research", "focus": "what Tesla was actually testing in Colorado Springs", "context": "In 1899 Tesla built a remote experimental station to study high voltage, large coils, resonance, propagation, and atmospheric/electrical phenomena.", "model": "research station as instrument", "links": ["colorado-notes", "carlson", "high-frequency-book"]},
    {"title": "Earth Resonance and Stationary Waves", "level": "research", "focus": "separating Tesla's earth-conduction claims from what his apparatus showed", "context": "Tesla believed he could use the Earth and atmosphere in a global electrical system. The exact claims must be checked against notes, measurements, and later physics.", "model": "hypothesis versus measurement", "links": ["colorado-notes", "world-system", "carlson"], "extra_prerequisites": ["physics-wave-properties"]},
    {"title": "The Problem of Increasing Human Energy", "level": "philosophy", "focus": "reading Tesla's grand theory of civilization, energy, and human progress", "context": "Tesla's 1900 essay blends engineering, social philosophy, energy thinking, and speculation. It reveals his ambition and where his thinking outran evidence.", "model": "civilizational energy lens", "links": ["human-energy", "tesla-articles", "carlson"]},
    {"title": "World Wireless System", "level": "systems", "focus": "understanding Tesla's plan for global wireless communication and energy", "context": "The World Wireless System proposed global transmission of signals and possibly energy through coordinated stations and tuned receivers.", "model": "global system architecture", "links": ["world-system", "smithsonian-papers", "wardenclyffe"]},
    {"title": "Wardenclyffe Financing and Morgan", "level": "business", "focus": "why the tower was not just an engineering project", "context": "Wardenclyffe required capital, trust, secrecy choices, clear deliverables, and a changing communications market. J. P. Morgan's support was finite.", "model": "capital allocation under uncertainty", "links": ["wardenclyffe", "smithsonian-papers", "carlson"]},
    {"title": "Wardenclyffe Technical Reality Check", "level": "systems", "focus": "separating the buildable parts of Wardenclyffe from the speculative parts", "context": "Wardenclyffe mixed plausible wireless communication infrastructure with more speculative wireless-power ambitions and unclear economics.", "model": "feasibility decomposition", "links": ["wardenclyffe", "world-system", "carlson"]},
    {"title": "Wireless Power: What Worked, What Did Not", "level": "technical", "focus": "learning the physics and limits of Tesla's wireless-power dreams", "context": "Wireless energy transfer exists, but global free power is not the same claim. Study near-field coupling, radiation, losses, tuning, safety, and economics.", "model": "physical constraints and loss budgets", "links": ["high-frequency-book", "colorado-notes", "carlson"], "extra_prerequisites": ["physics-electromagnetic-induction", "physics-wave-properties"]},
    {"title": "Turbine and Boundary-Layer Engineering", "level": "technical", "focus": "understanding Tesla's bladeless turbine as fluid mechanics and product strategy", "context": "Tesla's turbine used boundary-layer adhesion rather than conventional blades. It was elegant, but practical success depends on materials, loads, efficiency, and manufacturing.", "model": "elegant mechanism versus industrial fit", "links": ["patents-lab", "carlson", "munson"]},
    {"title": "Mechanical Oscillator and Resonance Myths", "level": "technical", "focus": "using resonance to separate real devices from earthquake folklore", "context": "Tesla's mechanical oscillator stories are famous. The learning target is resonance, feedback, structure, and why dramatic anecdotes need evidence.", "model": "resonance plus source criticism", "links": ["carlson", "cheney", "patents-lab"]},
    {"title": "Patents, Secrecy, and IP Strategy", "level": "business", "focus": "what Tesla protected, disclosed, sold, and failed to monetize", "context": "Tesla's career is a clinic in the difference between having ideas, owning claims, defending claims, and converting claims into durable income.", "model": "IP as strategy, not trophy", "links": ["patents-lab", "patents-universe", "carlson"]},
    {"title": "Business Partners, Investors, and Negotiation Failures", "level": "business", "focus": "mapping Tesla's pattern with financiers, managers, and collaborators", "context": "Tesla repeatedly needed partners for manufacturing, capital, and distribution. His strengths in invention did not always translate into deal design.", "model": "complementary-skill dependence", "links": ["carlson", "cheney", "munson"]},
    {"title": "Edison, Westinghouse, and Marconi: Rivalry and Credit", "level": "history", "focus": "learning how credit is assigned in multi-person technological revolutions", "context": "Tesla's rivals and partners were not cartoon villains. Edison, Westinghouse, Marconi, and Tesla each occupied different parts of invention, business, systems, and publicity.", "model": "credit allocation in ecosystems", "links": ["jonnes", "carlson", "pbs"]},
    {"title": "Press, Performance, and Mythmaking", "level": "culture", "focus": "understanding how Tesla became a media figure", "context": "Tesla used the press and was used by it. Spectacle produced opportunity, but also made later exaggeration easier.", "model": "attention as both asset and liability", "links": ["tesla-articles", "cheney", "oneill"]},
    {"title": "Work Habits, Visualization, and Solitude", "level": "mind", "focus": "extracting useful creative discipline without copying destructive extremes", "context": "Tesla's routines, intensity, and solitude are inspiring and dangerous. Learn the transferable parts without worshiping dysfunction.", "model": "creative process audit", "links": ["my-inventions", "cheney", "carlson"]},
    {"title": "Health, Obsession, and Human Cost", "level": "life", "focus": "studying the psychological and bodily cost of relentless invention", "context": "Tesla's story includes illness, compulsion, sensory sensitivity, isolation, and financial instability. Greatness did not make him invulnerable.", "model": "sustainable genius check", "links": ["cheney", "carlson", "munson"]},
    {"title": "Later Years: Radar Hints and Beam Weapon Claims", "level": "late-career", "focus": "evaluating late Tesla claims with evidence discipline", "context": "Tesla's later statements about detection systems, directed energy, and defense weapons mix foresight, ambiguity, and publicity. Treat them claim-by-claim.", "model": "extraordinary-claim review", "links": ["tesla-articles", "carlson", "seifer"]},
    {"title": "Pigeons, Hotels, and Decline", "level": "late-life", "focus": "seeing the human being beneath the icon", "context": "Tesla's final decades included hotel living, financial dependency, pigeons, press interviews, and fading institutional support.", "model": "biography without humiliation", "links": ["cheney", "carlson", "oneill"]},
    {"title": "Death, Estate, and Archive", "level": "archive", "focus": "tracking what happened to Tesla's papers after 1943", "context": "Tesla died in 1943. His papers, estate, government interest, and eventual archive history created another layer of myth and documentation.", "model": "archive provenance", "links": ["museum-archive", "museum-repository", "unesco-archive"]},
    {"title": "Tesla Museum and UNESCO Memory of the World", "level": "archive", "focus": "using the official archive as a learning instrument", "context": "The Nikola Tesla Museum preserves original documents, photographs, plans, books, journals, and artifacts. Serious Tesla study eventually returns to the archive.", "model": "archive-grounded mastery", "links": ["museum-home", "museum-archive", "museum-repository", "unesco-archive"]},
    {"title": "Myths: Free Energy, Death Rays, and Internet Tesla", "level": "myth-filter", "focus": "learning to love Tesla without believing every Tesla meme", "context": "Tesla attracts free-energy mythology, conspiracy claims, and simplified hero stories. Respect requires better standards, not less admiration.", "model": "admiration with epistemic hygiene", "links": ["carlson", "museum-archive", "tesla-articles"]},
    {"title": "What Tesla Actually Gave Modernity", "level": "synthesis", "focus": "identifying the durable contributions that survive myth filtering", "context": "Tesla's real legacy includes AC power systems, induction motors, high-frequency experimentation, radio-control concepts, and a model of systems imagination.", "model": "durable contribution map", "links": ["carlson", "magnet-academy", "rebus-history-tech"]},
    {"title": "How to Read Tesla's Patents", "level": "method", "focus": "turning patent documents into understandable engineering notes", "context": "Patents are not essays. Learn to read title, drawings, background, claims, embodiments, and what the patent does not prove.", "model": "patent literacy", "links": ["patents-lab", "patents-universe", "patent-416191"]},
    {"title": "Capstone: Build a Tesla Dossier", "level": "capstone", "focus": "wiring biography, physics, patents, books, archives, and judgment into one personal reference", "context": "The final task is not another fact. It is a structured Tesla dossier with timelines, source links, diagrams, myth checks, invention lessons, and open questions.", "model": "knowledge synthesis", "links": ["my-inventions", "carlson", "patents-lab", "museum-repository", "wardenclyffe"]},
]


def tesla_unit(topic: dict[str, Any], order: int, previous: str | None) -> Unit:
    title = str(topic["title"])
    unit_id = f"tesla-{slug(title)}"
    links = list(topic.get("links") or ["my-inventions", "carlson", "patents-lab"])
    source = TESLA_RESOURCE_CATALOG[links[0]]
    prereqs: list[str] = []
    if previous:
        prereqs.append(previous)
    for extra in topic.get("extra_prerequisites", []):
        if extra not in prereqs:
            prereqs.append(str(extra))
    focus = str(topic["focus"])
    context = str(topic["context"])
    model = str(topic["model"])
    level = str(topic.get("level", "core"))
    link_block = source_links_html(links)
    practice = f"Add one page to your Tesla dossier for '{title}': timeline anchor, 3 sourced facts, 1 diagram or model, 1 myth check, and 1 lesson for your own invention/building process."
    return {
        "id": unit_id,
        "title": title,
        "subtitle": f"{level}: {focus}",
        "summary": f"Learn {title} by connecting Tesla's life, inventions, sources, patents, and myths through {model}.",
        "kind": "substantial",
        "level": level,
        "order": order,
        "minutes": 35,
        "hero_article": "Nikola Tesla",
        "prerequisites": prereqs,
        "source": {"label": source["title"], "url": source["url"]},
        "objectives": [
            f"Explain {title} without relying on unsourced Tesla mythology.",
            f"Use {model} to connect the episode to Tesla's broader career.",
            "Name the strongest primary source, strongest secondary source, and biggest uncertainty.",
        ],
        "sections": [
            section("Source trail", f"<p>Start with the links below, then cross-check dates, claims, and incentives. Do not let a viral Tesla quote outrank a patent, archive item, or serious biography.</p>{link_block}"),
            section("Core storyline", f"<p>{html_lib.escape(context)}</p><p>Place this unit on Tesla's timeline and ask what had to be true technically, financially, and socially for the episode to matter.</p>"),
            section("Technical or strategic mechanism", f"<p>The working focus is <b>{html_lib.escape(focus)}</b>. Rebuild it as a mechanism: inputs, constraints, feedback loops, physical laws, people, capital, and outputs.</p>"),
            section("Model to keep", f"<p>Use <b>{html_lib.escape(model)}</b> as the durable mental model. Tesla is valuable only if you can convert admiration into a reusable way of seeing inventions, systems, and risk.</p>"),
            section("Myth and uncertainty check", f"<p>Ask what the sources actually prove, what Tesla claimed, what later admirers added, and what a skeptical engineer or historian would still dispute.</p>"),
            section("Dossier task", f"<p>{html_lib.escape(practice)}</p>"),
        ],
        "ideas": [
            ("Primary-source spine", "Anchor Tesla study in autobiography, patents, lectures, archive records, and serious biographies."),
            ("Mechanism over myth", f"For this unit, the mechanism is: {model}."),
            ("System imagination", "Tesla's strongest pattern was seeing whole technical systems, not just isolated gadgets."),
            ("Caution label", "Admiration is allowed; unsourced claims are not."),
        ],
        "thinking_questions": [
            f"What is the strongest sourced fact about {title}, and where did it come from?",
            f"What claim about {title} would you refuse to believe without a primary source?",
            "Which part is physics, which part is business, and which part is public narrative?",
            "What would Edison, Westinghouse, Morgan, or Marconi say against Tesla's version of the story?",
            f"How does {model} change the way you think about invention today?",
            "What diagram, timeline, or table would make this unit easier to remember?",
            "What is one thing Tesla got deeply right here, and one thing he may have overestimated?",
        ],
        "practice_prompt": practice,
        "application_prompt": practice,
        "review_prompts": [
            "Recall the timeline position and the main technical or strategic mechanism.",
            "Name one primary source and one secondary source from memory.",
            "State the myth check in one sentence.",
        ],
        "did_you_know": "The serious Tesla path is less about memorizing lightning stories and more about reading patents, lectures, notebooks, financing decisions, and failed systems together.",
        "sources": [TESLA_RESOURCE_CATALOG[k] for k in links],
    }


def build_tesla_units() -> list[Unit]:
    units: list[Unit] = []
    previous: str | None = None
    for order, topic in enumerate(TESLA_TOPICS, start=1):
        unit = tesla_unit(topic, order, previous)
        units.append(unit)
        previous = unit["id"]
    return units


CAESAR_RESOURCE_CATALOG: dict[str, Source] = {
    "mit-ocw-syllabus": {
        "title": "MIT OCW — Julius Caesar and the Fall of the Roman Republic syllabus",
        "url": "https://ocw.mit.edu/courses/21h-331-julius-caesar-and-the-fall-of-the-roman-republic-spring-2016/pages/syllabus/",
        "note": "University course frame for Caesar inside the collapse of the late Republic.",
    },
    "mit-ocw-readings": {
        "title": "MIT OCW — Julius Caesar course readings",
        "url": "https://ocw.mit.edu/courses/21h-331-julius-caesar-and-the-fall-of-the-roman-republic-spring-2016/pages/readings/",
        "note": "Reading list for primary and secondary material on Caesar and the Republic.",
    },
    "gutenberg-commentaries": {
        "title": "Internet Archive — Caesar Commentaries on the Gallic and Civil Wars",
        "url": "https://archive.org/details/caesarscommentar00caesrich",
        "note": "Public-domain English translation of Caesar's Gallic, Civil, Alexandrian, African, and Spanish war commentaries.",
    },
    "perseus-gallic": {
        "title": "Perseus — Caesar, Gallic War",
        "url": "https://www.perseus.tufts.edu/hopper/text?doc=Perseus%3Aabo%3Aphi%2C0448%2C001%3A1",
        "note": "Chunked classical text for close reading and citation.",
    },
    "mit-civil-war": {
        "title": "Internet Classics Archive — Caesar, The Civil Wars",
        "url": "https://classics.mit.edu/Caesar/civil.1.1.html",
        "note": "Caesar's Civil War narrative in accessible web form.",
    },
    "latin-commentaries": {
        "title": "Project Gutenberg — Caesar's Commentaries in Latin",
        "url": "https://www.gutenberg.org/files/218/218-h/218-h.htm",
        "note": "Latin text for original-language checks and famous phrases.",
    },
    "plutarch-caesar": {
        "title": "Perseus — Plutarch, Life of Caesar",
        "url": "http://www.perseus.tufts.edu/hopper/text?doc=Perseus%3Atext%3A1999.03.0078%3Atext%3DCaes.",
        "note": "Greek biographical tradition; moral portrait and narrative drama.",
    },
    "suetonius-caesar": {
        "title": "LacusCurtius — Suetonius, Life of Julius Caesar",
        "url": "http://penelope.uchicago.edu/Thayer/E/Roman/Texts/Suetonius/12Caesars/Julius*.html",
        "note": "Roman imperial biography; anecdotes, omens, public image, assassination details.",
    },
    "gutenberg-suetonius": {
        "title": "Project Gutenberg — Suetonius, Julius Caesar",
        "url": "https://www.gutenberg.org/cache/epub/6386/pg6386.html",
        "note": "Alternative public-domain Suetonius text.",
    },
    "appian-civil-wars": {
        "title": "LacusCurtius — Appian, Civil Wars Book II",
        "url": "http://penelope.uchicago.edu/Thayer/e/roman/texts/appian/civil_wars/2*.html",
        "note": "Civil-war narrative from a later Greek historian; essential for the wider crisis.",
    },
    "dio-book-44": {
        "title": "LacusCurtius — Cassius Dio, Roman History Book 44",
        "url": "https://penelope.uchicago.edu/Thayer/e/roman/texts/cassius_dio/44*.html",
        "note": "Later senatorial-imperial account of dictatorship, honors, conspiracy, and assassination.",
    },
    "cicero-letters": {
        "title": "Fordham Sourcebook — Cicero letters",
        "url": "https://sourcebooks.web.fordham.edu/ancient/cicero-letters.asp",
        "note": "Cicero's correspondence gives hostile, anxious, elite contemporary texture.",
    },
    "perseus-cicero-59": {
        "title": "Perseus — Cicero letters, year 59 BCE",
        "url": "http://www.perseus.tufts.edu/hopper/text?doc=Perseus%3Atext%3A1999.02.0022%3Ayear%3D59",
        "note": "Cicero around Caesar's first consulship and the triumviral settlement.",
    },
    "sallust-catilina": {
        "title": "Project Gutenberg — Sallust, Catiline",
        "url": "https://www.gutenberg.org/cache/epub/7990/pg7990.html",
        "note": "Late-Republic moral and political crisis background.",
    },
    "fordham-ancient": {
        "title": "Fordham Internet Ancient History Sourcebook — Rome",
        "url": "https://sourcebooks.web.fordham.edu/ancient/asbook09.asp",
        "note": "Gateway to ancient Roman primary sources and context.",
    },
    "livius-caesar": {
        "title": "Livius — Gaius Julius Caesar",
        "url": "https://www.livius.org/articles/person/caesar/",
        "note": "Readable modern reference with chronology and source discussion.",
    },
    "world-history-caesar": {
        "title": "World History Encyclopedia — Julius Caesar",
        "url": "https://www.worldhistory.org/Julius_Caesar/",
        "note": "Accessible overview; useful as a first map, not as final authority.",
    },
    "goldsworthy": {
        "title": "Adrian Goldsworthy — Caesar: Life of a Colossus",
        "url": "https://yalebooks.yale.edu/book/9780300126891/caesar/",
        "note": "Best all-around modern biography for serious readers.",
    },
    "gelzer": {
        "title": "Matthias Gelzer — Caesar: Politician and Statesman",
        "url": "https://www.hup.harvard.edu/books/9780674090019",
        "note": "Classic scholarly biography focused on Roman aristocratic politics.",
    },
    "meier": {
        "title": "Christian Meier — Caesar",
        "url": "https://www.hachettebookgroup.com/titles/christian-meier/caesar/9780465008957/",
        "note": "Dense biography strong on politics, contingency, and historical interpretation.",
    },
    "canfora": {
        "title": "Luciano Canfora — Julius Caesar: The People's Dictator",
        "url": "https://www.cambridge.org/core/journals/classical-review/article/abs/caesar-ra-billows-julius-caesar-the-colossus-of-rome-pp-xxii-312-maps-london-and-new-york-routledge-2009-cased-60-us120-isbn-9780415333146-paper-1999-us3495-isbn-9780415692601-m-gelzer-caesar-der-politiker-und-staatsmann-new-edition-pp-xxiv-310-map-stuttgart-franz-steiner-2008-paper-36-isbn-9783515091121-l-canfora-julius-caesar-the-peoples-dictator-translated-by-marian-hill-and-kevin-windle-pp-xvi-392-map-edinburgh-edinburgh-university-press-2007-first-published-as-giulio-cesare-il-dittatore-democratico-1999-cased-2499-isbn-9780748619368/8410A795E4E589FA2C26C76C21769A8A",
        "note": "Provocative Caesar-as-popular-leader interpretation; read against Gelzer and Meier.",
    },
    "holland-rubicon": {
        "title": "Tom Holland — Rubicon",
        "url": "https://www.penguinrandomhouse.com/books/288747/rubicon-by-tom-holland/",
        "note": "Narrative history of the late Republic; vivid context, not Caesar-only.",
    },
    "beard-spqr": {
        "title": "Mary Beard — SPQR",
        "url": "https://wwnorton.com/books/9780871404237",
        "note": "Broad Roman history with skeptical, modern framing of power, myth, and citizenship.",
    },
    "syme": {
        "title": "Ronald Syme — The Roman Revolution",
        "url": "https://global.oup.com/academic/product/the-roman-revolution-9780192803207",
        "note": "Classic analysis of elite power, revolution, and the Augustan settlement after Caesar.",
    },
    "cambridge-caesar-people": {
        "title": "Robert Morstein-Marx — Julius Caesar and the Roman People",
        "url": "https://www.cambridge.org/core/books/julius-caesar-and-the-roman-people/C8F2794563855533F26261F3DE54C91C",
        "note": "Recent challenge to the simple aspiring-autocrat story; useful for argument discipline.",
    },
}

CAESAR_CORE_SOURCES: list[Source] = list(CAESAR_RESOURCE_CATALOG.values())


def caesar_source_links_html(keys: list[str]) -> str:
    items: list[str] = []
    for key in keys:
        src = CAESAR_RESOURCE_CATALOG[key]
        title = html_lib.escape(src["title"])
        url = html_lib.escape(src["url"], quote=True)
        note = html_lib.escape(src.get("note", ""))
        tail = f" — {note}" if note else ""
        items.append(f"<li><a href='{url}' target='_blank' rel='noopener'>{title}</a>{tail}</li>")
    return "<ul>" + "".join(items) + "</ul>"


CAESAR_TOPICS: list[dict[str, Any]] = [
    {"title": "Source Map and Myth Filter", "level": "orientation", "focus": "building a source-backed Caesar dossier instead of memorizing emperor memes", "context": "Caesar is everywhere: history, Shakespeare, strategy books, politics, empire, calendars, salad jokes, and internet strongman fantasies. Start by separating Caesar's own propaganda from hostile contemporaries, later biographers, modern historians, and myth.", "model": "source triangulation under propaganda", "links": ["gutenberg-commentaries", "plutarch-caesar", "suetonius-caesar", "appian-civil-wars", "goldsworthy"]},
    {"title": "Books and Reading Order", "level": "orientation", "focus": "choosing the right Caesar books for biography, politics, war, and late-Republic context", "context": "A serious Caesar path needs ancient sources, one modern anchor biography, one political biography, a late-Republic narrative, and a skeptical interpretation of Caesar's relationship with the Roman people.", "model": "bibliography as campaign plan", "links": ["goldsworthy", "gelzer", "meier", "holland-rubicon", "beard-spqr", "cambridge-caesar-people"]},
    {"title": "Roman Republic Machinery", "level": "foundations", "focus": "understanding magistracies, Senate, assemblies, patronage, provinces, and honor", "context": "Caesar cannot be understood as a lone genius dropped into Rome. He moved through a competitive aristocratic machine built from offices, family prestige, debts, armies, courts, crowds, and sacred tradition.", "model": "institutional game board", "links": ["mit-ocw-syllabus", "beard-spqr", "fordham-ancient"], "extra_prerequisites": ["history-roman-republic-mixed-constitution-and-expansion"]},
    {"title": "Family, Gens Julia, and Marian Legacy", "level": "life", "focus": "seeing how ancestry, marriage, and inherited faction shaped Caesar's options", "context": "Caesar's family claimed ancient prestige but not overwhelming wealth. His links to Marius and Cinna gave him symbolic capital and political danger after Sulla's victory.", "model": "family as political capital", "links": ["plutarch-caesar", "suetonius-caesar", "goldsworthy"]},
    {"title": "Sulla and the Lesson of Force", "level": "formation", "focus": "learning what Caesar saw when Rome's own politics became civil war", "context": "Sulla showed that a Roman commander could march on Rome, purge enemies, reform institutions, and retire. Caesar grew up in the shadow of that precedent.", "model": "precedent as temptation", "links": ["appian-civil-wars", "holland-rubicon", "beard-spqr"]},
    {"title": "Early Oratory and Public Ambition", "level": "formation", "focus": "tracking Caesar's public voice before he had armies", "context": "Before Gaul, Caesar built reputation through speech, prosecutions, ceremonies, generosity, and relentless visibility. Roman politics rewarded performance as much as policy.", "model": "visibility compounding", "links": ["plutarch-caesar", "suetonius-caesar", "gelzer"]},
    {"title": "Pirates, Ransom, and Audacity", "level": "life", "focus": "reading the pirate story as character evidence and literary construction", "context": "The famous pirate episode reveals Caesar's audacity, humor, vengeance, and later biographical mythmaking. Treat it as both possible event and crafted signal.", "model": "anecdote with a warning label", "links": ["plutarch-caesar", "suetonius-caesar", "goldsworthy"]},
    {"title": "Pontifex Maximus and Religious Power", "level": "politics", "focus": "why religious office mattered in a supposedly practical Roman career", "context": "Caesar's election as pontifex maximus gave prestige, residence, sacred authority, and public permanence. Religion and politics were not separate games in Rome.", "model": "symbolic office as hard power", "links": ["plutarch-caesar", "suetonius-caesar", "gelzer"]},
    {"title": "Catiline Crisis and Caesar's Risk", "level": "politics", "focus": "placing Caesar inside the 63 BCE emergency and Cicero's rise", "context": "The Catiline crisis exposed elite fear, emergency politics, and Caesar's willingness to take unpopular procedural positions while avoiding direct association with conspiracy.", "model": "crisis positioning", "links": ["sallust-catilina", "cicero-letters", "goldsworthy"]},
    {"title": "Debt, Games, and Aedileship", "level": "politics", "focus": "understanding spending as a Roman investment strategy", "context": "Caesar used massive public spending, games, and debts to buy reputation and future leverage. In Rome, financial risk could be political fuel.", "model": "debt as ambition leverage", "links": ["suetonius-caesar", "plutarch-caesar", "gelzer"]},
    {"title": "Spanish Governorship and First Command", "level": "career", "focus": "how provincial command converted ambition into money, military credibility, and momentum", "context": "Hispania gave Caesar administrative experience, military action, plunder, and a glimpse of Alexander-scale ambition.", "model": "province as launchpad", "links": ["plutarch-caesar", "suetonius-caesar", "goldsworthy"]},
    {"title": "First Triumvirate", "level": "power", "focus": "how Caesar, Pompey, and Crassus bypassed normal elite resistance", "context": "The so-called First Triumvirate was an informal alliance: Caesar's ambition, Pompey's veterans and prestige, Crassus's wealth, and mutual frustration with senatorial obstruction.", "model": "informal coalition against formal institutions", "links": ["perseus-cicero-59", "appian-civil-wars", "gelzer"]},
    {"title": "Consulship of 59 BCE", "level": "power", "focus": "studying Caesar's first consulship as legal force, crowd politics, and norm-breaking", "context": "Caesar's consulship pushed land legislation, secured political deals, and made enemies. His colleague Bibulus's obstruction became a symbol of broken republican process.", "model": "legalism under pressure", "links": ["perseus-cicero-59", "appian-civil-wars", "goldsworthy"]},
    {"title": "Commentaries as Political Weapon", "level": "method", "focus": "reading Caesar's prose as report, propaganda, and reputation management", "context": "Caesar's Commentaries look plain and factual, but their simplicity is part of the weapon. They present speed, rationality, necessity, and controlled violence in Caesar's own frame.", "model": "narrative control", "links": ["gutenberg-commentaries", "perseus-gallic", "latin-commentaries"]},
    {"title": "Gaul Before Caesar", "level": "war", "focus": "understanding the political geography Caesar entered and then transformed", "context": "Gaul was not an empty stage for Roman genius. It contained tribes, alliances, rivalries, migration pressures, trade, elites, and internal politics Caesar exploited.", "model": "operational map before campaign", "links": ["gutenberg-commentaries", "perseus-gallic", "livius-caesar"]},
    {"title": "Helvetii Campaign", "level": "war", "focus": "studying Caesar's opening campaign as crisis framing and legitimacy creation", "context": "The Helvetii migration gave Caesar a security problem, a narrative opening, and a chance to show decisive command early in Gaul.", "model": "first move creates mandate", "links": ["perseus-gallic", "gutenberg-commentaries", "goldsworthy"]},
    {"title": "Ariovistus and the German Threat", "level": "war", "focus": "how Caesar framed intervention against a dangerous external power", "context": "Ariovistus let Caesar present himself as protector, strategist, and frontier commander. Fear, diplomacy, and morale mattered as much as battle.", "model": "threat framing", "links": ["perseus-gallic", "gutenberg-commentaries", "goldsworthy"]},
    {"title": "Belgae Campaign", "level": "war", "focus": "seeing coalition warfare, intelligence, and rapid response under pressure", "context": "Caesar describes the Belgae as especially formidable. The campaign tests Roman intelligence, alliance management, and tactical recovery.", "model": "coalition disruption", "links": ["perseus-gallic", "gutenberg-commentaries", "goldsworthy"]},
    {"title": "Logistics, Roads, Bridges, and Camps", "level": "war", "focus": "learning the engineering underside of Roman victory", "context": "Caesar's army won through marches, camps, supply, fortification, bridges, intelligence, and discipline before dramatic battle narratives began.", "model": "logistics as hidden strategy", "links": ["gutenberg-commentaries", "goldsworthy", "mit-ocw-readings"]},
    {"title": "Rhine Bridge", "level": "war", "focus": "reading engineering as psychological warfare", "context": "Caesar's Rhine bridge was a military crossing, an engineering feat, and a message: Rome could cross boundaries others treated as natural limits.", "model": "demonstration of reach", "links": ["perseus-gallic", "gutenberg-commentaries", "goldsworthy"]},
    {"title": "Britain Expeditions", "level": "war", "focus": "studying reconnaissance, prestige, and limits at the edge of known Roman power", "context": "Caesar's Britain expeditions produced limited conquest but enormous symbolic capital. Not every operation needs permanent occupation to change reputation.", "model": "prestige raid versus strategic depth", "links": ["perseus-gallic", "gutenberg-commentaries", "livius-caesar"]},
    {"title": "Vercingetorix and Gallic Revolt", "level": "war", "focus": "understanding the opponent who forced Caesar into his hardest Gallic test", "context": "Vercingetorix coordinated resistance, scorched-earth strategy, and fortified positions. Caesar's greatness is clearer when the enemy is not reduced to a prop.", "model": "enemy agency", "links": ["perseus-gallic", "gutenberg-commentaries", "goldsworthy"]},
    {"title": "Alesia Double Siege", "level": "war", "focus": "reconstructing Caesar's most famous operational problem", "context": "At Alesia, Caesar besieged Vercingetorix while preparing to be besieged by a relief army. The double line of fortifications made engineering, morale, timing, and intelligence one system.", "model": "systems battle", "links": ["perseus-gallic", "gutenberg-commentaries", "goldsworthy"]},
    {"title": "Violence, Enslavement, and Moral Reckoning", "level": "ethics", "focus": "refusing to let strategic admiration erase conquest's human cost", "context": "Gaul brought mass death, enslavement, dispossession, and Roman extraction. A Caesar track that ignores victims is propaganda, not learning.", "model": "moral accounting", "links": ["gutenberg-commentaries", "beard-spqr", "cambridge-caesar-people"]},
    {"title": "Military Leadership and Soldier Loyalty", "level": "leadership", "focus": "how Caesar built mutual dependence with his legions", "context": "Caesar used rewards, speed, shared danger, personal address, clemency, discipline, and victory to create loyalty that later became political power.", "model": "army as political constituency", "links": ["gutenberg-commentaries", "goldsworthy", "appian-civil-wars"]},
    {"title": "Intelligence, Speed, and Risk", "level": "strategy", "focus": "extracting Caesar's operational tempo without romanticizing recklessness", "context": "Caesar repeatedly moved faster than opponents expected, but speed worked because it was paired with reconnaissance, engineering, morale, and political calculation.", "model": "tempo with information", "links": ["gutenberg-commentaries", "goldsworthy", "plutarch-caesar"]},
    {"title": "Julia, Pompey, and the Family Alliance", "level": "politics", "focus": "why personal relationships held constitutional consequences", "context": "The marriage alliance between Pompey and Caesar's daughter Julia helped stabilize their political partnership. Her death weakened a human bridge between rival power centers.", "model": "family as coalition glue", "links": ["plutarch-caesar", "appian-civil-wars", "goldsworthy"]},
    {"title": "Crassus, Parthia, and Balance Collapse", "level": "politics", "focus": "how Crassus's death changed the strategic geometry of Rome", "context": "Crassus's defeat and death at Carrhae removed the third weight from the triumviral balance. Pompey and Caesar now faced each other more directly.", "model": "coalition triangle collapse", "links": ["appian-civil-wars", "holland-rubicon", "goldsworthy"]},
    {"title": "Senate, Law, Dignitas, and Fear", "level": "politics", "focus": "understanding the dispute before the Rubicon in Roman terms", "context": "The argument was not simply ambition versus law. It involved command, immunity, dignitas, fear of prosecution, senatorial authority, Pompey's position, and rival definitions of the Republic.", "model": "constitutional crisis as status conflict", "links": ["mit-civil-war", "appian-civil-wars", "gelzer"]},
    {"title": "Rubicon Decision", "level": "turning-point", "focus": "reconstructing Caesar's irreversible move into civil war", "context": "Crossing the Rubicon converted political standoff into armed conflict. The decision fused legality, personal survival, elite competition, army loyalty, and narrative audacity.", "model": "point of no return", "links": ["mit-civil-war", "plutarch-caesar", "suetonius-caesar"]},
    {"title": "Italian Blitz and Psychological Momentum", "level": "civil-war", "focus": "how Caesar moved faster than the Pompeian state could emotionally process", "context": "Caesar's advance through Italy forced choices before enemies had consolidated. Momentum became a weapon against hesitation.", "model": "shock tempo", "links": ["mit-civil-war", "appian-civil-wars", "goldsworthy"]},
    {"title": "Spain Before Pompey", "level": "civil-war", "focus": "why Caesar neutralized Pompey's western forces before facing Pompey directly", "context": "Caesar said he went to fight an army without a leader before fighting a leader without an army. The Spanish campaign shows sequencing and risk management.", "model": "strategic sequencing", "links": ["mit-civil-war", "gutenberg-commentaries", "goldsworthy"]},
    {"title": "Civil War Commentaries", "level": "method", "focus": "reading Caesar's self-defense during civil war as political literature", "context": "The Civil War text makes Caesar appear patient, lawful, and forced into action. The reader's job is to compare the narrative with hostile and later sources.", "model": "self-justification audit", "links": ["mit-civil-war", "gutenberg-commentaries", "appian-civil-wars"]},
    {"title": "Pharsalus", "level": "battle", "focus": "studying the decisive battle against Pompey without reducing it to fate", "context": "Pharsalus was a battlefield result of years of politics, logistics, morale, and command choices. Caesar won, but the Republic's crisis did not end.", "model": "decisive battle with unresolved politics", "links": ["mit-civil-war", "plutarch-caesar", "goldsworthy"]},
    {"title": "Pompey's Death and Egyptian Politics", "level": "civil-war", "focus": "why Pompey's murder did not solve Caesar's problem", "context": "Pompey's death in Egypt removed a rival but created moral theater, diplomatic complications, and new entanglement in Ptolemaic politics.", "model": "enemy removal versus legitimacy", "links": ["plutarch-caesar", "appian-civil-wars", "goldsworthy"]},
    {"title": "Cleopatra and Alexandria", "level": "power", "focus": "placing Cleopatra and Caesar inside dynastic strategy, not romance alone", "context": "The Alexandrian episode mixed civil war, Egyptian succession, Roman intervention, personal alliance, and Mediterranean statecraft.", "model": "personal alliance as geopolitical instrument", "links": ["gutenberg-commentaries", "plutarch-caesar", "goldsworthy"]},
    {"title": "Zela and Veni Vidi Vici", "level": "campaign", "focus": "understanding speed, slogan, and reputation after victory over Pharnaces", "context": "Veni, vidi, vici compresses a campaign into a brand. Caesar knew how to turn operational speed into public memory.", "model": "compressed victory narrative", "links": ["suetonius-caesar", "plutarch-caesar", "goldsworthy"]},
    {"title": "Africa, Cato, and Republican Resistance", "level": "civil-war", "focus": "seeing why Pompeian resistance continued after Pompey", "context": "The African campaign and Cato's suicide became moral symbols. Caesar could beat armies more easily than he could neutralize the meaning of Republican resistance.", "model": "symbolic opposition", "links": ["appian-civil-wars", "plutarch-caesar", "holland-rubicon"]},
    {"title": "Munda and the Last Battlefield", "level": "civil-war", "focus": "why the civil war kept reproducing enemies", "context": "Munda was one of Caesar's hardest and bloodiest victories. The lesson is that military victory can lag behind political settlement.", "model": "winning the war after winning the war", "links": ["gutenberg-commentaries", "appian-civil-wars", "goldsworthy"]},
    {"title": "Dictatorship and Reform Agenda", "level": "rule", "focus": "mapping Caesar's reforms without assuming every reform proves tyranny", "context": "As dictator, Caesar addressed calendars, debt, colonies, Senate size, citizenship, urban administration, and provincial governance. Reform and domination moved together.", "model": "state repair under personal rule", "links": ["suetonius-caesar", "dio-book-44", "goldsworthy"]},
    {"title": "Calendar Reform", "level": "rule", "focus": "why technical administrative reform became one of Caesar's most durable legacies", "context": "The Julian calendar solved a real administrative problem and outlived Caesar's regime. Not all political legacy comes from battles.", "model": "infrastructure hidden in timekeeping", "links": ["suetonius-caesar", "dio-book-44", "beard-spqr"]},
    {"title": "Colonies, Citizenship, Debt, and Senate Expansion", "level": "rule", "focus": "studying Caesar's reforms as social engineering and political consolidation", "context": "Colonization, debt measures, citizenship grants, and Senate expansion touched veterans, provincials, elites, and the urban poor. Each reform created beneficiaries and enemies.", "model": "policy as coalition redesign", "links": ["suetonius-caesar", "dio-book-44", "cambridge-caesar-people"]},
    {"title": "Caesar as Populist or Aristocrat", "level": "interpretation", "focus": "testing competing interpretations of Caesar's politics", "context": "Was Caesar a popularis reformer, aristocratic competitor, military monarch, opportunist, or something more unstable? Different sources and historians answer differently.", "model": "interpretive conflict", "links": ["cambridge-caesar-people", "gelzer", "canfora"]},
    {"title": "Clemency Strategy", "level": "rule", "focus": "evaluating clementia as mercy, propaganda, and control", "context": "Caesar's clemency spared enemies and advertised superiority, but it also humiliated rivals and left dangerous men alive. Mercy was political technology.", "model": "leniency as domination", "links": ["mit-civil-war", "plutarch-caesar", "dio-book-44"]},
    {"title": "Kingship Anxiety and Symbols", "level": "rule", "focus": "why crowns, thrones, honors, and gestures could become lethal", "context": "Romans hated the name king while accepting extraordinary power in other forms. Caesar's honors made ambiguity unbearable for opponents.", "model": "symbolic overload", "links": ["suetonius-caesar", "dio-book-44", "plutarch-caesar"]},
    {"title": "Assassination Conspiracy", "level": "fall", "focus": "understanding the motives and blind spots of Caesar's killers", "context": "The conspirators mixed fear, principle, status resentment, personal pardon, and misreadings of public reaction. Killing Caesar was easier than designing the next regime.", "model": "negative coalition", "links": ["plutarch-caesar", "suetonius-caesar", "dio-book-44"]},
    {"title": "Ides of March", "level": "fall", "focus": "reconstructing the mechanics, setting, and immediate meaning of the assassination", "context": "The assassination in 44 BCE happened inside dense symbols: Senate space, honors, omens, personal relationships, and staged republican restoration.", "model": "political theater by violence", "links": ["plutarch-caesar", "suetonius-caesar", "dio-book-44"]},
    {"title": "Why the Assassination Failed", "level": "aftermath", "focus": "why removing Caesar did not restore the Republic", "context": "The assassins removed the person but not the armies, debts, veterans, social forces, legitimacy problems, or appetite for revenge.", "model": "decapitation without replacement system", "links": ["appian-civil-wars", "dio-book-44", "syme"]},
    {"title": "Cicero, Brutus, Cassius, and Opposition Mind", "level": "aftermath", "focus": "seeing Caesar's opponents as serious political thinkers and flawed operators", "context": "Opposition to Caesar was not one thing. Cicero, Brutus, Cassius, Cato, and Pompeians had different fears, ideals, and incentives.", "model": "opposition mapping", "links": ["cicero-letters", "appian-civil-wars", "holland-rubicon"]},
    {"title": "Funeral, Will, and Antony", "level": "aftermath", "focus": "how memory, money, and performance turned murder into mobilization", "context": "Caesar's will, funeral, body, and Antony's politics transformed assassination into public crisis. Narrative moved the crowd.", "model": "posthumous power", "links": ["appian-civil-wars", "suetonius-caesar", "dio-book-44"]},
    {"title": "Octavian Inheritance and Caesarism", "level": "legacy", "focus": "how Caesar's name became a political machine", "context": "Octavian inherited money, name, veterans, legitimacy, and risk. Caesar became more powerful as a symbol after death than the conspirators expected.", "model": "brand inheritance", "links": ["appian-civil-wars", "syme", "beard-spqr"]},
    {"title": "Ancient Sources Compared", "level": "method", "focus": "comparing Caesar, Cicero, Plutarch, Suetonius, Appian, and Dio without flattening them", "context": "Each ancient source has genre, date, agenda, distance, and missing evidence. Mastery means knowing who is speaking and why.", "model": "source matrix", "links": ["gutenberg-commentaries", "cicero-letters", "plutarch-caesar", "suetonius-caesar", "appian-civil-wars", "dio-book-44"]},
    {"title": "Military Lessons That Still Matter", "level": "synthesis", "focus": "extracting durable strategic lessons without copying ancient brutality", "context": "Caesar teaches tempo, logistics, morale, engineering, narrative, and risk. He also teaches the danger of turning military loyalty into personal politics.", "model": "strategy with moral firewall", "links": ["goldsworthy", "gutenberg-commentaries", "mit-ocw-readings"]},
    {"title": "Political Lessons and Warning Labels", "level": "synthesis", "focus": "using Caesar to study charisma, institutions, emergency, and personal power", "context": "Caesar is useful because he is brilliant and dangerous. He exposes what happens when institutions cannot absorb ambition, inequality, military loyalty, and elite fear.", "model": "charisma versus institutions", "links": ["gelzer", "meier", "cambridge-caesar-people", "syme"]},
    {"title": "Capstone: Build a Caesar Dossier", "level": "capstone", "focus": "wiring biography, campaigns, sources, maps, books, moral judgment, and strategy into one reference", "context": "The final goal is a personal Caesar dossier: timeline, source matrix, campaign maps, Roman institutions, reading list, quote bank, moral accounting, and modern warning labels.", "model": "historical operating system", "links": ["mit-ocw-readings", "gutenberg-commentaries", "plutarch-caesar", "suetonius-caesar", "goldsworthy", "cambridge-caesar-people"]},
]


def caesar_unit(topic: dict[str, Any], order: int, previous: str | None) -> Unit:
    title = str(topic["title"])
    unit_id = f"caesar-{slug(title)}"
    links = list(topic.get("links") or ["gutenberg-commentaries", "goldsworthy"])
    source = CAESAR_RESOURCE_CATALOG[links[0]]
    prereqs: list[str] = []
    if previous:
        prereqs.append(previous)
    for extra in topic.get("extra_prerequisites", []):
        if extra not in prereqs:
            prereqs.append(str(extra))
    focus = str(topic["focus"])
    context = str(topic["context"])
    model = str(topic["model"])
    level = str(topic.get("level", "core"))
    link_block = caesar_source_links_html(links)
    practice = f"Add one page to your Caesar dossier for '{title}': timeline anchor, source comparison, map or institution sketch, moral/accountability note, and one strategic lesson with a warning label."
    return {
        "id": unit_id,
        "title": title,
        "subtitle": f"{level}: {focus}",
        "summary": f"Learn {title} by connecting Caesar's biography, Roman institutions, campaigns, sources, moral cost, and strategy through {model}.",
        "kind": "substantial",
        "level": level,
        "order": order,
        "minutes": 38,
        "hero_article": "Julius Caesar",
        "prerequisites": prereqs,
        "source": {"label": source["title"], "url": source["url"]},
        "objectives": [
            f"Explain {title} using sources instead of Caesar worship or anti-Caesar slogans.",
            f"Use {model} to connect events to institutions, incentives, war, and public narrative.",
            "Name one Caesar-authored claim, one hostile or later-source claim, and one modern historian's interpretation.",
        ],
        "sections": [
            section("Source trail", f"<p>Start with the links below, then compare Caesar's own story against hostile contemporaries, later biographers, and modern historians. Caesar was a writer of his own legend.</p>{link_block}"),
            section("Core storyline", f"<p>{html_lib.escape(context)}</p><p>Place this unit on the late-Republic timeline: what office, army, law, debt, alliance, or public audience mattered right now?</p>"),
            section("Power mechanism", f"<p>The working focus is <b>{html_lib.escape(focus)}</b>. Rebuild it as a mechanism: offices, laws, soldiers, money, prestige, geography, speed, fear, symbols, and audiences.</p>"),
            section("Model to keep", f"<p>Use <b>{html_lib.escape(model)}</b> as the durable mental model. The point is not to become Caesar; it is to understand how talent, institutions, violence, and narrative interact.</p>"),
            section("Moral and myth check", "<p>Ask what Caesar's version hides, what his enemies exaggerate, who paid the human cost, and what a republican, a conquered Gaul, a soldier, and a modern historian would each say.</p>"),
            section("Dossier task", f"<p>{html_lib.escape(practice)}</p>"),
        ],
        "ideas": [
            ("Source matrix", "Compare Caesar's Commentaries, Cicero, Plutarch, Suetonius, Appian, Dio, and modern scholarship."),
            ("Power mechanism", f"For this unit, the mechanism is: {model}."),
            ("Republic under stress", "Caesar matters because his career shows institutions failing under ambition, inequality, armies, debt, and fear."),
            ("Admiration firewall", "Study brilliance without laundering conquest, civil war, or dictatorship."),
        ],
        "thinking_questions": [
            f"What is the strongest sourced fact about {title}, and which source gives it?",
            "What does Caesar want you to believe, and what would his enemy say instead?",
            "Which force matters most here: law, money, family, army loyalty, crowd politics, geography, or symbolic honor?",
            "Who benefits, who pays, and who disappears from the narrative?",
            f"How does {model} change how you understand power today?",
            "What map, timeline, or institution diagram would make this unit stick?",
            "What is the one lesson to keep, and what warning label must travel with it?",
        ],
        "practice_prompt": practice,
        "application_prompt": practice,
        "review_prompts": [
            "Recall the timeline position, source trail, and power mechanism.",
            "Name one Caesar-authored source and one non-Caesar source from memory.",
            "State the moral or republican warning label in one sentence.",
        ],
        "did_you_know": "Caesar's own books are part of the evidence and part of the problem: they are military reports, political self-defense, and literary reputation-building at once.",
        "sources": [CAESAR_RESOURCE_CATALOG[k] for k in links if k in CAESAR_RESOURCE_CATALOG],
    }


def build_caesar_units() -> list[Unit]:
    units: list[Unit] = []
    previous: str | None = None
    for order, topic in enumerate(CAESAR_TOPICS, start=1):
        unit = caesar_unit(topic, order, previous)
        units.append(unit)
        previous = unit["id"]
    return units


def mastery_case_unit(
    track_id: str,
    title: str,
    order: int,
    level: str,
    prerequisites: list[str],
    sources: list[Source],
    focus: str,
    context: str,
    lens: str,
) -> Unit:
    unit_id = f"{track_id}-{slug(title)}"
    return {
        "id": unit_id,
        "title": title,
        "subtitle": f"{level}: {focus}",
        "summary": f"Study {title} as a case in {focus}: {context}",
        "kind": "case-study",
        "level": level,
        "order": order,
        "minutes": 28,
        "prerequisites": prerequisites,
        "source": primary_source(sources, order),
        "objectives": [
            f"Explain the strategic or analytical move behind {title}.",
            "Separate the durable principle from biography worship.",
            "Apply the principle to a current decision without forcing the analogy.",
        ],
        "sections": [
            section("Context", f"{context} Before extracting a lesson, locate the person, company, or institution inside its constraints: geography, technology, capital, rivals, ideology, timing, and available information."),
            section("Core move", f"The core move is {focus}. Ask what was noticed earlier than others, what tradeoff was accepted, and what resource was concentrated instead of spread thin."),
            section("Decision model", f"Read this through the lens of {lens}. Map objectives, constraints, feedback loops, second-order effects, and the cost of being wrong. The point is not admiration; it is reusable judgment."),
            section("Failure mode", f"Every great case has a shadow. Identify where {title} could mislead you: overconfidence, survivor bias, different incentives, luck, hidden violence, or conditions that no longer hold."),
            section("LifeOS transfer", f"Use {title} as a live drill. Pick one project, habit, negotiation, or learning path. State the analogous constraint, the non-analogous constraint, and one action that becomes clearer."),
        ],
        "thinking_questions": [
            f"What did {title} see or do that a smart contemporary could have missed?",
            "Which constraint mattered most: information, incentives, timing, talent, legitimacy, or logistics?",
            "What is the strongest counterexample to applying this lesson today?",
            "Where is the line between strategic clarity and moral compromise in this case?",
            "What one-sentence rule would you keep, and what warning label would you attach to it?",
        ],
        "application_prompt": f"Write a one-page strategic memo applying {focus} to a current LifeOS project. Include a counterargument and a kill condition.",
        "review_prompts": [
            "Recall the context, core move, and failure mode from memory.",
            "Name one modern analogy and one reason the analogy breaks.",
            "Turn the case into a decision checklist with three questions.",
        ],
        "sources": sources,
    }


def build_case_units(track_id: str, topics: list[tuple[str, str, str, str, str]], sources: list[Source]) -> list[Unit]:
    units: list[Unit] = []
    prev: list[str] = []
    for order, (title, level, focus, context, lens) in enumerate(topics, start=1):
        prereqs = prev[-1:]
        unit = mastery_case_unit(track_id, title, order, level, prereqs, sources, focus, context, lens)
        units.append(unit)
        prev.append(unit["id"])
    return units


STARTUP_STRATEGY_TOPICS: list[tuple[str, str, str, str, str]] = [
    ("Customer Discovery", "startup", "learning from users before scaling", "Customer development treats startup facts as hypotheses that must survive contact with real users.", "evidence before conviction"),
    ("Founder Market Fit", "startup", "matching unusual founder insight to a painful market", "Strong founders often notice problems because they live near them, not because a slide says the market is large.", "earned information"),
    ("Wedge Markets", "startup", "entering through a narrow painful segment", "Many durable companies start with a small group that cares intensely, then expand outward from a beachhead.", "focus and expansion"),
    ("Concierge MVPs", "startup", "doing unscalable work to discover the real workflow", "Manual service can reveal what software should later automate, price, or refuse to do.", "manual learning loops"),
    ("Distribution Before Polish", "startup", "testing channels before perfecting product", "A beautiful product without a route to users is a diary; distribution is part of product strategy.", "go-to-market reality"),
    ("Pricing as Strategy", "startup", "using price to reveal value, segment, and trust", "Price encodes positioning, buyer identity, sales motion, and product promise.", "value capture"),
    ("Sales Learning Loops", "startup", "turning objections into product roadmap", "Early sales calls expose confused messaging, missing trust, and hidden buying committees faster than dashboards.", "feedback compression"),
    ("Retention Cohorts", "startup", "judging product truth by repeated use", "Growth can be purchased temporarily; retention shows whether users return when novelty and persuasion fade.", "behavioral evidence"),
    ("Marketplace Liquidity", "startup", "solving chicken-and-egg supply and demand", "Marketplaces die when either side arrives and finds emptiness; liquidity is the product before the product.", "network coordination"),
    ("Network Effects", "startup", "building value that increases with adoption", "Network effects need density, repeated interaction, switching costs, and defensible nodes.", "compounding loops"),
    ("Platform Strategy", "startup", "letting others build on your bottleneck", "A platform wins when complementors create value while the platform keeps the scarce coordination layer.", "ecosystem control"),
    ("Developer Tools Adoption", "startup", "winning through workflow trust and low-friction proof", "Developer products spread when they save time quickly, fit existing stacks, and earn credibility from peers.", "technical distribution"),
    ("Enterprise Trust", "startup", "selling reliability, security, and political safety", "Enterprise buyers purchase risk reduction as much as features.", "institutional buying"),
    ("Consumer Habit Loops", "startup", "earning repeated attention without addiction traps", "Consumer products compete with boredom, identity, and social reward.", "attention systems"),
    ("Fundraising Narrative", "startup", "compressing market, team, traction, and inevitability", "Fundraising works when investors can retell a believable future with evidence and urgency.", "capital storytelling"),
    ("Default Alive Finance", "startup", "controlling burn, runway, and growth assumptions", "Strategic freedom collapses when cash runs out before evidence compounds.", "survival math"),
    ("Hiring Bar and Talent Density", "startup", "raising execution quality through people decisions", "Early hires set standard, culture, and operating tempo more than any memo can.", "team leverage"),
    ("Founder Psychology Under Uncertainty", "startup", "deciding while evidence is incomplete", "Startups punish both panic and denial; the skill is updating fast without losing nerve.", "emotional epistemology"),
    ("Strategic Positioning", "startup", "choosing the category and comparison set", "Positioning tells users what problem you solve and competitors what game you refuse to play.", "category choice"),
    ("Competitive Moats", "startup", "turning temporary advantage into durable defense", "Moats can come from data, network density, brand, regulation, switching costs, workflow depth, or scale.", "defensibility"),
    ("Category Creation", "startup", "teaching the market a new frame", "Some companies win by making buyers see a new problem, budget, and vocabulary.", "market education"),
    ("Product Taste", "startup", "knowing what should be removed, emphasized, or made obvious", "Taste is judgment under constraints: what matters, what distracts, and what makes a product feel inevitable.", "aesthetic strategy"),
    ("Operational Cadence", "startup", "turning strategy into weekly execution rhythm", "Cadence converts ambition into shipped work, feedback, and accountability.", "execution systems"),
    ("Metrics That Matter", "startup", "choosing numbers that change decisions", "Bad metrics decorate dashboards. Good metrics force tradeoffs and expose reality.", "measurement discipline"),
    ("AI Product Strategy", "startup", "using models where uncertainty, workflow, and leverage meet", "AI products win when model capability is wrapped in distribution, trust, data loops, and user workflow.", "capability packaging"),
    ("Crisis Communication", "startup", "preserving trust under stress", "Crises reveal whether users, employees, investors, and partners believe the company is honest and competent.", "trust under pressure"),
    ("Exit vs Independence", "startup", "deciding what game the company is really playing", "Selling, raising, staying private, or compounding independently are different games.", "strategic ownership"),
    ("Long Term Compounding", "startup", "building advantages that get stronger with time", "The rare startup keeps learning, trust, distribution, and product depth compounding after the first win.", "time as strategy"),
]

STRATEGIC_MIND_TOPICS: list[tuple[str, str, str, str, str]] = [
    ("Sun Tzu and Positional Advantage", "ancient", "winning before battle through position and information", "The Sunzi tradition treats open battle as a late result of terrain, deception, morale, and timing.", "indirect strategy"),
    ("Pericles and Democratic Grand Strategy", "ancient", "aligning rhetoric, naval power, and civic endurance", "Periclean Athens shows how public persuasion and strategic restraint can support an empire under pressure.", "strategy under democracy"),
    ("Thucydides and Power Analysis", "ancient", "seeing fear, honor, interest, and escalation", "Thucydides explains war through incentives and perception, not heroic slogans.", "realist diagnosis"),
    ("Alexander and Operational Tempo", "ancient", "using speed and combined arms to break larger systems", "Alexander paired personal risk, logistics, diplomacy, and shock action across huge distances.", "tempo and legitimacy"),
    ("Kautilya and Statecraft", "ancient", "combining intelligence, economics, alliance, and coercion", "The Arthashastra tradition studies rule as revenue, spies, diplomacy, law, and force.", "state capacity"),
    ("Hannibal and Asymmetric Campaign Design", "ancient", "using surprise, terrain, and coalition pressure", "Hannibal's victories show brilliance that still could not solve Rome's strategic depth.", "tactical genius vs strategic base"),
    ("Julius Caesar and Narrative Power", "ancient", "turning military success into political inevitability", "Caesar combined speed, clemency, writing, patronage, and risk-taking to transform Roman politics.", "military-politics fusion"),
    ("Augustus and Institutional Patience", "ancient", "hiding revolution inside restoration", "Augustus outlasted rivals by making monarchy look like republican continuity.", "legitimacy design"),
    ("Ashoka and Moral Statecraft", "ancient", "using remorse and public ethics as imperial policy", "Ashoka's inscriptions present conquest converted into moral administration.", "soft power and governance"),
    ("Genghis Khan and Scalable Command", "medieval", "building a mobile empire through discipline and adaptation", "Mongol success depended on intelligence networks, merit, mobility, terror, and coordination.", "scalable systems"),
    ("Saladin and Coalition Legitimacy", "medieval", "uniting factions through credibility and authority", "Saladin's power came from coalition-building as much as battlefield action.", "coalition legitimacy"),
    ("Elizabeth I and Strategic Ambiguity", "early-modern", "surviving by balancing factions, faith, and foreign threats", "Elizabethan policy often delayed, hedged, and signaled without overcommitting.", "ambiguity as control"),
    ("Tokugawa Ieyasu and Durable Order", "early-modern", "turning victory into stable political architecture", "The Tokugawa settlement shows strategy after battle: hostages, domains, status, law, and ritual.", "institutional lock-in"),
    ("Machiavelli and Political Reality", "early-modern", "separating how power works from how people wish it worked", "Machiavelli is useful as a diagnostic of incentives, fear, virtue, fortune, and appearances.", "uncomfortable realism"),
    ("Frederick the Great and Small-State Leverage", "early-modern", "using bureaucracy and army reform for survival", "Prussia survived among larger powers through administration, discipline, and calculated risk.", "small-state leverage"),
    ("George Washington and Restraint", "revolutionary", "winning legitimacy by refusing personal power", "Washington's strategic greatness includes retreat, endurance, alliance management, and leaving office.", "restraint as strategy"),
    ("Napoleon and Campaign Systems", "modern", "organizing corps, speed, and decisive concentration", "Napoleon's genius was systemic: operational mobility, staff work, morale, law, and myth.", "systemic warfare"),
    ("Clausewitz and Friction", "modern", "thinking clearly under uncertainty, chance, and politics", "Clausewitz gives language for war as a political act full of fog, friction, and moral forces.", "uncertainty doctrine"),
    ("Toussaint Louverture and Revolutionary Strategy", "modern", "maneuvering among empires, armies, and emancipation", "The Haitian Revolution required military skill, diplomacy, legitimacy, and adaptation.", "strategy from below"),
    ("Lincoln and Strategic Communication", "modern", "connecting moral purpose, coalition politics, and war aims", "Lincoln shifted aims, held coalitions, and made policy legible through language.", "moral-political strategy"),
    ("Bismarck and Limited Objectives", "modern", "using diplomacy and war without losing the endgame", "Bismarck's unification strategy depended on sequencing, isolating enemies, and stopping after success.", "limited war and diplomacy"),
    ("Meiji Oligarchs and National Modernization", "modern", "copying selectively to preserve sovereignty", "Meiji leaders studied foreign systems, imported what worked, and rebuilt institutions under threat.", "adaptive modernization"),
    ("Churchill and Strategic Morale", "modern", "using language to sustain resistance", "Churchill's 1940 role shows rhetoric as strategic infrastructure when morale is scarce.", "morale under pressure"),
    ("George Marshall and Institution Building", "modern", "designing capacity rather than chasing personal glory", "Marshall selected people, built systems, and aligned military and political objectives.", "quiet leverage"),
    ("Gandhi and Nonviolent Mobilization", "modern", "turning moral discipline into political pressure", "Gandhi made legitimacy, mass participation, and self-restraint into strategic tools.", "moral mobilization"),
    ("Deng Xiaoping and Experimental Reform", "modern", "using pilots, incentives, and ambiguity to change a system", "Deng's reforms show gradualism, local experimentation, and pragmatic sequencing under constraint.", "experimental governance"),
    ("Lee Kuan Yew and State Capacity", "modern", "building institutions around talent, order, and positioning", "Singapore's rise is a case in governance, trade positioning, anti-corruption, and execution.", "city-state strategy"),
    ("Nelson Mandela and Reconciliation Strategy", "modern", "using forgiveness without surrendering purpose", "Mandela converted moral authority into a transition strategy that reduced revenge spirals.", "conflict transformation"),
    ("John Boyd and OODA Loops", "modern", "competing through faster orientation and adaptation", "Boyd's OODA frame is about updating mental models under conflict, not just moving faster.", "adaptive decision cycles"),
    ("Andy Grove and Strategic Inflection Points", "modern", "recognizing when old business logic is dying", "Grove's Intel leadership shows paranoia, data, and decisive reallocation under technological shift.", "inflection awareness"),
    ("Jeff Bezos and Long-Term Optionality", "modern", "compounding infrastructure, customer trust, and strategic patience", "Amazon repeatedly traded short-term optics for platform depth and optionality.", "long-term compounding"),
]

ANALYTICAL_MIND_TOPICS: list[tuple[str, str, str, str, str]] = [
    ("Aristotle and Classification", "ancient", "making knowledge inspectable by sorting causes and categories", "Aristotle separated kinds of explanation and built vocabularies for inquiry.", "taxonomic reasoning"),
    ("Euclid and Axiomatic Structure", "ancient", "deriving a world from definitions and postulates", "Euclid models durable knowledge by making assumptions explicit.", "axiomatic systems"),
    ("Archimedes and Mathematical Physics", "ancient", "combining geometry, measurement, and physical insight", "Archimedes turned bodies, levers, and fluids into mathematics.", "model-based insight"),
    ("Al-Khwarizmi and Algorithmic Procedure", "medieval", "turning classes of problems into repeatable methods", "Al-Khwarizmi's algebraic tradition shows the power of named procedures and generality.", "algorithmic thinking"),
    ("Ibn al-Haytham and Experimental Optics", "medieval", "testing vision with controlled observation", "Ibn al-Haytham emphasized experiment, geometry, and criticism of inherited theories.", "experimental discipline"),
    ("Galileo and Idealization", "scientific", "simplifying messy motion to reveal law", "Galileo's inclined planes and mathematical descriptions show how ideal models expose regularities.", "controlled abstraction"),
    ("Descartes and Coordinate Method", "scientific", "turning geometry into algebraic representation", "Descartes made curves and equations speak to each other.", "representation shift"),
    ("Newton and System Unification", "scientific", "linking terrestrial and celestial motion", "Newton joined calculus, mechanics, and gravitation into a predictive system.", "unifying models"),
    ("Leibniz and Symbolic Design", "scientific", "creating notation that makes thought easier", "Leibniz shows that symbols are tools for cognition; good notation changes what minds can hold.", "notation as leverage"),
    ("Euler and Productive Calculation", "enlightenment", "solving by fluent transformation across domains", "Euler's output came from symbolic fluency and pattern recognition.", "mathematical fluency"),
    ("Gauss and Hidden Structure", "modern", "finding invariants beneath computation", "Gauss repeatedly turned messy numerical or geometric problems into deeper structures.", "structural compression"),
    ("Laplace and Probabilistic Worldview", "modern", "treating uncertainty as something to calculate", "Laplace advanced probability as a general logic of inference, astronomy, and error.", "uncertainty calculus"),
    ("Faraday and Physical Intuition", "modern", "discovering field patterns through experiment and imagery", "Faraday's lines of force show how intuition can precede formal mathematics.", "experimental imagination"),
    ("Maxwell and Field Equations", "modern", "translating physical imagery into mathematical law", "Maxwell unified electricity, magnetism, and light through equations.", "formal synthesis"),
    ("Darwin and Mechanism from Variation", "modern", "explaining complexity through selection over time", "Darwin made design-like order emerge from variation, inheritance, and selection.", "population thinking"),
    ("Florence Nightingale and Data Persuasion", "modern", "using statistics and visualization to force institutional change", "Nightingale turned mortality data into arguments administrators could not ignore.", "quantified reform"),
    ("Marie Curie and Measurement Persistence", "modern", "isolating hidden phenomena through relentless measurement", "Curie's work shows analysis as patience: refining signals until invisible structure becomes undeniable.", "measurement stamina"),
    ("Einstein and Principle Reasoning", "modern", "starting from invariants and following consequences", "Einstein's relativity work asks what must remain true for all observers.", "invariant reasoning"),
    ("Emmy Noether and Symmetry", "modern", "linking conservation laws to invariance", "Noether revealed a deep bridge between symmetry and physical conservation.", "symmetry analysis"),
    ("Keynes and Macro Judgment", "modern", "reasoning about economies as systems under uncertainty", "Keynes analyzed expectations, demand, money, and policy as interacting mechanisms.", "system-level economics"),
    ("Alan Turing and Computability", "modern", "defining what mechanical reasoning can and cannot do", "Turing's machine model made computation mathematically precise.", "formal limits"),
    ("John von Neumann and Architecture", "modern", "connecting games, computers, physics, and strategy", "Von Neumann moved formal structures across domains quickly and rigorously.", "cross-domain formalism"),
    ("Claude Shannon and Information", "modern", "measuring communication without caring about meaning", "Shannon separated signal, noise, entropy, and coding in a way that powered the digital world.", "abstraction that travels"),
    ("Richard Feynman and First-Principles Explanation", "modern", "rebuilding understanding from simple physical pictures", "Feynman's style used diagrams, intuition, and ruthless clarity to avoid empty formalism.", "explainable physics"),
    ("Herbert Simon and Bounded Rationality", "modern", "studying decision-makers with limits", "Simon replaced ideal rationality with satisficing, search, attention, and organizational constraint.", "realistic cognition"),
    ("Jane Jacobs and City Observation", "modern", "reading complex systems from street-level evidence", "Jacobs analyzed cities as living networks of use, trust, density, and local knowledge.", "bottom-up systems"),
    ("Elinor Ostrom and Commons Governance", "modern", "showing how communities manage shared resources", "Ostrom challenged simple tragedy stories with field evidence and institutional design principles.", "institutional analysis"),
    ("Daniel Kahneman and Cognitive Bias", "modern", "measuring systematic error in judgment", "Kahneman's work shows that human intuition has patterned errors, not just random flaws.", "bias diagnosis"),
    ("Judea Pearl and Causal Graphs", "modern", "separating correlation from intervention", "Pearl's causal diagrams make assumptions visible and clarify what evidence can answer.", "causal structure"),
    ("Donella Meadows and Systems Leverage", "modern", "finding where interventions change a system", "Meadows showed that information flows, rules, goals, and paradigms often beat parameter tweaks.", "leverage points"),
]


CURRICULUM_TRACKS: list[dict[str, Any]] = [
    {
        "id": "math-mastery",
        "title": "Math Mastery",
        "name": "Math Mastery",
        "domain": "math",
        "description": "Arithmetic and number sense through ML mathematics, organized as prerequisite mastery units with daily retrieval and spaced review.",
        "daily_policy": {
            "new_minutes": 30,
            "review_minutes": 15,
            "mastery_rule": "Advance after accurate recall, one worked example, one transfer example, and one interleaved review.",
            "interleaving": "Mix current strand with two older strands every day.",
        },
        "sources": OPEN_MATH_SOURCES,
        "units": build_units("math", MATH_TOPICS, MATH_SUBSTANTIAL, OPEN_MATH_SOURCES),
    },
    {
        "id": "physics-mastery",
        "title": "Physics Mastery",
        "name": "Physics Mastery",
        "domain": "physics",
        "description": "Measurement and vectors through modern physics, with problem-first conceptual sections and repeated model selection practice.",
        "daily_policy": {
            "new_minutes": 35,
            "review_minutes": 15,
            "mastery_rule": "Advance after free-body/model setup, units check, conceptual prediction, and numerical or symbolic solve.",
            "interleaving": "Mix mechanics, fields, thermodynamics, and modern physics once foundations are active.",
        },
        "sources": OPEN_PHYSICS_SOURCES,
        "units": build_units("physics", PHYSICS_TOPICS, PHYSICS_SUBSTANTIAL, OPEN_PHYSICS_SOURCES),
    },
    {
        "id": "civilization-history",
        "title": "Civilization and History",
        "name": "Civilization and History",
        "domain": "history",
        "description": "A serious civilization sequence from agriculture and early states through science and industrialization, with institution-level questions.",
        "daily_policy": {
            "new_minutes": 30,
            "review_minutes": 10,
            "mastery_rule": "Advance after timeline placement, causal explanation, source awareness, and modern analogy.",
            "interleaving": "Review geography, institutions, belief systems, and technology across non-adjacent eras.",
        },
        "sources": OPEN_HISTORY_SOURCES,
        "units": build_units("history", HISTORY_TOPICS, HISTORY_SUBSTANTIAL, OPEN_HISTORY_SOURCES),
    },
    {
        "id": "startup-strategy-builders",
        "title": "Startup Strategy Builders",
        "name": "Startup Strategy Builders",
        "domain": "startup",
        "description": "Startup strategy units focused on users, distribution, pricing, moats, founder judgment, and long-term compounding.",
        "daily_policy": {
            "new_minutes": 25,
            "review_minutes": 10,
            "mastery_rule": "Advance after applying the unit to one active project and naming a counterexample.",
            "interleaving": "Mix startup units with Paul Graham essays and current LifeOS product decisions.",
        },
        "sources": OPEN_STARTUP_STRATEGY_SOURCES,
        "units": build_case_units("startup-strategy", STARTUP_STRATEGY_TOPICS, OPEN_STARTUP_STRATEGY_SOURCES),
    },
    {
        "id": "strategic-minds-history",
        "title": "Strategic Minds in History",
        "name": "Strategic Minds in History",
        "domain": "history",
        "description": "Case studies of statesmen, commanders, institution builders, and operators whose strategic decisions reshaped history.",
        "daily_policy": {
            "new_minutes": 30,
            "review_minutes": 10,
            "mastery_rule": "Advance after explaining context, core move, failure mode, and modern transfer.",
            "interleaving": "Compare ancient, early-modern, and modern strategic choices rather than memorizing biographies.",
        },
        "sources": OPEN_STRATEGIC_MIND_SOURCES,
        "units": build_case_units("strategic-minds", STRATEGIC_MIND_TOPICS, OPEN_STRATEGIC_MIND_SOURCES),
    },
    {
        "id": "nikola-tesla-mastery",
        "title": "Nikola Tesla: Complete Invention Dossier",
        "name": "Nikola Tesla: Complete Invention Dossier",
        "domain": "invention",
        "description": "A deep Tesla learning path that wires together biography, books, primary sources, patents, AC power, radio, Wardenclyffe, business failures, myths, and modern invention lessons.",
        "daily_policy": {
            "new_minutes": 35,
            "review_minutes": 15,
            "mastery_rule": "Advance after adding a sourced page to the Tesla dossier with timeline, source links, mechanism, myth check, and invention lesson.",
            "interleaving": "Mix Tesla units with physics electricity/magnetism, analytical minds, startup strategy, and history of technology.",
        },
        "sources": TESLA_CORE_SOURCES,
        "units": build_tesla_units(),
    },
    {
        "id": "julius-caesar-mastery",
        "title": "Julius Caesar: Power, War, and the Fall of the Republic",
        "name": "Julius Caesar: Power, War, and the Fall of the Republic",
        "domain": "statecraft",
        "description": "A deep Caesar learning path wiring together primary sources, modern books, Roman institutions, military campaigns, political coalitions, civil war, dictatorship, assassination, moral cost, and modern strategy lessons.",
        "daily_policy": {
            "new_minutes": 38,
            "review_minutes": 15,
            "mastery_rule": "Advance after adding a sourced Caesar dossier page with source comparison, timeline, power mechanism, moral accounting, and warning label.",
            "interleaving": "Mix Caesar units with Roman Republic history, strategic minds, analytical methods, and startup/power lessons about coalitions, narrative, and institutions.",
        },
        "sources": CAESAR_CORE_SOURCES,
        "units": build_caesar_units(),
    },
    {
        "id": "analytical-minds",
        "title": "Analytical Minds",
        "name": "Analytical Minds",
        "domain": "thinking",
        "description": "Analytical people and methods: how great thinkers formed models, abstractions, experiments, measurements, and decision frameworks.",
        "daily_policy": {
            "new_minutes": 30,
            "review_minutes": 10,
            "mastery_rule": "Advance after converting the thinker into a reusable method and applying it to a problem.",
            "interleaving": "Mix mathematical, scientific, economic, and systems thinkers to build cross-domain analytical taste.",
        },
        "sources": OPEN_ANALYTICAL_MIND_SOURCES,
        "units": build_case_units("analytical-minds", ANALYTICAL_MIND_TOPICS, OPEN_ANALYTICAL_MIND_SOURCES),
    },
    {
        "id": "paul-graham-essays",
        "title": "Paul Graham Essays",
        "name": "Paul Graham Essays",
        "domain": "startup",
        "description": "Original LifeOS study digests for Paul Graham's official essay corpus, exposing source URLs, key ideas, questions, and application prompts without storing essay bodies.",
        "daily_policy": {
            "new_minutes": 20,
            "review_minutes": 10,
            "mastery_rule": "Advance after restating the thesis, extracting the practical rule, naming a fair objection, and applying one behavior change.",
            "interleaving": "Mix startup, writing, wealth, programming, and independent-thinking essays so themes transfer across contexts.",
        },
        "sources": [PG_INDEX_SOURCE],
        "units": build_paul_graham_units(),
    },
]


def counts() -> dict[str, Any]:
    return {
        track["id"]: {
            "units": len(track["units"]),
            "substantial_units": sum(1 for unit in track["units"] if unit["kind"] == "substantial"),
            "sections": sum(len(unit["sections"]) for unit in track["units"]),
            "thinking_questions": sum(len(unit["thinking_questions"]) for unit in track["units"]),
        }
        for track in CURRICULUM_TRACKS
    }


def main() -> int:
    print(json.dumps(counts(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
