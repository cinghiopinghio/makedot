SHELL := /bin/bash
LOCAL := $(PWD)
SELF := makedot
ifndef XDG_DATA_HOME
	XDG_DATA_HOME := ${HOME}/.local/share
endif

# All repos to be installed need to be cloned or copied inside ./repos
REPOS := $(wildcard repos/*)
REPOS += "utils"

PKGS := $(wildcard $(REPOS:=/dotfiles))
TMPL := $(wildcard $(REPOS:=/templates))

HOOKS_PRE := $(wildcard $(REPOS:=/hooks/pre))
HOOKS_POST := $(wildcard $(REPOS:=/hooks/post))

LOCALBIN := $(abspath ./stowsh/)
STOW := $(LOCALBIN)/stowsh
STOW_ARGS := -v -s -t $(HOME)

.PHONY: $(PKGS) $(TMPL) install help prepare main clean $(HOOKS_POST) $(HOOKS_PRE) test all

main:
	@echo ------------------
	@echo "Usage: make install"
	@echo "            install all repos found in subdir \`repos\`"
	@echo "       make clean"
	@echo "            find and remove all dead links"
	@echo ------------------
	echo $(PKGS)


prepare: $(STOW)
	@echo ------------------
	@echo DONE
	@echo ------------------


$(STOW):
	@echo ------------------
	@echo Installing stowsh
	@echo from: https://github.com/mikepqr/stowsh
	@echo ------------------
	mkdir -p $(LOCALBIN)
	curl "https://raw.githubusercontent.com/williamsmj/stowsh/master/stowsh" --output $(STOW)
	chmod 744 $(STOW)


install: prepare $(HOOKS_PRE) $(PKGS) tmpl $(HOOKS_POST)
	@echo -------------------
	@echo All done. No errors
	@echo -------------------


$(HOOKS_PRE):
	@echo ------------------
	@echo Running pre hooks
	@echo ------------------
	$(SHELL) $@


$(HOOKS_POST):
	@echo ------------------
	@echo Running post hooks
	@echo ------------------
	$(SHELL) $@


$(PKGS):
	@echo ------------------
	@echo Installing $(@)
	@echo ------------------
	$(STOW) $(STOW_ARGS) $(@)


$(TMPL):
	@echo ------------------
	@echo Installing $(@)
	@echo ------------------
	python utils/makedottheme.py $(@)


tmpl: $(TMPL)
	@echo ------------------
	@echo Installing $(@)
	@echo ------------------
	$(STOW) $(STOW_ARGS) $(XDG_DATA_HOME)/makedot/compiled


clean:
	@echo ------------------
	@echo Remove all dead symlinks
	@echo ------------------
	find $(HOME) -type l ! -exec test -e {} \; -delete


help: main
