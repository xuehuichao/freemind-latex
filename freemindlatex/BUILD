load("@py_deps//:requirements.bzl", "requirement")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_grpc_library", "py_proto_library")

py_library(
    name = "init_dir_lib",
    srcs = ["init_dir_lib.py"],
    data = [
        "//freemindlatex/example",
    ],
)

proto_library(
    name = "compilation_service_proto",
    srcs = ["compilation_service.proto"],
)

py_proto_library(
    name = "compilation_service_pb2",
    deps = [":compilation_service_proto"],
)

py_grpc_library(
    name = "compilation_service_pb2_grpc",
    srcs = [":compilation_service_proto"],
    deps = [":compilation_service_pb2"],
)

py_library(
    name = "compilation_client_lib",
    srcs = ["compilation_client_lib.py"],
    data = [
        "@freemind",
    ],
    deps = [
        requirement("python-gflags"),
        ":compilation_service_pb2",
        ":compilation_service_pb2_grpc",
        requirement("grpcio"),
    ],
)

py_test(
    name = "compilation_client_lib_test",
    srcs = ["compilation_client_lib_test.py"],
    deps = [
        ":compilation_client_lib",
    ],
    python_version = "PY2",
)

py_library(
    name = "convert_lib",
    srcs = ["convert_lib.py"],
    deps = [
        requirement("python-gflags"),
        requirement("bibtexparser"),
    ],
)

py_library(
    name = "compilation_server_lib",
    srcs = ["compilation_server_lib.py"],
    data = [
        "@freemind",
    ],
    deps = [
        ":compilation_service_pb2",
        ":compilation_service_pb2_grpc",
        ":convert_lib",
        requirement("futures"),
        requirement("grpcio"),
    ],
)

py_binary(
    name = "freemindlatex_app_main",
    srcs = [
        "freemindlatex_app_main.py",
    ],
    data = [
        "//freemindlatex/static_files",
    ],
    deps = [
        ":compilation_client_lib",
        ":compilation_server_lib",
        ":compilation_service_pb2",
        ":compilation_service_pb2_grpc",
        ":init_dir_lib",
        requirement("six"),
        requirement("portpicker"),
    ],
    python_version = "PY2",
)

py_library(
    name = "integration_test_lib",
    testonly = 1,
    srcs = ["integration_test_lib.py"],
    data = [":freemindlatex_app_main"],
)

py_test(
    name = "test_on_mm_files",
    srcs = ["test_on_mm_files.py"],
    data = ["//freemindlatex/test_data"],
    deps = [
        ":init_dir_lib",
        ":integration_test_lib",
        ":compilation_service_pb2",
        ":compilation_service_pb2_grpc",
        requirement("pypdf2"),
        requirement("timeout-decorator"),
    ],
    python_version = "PY2",
)
