from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="kal_utils",
    version="0.1.0",
    author="Bar Horovitz",
    author_email="barh@kaleidoo.ai",
    description="A utility library for event messaging, monitoring, and storage managers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kaleidoo-ai/Kal-Utils",
    packages=find_packages(include=["kal_utils", "kal_utils.*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    extras_require={
        "dev": [
            line.strip()
            for line in open("requirements_dev.txt")
            if line.strip() and not line.startswith("#")
        ],
    },
    include_package_data=True,
    package_data={
        "kal_utils": [
            "event_messaging/**/*",
            "logging/**/*",
            "monitoring/**/*",
            "storage/**/*",
        ]
    },
)
