"""
BSD3513 Introduction to Artificial Intelligence
Lab Report 3 - Chapter 3: Knowledge Representation System
Rule-Based Scholarship Advisory System (Streamlit)

Run locally :  streamlit run StudentID_Lab3.py
Knowledge   :  facts (applicant data) + rules (JSON: name, priority, conditions, action)
Inference   :  forward chaining; every rule is tested against the facts, all rules
               whose conditions are ALL true "apply" (applicable rules), and the
               conflict is resolved by choosing the rule with the HIGHEST priority.
"""

import json
import operator
from typing import Any

# ---------------------------------------------------------------------------
# 1. KNOWLEDGE BASE: the rules supplied in the lab sheet (used EXACTLY)
# ---------------------------------------------------------------------------
DEFAULT_RULES_JSON = """[
  {
    "name": "Top merit candidate",
    "priority": 100,
    "conditions": [
      ["cgpa", ">=", 3.7],
      ["co_curricular_score", ">=", 80],
      ["family_income", "<=", 8000],
      ["disciplinary_actions", "==", 0]
    ],
    "action": {
      "decision": "AWARD_FULL",
      "reason": "Excellent academic & co-curricular performance, with acceptable need"
    }
  },
  {
    "name": "Good candidate - partial scholarship",
    "priority": 80,
    "conditions": [
      ["cgpa", ">=", 3.3],
      ["co_curricular_score", ">=", 60],
      ["family_income", "<=", 12000],
      ["disciplinary_actions", "<=", 1]
    ],
    "action": {
      "decision": "AWARD_PARTIAL",
      "reason": "Good academic & involvement record with moderate need"
    }
  },
  {
    "name": "Need-based review",
    "priority": 70,
    "conditions": [
      ["cgpa", ">=", 2.5],
      ["family_income", "<=", 4000]
    ],
    "action": {
      "decision": "REVIEW",
      "reason": "High need but borderline academic score"
    }
  },
  {
    "name": "Low CGPA \u2013 not eligible",
    "priority": 95,
    "conditions": [
      ["cgpa", "<", 2.5]
    ],
    "action": {
      "decision": "REJECT",
      "reason": "CGPA below minimum scholarship requirement"
    }
  },
  {
    "name": "Serious disciplinary record",
    "priority": 90,
    "conditions": [
      ["disciplinary_actions", ">=", 2]
    ],
    "action": {
      "decision": "REJECT",
      "reason": "Too many disciplinary records"
    }
  }
]"""

# Decision used when no rule applies at all (safe default = human review)
FALLBACK_ACTION = {
    "decision": "REVIEW",
    "reason": "No rule matched; refer to scholarship committee for manual review",
}

# ---------------------------------------------------------------------------
# 2. FACT SCHEMA (field -> (label, type, min, max, default))
# ---------------------------------------------------------------------------
FACT_FIELDS = {
    "cgpa": "Cumulative GPA (0.00 - 4.00)",
    "family_income": "Monthly family income (RM)",
    "co_curricular_score": "Co-curricular score (0 - 100)",
    "community_service_hours": "Community service hours",
    "semester": "Current semester of study",
    "disciplinary_actions": "Disciplinary actions on record",
}

OPERATORS = {
    ">=": operator.ge,
    ">": operator.gt,
    "<=": operator.le,
    "<": operator.lt,
    "==": operator.eq,
    "!=": operator.ne,
}

DECISION_STYLE = {
    "AWARD_FULL": ("success", "Full scholarship awarded"),
    "AWARD_PARTIAL": ("success", "Partial scholarship awarded"),
    "REVIEW": ("warning", "Refer for committee review"),
    "REJECT": ("error", "Application rejected"),
}


# ---------------------------------------------------------------------------
# 3. RULE ENGINE (pure Python, no Streamlit dependency -> easy to test)
# ---------------------------------------------------------------------------
class RuleError(ValueError):
    """Raised when the rule configuration is malformed."""


def parse_rules(text: str) -> list[dict]:
    """Parse + validate the JSON rule configuration. Raises RuleError."""
    try:
        rules = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuleError(f"Invalid JSON (line {exc.lineno}, col {exc.colno}): {exc.msg}")

    if not isinstance(rules, list) or not rules:
        raise RuleError("Rules must be a non-empty JSON list of rule objects.")

    for i, rule in enumerate(rules, start=1):
        where = f"Rule #{i}"
        if not isinstance(rule, dict):
            raise RuleError(f"{where}: must be a JSON object.")
        for key in ("name", "priority", "conditions", "action"):
            if key not in rule:
                raise RuleError(f"{where}: missing key '{key}'.")
        where = f"Rule #{i} ('{rule['name']}')"
        if isinstance(rule["priority"], bool) or not isinstance(rule["priority"], (int, float)):
            raise RuleError(f"{where}: 'priority' must be a number.")
        if not isinstance(rule["conditions"], list) or not rule["conditions"]:
            raise RuleError(f"{where}: 'conditions' must be a non-empty list.")
        for cond in rule["conditions"]:
            if not (isinstance(cond, list) and len(cond) == 3):
                raise RuleError(f"{where}: each condition must be [field, operator, value].")
            field, op, value = cond
            if field not in FACT_FIELDS:
                raise RuleError(
                    f"{where}: unknown field '{field}'. Valid fields: {', '.join(FACT_FIELDS)}."
                )
            if op not in OPERATORS:
                raise RuleError(
                    f"{where}: unknown operator '{op}'. Valid: {', '.join(OPERATORS)}."
                )
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise RuleError(f"{where}: condition value for '{field}' must be a number.")
        action = rule["action"]
        if not isinstance(action, dict) or "decision" not in action or "reason" not in action:
            raise RuleError(f"{where}: 'action' needs 'decision' and 'reason'.")
    return rules


