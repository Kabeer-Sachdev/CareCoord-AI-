import re

class TextCleaner:
    @staticmethod
    def clean(text: str) -> str:
        """
        Cleans extracted document text by removing OCR noise, normalizing whitespace,
        and standardizing line breaks.
        """
        if not text:
            return ""

        # Replace non-breaking spaces and special zero-width spaces
        text = text.replace("\u00a0", " ").replace("\u200b", "").replace("\ufeff", "")

        # Normalize carriage returns
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Replace multiple spaces with a single space
        text = re.sub(r"[ \t]+", " ", text)

        # Replace 3 or more consecutive newlines with 2
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Strip leading and trailing whitespace per line
        lines = [line.strip() for line in text.split("\n")]
        cleaned_text = "\n".join(lines).strip()

        return cleaned_text
