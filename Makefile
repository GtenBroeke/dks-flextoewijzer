.PHONY: env docs tests remove_env

env:
	conda env create -f dks-flextoewijzer_env.yml

docs:
	cd docs; \
	make clean; \
	make html; \
	cd ..

tests:
	pytest tests

remove_env:
	conda env remove -n dks-flextoewijzer
