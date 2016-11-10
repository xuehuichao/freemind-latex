# Write Slides with Mindmaps
This tool converts freemind documents into LaTex Beamer.

### Usage
Go to an empty directory and start editing it
```sh
cd /path/to/your/document/directory
freemindlatex edit
```

It will bring up freemind for editing, evince for slides preview, and keep monitoring the file changes. While you edit the mindmap, slides content will refresh.

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

The tool runs on Linux and MacOS, with Python.
## Installation
You'll need to first install latex, python, python-bibtexparser, python-gflags.
For example, in Ubuntu, that would be
```sh
sudo apt-get install texlive-full python python-bibtexparser python-gflags evince
```

Then just run the installation shell script installtion directory
```sh
# First build an installation dir
INSTALLDIR=/path/to/installation
mkdir -p $INSTALLDIR && cd $INSTALLDIR
# Downloading source code
git clone https://github.com/xuehuichao/freemind-latex.git .
mkdir freemind
cd freemind
curl -L 'http://downloads.sourceforge.net/project/freemind/freemind/1.0.0/freemind-bin-max-1.0.0.zip?r=https%3A%2F%2Fsourceforge.net%2Fprojects%2Ffreemind%2Ffiles%2Ffreemind%2F1.0.0%2F&ts=1478756204&use_mirror=pilotfiber' -o freemind.zip
unzip freemind.zip
# Enablig the freemindlatex command
echo "alias freemindlatex=$INSTALLDIR/bin/freemindlatex" | cat >> ~/.bash_profile
```
Then re-login (e.g. ssh localhost), and you will have access to freemindlatex
