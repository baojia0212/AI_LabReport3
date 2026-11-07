# Rule-Based Scholarship Advisory System

**Course: BSD3513 Introduction to Artificial Intelligence**

**Topic: Chapter 3: Knowledge Representation System (Lab Report 3 - Question 2)**

# Project Overview
A Streamlit decision-support app that helps a university scholarship committee screen applicants with transparent, editable IF-THEN rules. Every decision comes with an explanation of which rules were checked and why one was selected.

Try to run the live app below!!
- **Live app:** https://ai-labreport3-rule-based-system.streamlit.app/

## Screenshots Output
<img width="1916" height="767" alt="Screenshot 2026-11-07 014016" src="https://github.com/user-attachments/assets/9ee65ef3-d0e0-472b-9601-f0f037614522" />
<img width="1901" height="787" alt="Screenshot 2026-11-07 014049" src="https://github.com/user-attachments/assets/8a85fde7-d941-451f-a198-6900c9038c19" />
<img width="1900" height="803" alt="Screenshot 2026-11-07 014208" src="https://github.com/user-attachments/assets/a88a563b-a566-4cf0-9cb4-da86ed489160" />
<img width="1907" height="782" alt="Screenshot 2026-11-07 014134" src="https://github.com/user-attachments/assets/45a5e50f-5114-4d03-9a16-61e08fd7293f" />






## Features

- **Sidebar:** enter the applicant's six facts and press **Evaluate**
- **Evaluation page:** applicant information, final decision, winning rule and reason, then a rule-by-rule explanation 
- **Rules page:** edit the rules as JSON and press **Apply rules**; mistakes (bad JSON, unknown field, unknown operator, missing key) are reported without crashing
- **Batch page:** upload a CSV of applicants, view decisions for all of them, see a chart and download the results
- **Safe default:** if no rule applies, the applicant is referred for manual review

## How it works

**Knowledge representation.** Applicant data are the *facts*. Rules are IF-THEN production rules stored as JSON:

```json
{
  "name": "Top merit candidate",
  "priority": 100,
  "conditions": [["cgpa", ">=", 3.7], ["co_curricular_score", ">=", 80]],
  "action": {"decision": "AWARD_FULL", "reason": "Excellent academic & co-curricular performance, with acceptable need"}
}
```

**Inference (forward chaining).**
1. Each applicant is checked against every rule.
2. A rule applies only if all of its conditions are met.
3. If multiple rules apply, the rule with the highest priority wins.
4. If none apply, the result is `REVIEW`.

| Field | Meaning |
|---|---|
| `cgpa` | Cumulative GPA (0.00 to 4.00) |
| `family_income` | Monthly family income (RM) |
| `co_curricular_score` | Co-curricular involvement score (0 to 100) |
| `community_service_hours` | Community service hours |
| `semester` | Current semester of study |
| `disciplinary_actions` | Number of disciplinary actions on record |

Operators: `>=`, `>`, `<=`, `<`, `==`, `!=`

### Default rules (from the lab sheet)

| Rule | Priority | Decision |
|---|---|---|
| Top merit candidate | 100 | AWARD_FULL |
| Low CGPA – not eligible | 95 | REJECT |
| Serious disciplinary record | 90 | REJECT |
| Good candidate - partial scholarship | 80 | AWARD_PARTIAL |
| Need-based review | 70 | REVIEW |

## Run locally

```bash
pip install -r requirements.txt
streamlit run StudentID_Lab3.py
```

## Deploy on Streamlit Community Cloud

1. Push this repository to GitHub (public).
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app**, choose the repository and branch, and set the main file path to `StudentID_Lab3.py`.
4. Click **Deploy**, then copy the public URL into the **Live app** line above.

## Batch CSV format

Required columns: `cgpa, family_income, co_curricular_score, community_service_hours, semester, disciplinary_actions`. An optional `name` column is kept in the output. A sample file can be downloaded from the Batch page.

## Example results

| Applicant | CGPA | Income (RM) | Co-cur. | Disciplinary | Decision |
|---|---|---|---|---|---|
| A | 3.85 | 6000 | 90 | 0 | AWARD_FULL |
| B | 3.40 | 10000 | 65 | 1 | AWARD_PARTIAL |
| C | 2.80 | 3000 | 40 | 0 | REVIEW |
| D | 2.30 | 2000 | 70 | 0 | REJECT |
| E | 3.90 | 5000 | 95 | 2 | REJECT |

