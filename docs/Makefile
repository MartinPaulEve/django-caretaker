# Minimal makefile for Sphinx documentation
#
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)


# To run with docker, first build the image with `make build-docker-image`
# then you can run `make docker` to generate the autodocs and regular documentation
# if you only want the autodoc in RST format run `make docker-autodoc`
build-docker-image:
	@docker build -f Dockerfile ${PWD}../../ -t django-caretaker/sphinx-rtd
docker-autodoc:
	@docker run  --rm -ti -v ${PWD}:/docs  -v ${PWD}/../django-caretaker:/vol/django-caretaker -e CARETAKER_PATH=/vol/django-caretaker sphinxdoc/sphinx sphinx-apidoc -o "." /vol/django-caretaker/caretaker
docker:
	@bash -c "make docker-autodoc"
	@docker run  --rm -ti -v ${PWD}:/docs  -v ${PWD}/../django-caretaker:/vol/django-caretaker -e CARETAKER_PATH=/vol/django-caretaker django-caretaker/sphinx-rtd

