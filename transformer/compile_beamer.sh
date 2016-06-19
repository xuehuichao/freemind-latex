#!/bin/bash
set -e

python convert.py --beamer_latex_file=mindmap.tex --mindmap_file=mindmap.mm
pdflatex -interaction=nonstopmode slides.tex
bibtex slides
pdflatex -interaction=nonstopmode slides.tex
pdflatex -interaction=nonstopmode slides.tex
