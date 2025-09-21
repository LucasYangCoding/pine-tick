import pathlib

from setuptools import setup, find_packages


here = pathlib.Path(__file__).parent.resolve()

setup(
    name="PineTick",
    version="0.0.6",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    description="Placeholder package to reserve the name",
    long_description=(here / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    author="LucasYang",
    author_email="lucas.yang.email@gmail.com",
    python_requires=">=3.9",
    project_urls={
        "Source code": "https://github.com/LucasYangCoding/pine-tick",
        "Changelog": "https://github.com/LucasYangCoding/pine-tick/blob/main/CHANGELOG.md",
        "Documentation": "https://github.com/LucasYangCoding/pine-tick/blob/main/DOCS.md"
    },
    license="MIT"
)
