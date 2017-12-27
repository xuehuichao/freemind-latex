load("@py_deps//:requirements.bzl", "requirement")
load("@org_pubref_rules_protobuf//python:rules.bzl", "py_proto_library")

py_library(
    name = "init_dir_lib",
    srcs = ["init_dir_lib.py"],
)

py_proto_library(
    name = "compilation_service_proto_lib",
    protos = ["compilation_service.proto"],
    with_grpc = True,
    deps = [requirement("protobuf")],
)

py_binary(
    name = "run_app",
    srcs = [
        "compilation_client_lib.py",
        "compilation_server_lib.py",
        "convert.py",
        "run_app.py",
    ],
    data = [
        "//freemindlatex/example",
        "//freemindlatex/static_files",
        "@freemind",
    ],
    deps = [
        ":compilation_service_proto_lib",
        ":init_dir_lib",
        requirement("six"),
        requirement("python-gflags"),
        requirement("bibtexparser"),
        requirement("pypdf2"),
        requirement("timeout-decorator"),
        requirement("portpicker"),
        requirement("futures"),
        requirement("gevent"),
        requirement("grpcio"),
    ],
)

py_library(
    name = "integration_test_lib",
    testonly = 1,
    srcs = ["integration_test_lib.py"],
    data = [":run_app"],
)

py_test(
    name = "test_on_mm_files",
    srcs = ["test_on_mm_files.py"],
    data = ["//freemindlatex/test_data"],
    deps = [
        ":init_dir_lib",
        ":integration_test_lib",
        requirement("pypdf2"),
        requirement("timeout-decorator"),
    ],
)
