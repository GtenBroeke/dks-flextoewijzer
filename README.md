# dks-flextoewijzer

> This readme functions as a template for a readme that is required as part of the code base.
> A sound documentation helps colleagues to quickly grasp the working of the algorithm and why certain choices have been
> made.
>
> The readme should (if applicable) contain the following sections:
> - Table of contents
> - Introduction / Project background
> - Installation instructions
> - Quick start
> - Info on the code
> - Steps
>   - Filtering
>   - Input (data)
>   - Runtime
>   - Output
> - Parameter settings
> - Assumptions
> - Contact information
> - Repository structure

## Introduction / Project background

___
> What, why, how?
> What does the algorithm/model do, how this process came to live and who has worked on the project.
> Also explain why this project exists in the first place.

## Installation instructions

___
> Short description on how to install the package.
> Also explain certain prerequisites and non-Python dependencies, such as a database, Tesseract, specific Java versions,
> etc.
> If certain (API) credentials, database passwords, etc. are needed, please include information (e.g. on how to get
> those) as well.

### Instructions for conda environment (recommended)

1. Make sure you have `conda` installed on your system. If not, install
   [Miniconda](https://docs.conda.io/en/latest/miniconda.html).
2. Open a terminal, clone the repository and `cd` into the repository.
3. Create a conda environment named dks-flextoewijzer, install the project and its dependencies:

   `make env`

4. Select the conda environment in your favourite IDE, or activate it in the terminal via:

   `conda activate dks-flextoewijzer`

   Optional: To install the requirements for development, testing and creating documentation, run:

   `pip install -e .[dev,docs,tests]`

5. If you are in the created conda environment, you can run for instance the data preparation code via:

   `python flex_package/data/prepare_data.py`

### Instructions for manual installation

1. Open a terminal, clone the repository and `cd` into the repository.
2. Install the project and its dependencies:

   `pip install -e .`

   Optional: To install the requirements for development, testing and creating documentation, run the following line
   instead:

   `pip install -e .[dev,docs,tests]`

3. If you are in the created conda environment, you can run for instance the data preparation code via:

   `python flex_package/data/prepare_data.py`

4. Finally, to remove the package from the environment it is currently installed:

   `pip uninstall flex_package`

   However `pip` does not remove all the dependencies that were installed alongside the package. Consider using for
   instance [pip-autoremove](https://pypi.org/project/pip-autoremove/) for this purpose.

## Quick start

___
> Where to start with the project?
> What is / what are the entrypoint(s) for the script?
> Maybe include an example of how to use the code.

## Commands

___

The following commands can be used from the terminal:

- `make env`: create a conda environment named 'dks-flextoewijzer', install the project and its
  dependencies.
- `make remove_env`: remove the conda environment.

If the additional requirements for development, tests and creating documentation are installed:

- `make tests`: run the tests.
- `make docs`: generate Sphinx documentation (HTML page in docs folder).

## Info on the code

___
> In the readme we expect a description of the code. The following information shall be present:
> - Steps
> - Filtering
> - Input (data)
> - Runtime
> - Output
>
> Also include some higher-level information, such as why a random forest is chosen, why 10% is used as training data,
> etc.

### Steps

> Overview of ‘steps’, such as data cleaning, feature engineering, model training, etc. Also mention which
> script/function corresponds with which step.

### Filtering

> Which filters are applied, and why?
> For example, why filter sundays from the training data?
> Why filter companies that don't have a KVK-number?

### Input (data)

> What is the input to the model/algorithm?

The model for predicting 'afvoertekorten' requires the output data from the 'afvoervoorspeller', which should be run in advance
of the process day. This data is used by the model to compute a 'baseline' for the expected afvoer. 

The model uses transport data from VAR to determine planned inter transport. This data should be obtained in advance of the process
day to be combined with the data from the 'afvoerlijnvoorspeller'. During the process day the VAR data needs to be accessed as well, 
to get the latest status of planned inter tranports. 

The model will need MCP data to get updates regarding how many RC are present at the depot for different directions at the current time. 

> Is there manual input required?
No manual input is required. 

> If a more detailed description of e.g. data types is required, please write a separate readme file.

### Runtime

> How long does each part of the script take?
> Mention all relevant times, both very short and very long time periods.
> For example training, which may take hours, versus an API call, which should take a fraction of a second.

### Output

> What does the project/model output? Where does the output get stored, how is it shared with the users?

## Parameter settings

___
> Some models require certain parameter settings, such as the number of trees in random forest.
> Explain what parameters you expect to require changes.
>1) always (each retraining),
>2) regularly (~monthly),
>3) sporadically (~yearly).
>
>Also explain the (desired and undesired) effects of parameter tuning and the reason behind the current settings.

## Assumptions

___
> What assumptions were made for this project?
> Explain the assumptions that were made during development of the algorithm and why they were made.

## Contact information

___
> If the user of the code does need help, where can he/she get it? Who is the maintainer of the code, who is accountable
> for the project? Include name, department and e-mail address.

- Team members:
    - <firstname lastname (e.mail@address), department\>
    - <firstname lastname (e.mail@address), department\>
- Business contact persons:
    - <firstname lastname (e.mail@address), department\>
    - <firstname lastname (e.mail@address), department\>

## Repository structure 57275 - 32747 = 24528 

___

This repository is structured as follows.

```
├───docs                            <- A default Sphinx project with documentation; see sphinx-doc.org for details.
│
├───experiments                     <- Folder for exploration and experiments. Notebooks should be placed here, but it
│                                      can also contain other file types such as python. Naming convention is a
│                                      two-digit number (for ordering), and a short '_' delimited description. E.g.
|                                      '01_data_exploration'.
│
├───pipelines                       <- Scripts to run data pipelines.
│
├───tests                           <- Folder with test scripts (unit/integration/functional tests).
├───flex_package   <- Source code for use in this project.
│   │
│   ├───data                        <- Scripts to retrieve, validate and prepare data
|   |   └──prepare_data.py
│   │
│   ├───models                      <- Scripts to train models, make predictions, run optimization or simulation models.
│   │   ├──optimize_model.py
│   │   ├──predict_model.py
│   │   └──train_model.py
│   │
│   ├───visualization               <- Scripts to create plots and other visualizations.
|   |   └──visualize.py
│   │
|   ├───config.py                   <- Configuration file with parameters.
│   │
│   └───logs.py                     <- Module with generic function for logging.
│
├───.gitignore                      <- File containing all items to ignore.
├───CHANGELOG.md                    <- Log with changes.
├───CONTRIBUTING.md                 <- Description of how to contribute.
├───Dockerfile                      <- Docker configurations.
├───make.bat                        <- Usefull 'make' commands, see Commands section (Windows).
├───Makefile                        <- Usefull 'make' commands, see Commands section (Linux).
├───README.md                       <- The top-level README for developers using this project.
├───requirements.txt                <- The requirements file for reproducing the analysis environment, e.g.
│                                      generated with 'pip freeze > requirements.txt'.
├───setup.py                        <- Makes project pip installable (pip install -e .) so the package can be imported.
├───tox.ini                         <- Configuration file for formatting.
└───dks-flextoewijzer_env.yml    <- Environment configurations.
```
