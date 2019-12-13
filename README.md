[![Build Status](https://travis-ci.org/xuehuichao/freemind-latex.svg?branch=master)](https://travis-ci.org/xuehuichao/freemind-latex)


# Focus on Ideas, and Slides will Follow
This tool converts a mindmap into PDF slides (via LaTeX beamer). You can write [complex yet fine-tuned slides](http://www.xuehuichao.com/thesis_slides.pdf) with this tool.

![Focus on your idea, and slides will be generated automatically.](demo.gif)

### Usage
Go to an empty directory and start editing it
```sh
cd /path/to/your/document/directory
python /path/to/freemindlatex.zip
```

It will bring up freemind for editing, evince for slides preview, and keep monitoring the file changes. While you edit the mindmap, slides content will refresh.

## Why not just PowerPoint?

Tweaking fonts suck. But you do it all the time.

* During the first round.
* After you move slides.
* After you add content.
* After you indent a paragraph
* ...

With freemindlatex, we ask you to just focus on the logic.

* Work on the outline, with freemind.
* Auto formatting, with LaTeX beamer.
* Bonus: LaTex math equations for free.


## Installation

The software is packaged into a zip file. It definitely supports Mac and linux.

	bash -c "$(curl -L -s https://raw.githubusercontent.com/xuehuichao/freemind-latex/bazel/install.sh)" -- /path/to/freemindlatex.zip

### Prerequisites

By default, the tool opens a PDF viewer, and compiles LaTeX locally. We will need to 
install a PDF viewer as well as a LaTeX compiler.

For LaTeX compiler, we need the full texlive (https://www.tug.org/texlive).

1. On MacOS: https://tug.org/mactex/
2. On Ubuntu: `sudo apt-get install texlive-full`

For PDF viewer: we need evince, or skim:

1. Evince, for linux: https://wiki.gnome.org/Apps/Evince
2. Skim, for MacOS: http://skim-app.sourceforge.net/


### Running LaTeX remotely
You may also use a remote server (e.g. sword.xuehuichao.com:8117) for LaTeX compilation.
Then, instead of `freemindlatex`, please run `freemindlatex client` in your working directory.


## For development

### Testing
```sh
bazel test ...
```

### Code style checking
```sh
find freemindlatex/ -name *.py |  xargs pylint --rcfile=.pylintrc
```
