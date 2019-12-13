#/bin/bash
set -e

if [[ $# -ne 1 ]]; then
  cat <<EOF
Build freemindlatex into a zip file.

Usage:
  ./install.sh /path/to/target/file.zip
EOF
  exit 1
fi
target_loc="$1"

compile_dir=$(mktemp -d)
finish() {
  rm -Rf "$compile_dir"
}
trap finish EXIT

cd "$compile_dir"
curl -s -L https://github.com/xuehuichao/freemind-latex/archive/bazel.zip -o freemindlatex.zip
unzip -q freemindlatex.zip
cd freemind-latex-bazel
./bazel build -c opt --build_python_zip freemindlatex:freemindlatex_app_main
cp bazel-out/k8-py2-opt/bin/freemindlatex/freemindlatex_app_main.zip -f "$target_loc"
cat <<EOF
Installed freemindlatex to $target_loc.

Please consider adding the following line to ~/.bashrc file:

alias freemindlatex="python $target_loc"
EOF
