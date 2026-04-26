def build_prompt(text_blocks: list[str]) -> str:
    return "\n\n".join(block.strip() for block in text_blocks if block.strip())