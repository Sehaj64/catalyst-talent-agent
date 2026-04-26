from __future__ import annotations

import argparse

from skillproof.assessment import build_assessment, score_assessment
from skillproof.file_readers import read_file_path
from skillproof.report import build_markdown_report
from skillproof.sample_data import SAMPLE_ANSWERS, SAMPLE_JD, SAMPLE_RESUME


def read_text(path: str | None, fallback: str) -> str:
    if not path:
        return fallback
    return read_file_path(path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SkillProof AI from the command line.")
    parser.add_argument("--jd-file", help="Path to a JD file: TXT, MD, PDF, DOCX, CSV, or XLSX.")
    parser.add_argument("--resume-file", help="Path to a resume file: TXT, MD, PDF, DOCX, CSV, or XLSX.")
    parser.add_argument("--sample", action="store_true", help="Use the bundled sample JD and resume.")
    args = parser.parse_args()

    if not args.sample and not (args.jd_file and args.resume_file):
        parser.error("Use --sample or provide both --jd-file and --resume-file.")

    jd_text = read_text(args.jd_file, SAMPLE_JD)
    resume_text = read_text(args.resume_file, SAMPLE_RESUME)

    assessment = build_assessment(jd_text, resume_text)
    scored = score_assessment(assessment, SAMPLE_ANSWERS)
    print(build_markdown_report(scored))


if __name__ == "__main__":
    main()