def check_condition(facts: dict[str, Any], cond: list) -> bool:
    """Evaluate a single [field, operator, value] condition against the facts."""
    field, op, value = cond
    return OPERATORS[op](facts[field], value)


def evaluate_rule(facts: dict[str, Any], rule: dict) -> dict:
    """Evaluate every condition of one rule (AND logic) and keep a trace."""
    details = []
    for cond in rule["conditions"]:
        field, op, value = cond
        details.append(
            {
                "condition": f"{field} {op} {value}",
                "applicant_value": facts[field],
                "passed": check_condition(facts, cond),
            }
        )
    return {
        "name": rule["name"],
        "priority": rule["priority"],
        "applies": all(d["passed"] for d in details),
        "details": details,
        "action": rule["action"],
    }


def evaluate_applicant(facts: dict[str, Any], rules: list[dict]) -> dict:
    """
    Forward-chaining inference with conflict resolution.
      1. MATCH   : test every rule against the facts
      2. CONFLICT SET : rules whose conditions are all satisfied
      3. RESOLVE : highest priority wins (ties -> the rule listed first)
      4. ACT     : return the winner's action (or the fallback)
    """
    trace = [evaluate_rule(facts, r) for r in rules]
    applicable = [t for t in trace if t["applies"]]
    # sorted() is stable, so equal priorities keep their original order
    applicable_sorted = sorted(applicable, key=lambda t: -t["priority"])
    winner = applicable_sorted[0] if applicable_sorted else None
    return {
        "decision": winner["action"]["decision"] if winner else FALLBACK_ACTION["decision"],
        "reason": winner["action"]["reason"] if winner else FALLBACK_ACTION["reason"],
        "winning_rule": winner["name"] if winner else "(none - default)",
        "applicable_rules": [t["name"] for t in applicable_sorted],
        "trace": trace,
    }


