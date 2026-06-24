import sys, pathlib
SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "skills" / "compiling-graphify-wiki" / "scripts"
sys.path.insert(0, str(SCRIPTS))
GEN_SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "skills" / "generating-knowledge-graph" / "scripts"
sys.path.insert(0, str(GEN_SCRIPTS))
sys.path.insert(0, str(GEN_SCRIPTS / "backends"))
