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
	sphinx-autobuild -b html --watch ../pyobs-core/ $(ALLSPHINXOPTS) "$(SOURCEDIR)/" "$(BUILDDIR)/html/"

github: export PYTHONPATH=$PYTHONPATH:../pyobs-andor:../pyobs-archive:../pyobs-ascom:../pyobs-core:../pyobs-fli:../pyobs-gemini:../pyobs-gui:../pyobs-pilar:pyobs_qhyccd:../pyobs-sbig:../pyobs-weather

github:
	make html && rsync -a --delete $(BUILDDIR)/html/* ../pyobs.github.io/

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

