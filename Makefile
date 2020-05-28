# -*- mode: makefile -*-

COMPOSE = docker-compose -p mako


.PHONY: run
run:
	$(COMPOSE) build mako
	$(COMPOSE) run mako

.PHONY: down
down:
	$(COMPOSE) down --volumes --rmi=local


.PHONY: format
format:
	black --target-version py37 mako


.PHONY: style
style:
	black --target-version py37 --check mako


.PHONY: complexity
complexity:
	xenon --ignore "tests" --max-absolute A --max-modules A --max-average A mako


.PHONY: test
test:
	pytest -s mako


.PHONY: security-sast
security-sast:
	bandit -r mako -x test


.PHONY: type
type:
	mypy mako --ignore-missing-import
