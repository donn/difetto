
venv/manifest.txt: pyproject.toml poetry.lock
	python3 -m venv venv
	./venv/bin/python3 -m pip install poetry poetry-plugin-export
	./venv/bin/poetry export -f requirements.txt --without-hashes --all-groups --no-interaction > ./requirements.txt
	./venv/bin/python3 -m pip install -r ./requirements.txt
	./venv/bin/python3 -m pip freeze > $@
