#!/bin/bash
# Run from this directory: cd into it first, then: bash compile.sh
set -e
MAIN=main
pdflatex -interaction=nonstopmode $MAIN.tex
bibtex $MAIN
pdflatex -interaction=nonstopmode $MAIN.tex
pdflatex -interaction=nonstopmode $MAIN.tex
echo "Done -- check $MAIN.pdf"
