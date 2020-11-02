import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="twiprocess",
    version="0.0.1",
    description="Tweet processing tool",
    # long_description=long_description,
    # long_description_content_type="text/markdown",
    url="https://github.com/crowdbreaks/twiprocess",
    packages=setuptools.find_packages(),
    # Updated for fasttext model
    install_requires=[
        'pandas', 'shapely', 'unidecode', 'emoji'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"],
    python_requires='>=3.6')
