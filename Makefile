
dist-upload:
	pip install twine packaging
	pip install -U twine
	pip install -U packaging
	rm -rf dist/*
	pytest
	python3 -m build .
	twine upload dist/*

