"""
This script uses the cx_Freeze library to package Python scripts into executable files.
It includes additional files and folders required for the application to work correctly,
and creates an executable that can be distributed to others.

Modules:
    cx_Freeze.setup
    cx_Freeze.Executable

Files included in the build:
    - logo.png: A logo image file for the application.
    - test_scripts: A folder containing test scripts.
    - encrypted_file.jinja2: A Jinja2 template file for encrypted configurations.
    - object_repository.properties: A properties file for object repositories.
    - encrypted_ts_file.jinja2: Another Jinja2 template file for encrypted configurations.
    - start.properties: A properties file to initiate configurations.

Usage:
    To create the executable, run the following command in your terminal:
        python setup.py build
    This will create a `build` folder containing an `exe` folder and necessary scripts.

    To distribute the application, share the `build` folder. To run the application:
        1. Navigate to the `exe` folder.
        2. Open a command prompt.
        3. Type and run: `runner.exe start`.
"""

from cx_Freeze import setup, Executable

# Files to include in the exe folder
include_files = [
    ('logo.png', 'logo.png'),
    ('test_scripts', 'test_scripts'),
    ('encrypted_file.jinja2', 'encrypted_file.jinja2'),
    ('object_repository.properties', 'object_repository.properties'),
    ('encrypted_ts_file.jinja2', 'encrypted_ts_file.jinja2'),
    ('start.properties', 'start.properties')
]

setup(
    name="WebAutFramework",
    version="1.0",
    description="Keyword Framework",
    options={"build_exe": {"include_files": include_files}},
    executables=[Executable("runner.py", base=None)]
)

# run "python setup.py build" command in prompt
# this will create a build folder and under that a exe folder and a runner folder and copies all dependent properties and scripts folder.

# distribute the build folder to others
# for others to run, navigate to exe folder and open command prompt and type "runner.exe start"