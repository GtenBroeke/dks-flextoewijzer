@ECHO OFF

if "%1" == "env" (
    conda env create -f dks-flextoewijzer_env.yml
)

if "%1" == "docs" (
    pushd docs \
	make clean \
	make html \
	popd \
	start "" "docs\_build\html\index.html"
)

if "%1" == "tests" (
    pytest tests
)

if "%1" == "remove_env" (
    conda env remove -n dks-flextoewijzer
)

:end
