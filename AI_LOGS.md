I am building this coding assessment project entirely inside a GitHub Codespace.
Problem statement:
"Friday night at the multiplex
The multiplex booking counter keeps mis-pricing tickets and the queue is getting angry. Seats come in tiers — Silver, Gold, Recliner — at different prices, and by showtime some tiers sell out and shouldn’t be bookable. There are offers on: a flat festival discount and a percentage off for members (capped). Every booking then adds a small per-ticket convenience fee and GST on top, and it all has to total to the exact paisa. Customers keep demanding a clear line-by-line breakup of the bill.
Build a pricing engine the counter can trust.
The final solution must be a public GitHub repository, and its root folder must contain:

README.md
REASONING.md
AI_LOGS.md

AI_LOGS.md must contain the complete AI conversation exactly as required by the assessment."
Your job is to guide me through the implementation inside GitHub Codespaces.
IMPORTANT:

Do NOT give me long explanations.
Do NOT give me background theory.
Do NOT give me a high-level essay.
Give me ONLY direct, numbered, actionable steps.
Keep each step short and beginner-friendly.
Whenever I need to run a command, show the exact command.
Whenever I need to create/edit a file, give me the exact file path and tell me what to do.
Do not make unnecessary files or use unnecessary technologies.
Keep the project simple and assessment-friendly.
Do not skip testing.
Do not assume unspecified business rules. If an exact requirement is missing, stop and ask me only for that missing requirement.
Do not move to the next major stage until I confirm that the current stage is completed.

Start with STEP 1 only.
For STEP 1:

Tell me exactly what to do in GitHub Codespaces.
Include the exact commands, if any.
Tell me exactly what files/folders should be created.
End by asking me to confirm when STEP 1 is complete.

Do not provide STEP 2 or any later step until I confirm STEP 1 is complete.

Two things before STEP 1
AI_LOGS.md risk: It must contain the complete AI conversation. Your planning chat with me earlier is part of that. If you only start logging from now, the log is incomplete and you can lose marks. Plan to paste everything, including that earlier session.
Stack assumption I'm making: Python + pytest, money stored as integer paisa (no floats). This matches your background and the "exact paisa" requirement. Tell me now if you want something else, because changing later costs rework.
STEP 1 — Repo + Codespace skeleton
On GitHub, click New repository.
Name: multiplex-pricing-engine
Visibility: Public
Tick Add a README file
Click Create repository
On the repo page, click Code → Codespaces tab → Create codespace on main. Wait for the editor to load.
In the Codespace terminal, check Python:
bash
python3 --version

Expect 3.10 or higher. Tell me if it's lower.

Create the folder and file structure:
bash
mkdir -p pricing tests
touch REASONING.md AI_LOGS.md requirements.txt .gitignore
touch pricing/__init__.py pricing/engine.py tests/test_engine.py
Put pytest in requirements.txt:
bash
echo "pytest" > requirements.txt
Put this in .gitignore:
bash
printf "__pycache__/\n*.pyc\n.pytest_cache/\n" > .gitignore
Install pytest:
bash
pip install -r requirements.txt
Confirm pytest works (it will say "no tests ran" — that is correct for now):
bash
python3 -m pytest
Commit and push:
bash
git add .
git commit -m "Set up project skeleton"
git push
Check the structure:
bash
ls -R

Expected result:

README.md
REASONING.md
AI_LOGS.md
requirements.txt
.gitignore
pricing/__init__.py
pricing/engine.py
tests/test_engine.py

All files except README.md, requirements.txt and .gitignore are empty right now. That is intentional.

Reply "STEP 1 done" when all 10 steps are finished and pushed. Also tell me if you disagree with Python + integer paisa, before we go further.

done

Good. Before STEP 2, I need exact business rules — you told me not to assume these, and the problem statement doesn't specify them. Answer only what you know; if the assessment doesn't say, tell me and we'll pick a reasonable default and document it in REASONING.md.

Tier prices — exact price for Silver, Gold, Recliner (in ₹)?
Festival discount — flat amount in ₹? Applied per ticket or per booking?
Member discount — percentage value, and the cap (max ₹ discount, or max % after cap)?
Discount stacking — if both festival and member discounts apply, in what order, and on what base (original price, or after the other discount)?
Convenience fee — exact ₹ amount per ticket, and is it before or after discounts?
GST rate — percentage, and is it applied on (ticket price − discounts) or on (ticket price − discounts + convenience fee)?
Rounding rule — when a calculation doesn't land on a whole paisa, round up, round down, or round to nearest?
Sold-out tiers — is availability given as a seat count per tier, or just a boolean flag ("sold out: yes/no")?

Give me what's specified in your assessment doc. Whatever's missing, say "not specified" and we'll lock a default together.

Reconciling the mismatched test counts.

All 44 pass, pushed cleanly. (My earlier "~46" estimate was just a rough guess — actual is 29 + 15 new importer tests = 44, correct.)