# ---------------------------------------------------------------------------
# 4. STREAMLIT USER INTERFACE
# ---------------------------------------------------------------------------
def main() -> None:
    import pandas as pd
    import streamlit as st

    st.set_page_config(page_title="Scholarship Advisory (Rule-Based)", page_icon="🎓", layout="wide")
    st.title("🎓 Scholarship Advisory System")
    st.caption("BSD3513 Lab Report 3 · Rule-based knowledge representation · transparent, editable rules")
    st.caption("Enter the applicant information at the sidebar to get the results. Rules can be viewed and edited in the Rules tab.")
    st.caption("To evaluate more applicant can upload in the csv file at Batch (CSV) tab.")

    # editable rules live in session state so edits survive reruns
    if "rules_text" not in st.session_state:
        st.session_state["rules_text"] = DEFAULT_RULES_JSON

    try:
        rules = parse_rules(st.session_state["rules_text"])
        rules_ok = True
    except RuleError as exc:
        rules, rules_ok = [], False
        st.error(f"Rule configuration error: {exc}")

    # ---- Sidebar: applicant facts + Evaluate button -----------------------
    with st.sidebar:
        st.header("Applicant information")
        facts = {
            "cgpa": st.number_input(FACT_FIELDS["cgpa"], 0.0, 4.0, 3.50, 0.01, format="%.2f"),
            "family_income": st.number_input(FACT_FIELDS["family_income"], 0.0, 100000.0, 5000.0, 100.0),
            "co_curricular_score": st.number_input(FACT_FIELDS["co_curricular_score"], 0, 100, 70, 1),
            "community_service_hours": st.number_input(FACT_FIELDS["community_service_hours"], 0, 1000, 20, 1),
            "semester": st.number_input(FACT_FIELDS["semester"], 1, 14, 3, 1),
            "disciplinary_actions": st.number_input(FACT_FIELDS["disciplinary_actions"], 0, 20, 0, 1),
        }
        if st.button("Evaluate", type="primary", use_container_width=True, disabled=not rules_ok):
            st.session_state["result"] = evaluate_applicant(facts, rules)
            st.session_state["result_facts"] = dict(facts)

    tab_eval, tab_rules, tab_batch = st.tabs(["📋 Evaluation", "⚙️ Rules (JSON)", "📦 Batch (CSV)"])

    # ---- Page 1: applicant info, result and explanation -------------------
    with tab_eval:
        st.subheader("Applicant information")
        st.dataframe(
            pd.DataFrame({"Fact": [FACT_FIELDS[k] for k in FACT_FIELDS], "Value": [facts[k] for k in FACT_FIELDS]}),
            hide_index=True, use_container_width=True,
        )

        st.subheader("Result")
        result = st.session_state.get("result")
        if result is None:
            st.info("Enter the applicant information in the sidebar and press **Evaluate**.")
        else:
            if st.session_state["result_facts"] != facts:
                st.warning("The sidebar values changed since the last evaluation. Press Evaluate to update the result.")
            kind, label = DECISION_STYLE.get(result["decision"], ("info", result["decision"]))
            getattr(st, kind)(f"**{result['decision']}** – {label}")
            st.markdown(f"**Winning rule:** {result['winning_rule']}  \n**Reason:** {result['reason']}")
            st.markdown(
                "**Rules that apply (by priority):** "
                + (", ".join(result["applicable_rules"]) if result["applicable_rules"] else "none")
            )

            st.subheader("Why this result? (rule explanation)")
            used = st.session_state["result_facts"]
            st.caption(
                "Each applicant is checked against every rule. A rule only applies if all of its conditions are met. "
                "If multiple rules apply, the rule with the highest priority wins."
            )
            for t in sorted(result["trace"], key=lambda x: -x["priority"]):
                is_winner = t["name"] == result["winning_rule"]
                icon = "✅" if is_winner else ("✅" if t["applies"] else "❌")
                with st.expander(f"{icon} {t['name']} (priority {t['priority']}) → {t['action']['decision']}", expanded=is_winner):
                    st.dataframe(
                        pd.DataFrame(t["details"]).rename(
                            columns={"condition": "Condition", "applicant_value": "Applicant value", "passed": "Met?"}
                        ),
                        hide_index=True, use_container_width=True,
                    )
                    if is_winner:
                        box = DECISION_STYLE.get(t["action"]["decision"], ("info", ""))[0]  # green / yellow / red
                        getattr(st, box)("Selected: highest-priority rule among those that apply.")
                    elif t["applies"]:
                        st.info("This rule applies, but a higher-priority rule takes precedence.")
                    else:
                        st.write(
                            "Does not apply. This rule is for applicants with: "
                            f"*{t['action']['reason']}*"
                        )

    # ---- Page 2: rule editor (Apply only) ---------------------------------
    with tab_rules:
        st.subheader("Rules of evaluation")
        st.write(
            "Edit the JSON to change thresholds, priorities or decisions, or to add rules. "
            f"Fields: `{', '.join(FACT_FIELDS)}`; operators: `{', '.join(OPERATORS)}`."
        )
        edited = st.text_area("Rules (JSON)", value=st.session_state["rules_text"], height=520)
        if st.button("Apply rules", type="primary"):
            st.session_state["rules_text"] = edited
            st.session_state.pop("result", None)  # old result used the old rules
            st.rerun()

    # ---- Page 3: batch CSV ------------------------------------------------
    with tab_batch:
        st.subheader("Evaluate many applicants")
        st.write(f"Upload a CSV with columns: `{', '.join(FACT_FIELDS)}` (an optional `name` column is kept).")
        sample = pd.DataFrame(
            [
                {"name": "A", "cgpa": 3.85, "family_income": 6000, "co_curricular_score": 90,
                 "community_service_hours": 40, "semester": 4, "disciplinary_actions": 0},
                {"name": "B", "cgpa": 3.40, "family_income": 10000, "co_curricular_score": 65,
                 "community_service_hours": 25, "semester": 5, "disciplinary_actions": 1},
                {"name": "C", "cgpa": 2.80, "family_income": 3000, "co_curricular_score": 40,
                 "community_service_hours": 10, "semester": 3, "disciplinary_actions": 0},
                {"name": "D", "cgpa": 2.30, "family_income": 2000, "co_curricular_score": 70,
                 "community_service_hours": 15, "semester": 2, "disciplinary_actions": 0},
                {"name": "E", "cgpa": 3.90, "family_income": 5000, "co_curricular_score": 95,
                 "community_service_hours": 60, "semester": 6, "disciplinary_actions": 2},
            ]
        )
        st.download_button("Download sample CSV", sample.to_csv(index=False), "sample_applicants.csv", "text/csv")
        up = st.file_uploader("CSV file", type="csv")
        df = pd.read_csv(up) if up else sample
        if not up:
            st.info("Showing the built-in sample until you upload a file.")
        missing = [c for c in FACT_FIELDS if c not in df.columns]
        if missing:
            st.error(f"Missing columns: {', '.join(missing)}")
        elif rules_ok:
            out = []
            for _, row in df.iterrows():
                res = evaluate_applicant({k: row[k] for k in FACT_FIELDS}, rules)
                out.append({"decision": res["decision"], "winning_rule": res["winning_rule"], "reason": res["reason"]})
            full = pd.concat([df.reset_index(drop=True), pd.DataFrame(out)], axis=1)
            st.dataframe(full, hide_index=True, use_container_width=True)
            st.bar_chart(full["decision"].value_counts())
            st.download_button("Download results", full.to_csv(index=False), "results.csv", "text/csv")


if __name__ == "__main__":
    main()