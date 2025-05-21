from setuptools import setup, find_packages

setup(
    name="pylama",
    version="0.1.0",
    description="Python code generation and execution using Ollama language models",
    author="Tom Sapletta",
    author_email="info@softreck.dev",
    license="Apache-2.0",
    packages=find_packages(),
    install_requires=[
        "requests",
        "python-dotenv",
        "pybox",
        "pyllm",
    ],
    entry_points={
        'console_scripts': [
            'pylama=pylama.cli:main',
        ],
    },
    python_requires='>=3.8',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)
