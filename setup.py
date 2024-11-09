from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="recaptcha_solver_google",
    version="0.0.1",
    author="Mohd Shakir",
    description="A package to solve Google reCAPTCHA using Selenium.",
    long_description=long_description,
    long_description_content_type="text/markdown",  # Specify markdown format
    url="https://github.com/yourusername/recaptcha_solver_google",  # Replace with your URL
    packages=find_packages(),
    install_requires=[
        "selenium",
        "pydub",
        "SpeechRecognition",
        "urllib3",
        "platform",
        "zipfile",
        "tarfile"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
