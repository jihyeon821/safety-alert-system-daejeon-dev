"""Regenerate every PM deliverable and the index.  Usage: python docs/_source/build_all.py"""
import build_docx
import build_index
import build_xlsx

if __name__ == "__main__":
    n = len(build_xlsx.build()) + len(build_docx.build())
    out, missing = build_index.build()
    print(f"generated {n} deliverables + index; missing: {missing or 'none'}")
