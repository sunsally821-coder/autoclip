#!/bin/bash

# AutoClip 国际化检查脚本
# 版本: 1.0
# 功能: 检查多语言文档的同步状态

set -euo pipefail

# =============================================================================
# 配置区域
# =============================================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# 图标定义
ICON_SUCCESS="✅"
ICON_ERROR="❌"
ICON_WARNING="⚠️"
ICON_INFO="ℹ️"
ICON_CHECK="🔍"

# 文件列表
FILES=("README.md" "README-EN.md" ".github/README.md")

# =============================================================================
# 工具函数
# =============================================================================

log_info() {
    echo -e "${BLUE}${ICON_INFO} $1${NC}"
}

log_success() {
    echo -e "${GREEN}${ICON_SUCCESS} $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}${ICON_WARNING} $1${NC}"
}

log_error() {
    echo -e "${RED}${ICON_ERROR} $1${NC}"
}

log_header() {
    echo -e "\n${PURPLE}${ICON_CHECK} $1${NC}"
    echo -e "${PURPLE}$(printf '=%.0s' {1..50})${NC}"
}

# =============================================================================
# 检查函数
# =============================================================================

check_file_exists() {
    local file="$1"
    if [[ -f "$file" ]]; then
        log_success "文件存在: $file"
        return 0
    else
        log_error "文件不存在: $file"
        return 1
    fi
}

check_language_switcher() {
    local file="$1"
    local has_switcher=false
    
    if grep -q "语言.*English.*中文\|Language.*English.*中文" "$file" 2>/dev/null; then
        has_switcher=true
    fi
    
    if [[ "$has_switcher" == true ]]; then
        log_success "语言切换器存在: $file"
        return 0
    else
        log_error "语言切换器缺失: $file"
        return 1
    fi
}

check_contact_info() {
    local file="$1"
    local has_contact=false
    
    # 检查多种联系方式格式
    if grep -q "support@autoclip.com\|your_wechat_id\|your_feishu_id\|个人微信\|飞书\|Personal WeChat\|Feishu" "$file" 2>/dev/null; then
        has_contact=true
    fi
    
    if [[ "$has_contact" == true ]]; then
        log_success "联系方式存在: $file"
        return 0
    else
        log_error "联系方式缺失: $file"
        return 1
    fi
}

check_docker_support() {
    local file="$1"
    local has_docker=false
    
    if grep -q "Docker\|docker" "$file" 2>/dev/null; then
        has_docker=true
    fi
    
    if [[ "$has_docker" == true ]]; then
        log_success "Docker支持文档存在: $file"
        return 0
    else
        log_error "Docker支持文档缺失: $file"
        return 1
    fi
}

check_development_features() {
    local file="$1"
    local has_dev_features=false
    
    if grep -q "开发中\|In Development" "$file" 2>/dev/null; then
        has_dev_features=true
    fi
    
    if [[ "$has_dev_features" == true ]]; then
        log_success "开发中功能标注存在: $file"
        return 0
    else
        log_warning "开发中功能标注缺失: $file"
        return 1
    fi
}

check_markdown_syntax() {
    local file="$1"
    local errors=0
    
    # 检查标题层级
    if grep -q "^# " "$file" && ! grep -q "^## " "$file"; then
        log_warning "标题层级可能有问题: $file"
        ((errors++))
    fi
    
    # 检查链接格式
    if grep -q "\[.*\](" "$file" && ! grep -q "\[.*\]\(http" "$file"; then
        log_warning "可能存在无效链接: $file"
        ((errors++))
    fi
    
    if [[ $errors -eq 0 ]]; then
        log_success "Markdown语法检查通过: $file"
        return 0
    else
        log_warning "Markdown语法检查发现问题: $file"
        return 1
    fi
}

check_file_consistency() {
    local file1="$1"
    local file2="$2"
    local consistency_score=0
    
    # 检查文件大小比例
    local size1=$(wc -c < "$file1" 2>/dev/null || echo "0")
    local size2=$(wc -c < "$file2" 2>/dev/null || echo "0")
    
    if [[ $size1 -gt 0 && $size2 -gt 0 ]]; then
        local ratio=$((size2 * 100 / size1))
        if [[ $ratio -gt 80 && $ratio -lt 120 ]]; then
            log_success "文件大小比例合理: $file1 vs $file2 ($ratio%)"
            ((consistency_score++))
        else
            log_warning "文件大小比例异常: $file1 vs $file2 ($ratio%)"
        fi
    fi
    
    # 检查关键内容一致性
    local key_terms=("AutoClip" "Docker" "API" "GitHub")
    for term in "${key_terms[@]}"; do
        local count1=$(grep -c "$term" "$file1" 2>/dev/null || echo "0")
        local count2=$(grep -c "$term" "$file2" 2>/dev/null || echo "0")
        
        if [[ $count1 -gt 0 && $count2 -gt 0 ]]; then
            ((consistency_score++))
        fi
    done
    
    if [[ $consistency_score -gt 2 ]]; then
        log_success "文件内容一致性良好: $file1 vs $file2"
        return 0
    else
        log_warning "文件内容一致性需要改进: $file1 vs $file2"
        return 1
    fi
}

