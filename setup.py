import glob
from setuptools import setup
from setuptools import find_packages

setup(
  name="freemindlatex",
  version="1.0",
  author="Huichao Xue",
  author_email="xue.huichao@gmail.com",
  url="https://github.com/xuehuichao/freemind-latex",
  license="MIT",
  description="Compiles your freemind document into latex beamer.",
  keywords="freemind beamer latex slides editor",
  packages=find_packages("src"),
  package_dir={"": "src"},
  test_suite="tests",
  platforms="any",
  zip_safe=True,
  include_package_data=True,
  entry_points={'console_scripts': [
      "freemindlatex = freemindlatex.__main__:main"]},
  data_files=[
    ("static_files", glob.glob("static_files/*")),
  ]
)
