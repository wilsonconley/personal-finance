# personal-finance

## Prerequisites

- [Python 3.9](https://www.python.org/downloads/release/python-390/)
- [Plaid](https://plaid.com/docs/) API keys
- [Conda](https://anaconda.org/anaconda/conda)
- [Make](https://www.gnu.org/software/make/)

## Setup

Clone the repo and its submodules:

```shell
git clone --recursive https://github.com/wilsonconley/personal-finance.git
```

Set up the Plaid `.env` file with your API keys:

```shell
cp quickstart/.env.example quickstart/.env
vim quickstart/.env
```

Then, you can link your account:

```shell
make link-account
```

Now, set up the finance app to use the linked Plaid account keys for the
environments you want to use (i.e., `sandbox`, `development`, etc.):

```shell
cp finance/api_keys/sample_keystore.py finance/api_keys/keystore.py
vim finance/api_keys/keystore.py
```

Finally, set up the conda environment:

```shell
make init-env
```

## Usage

To run the application:

```shell
python test.py
```

Then you can access the application at [http://localhost:8000](http://localhost:8000)
