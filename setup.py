import glob
import os

from setuptools import find_packages, setup

freemind_dirlist = []
for (path, dirs, filenames) in os.walk("freemind"):
  freemind_dirlist.append(
    (os.path.join("share/freemindlatex", path),
     [os.path.join(path, filename) for filename in filenames])
  )

setup(
  name="freemindlatex",
  version="1.0.1",
  author="Huichao Xue",
  author_email="xue.huichao@gmail.com",
  url="https://github.com/xuehuichao/freemind-latex",
  license="GPLv2",
  description="Compiles your freemind document into latex beamer.",
  keywords="freemind beamer latex slides editor",
  packages=find_packages("src"),
  package_dir={"": "src"},
  test_suite="tests",
  platforms="any",
  zip_safe=True,
  include_package_data=True,
  entry_points={'console_scripts': [
    "freemindlatex = freemindlatex.main_stub:main",
  ]},
  data_files=[
    ("share/freemindlatex/static_files", glob.glob("static_files/*")),
    ("share/freemindlatex/example", glob.glob("example/*")),
  ] + freemind_dirlist,
  install_requires=open("requirements.txt").read().strip().split(),
)
