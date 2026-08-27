"""Terminal UI formatting, menus, progress bars, and report viewers for Pipeline Console Application."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# ANSI Color Code Constants
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"


def flush_stdin() -> None:
    """Flush pending unread input characters from sys.stdin buffer across Windows and Unix platforms."""
    try:
        if sys.platform == "win32":
            import msvcrt
            while msvcrt.kbhit():
                msvcrt.getch()
        else:
            if sys.stdin.isatty():
                import termios
                termios.tcflush(sys.stdin, termios.TCIFLUSH)
    except Exception:
        pass


class ConsoleUI:
    """Terminal UI helper providing banners, menus, progress bars, and formatted reports."""

    @staticmethod
    def read_multiline_input(prompt_prefix: str = "> ") -> str:
        """Read single-line or multi-line pasted text from terminal input."""
        lines = []
        try:
            first_line = input(prompt_prefix)
        except (EOFError, KeyboardInterrupt):
            return ""

        if not first_line.strip():
            return ""

        lines.append(first_line)

        # Collect additional lines pasted in buffer
        while True:
            has_more = False
            try:
                if sys.platform == "win32":
                    import msvcrt
                    time.sleep(0.02)
                    has_more = msvcrt.kbhit()
                else:
                    import select
                    if sys.stdin.isatty():
                        r, _, _ = select.select([sys.stdin], [], [], 0.02)
                        has_more = bool(r)
            except Exception:
                has_more = False

            if has_more:
                try:
                    line = input()
                    lines.append(line)
                except (EOFError, KeyboardInterrupt):
                    break
            else:
                break

        return "\n".join(lines).strip()

    @staticmethod
    def print_banner() -> None:
        """Display main header banner."""
        print(f"\n{CYAN}{BOLD}{'=' * 70}{RESET}")
        print(f"{CYAN}{BOLD}         AI SOFTWARE ARCHITECTURE PLATFORM — UNIFIED PIPELINE{RESET}")
        print(f"{CYAN}{BOLD}{'=' * 70}{RESET}\n")

    @staticmethod
    def main_menu() -> str:
        """Display main input selection menu."""
        print(f"{BOLD}Select Input Type:{RESET}")
        print(f"  1. Text Prompt")
        print(f"  2. PDF Document (.pdf)")
        print(f"  3. Word Document (.docx)")
        print(f"  4. Markdown Document (.md)")
        print(f"  5. Existing ARSRS JSON (Skip REE)")
        print(f"  6. Exit\n")
        flush_stdin()
        sys.stdout.flush()
        return input(f"{BOLD}Choice [1-6]: {RESET}").strip()

    @staticmethod
    def draw_progress_bar(current: int, total: int, stage_name: str, elapsed_sec: float) -> None:
        """Render live ASCII progress bar with stage name and elapsed time."""
        bar_len = 24
        filled_len = int(round(bar_len * current / float(total)))
        percents = round(100.0 * current / float(total), 1)
        bar = "#" * filled_len + "-" * (bar_len - filled_len)

        sys.stdout.write(
            f"\r{CYAN}[{bar}]{RESET} ({current:2d}/{total:2d}) {percents:5.1f}% | "
            f"{BOLD}{stage_name[:25]:<25}{RESET} | {YELLOW}{elapsed_sec:5.2f}s{RESET}"
        )
        sys.stdout.flush()
        if current == total:
            sys.stdout.write("\n")

    @staticmethod
    def print_section_header(title: str) -> None:
        """Display stage section header."""
        print(f"\n{BLUE}{BOLD}{'=' * 50}{RESET}")
        print(f"{BLUE}{BOLD} {title}{RESET}")
        print(f"{BLUE}{BOLD}{'=' * 50}{RESET}")

    @staticmethod
    def print_stage_success(stage_name: str) -> None:
        """Print completed stage item."""
        print(f" {GREEN}✓{RESET} {stage_name}")

    @staticmethod
    def print_stage_warning(msg: str) -> None:
        """Print warning item."""
        print(f" {YELLOW}⚠{RESET} {msg}")

    @staticmethod
    def print_stage_error(msg: str) -> None:
        """Print error item."""
        print(f" {RED}✗{RESET} {msg}")

    @staticmethod
    def confirm_action(prompt_msg: str = "Continue to Software Architecture Generation?") -> bool:
        """Prompt user for explicit confirmation (Y/N)."""
        flush_stdin()
        sys.stdout.flush()
        ans = input(f"\n{BOLD}{prompt_msg} (Y/N): {RESET}").strip().upper()
        return ans in ("Y", "YES")


    @staticmethod
    def arsrs_review_menu(arsrs: Dict[str, Any]) -> str:
        """Display ARSRS review gateway options."""
        print(f"\n{GREEN}{BOLD}✓ Requirement Engineering Completed Successfully.{RESET}\n")
        print(f"{BOLD}Options:{RESET}")
        print(f"  1. View ARSRS Summary")
        print(f"  2. Export ARSRS JSON")
        print(f"  3. Continue to Software Architecture Generation")
        print(f"  4. Main Menu / Exit\n")
        flush_stdin()
        sys.stdout.flush()
        return input(f"{BOLD}Choice [1-4]: {RESET}").strip()

    @staticmethod
    def post_execution_menu() -> str:
        """Display post-execution options."""
        print(f"\n{BOLD}What would you like to do next?{RESET}")
        print(f"  1. Open Output Folder")
        print(f"  2. View Executive Review (architecture_review.md)")
        print(f"  3. View Architecture Summary (summary.md)")
        print(f"  4. Generate Another Architecture")
        print(f"  5. Exit\n")
        flush_stdin()
        sys.stdout.flush()
        return input(f"{BOLD}Choice [1-5]: {RESET}").strip()

    @staticmethod
    def print_final_summary(
        request_id: str,
        total_time: float,
        ree_time: float,
        sae_time: float,
        quality_score: float,
        completion_pct: float,
        primary_ref: str,
        output_dir: str,
        files_count: int,
    ) -> None:
        """Display comprehensive final execution summary dashboard."""
        print(f"\n{GREEN}{BOLD}{'=' * 70}{RESET}")
        print(f"{GREEN}{BOLD}                     PIPELINE COMPLETED SUCCESSFULLY{RESET}")
        print(f"{GREEN}{BOLD}{'=' * 70}{RESET}")
        print(f" Request ID               : {BOLD}{request_id}{RESET}")
        print(f" Total Execution Time     : {YELLOW}{total_time:.2f}s{RESET} (REE: {ree_time:.2f}s | SAE: {sae_time:.2f}s)")
        print(f" Overall Architectural Quality: {GREEN}{quality_score:.1f}%{RESET}")
        print(f" Overall Field Completion : {GREEN}{completion_pct:.2f}%{RESET}")
        print(f" Primary Reference Match  : {MAGENTA}{primary_ref}{RESET}")
        print(f" Total Generated Files    : {BOLD}{files_count} Artifacts{RESET}")
        print(f" Output Folder            : {CYAN}{output_dir}{RESET}")
        print(f"{GREEN}{'=' * 70}{RESET}\n")

        print(f"{BOLD}Generated Deliverables Checklist:{RESET}")
        items = [
            "ARSRS Specification (arsrs.json)",
            "01 Requirement Analysis JSON",
            "02 Technology Recommendation JSON",
            "03 Architecture Decision Plan JSON",
            "04 HLD Specification JSON",
            "05 Backend LLD Specification JSON",
            "06 Database LLD Specification JSON",
            "07 Frontend LLD Specification JSON",
            "08 Security LLD Specification JSON",
            "09 Cloud LLD Specification JSON",
            "10 Architecture Validation Report JSON",
            "11 Merged Canonical Package JSON",
            "12 Evolution & Governance Package JSON",
            "Reference Architecture Analysis (JSON & MD)",
            "Decision Traceability & RAG Provenance JSON",
            "Completeness & Audit Report JSON",
            "7-Dimension Quality Report JSON",
            "Interactive Single-File HTML Report (report.html)",
            "Executive Architecture Review Report (architecture_review.md)",
        ]
        for item in items:
            print(f"  {GREEN}✓{RESET} {item}")
        print(f"{GREEN}{'=' * 70}{RESET}")

    @staticmethod
    def display_file_content(file_path: Path) -> None:
        """View text content of a markdown or summary file."""
        if not file_path.exists():
            print(f"{RED}File not found: {file_path}{RESET}")
            return

        print(f"\n{CYAN}{BOLD}--- Displaying: {file_path.name} ---{RESET}\n")
        try:
            content = file_path.read_text(encoding="utf-8")
            print(content)
        except Exception as e:
            print(f"{RED}Error reading file: {e}{RESET}")
        print(f"\n{CYAN}{BOLD}--- End of File ---{RESET}\n")
