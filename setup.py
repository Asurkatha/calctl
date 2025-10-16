from setuptools import setup, find_packages


setup(
    name="calctl",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "typer[all]==0.9.0",
        "python-dateutil==2.8.2", 
        "rich==13.5.2",
    ],
    entry_points={
        "console_scripts": [
            "calctl=calctl.app:app",
        ],
    },
    python_requires=">=3.8",
    author="Aarav Surkatha",
    description="A command-line calendar management tool",
)
