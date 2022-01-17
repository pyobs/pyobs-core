# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SPHINXPROJ    = pyobs
SOURCEDIR     = source
BUILDDIR      = ../.doc-build

#.EXPORT_ALL_VARIABLES:

#PYTHONPATH:=../pyobs-core/:../pyobs-sbig/:../pyobs-fli:../pyobs-weather:../pyobs-archive:${PYTHONPATH}

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

html:
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS)

livehtml:
	sphinx-autobuild -b html --watch ../pyobs/ $(ALLSPHINXOPTS) "$(SOURCEDIR)/" "$(BUILDDIR)/html/"

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

