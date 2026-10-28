"""CLI script to pre-warm the real-world profile extraction cache.

Usage:
    python -m Validator_Engine_v2.real_world.warm_cache
"""

from __future__ import annotations

import asyncio
import sys
from Validator_Engine_v2.real_world.corpus_loader import CorpusLoader
from Validator_Engine_v2.real_world.profile_extractor import ProfileExtractor


async def main() -> None:
    print("Pre-warming Real-World Benchmark pattern cache...")
    loader = CorpusLoader()
    docs = loader.load_corpus()
    print(f"Loaded {len(docs)} documents from corpus.")

    extractor = ProfileExtractor()
    success_count = 0
    pattern_count = 0

    for idx, doc in enumerate(docs, 1):
        try:
            profile = await extractor.extract_profile(doc)
            if not profile.extraction_failed:
                success_count += 1
                pattern_count += len(profile.patterns)
                print(f"[{idx}/{len(docs)}] Cached {doc.system_name}: {len(profile.patterns)} patterns")
            else:
                print(f"[{idx}/{len(docs)}] Failed {doc.system_name}: {profile.error}")
        except Exception as exc:
            print(f"[{idx}/{len(docs)}] Error on {doc.system_name}: {exc}")

    print(f"\nWarm cache complete! {success_count}/{len(docs)} systems cached ({pattern_count} total patterns).")


if __name__ == "__main__":
    asyncio.run(main())
