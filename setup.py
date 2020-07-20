import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="odoo_xmlrcp_migration",
    version="0.0.1",
    author="filoquin",
    author_email="filquin@sipecu.com.ar",
    description="Semi-automatized odoo migration scrip",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/filoquin/xmlrcp_migration",
    packages=setuptools.find_packages(),
    package_data={},
    include_package_data=False,
    classifiers=(
        "Programming Language :: Python :: 2-3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
)
