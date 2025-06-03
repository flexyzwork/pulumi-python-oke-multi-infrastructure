# 기본 목표
.DEFAULT_GOAL := help

# 도움말 출력
.PHONY: help
help:
	@echo "Usage:"
	@echo "  make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  help                Show this help message."
	@echo "  add-init            Make __init__ files in python dirs."
	@echo "  venv                Create venv and activate venv."
	@echo "  install             Install dependencies."
	@echo "  tree                Display the project directory structure."
	@echo "  lint                Run code linters."
	@echo "  clean               Clean build files."
	@echo "  zip                 Make zip file for project"
	@echo "  preview             Run Pulumi preview."
	@echo "  up                  Deploy infrastructure with Pulumi."
	@echo "  destroy             Destroy infrastructure with Pulumi."


# 가상환경 생성 및 활성화
.PHONY: venv
venv:
	pyenv exec python -m venv venv && bash -c 'source venv/bin/activate'

# 종속성 설치
.PHONY: install
install:
	pyenv exec python -m venv venv && bash -c 'source venv/bin/activate && \
	pip install --upgrade pip && pip install -e ".[dev]" --config-settings editable_mode=compat && \
	([ ! -d .git ] && git init || echo "Git repository already initialized") && \
	pre-commit install --install-hooks && pre-commit autoupdate'

# 프로젝트 디렉토리 구조 출력
.PHONY: tree
tree:
	tree -I '__pycache__|*.pyc|*.pyo|venv|*.egg-info|build|*.md' > .tree

# lint 실행
.PHONY: lint
lint:
	pre-commit run --all-files

# 빌드 파일 정리
.PHONY: clean
clean:
	find . -type d -name '__pycache__' -exec rm -r {} + && \
	find . -type f -name '*.pyc' -delete && \
	rm -rf venv .mypy_cache .pytest_cache .tree

# 압축
.PHONY: zip clean
zip: clean
	zip -r ziped_project.zip . -x "*/__pycache__/*" -x ".git/*" -x "*/.DS_Store" -x "auto_diagrams/*" -x "codelab_oci_pulumi.egg-info/*" -x "docs/*"

# Pulumi 명령어 실행
.PHONY: preview
preview:
	pulumi preview

.PHONY: up
up:
	pulumi up --yes

.PHONY: destroy
destroy:
	pulumi destroy --yes
