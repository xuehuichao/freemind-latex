#/bin/bash
set -e

if [[ $# -ne 1 ]]; then
  echo <<EOF
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
./bazel build -c opt --build_python_zip freemindlatex:freemindlatex_app_main
cp bazel-bin/freemindlatex/freemindlatex_app_main.zip "$target_loc"
