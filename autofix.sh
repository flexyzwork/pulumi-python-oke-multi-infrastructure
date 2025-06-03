#!/bin/bash
# 🚀 초고속 Python 코드 자동 수정 스크립트 (Ruff 통합 버전 v2.0)

set -e  # 오류 시 스크립트 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 로그 함수
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_step() { echo -e "${PURPLE}🔧 $1${NC}"; }

# 도움말 표시
show_help() {
    echo -e "${CYAN}📖 Python 코드 자동 수정 도구 사용법:${NC}"
    echo ""
    echo "  ./autofix.sh [OPTIONS]"
    echo ""
    echo "옵션:"
    echo "  --help, -h              이 도움말 표시"
    echo "  --with-mypy            MyPy 타입 체크 포함"
    echo "  --with-precommit       Pre-commit 훅 실행 포함"
    echo "  --check-only           수정 없이 검사만 수행"
    echo "  --config FILE          사용자 정의 ruff 설정 파일 사용"
    echo "  --target-version VER   Python 버전 지정 (예: py38, py39, py310)"
    echo "  --line-length NUM      최대 줄 길이 설정 (기본값: 88)"
    echo "  --exclude PATTERN      제외할 패턴 (예: migrations/,tests/)"
    echo "  --verbose              상세 출력"
    echo ""
    echo "예시:"
    echo "  ./autofix.sh                                    # 기본 실행"
    echo "  ./autofix.sh --with-mypy --with-precommit       # 모든 도구 포함"
    echo "  ./autofix.sh --check-only                       # 검사만 수행"
    echo "  ./autofix.sh --line-length 120 --verbose        # 줄 길이 120자, 상세 출력"
}

# 매개변수 파싱
WITH_MYPY=false
WITH_PRECOMMIT=false
CHECK_ONLY=false
VERBOSE=false
RUFF_CONFIG=""
TARGET_VERSION=""
LINE_LENGTH="88"
EXCLUDE_PATTERN=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
        --with-mypy)
            WITH_MYPY=true
            shift
            ;;
        --with-precommit)
            WITH_PRECOMMIT=true
            shift
            ;;
        --check-only)
            CHECK_ONLY=true
            shift
            ;;
        --config)
            RUFF_CONFIG="$2"
            shift 2
            ;;
        --target-version)
            TARGET_VERSION="$2"
            shift 2
            ;;
        --line-length)
            LINE_LENGTH="$2"
            shift 2
            ;;
        --exclude)
            EXCLUDE_PATTERN="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        *)
            log_error "알 수 없는 옵션: $1"
            show_help
            exit 1
            ;;
    esac
done

echo -e "${CYAN}🚀 초고속 Python 코드 자동 수정을 시작합니다...${NC}"
echo ""

# Ruff 설치 확인 및 설치
check_and_install_ruff() {
    if ! command -v ruff &> /dev/null; then
        log_warning "Ruff가 설치되지 않았습니다. 설치 중..."
        if command -v pip &> /dev/null; then
            pip install ruff
        elif command -v pip3 &> /dev/null; then
            pip3 install ruff
        else
            log_error "pip 또는 pip3를 찾을 수 없습니다."
            exit 1
        fi
        log_success "Ruff 설치 완료!"
    else
        local ruff_version=$(ruff --version | cut -d' ' -f2)
        log_info "Ruff 버전: $ruff_version"
    fi
}

# Python 파일 확인
check_python_files() {
    local exclude_args=""
    if [[ -n "$EXCLUDE_PATTERN" ]]; then
        exclude_args="--exclude='$EXCLUDE_PATTERN'"
    fi

    local python_files
    if [[ -n "$exclude_args" ]]; then
        python_files=$(find . -name "*.py" -not -path "./.venv/*" -not -path "./venv/*" -not -path "./.git/*" | grep -v -E "$EXCLUDE_PATTERN" | wc -l | tr -d ' ')
    else
        python_files=$(find . -name "*.py" -not -path "./.venv/*" -not -path "./venv/*" -not -path "./.git/*" | wc -l | tr -d ' ')
    fi

    if [[ $python_files -eq 0 ]]; then
        log_warning "Python 파일을 찾을 수 없습니다."
        exit 1
    fi

    log_info "Python 파일 수: $python_files"
}

# Ruff 명령어 옵션 구성
build_ruff_args() {
    local args=""

    if [[ -n "$RUFF_CONFIG" ]]; then
        args="$args --config $RUFF_CONFIG"
    fi

    if [[ -n "$TARGET_VERSION" ]]; then
        args="$args --target-version $TARGET_VERSION"
    fi

    if [[ -n "$EXCLUDE_PATTERN" ]]; then
        args="$args --exclude '$EXCLUDE_PATTERN'"
    fi

    if [[ "$VERBOSE" == true ]]; then
        args="$args --verbose"
    fi

    echo "$args"
}

# 1단계: Ruff 린팅 및 자동 수정
run_ruff_linting() {
    log_step "1단계: 코드 분석 및 자동 수정 중..."
    echo "   - Import 정렬 (isort 대체)"
    echo "   - 사용하지 않는 import 제거 (autoflake 대체)"
    echo "   - 따옴표 통일 (unify 대체)"
    echo "   - 코딩 스타일 수정 (flake8 규칙 적용)"
    echo "   - 타입 어노테이션 개선"
    echo ""

    local ruff_args=$(build_ruff_args)
    local cmd="ruff check . $ruff_args"

    if [[ "$CHECK_ONLY" == false ]]; then
        cmd="$cmd --fix"
    fi

    if [[ "$VERBOSE" == true ]]; then
        cmd="$cmd --show-fixes"
    fi

    if eval $cmd; then
        if [[ "$CHECK_ONLY" == false ]]; then
            log_success "자동 수정 완료!"
        else
            log_success "코드 검사 완료!"
        fi
    else
        log_warning "일부 수정할 수 없는 문제가 발견되었습니다."
    fi
    echo ""
}

# 2단계: Ruff 포맷팅
run_ruff_formatting() {
    if [[ "$CHECK_ONLY" == true ]]; then
        log_info "검사 전용 모드로 포맷팅을 건너뜁니다."
        return
    fi

    log_step "2단계: 코드 포맷팅 중..."
    echo "   - 줄 길이 ${LINE_LENGTH}자로 조정"
    echo "   - 들여쓰기 정규화"
    echo "   - 따옴표 스타일 통일"
    echo "   - 공백 및 빈 줄 정리"
    echo ""

    local format_args="--line-length $LINE_LENGTH"
    if [[ -n "$EXCLUDE_PATTERN" ]]; then
        format_args="$format_args --exclude '$EXCLUDE_PATTERN'"
    fi

    # 포맷팅 미리보기
    if [[ "$VERBOSE" == true ]]; then
        log_info "포맷팅 변경사항 미리보기:"
        eval "ruff format . $format_args --diff" || true
        echo ""
    fi

    # 실제 포맷팅 적용
    if eval "ruff format . $format_args"; then
        log_success "포맷팅 적용 완료!"
    else
        log_warning "포맷팅 중 문제가 발생했습니다."
    fi
    echo ""
}

# 3단계: 최종 검증
run_final_verification() {
    log_step "3단계: 최종 코드 품질 검증..."
    echo "   - Ruff 규칙 준수 확인"
    echo "   - 문법 오류 검사"
    echo "   - 스타일 가이드 준수 확인"
    echo ""

    local ruff_args=$(build_ruff_args)
    local cmd="ruff check . $ruff_args --statistics"

    if eval $cmd; then
        log_success "모든 검증 통과!"
    else
        log_warning "아직 수정이 필요한 항목이 있습니다."
        log_info "수동으로 수정하거나 'ruff check . --fix'를 다시 실행하세요."
    fi
    echo ""
}

# 4단계: MyPy 타입 체크 (선택사항)
run_mypy_check() {
    if [[ "$WITH_MYPY" == false ]]; then
        return
    fi

    log_step "4단계: 타입 체크 실행 중..."
    if command -v mypy &> /dev/null; then
        local mypy_args="--ignore-missing-imports --show-error-codes"
        if [[ -n "$EXCLUDE_PATTERN" ]]; then
            mypy_args="$mypy_args --exclude '$EXCLUDE_PATTERN'"
        fi

        if eval "mypy . $mypy_args"; then
            log_success "타입 체크 완료!"
        else
            log_warning "타입 관련 문제가 발견되었습니다."
        fi
    else
        log_warning "MyPy가 설치되지 않았습니다."
        log_info "'pip install mypy'로 설치하세요."
    fi
    echo ""
}

# 5단계: Pre-commit 훅 실행 (선택사항)
run_precommit_hooks() {
    if [[ "$WITH_PRECOMMIT" == false ]]; then
        return
    fi

    log_step "5단계: Pre-commit 훅 실행 중..."
    if command -v pre-commit &> /dev/void; then
        if pre-commit run --all-files; then
            log_success "Pre-commit 훅 실행 완료!"
        else
            log_warning "Pre-commit 훅에서 문제가 발견되었습니다."
        fi
    else
        log_warning "Pre-commit이 설치되지 않았습니다."
        log_info "'pip install pre-commit'으로 설치하세요."
    fi
    echo ""
}

# 결과 요약
show_summary() {
    echo -e "${CYAN}🎉 초고속 자동 수정 완료!${NC}"
    echo -e "${YELLOW}⏱️  처리 속도: Ruff는 기존 도구들(flake8+isort+yapf+autoflake)보다 10-100배 빠릅니다!${NC}"
    echo ""

    echo -e "${BLUE}🔧 개별 명령어로도 실행 가능합니다:${NC}"
    echo "   ruff check . --fix    # 린팅 + 자동수정"
    echo "   ruff format .         # 포맷팅"
    echo "   ruff check .          # 최종 검증"
    echo ""

    if [[ "$CHECK_ONLY" == false ]]; then
        echo -e "${GREEN}📈 개선 사항:${NC}"
        echo "   - 코드 스타일 통일"
        echo "   - Import 정리 및 최적화"
        echo "   - 사용하지 않는 코드 제거"
        echo "   - PEP 8 스타일 가이드 준수"
        echo "   - 따옴표 스타일 통일"
    fi
}

# 메인 실행 함수
main() {
    check_and_install_ruff
    check_python_files
    run_ruff_linting
    run_ruff_formatting
    run_final_verification
    run_mypy_check
    run_precommit_hooks
    show_summary
}

# 스크립트 실행
main