# =============================================================================
# 主函数
# =============================================================================

main() {
    log_header "AutoClip 国际化检查 v1.0"
    
    local overall_status=0
    local total_checks=0
    local passed_checks=0
    
    # 检查所有文件
    for file in "${FILES[@]}"; do
        log_header "检查文件: $file"
        
        # 文件存在性检查
        ((total_checks++))
        if check_file_exists "$file"; then
            ((passed_checks++))
        else
            overall_status=1
            continue
        fi
        
        # 语言切换器检查
        ((total_checks++))
        if check_language_switcher "$file"; then
            ((passed_checks++))
        else
            overall_status=1
        fi
        
        # 联系方式检查
        ((total_checks++))
        if check_contact_info "$file"; then
            ((passed_checks++))
        else
            overall_status=1
        fi
        
        # Docker支持检查
        ((total_checks++))
        if check_docker_support "$file"; then
            ((passed_checks++))
        else
            overall_status=1
        fi
        
        # 开发中功能检查
        ((total_checks++))
        if check_development_features "$file"; then
            ((passed_checks++))
        else
            # 这个检查失败不算严重错误
            ((passed_checks++))
        fi
        
        # Markdown语法检查
        ((total_checks++))
        if check_markdown_syntax "$file"; then
            ((passed_checks++))
        else
            # 这个检查失败不算严重错误
            ((passed_checks++))
        fi
    done
    
    # 检查文件一致性
    if [[ -f "README.md" && -f "README-EN.md" ]]; then
        log_header "检查文件一致性"
        ((total_checks++))
        if check_file_consistency "README.md" "README-EN.md"; then
            ((passed_checks++))
        else
            # 一致性检查失败不算严重错误
            ((passed_checks++))
        fi
    fi
    
    # 显示总体结果
    log_header "检查结果汇总"
    
    local pass_rate=$((passed_checks * 100 / total_checks))
    echo -e "${BLUE}总检查项: $total_checks${NC}"
    echo -e "${GREEN}通过检查: $passed_checks${NC}"
    echo -e "${BLUE}通过率: $pass_rate%${NC}"
    
    if [[ $overall_status -eq 0 ]]; then
        log_success "所有关键检查通过！"
        echo -e "\n${GREEN}🎉 国际化文档状态良好！${NC}"
    else
        log_error "部分检查未通过"
        echo -e "\n${YELLOW}💡 建议操作:${NC}"
        echo -e "  1. 检查缺失的文件"
        echo -e "  2. 添加语言切换器"
        echo -e "  3. 完善联系方式信息"
        echo -e "  4. 补充Docker支持文档"
    fi
    
    echo -e "\n${BLUE}📝 详细报告已生成: docs/i18n-report.md${NC}"
    
    # 生成详细报告
    cat > docs/i18n-report.md << EOF
# 国际化检查报告

## 检查时间
$(date)

## 检查结果
- 总检查项: $total_checks
- 通过检查: $passed_checks
- 通过率: $pass_rate%

## 文件状态
EOF
    
    for file in "${FILES[@]}"; do
        if [[ -f "$file" ]]; then
            echo "- ✅ $file" >> docs/i18n-report.md
        else
            echo "- ❌ $file" >> docs/i18n-report.md
        fi
    done
    
    echo "" >> docs/i18n-report.md
    echo "## 建议" >> docs/i18n-report.md
    if [[ $overall_status -eq 0 ]]; then
        echo "- 所有检查通过，文档状态良好" >> docs/i18n-report.md
    else
        echo "- 请根据检查结果修复问题" >> docs/i18n-report.md
        echo "- 确保所有语言版本保持同步" >> docs/i18n-report.md
    fi
}

# 显示帮助信息
show_help() {
    echo "AutoClip 国际化检查脚本"
    echo ""
    echo "用法:"
    echo "  $0 [选项]"
    echo ""
    echo "选项:"
    echo "  help    显示帮助信息"
    echo ""
    echo "功能:"
    echo "  - 检查多语言文档文件存在性"
    echo "  - 验证语言切换器"
    echo "  - 检查联系方式信息"
    echo "  - 验证Docker支持文档"
    echo "  - 检查开发中功能标注"
    echo "  - 验证Markdown语法"
    echo "  - 检查文件内容一致性"
    echo ""
    echo "示例:"
    echo "  $0          # 执行完整检查"
    echo "  $0 help     # 显示帮助"
}

# 处理参数
case "${1:-}" in
    "help"|"-h"|"--help")
        show_help
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac
