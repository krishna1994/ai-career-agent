"""
app_config_store.py - Non-destructive user settings storage for the GUI.

Problem this solves: `config.py` is a richly-commented Python file meant to
be hand-edited, and `additionalQuestions.yaml` is a 650+ line reference
file full of example questions in many languages. Having the GUI rewrite
either of those files directly would destroy all of that documentation
the very first time a user clicks "Save".

Instead:
- GUI-editable *settings* (locations, keywords, dryRun, etc.) are stored in
  a small `user_config.json` file. `config.py` loads this file at import
  time and uses any keys found there to OVERRIDE its own defaults, so the
  original file's comments/defaults stay intact and keep working for
  anyone who prefers to hand-edit `config.py` directly (GUI absent).
- GUI-editable *application answers* (name, phone, salary expectations,
  custom Q&A pairs) are stored in a small `my_answers.yaml` file.
  `question_answerer.py` loads the big reference file first, then merges
  `my_answers.yaml` on top (your own answers win), so the original
  `additionalQuestions.yaml` keeps serving as a living example/reference
  without ever being overwritten by the GUI.
"""
import json
import os
from typing import Any, Dict

USER_CONFIG_PATH = "user_config.json"
MY_ANSWERS_PATH = "my_answers.yaml"

# Keys that are safe for the GUI to read/write as simple JSON-serializable
# values. Kept as an explicit allow-list so the GUI can never accidentally
# clobber something it doesn't understand.
SETTINGS_KEYS = [
    "email",
    "password",
    "headless",
    "chromeProfilePath",
    "location",
    "allowedCountries",
    "keywords",
    "experienceLevels",
    "datePosted",
    "jobType",
    "remote",
    "salary",
    "sort",
    "blacklistCompanies",
    "blackListTitles",
    "followCompanies",
    "preferredCv",
    "resumePath",
    "Phone",
    "displayWarnings",
    "dryRun",
    "maxApplicationsPerRun",
    "maxJobsToProcess",
    "use_ai_features",
    "ai_api_key",
    "ai_model",
    "min_ats_score",
    "enable_resume_tailoring",
    # Plain-text resume content used ONLY for AI ATS scoring / resume
    # tailoring / AI-generated question answers (ai_engine.py). This is
    # separate from "resumePath" (the binary PDF/DOCX actually uploaded
    # to LinkedIn's Easy Apply file input) because the AI provider needs
    # plain text, and no PDF/DOCX text-extraction library is bundled.
    "resumeText",
]


def load_user_settings() -> Dict[str, Any]:
    """Load user_config.json, returning {} if it doesn't exist or is invalid."""
    if not os.path.exists(USER_CONFIG_PATH):
        return {}
    try:
        with open(USER_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {}
        return {k: v for k, v in data.items() if k in SETTINGS_KEYS}
    except Exception:
        return {}


def save_user_settings(settings: Dict[str, Any]) -> None:
    """Persist settings to user_config.json. Only known keys are saved."""
    filtered = {k: v for k, v in settings.items() if k in SETTINGS_KEYS}
    with open(USER_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(filtered, f, indent=2, ensure_ascii=False)


def apply_overrides_to_config(config_module) -> None:
    """Override attributes on an already-imported `config` module with any
    values found in user_config.json. Called once from config.py itself."""
    overrides = load_user_settings()
    for key, value in overrides.items():
        setattr(config_module, key, value)


# ---------------------------------------------------------------------------
# my_answers.yaml helpers
# ---------------------------------------------------------------------------

def load_my_answers() -> Dict[str, Dict[str, str]]:
    """Load my_answers.yaml as {section: {keyword: answer}}.
    Returns an empty skeleton if the file doesn't exist yet."""
    import yaml

    skeleton = {"inputField": {}, "radio": {}, "dropdown": {}}
    if not os.path.exists(MY_ANSWERS_PATH):
        return skeleton
    try:
        with open(MY_ANSWERS_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        for section in skeleton:
            section_data = data.get(section) or {}
            if isinstance(section_data, dict):
                skeleton[section] = {str(k): str(v) for k, v in section_data.items()}
        return skeleton
    except Exception:
        return skeleton


def save_my_answers(data: Dict[str, Dict[str, str]]) -> None:
    """Save {section: {keyword: answer}} to my_answers.yaml."""
    import yaml

    # Only persist the three known sections, each as a plain dict.
    to_save = {
        "inputField": dict(data.get("inputField", {})),
        "radio": dict(data.get("radio", {})),
        "dropdown": dict(data.get("dropdown", {})),
    }
    header = (
        "# my_answers.yaml - YOUR personal application answers.\n"
        "# This file is managed by the AI Career Agent app (gui_app.py) and\n"
        "# is merged on top of additionalQuestions.yaml at runtime (your\n"
        "# answers here always take priority). You can also edit this file\n"
        "# by hand using the same inputField/radio/dropdown structure.\n\n"
    )
    with open(MY_ANSWERS_PATH, "w", encoding="utf-8") as f:
        f.write(header)
        yaml.safe_dump(to_save, f, allow_unicode=True, default_flow_style=False, sort_keys=False)