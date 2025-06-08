from setuptools import setup, find_packages

setup(
    name="aiayer",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "psutil",
        "websockets",
    ],
    python_requires=">=3.7",
    author="SensAI",
    author_email="info@sensai.ai",
    description="Memory system for AI applications",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/sensai/aiayer",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
) 