[![Build Status](https://travis-ci.org/xuehuichao/freemind-latex.svg?branch=master)](https://travis-ci.org/xuehuichao/freemind-latex)


# Focus on Ideas, and Slides will Follow
This tool converts a mindmap into slides (via LaTeX beamer).

![Focus on your idea, and slides will be generated automatically.](demo.gif)

### Usage
Go to an empty directory and start editing it
```sh
cd /path/to/your/document/directory
freemindlatex
```

It will bring up freemind for editing, evince for slides preview, and keep monitoring the file changes. While you edit the mindmap, slides content will refresh.

## Why not just PowerPoint?

Writing slides is hard -- you have to get the logics and details to work at the same time.

* While you are tweaking the fonts, are you sure the high-level logic already makes sense? 
* Want to move text between slides? Congrats, please re-tweak the fonts again.

With freemindlatex, we ask you to just focus on the logic.

* You see the outline and content in one page, in freemind.
* We format everything automatically for you, in the most professional template -- LaTeX beamer.
* Plus -- you get LaTex math equations for free.

The slides will follow.

## Installation
The tool runs on Linux and MacOS, with Python.
You'll need to first install LaTeX, python, [pip](https://pypi.python.org/pypi/pip), and a PDF viewer.

### Linux

Install Latex and most of the packages. For example, in Ubuntu, that would be
```sh
sudo apt-get install texlive-full python evince
pip install freemind-latex
```

### MacOS

You'll need to install

1. MacTex: https://tug.org/mactex/
2. Skim: http://skim-app.sourceforge.net/

Then
```sh
pip install freemind-latex
```

## For development

### Testing

```sh
virtualenv testenv
source testenv/bin/activate
pip install --upgrade . && python -m pytest tests/
```

### Release

```sh
python setup.py sdist
python setup.py bdist_wheel
python setup.py bdist_wheel --universal
twine upload dist/*
```
