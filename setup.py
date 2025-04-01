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