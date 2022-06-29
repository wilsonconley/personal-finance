.PHONY: init-env
init-env:
	conda create --yes -n finance python=3.9
	. ~/.bash_profile && conda activate finance && pip install -e .

.PHONY: link-account
link-account:
	make -C quickstart/ up language=python
