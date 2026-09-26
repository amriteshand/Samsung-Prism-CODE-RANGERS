import re
from typing import Optional


class PipelineSanitizer:
    """
    Sanitizes LLM responses and raw queries to enforce:
    1. Zero Web URL Leaks: Strips http, https, www, markdown links. Permits ONLY bixby://
    2. Pure JSON Output: Strips markdown fences, preambles, and conversational intros.
    3. Syntax Normalization: Ensures 2-3 word sentence-case titles, 5-7 word descriptions, and strict goals.
    """

    WEB_URL_PATTERN = re.compile(r"https?://\S+|www\.\S+|\[([^\]]+)\]\(([^)]+)\)", re.IGNORECASE)
    MARKDOWN_CODE_BLOCK = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)

    @classmethod
    def sanitize_web_urls(cls, text: str) -> str:
        """Removes any web URLs or markdown links, preserving only bixby:// protocol."""
        if not text:
            return ""

        # Replace markdown links [title](url) where url is web
        def replace_md(match):
            label = match.group(1)
            target = match.group(2)
            if target.startswith("bixby://"):
                return f"{label} ({target})"
            return label

        cleaned = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", replace_md, text)

        # Remove http://, https://, www.
        cleaned = re.sub(r"https?://\S+", "", cleaned)
        cleaned = re.sub(r"www\.\S+", "", cleaned)
        return cleaned.strip()

    @classmethod
    def sanitize_uri(cls, uri: str) -> str:
        """Enforces valid bixby:// URI and strips web components."""
        if not uri:
            return "bixby://settings/device_care"
        uri = cls.sanitize_web_urls(uri).strip()
        if not uri.startswith("bixby://"):
            # Normalize to bixby://
            path = uri.lstrip("/").replace(" ", "_").lower()
            return f"bixby://settings/{path}"
        return uri

    @classmethod
    def format_title(cls, title: str) -> str:
        """
        Enforces 2 to 3 words in sentence case.
        Example: 'Swipe navigation settings', 'Battery saving mode'.
        """
        title = re.sub(r"[^\w\s]", "", title).strip()
        words = title.split()
        if not words:
            return "Troubleshoot setting action"
        if len(words) == 1:
            words.append("setting")
        elif len(words) > 3:
            words = words[:3]

        # Sentence case: First word capitalized, remaining words lowercase unless recognized acronym
        acronyms = {"RAM", "HDR", "DNS", "GPS", "NFC", "UWB", "SIM", "APN", "LED", "CPU", "GPU", "OIS", "FHD", "QHD"}
        cased_words = []
        for i, w in enumerate(words):
            if w.upper() in acronyms:
                cased_words.append(w.upper())
            elif i == 0:
                cased_words.append(w.capitalize())
            else:
                cased_words.append(w.lower())

        return " ".join(cased_words)

    @classmethod
    def format_description(cls, desc: str) -> str:
        """
        Enforces exactly 5 to 7 words starting with 'It will...'
        Example: 'It will turn on power saving.' (6 words)
        """
        desc = cls.sanitize_web_urls(desc)
        desc = desc.strip().rstrip(".")
        if not desc.startswith("It will"):
            # Strip preamble and prepend 'It will'
            clean = re.sub(r"^(this will|to|you should|please|will)\s+", "", desc, flags=re.IGNORECASE)
            desc = f"It will {clean}"

        words = desc.split()
        # Words must be 5 to 7
        if len(words) < 5:
            padding = ["for", "your", "device", "settings"]
            for pad in padding:
                if len(words) >= 6:
                    break
                words.append(pad)
        elif len(words) > 7:
            words = words[:6]

        return " ".join(words) + "."

    @classmethod
    def format_goal(cls, topic: str, is_configuration: bool = False) -> str:
        """
        Strictly follows: Follow these steps to perform <Topic> Troubleshooting or Configuration
        """
        # Clean topic
        clean_topic = re.sub(r"[^\w\s]", "", topic).strip().title()
        if not clean_topic:
            clean_topic = "Device System"
        mode = "Configuration" if is_configuration else "Troubleshooting"
        return f"Follow these steps to perform {clean_topic} {mode}"

    @classmethod
    def extract_pure_json(cls, raw_output: str) -> str:
        """
        Strips markdown code blocks, conversational introductions, and trailing remarks
        to guarantee pure raw JSON output.
        """
        if not raw_output:
            return "{}"

        # Match ```json ... ``` or ``` ... ```
        fence_match = cls.MARKDOWN_CODE_BLOCK.search(raw_output)
        if fence_match:
            candidate = fence_match.group(1).strip()
            return candidate

        # Find first '{' or '[' and last '}' or ']'
        start_obj = raw_output.find("{")
        end_obj = raw_output.rfind("}")
        if start_obj != -1 and end_obj != -1 and end_obj > start_obj:
            return raw_output[start_obj : end_obj + 1].strip()

        start_arr = raw_output.find("[")
        end_arr = raw_output.rfind("]")
        if start_arr != -1 and end_arr != -1 and end_arr > start_arr:
            return raw_output[start_arr : end_arr + 1].strip()

        return raw_output.strip()
