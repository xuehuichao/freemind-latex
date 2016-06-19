# freemind-latex
Convert freemind documents into latex or HTML documents.


## How to use it?

The tool runs on Mac and Linux, using Python.
### Installation
You'll need to first install latex, python, python-bibtexparser, python-gflags. Then
```sh
git clone https://github.com/xuehuichao/freemind-latex.git
```

### Usage
```sh
xdg-open transformer/slides.pdf
transformer/inotify_beamer.sh
```
Meanwhile, open `transformer/mindmap.mm` in freemind, and start editing it. Upon file saves, the slides will be updated.

#### Generating PDF slides
1. Create a freemind document. Place `PATH_TO_FREEMIND_LATEX/compile_beamer.sh` into the same directory.
2. Go into the freemind document directory, and run `./compile_beamer.sh`. Then slides.tex will be the slides.


## Why Freemind?

When writing docs/presentations, you'll often found yourself:

* Strayed away from the outline you planned in the beginning.
* Need to move paragraphs/sentences between different sections.
* Missed the point. Or forgot what points you wanted to make in a paragraph/section

Freemind is better than traditional editors:

* Keep outline in-sync with low-level sentences.
* Moving sentences/paragraphs just by dragging -- don't need to select, then copy, then move, then paste.
* Write the point you want to make explicitly, upfront.

## What does freemind-latex do?

This tool converts a freemind document into a doc (HTML or pdf), or slides (pdf). With this tool, you may focus on writing the high-level logic. We take care of formatting it into pretty latex PDFs.
