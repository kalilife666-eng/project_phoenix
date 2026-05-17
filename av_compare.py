#!/usr/bin/env python3
"""
Compare a supporting statement against A/V evidence transcript.

Usage:
  python av_compare.py --statement-file statement.txt --video-file clip.mp4 --output av_report.json
  python av_compare.py --statement-text "..." --transcript-file transcript.txt
"""

import argparse
import json
from pathlib import Path

from charter_analyzer import CharterAnalyzer


def _read_text(path):
    return Path(path).read_text(encoding="utf-8", errors="replace")


def main():
    parser = argparse.ArgumentParser(description="A/V vs supporting statement comparison")
    parser.add_argument("--statement-file", dest="witness_file", help="Path to supporting statement text file")
    parser.add_argument("--statement-text", dest="witness_text", help="Supporting statement text inline")
    parser.add_argument("--witness-file", help=argparse.SUPPRESS)
    parser.add_argument("--witness-text", help=argparse.SUPPRESS)
    parser.add_argument("--video-file", help="Path to video file")
    parser.add_argument("--audio-file", help="Path to audio file")
    parser.add_argument("--transcript-file", help="Optional transcript text file")
    parser.add_argument("--transcript-text", help="Optional transcript text inline")
    parser.add_argument("--output", help="Output JSON path")
    args = parser.parse_args()

    witness_text = args.witness_text or (_read_text(args.witness_file) if args.witness_file else "")
    transcript_text = args.transcript_text or (_read_text(args.transcript_file) if args.transcript_file else "")

    if not witness_text.strip():
        raise SystemExit("A supporting statement is required (--statement-file or --statement-text).")

    analyzer = CharterAnalyzer()
    result = analyzer.analyze_av_against_witness(
        witness_statement_text=witness_text,
        video_path=args.video_file,
        audio_path=args.audio_file,
        transcript_text=transcript_text,
    )

    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(args.output)
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
