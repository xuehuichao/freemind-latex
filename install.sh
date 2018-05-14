#/bin/bash

bazel build install && bazel-bin/install/install $@
