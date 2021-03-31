SHELL := /bin/bash
LOCAL := $(PWD)
SELF := makedot

REPOS := $(wildcard repos/*)
REPOS += "utils"

PKGS := $(wildcard $(REPOS:=/dotfiles))
# PKGS := $(wildcard repos/*/dotfiles)
# PKGS += 'utils/dotfiles'

HOOKS_PRE := $(wildcard $(REPOS:=/hooks/pre))
HOOKS_POST := $(wildcard $(REPOS:=/hooks/post))

LOCALBIN := $(abspath ./stowsh/)
STOW := $(LOCALBIN)/stowsh
STOW_ARGS := -v -s -t $(HOME)

.PHONY: $(PKGS) install help prepare main clean $(HOOKS_POST) $(HOOKS_PRE)

main:
	@echo ------------------
	@echo "Usage: make install"
	@echo "            install all repos found in subdir \`repos\`"
	@echo "       make clean"
	@echo "            find and remove all dead links"
	@echo ------------------


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


install: prepare $(HOOKS_PRE) $(PKGS) $(HOOKS_POST)
	@echo ------------------
	@echo all well done.
	@echo ------------------


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


clean:
	@echo ------------------
	@echo Remove all dead symlinks
	@echo ------------------
	find $(HOME) -type l ! -exec test -e {} \; -delete


help: main
