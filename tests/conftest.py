import sys, pathlib
SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "skills" / "compiling-graphify-wiki" / "scripts"
sys.path.insert(0, str(SCRIPTS))
