#!/bin/bash

TIME_FORMAT='%F %H:%M'
OUTPUT_FORMAT='%T Event(s): %e fired for file: %w. Refreshing.'
while inotifywait -q -r --timefmt "${TIME_FORMAT}" --format "${OUTPUT_FORMAT}" mindmap.mm slides.tex convert.py; do
    ./compile_beamer.sh
done
