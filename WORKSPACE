new_http_archive(
  name="freemind",
  url="https://versaweb.dl.sourceforge.net/project/freemind/freemind/1.0.0/freemind-bin-1.0.0.zip",
  sha256="c97b19bb9b021cc0987a85bf0fd8dffa127f02e7736cf7aaf9f86723305c9a7d",
  build_file="BUILD.freemind"
)


git_repository(
  name="io_bazel_rules_python",
  remote="https://github.com/bazelbuild/rules_python.git",
  commit="44711d8ef543f6232aec8445fb5adce9a04767f9",
)

git_repository(
  name="io_bazel_rules_docker",
  remote="https://github.com/bazelbuild/rules_docker.git",
  tag="v0.3.0",
)

load("@io_bazel_rules_python//python:pip.bzl", "pip_repositories")
pip_repositories()
load(
  "@io_bazel_rules_python//python:python.bzl",
  "py_binary", "py_library", "py_test",
)
load("@io_bazel_rules_python//python:pip.bzl", "pip_import")
pip_import(
  name="py_deps",
  requirements="//:requirements.txt",
)

load("@py_deps//:requirements.bzl", "pip_install")
pip_install()

load(
  "@io_bazel_rules_docker//container:container.bzl",
  "container_pull",
  container_repositories="repositories",
)

container_repositories()

container_pull(
  name="python_base",
  registry="index.docker.io",
  repository="library/python",
  tag="2.7",
)


load(
  "@io_bazel_rules_docker//python:image.bzl",
  _py_image_repos="repositories",
)

_py_image_repos()

git_repository(
  name="org_pubref_rules_protobuf",
  remote="https://github.com/pubref/rules_protobuf",
  tag="v0.8.1",
)

load("@org_pubref_rules_protobuf//python:rules.bzl", "py_proto_repositories")
py_proto_repositories()
