"""
question_answerer.py - Answers LinkedIn Easy Apply custom questions using
the static key/value mappings defined in additionalQuestions.yaml.

This implements the feature that additionalQuestions.yaml was originally
designed for (previously an unused "PRO FEATURE" stub with no code behind
it): scanning the Easy Apply form for input fields, radio-button groups,
and dropdowns, matching each question's visible label text against the
keywords configured in additionalQuestions.yaml, and filling/selecting the
configured answer.

Matching strategy:
- Case-insensitive substring match: if a configured keyword appears
  anywhere in the question's label text, that keyword's answer is used.
- For input fields: the keyword is typed only into empty fields so we
  never overwrite something already filled in automatically by LinkedIn.
- For radio buttons: we look for an option whose visible text matches
  the configured answer, or equals "yes"/"no" exactly when the answer is
  a boolean-ish string.
- For dropdowns (<select> or ARIA listbox-style widgets): we select the
  option whose visible text matches the configured answer.

This is a best-effort heuristic matcher, not a guarantee every question
will be answered correctly -- always review applications in `dryRun`
mode first.
"""
import os
from typing import Dict, Optional

import yaml
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

import utils


class QuestionAnswerer:
    def __init__(self, yaml_path: str = "additionalQuestions.yaml"):
        self.yaml_path = yaml_path
        self.input_fields: Dict[str, str] = {}
        self.radio_answers: Dict[str, str] = {}
        self.dropdown_answers: Dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if os.path.exists(self.yaml_path):
            try:
                with open(self.yaml_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                self.input_fields = {
                    str(k).lower(): str(v) for k, v in (data.get("inputField") or {}).items()
                }
                self.radio_answers = {
                    str(k).lower(): str(v) for k, v in (data.get("radio") or {}).items()
                }
                self.dropdown_answers = {
                    str(k).lower(): str(v) for k, v in (data.get("dropdown") or {}).items()
                }
            except Exception as e:
                utils.prYellow(f"⚠️ Warning: Could not load {self.yaml_path}: {str(e)[0:100]}")

        # Merge the user's own answers (e.g. saved via the GUI's "My
        # Answers" tab) on top of the big reference file. The user's
        # values always win on key collisions, and this file is small
        # and safe for a GUI to rewrite freely without destroying the
        # 650+ line example/reference file above.
        try:
            import app_config_store
            my_answers = app_config_store.load_my_answers()
            self.input_fields.update({str(k).lower(): str(v) for k, v in my_answers.get("inputField", {}).items()})
            self.radio_answers.update({str(k).lower(): str(v) for k, v in my_answers.get("radio", {}).items()})
            self.dropdown_answers.update({str(k).lower(): str(v) for k, v in my_answers.get("dropdown", {}).items()})
        except Exception:
            pass

    def _find_answer(self, label_text: str, bucket: Dict[str, str]) -> Optional[str]:
        if not label_text:
            return None
        label_lower = label_text.lower()
        best_match = None
        best_len = -1
        for keyword, answer in bucket.items():
            keyword = keyword.strip()
            if not keyword:
                continue
            if keyword in label_lower and len(keyword) > best_len:
                best_match = answer
                best_len = len(keyword)
        return best_match

    def answer_text_inputs(self, driver, ai_answer_fn=None) -> int:
        """Fill empty text inputs whose associated label matches a
        configured keyword. Returns the number of fields filled.

        If no static keyword match is found and `ai_answer_fn` is
        provided (a callable taking the question's label text and
        returning an answer string, or None), it is used as a fallback
        so AI-generated answers (ai_engine.py) can cover questions not
        present in additionalQuestions.yaml / my_answers.yaml.
        """
        filled = 0
        try:
            inputs = driver.find_elements(
                By.XPATH,
                "//input[@type='text' or @type='number' or not(@type)] | //textarea",
            )
        except Exception:
            return filled

        for field in inputs:
            try:
                if not field.is_displayed():
                    continue
                current_value = field.get_attribute("value") or ""
                if current_value.strip():
                    continue  # don't overwrite an already-filled field

                label_text = self._get_label_text(driver, field)
                answer = self._find_answer(label_text, self.input_fields)
                if answer is None and ai_answer_fn and label_text:
                    try:
                        answer = ai_answer_fn(label_text)
                    except Exception:
                        answer = None
                if answer:
                    field.clear()
                    field.send_keys(answer)
                    filled += 1
            except Exception:
                continue
        return filled

    def answer_radio_groups(self, driver) -> int:
        """Select radio buttons / checkbox groups whose question text
        matches a configured keyword. Returns the number of groups
        answered."""
        answered = 0
        try:
            fieldsets = driver.find_elements(By.XPATH, "//fieldset")
        except Exception:
            return answered

        for fieldset in fieldsets:
            try:
                legend_text = ""
                try:
                    legend_text = fieldset.find_element(By.XPATH, ".//legend").text
                except Exception:
                    legend_text = fieldset.text[:200]

                answer = self._find_answer(legend_text, self.radio_answers)
                if answer is None:
                    continue

                options = fieldset.find_elements(
                    By.XPATH, ".//input[@type='radio' or @type='checkbox']"
                )
                target_text = answer.strip().lower()
                selected_this_group = False
                for opt in options:
                    try:
                        opt_label = self._get_label_text(driver, opt).strip().lower()
                        if opt_label == target_text or target_text in opt_label:
                            if not opt.is_selected():
                                opt.click()
                            selected_this_group = True
                            break
                    except Exception:
                        continue
                if selected_this_group:
                    answered += 1
            except Exception:
                continue
        return answered

    def answer_dropdowns(self, driver) -> int:
        """Select <select> dropdown options whose question text matches
        a configured keyword. Returns the number of dropdowns answered."""
        answered = 0
        try:
            selects = driver.find_elements(By.XPATH, "//select")
        except Exception:
            return answered

        for select_el in selects:
            try:
                if not select_el.is_displayed():
                    continue
                label_text = self._get_label_text(driver, select_el)
                answer = self._find_answer(label_text, self.dropdown_answers)
                if answer is None:
                    continue

                dropdown = Select(select_el)
                target_text = answer.strip().lower()
                for option in dropdown.options:
                    if option.text.strip().lower() == target_text:
                        dropdown.select_by_visible_text(option.text)
                        answered += 1
                        break
            except Exception:
                continue
        return answered

    def answer_all(self, driver, ai_answer_fn=None) -> Dict[str, int]:
        """Run all three answering strategies and return a summary dict
        of how many fields/groups were answered in each category.

        `ai_answer_fn`, if provided, is forwarded to `answer_text_inputs`
        as a fallback for text questions with no static keyword match.
        """
        return {
            "inputs": self.answer_text_inputs(driver, ai_answer_fn=ai_answer_fn),
            "radios": self.answer_radio_groups(driver),
            "dropdowns": self.answer_dropdowns(driver),
        }

    @staticmethod
    def _get_label_text(driver, element) -> str:
        """Best-effort extraction of the human-readable question label
        associated with a form element: checks aria-label, the
        <label for="id">, and finally falls back to nearby text in the
        containing block."""
        try:
            aria_label = element.get_attribute("aria-label")
            if aria_label:
                return aria_label
        except Exception:
            pass

        try:
            element_id = element.get_attribute("id")
            if element_id:
                label = driver.find_element(By.CSS_SELECTOR, f"label[for='{element_id}']")
                if label and label.text:
                    return label.text
        except Exception:
            pass

        try:
            # Walk up a couple of ancestor levels and grab their text as a
            # fallback "question" context.
            container = element
            for _ in range(3):
                container = container.find_element(By.XPATH, "..")
                text = container.text
                if text and len(text.strip()) > 0:
                    return text
        except Exception:
            pass

        return ""