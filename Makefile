PYTHON ?= .venv/bin/python
LATEXMK ?= latexmk
PNPM ?= pnpm
TEXBIN := /Library/TeX/texbin
export PATH := $(TEXBIN):$(PATH)

.PHONY: all setup data check cv site
.NOTPARALLEL:
all: site

setup:
	python3 -m venv .venv
	$(PYTHON) -m pip install -r requirements.txt

data:
	$(PYTHON) scripts/publications.py

check:
	$(PYTHON) scripts/publications.py --check
	$(PYTHON) -m unittest discover -s scripts -p 'test_*.py'

cv:
	$(PYTHON) scripts/publications.py --cv
	cd cv && $(LATEXMK) -interaction=nonstopmode -halt-on-error main.tex
	cp cv/build/main.pdf public/pdf/zhuolun_he_cv.pdf

# The production site always includes a CV compiled from the current sources.
site: cv
	$(PNPM) exec astro build
