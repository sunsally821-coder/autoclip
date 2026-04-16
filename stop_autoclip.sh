#!/bin/bash

# AutoClip 系统停止脚本
# 版本: 2.0
# 功能: 优雅地停止所有AutoClip服务

set -euo pipefail

# =============================================================================
# 配置区域
# =============================================================================

# PID文件
BACKEND_PID_FILE="backend.pid"
FRONTEND_PID_FILE="frontend.pid"
CELERY_PID_FILE="celery.pid"

# 日志目录
LOG_DIR="logs"

# =============================================================================
# 颜色和样式定义
# =============================================================================

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
ICON_STOP="🛑"
ICON_CLEAN="🧹"

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
    echo -e "\n${PURPLE}${ICON_STOP} $1${NC}"
    echo -e "${PURPLE}$(printf '=%.0s' {1..50})${NC}"
}

# 停止进程
stop_process() {
    local pid_file="$1"
    local service_name="$2"
    
    if [[ -f "$pid_file" ]]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            log_info "停止 $service_name (PID: $pid)..."
            
            # 优雅停止
            kill "$pid" 2>/dev/null || true
            
            # 等待进程结束
            local count=0
            while kill -0 "$pid" 2>/dev/null && [[ $count -lt 10 ]]; do
                sleep 1
                ((count++))
            done
            
            # 如果进程仍在运行，强制停止
            if kill -0 "$pid" 2>/dev/null; then
                log_warning "强制停止 $service_name..."
                kill -9 "$pid" 2>/dev/null || true
                sleep 1
            fi
            
            if kill -0 "$pid" 2>/dev/null; then
                log_error "无法停止 $service_name"
            else
                log_success "$service_name 已停止"
            fi
        else
            log_warning "$service_name 进程不存在"
        fi
        rm -f "$pid_file"
    else
        log_info "$service_name PID文件不存在"
    fi
}

# 停止所有相关进程
stop_all_processes() {
    log_header "停止所有AutoClip服务"
    
    # 停止通过PID文件管理的进程
    stop_process "$BACKEND_PID_FILE" "后端服务"
    stop_process "$FRONTEND_PID_FILE" "前端服务"
    stop_process "$CELERY_PID_FILE" "Celery Worker"
    
    # 停止所有相关进程
    log_info "停止所有Celery Worker进程..."
    pkill -f "celery.*worker" 2>/dev/null || true
    
    log_info "停止所有后端API进程..."
    pkill -f "uvicorn.*backend.main:app" 2>/dev/null || true
    
    log_info "停止所有前端开发服务器..."
    pkill -f "npm.*dev" 2>/dev/null || true
    pkill -f "vite" 2>/dev/null || true
    
    # 等待进程完全停止
    sleep 2
    
    log_success "所有服务已停止"
}

# 清理临时文件
cleanup_temp_files() {
    log_header "清理临时文件"
    
    # 清理PID文件
    rm -f "$BACKEND_PID_FILE" "$FRONTEND_PID_FILE" "$CELERY_PID_FILE"
    log_success "PID文件已清理"
    
    # 清理Celery临时文件
    rm -f /tmp/celerybeat-schedule /tmp/celerybeat.pid 2>/dev/null || true
    log_success "Celery临时文件已清理"
    
    # 清理Python缓存
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    log_success "Python缓存已清理"
}

# 显示系统状态
show_system_status() {
    log_header "系统状态检查"
    
    local services_running=false
    
    # 检查后端服务
    if pgrep -f "uvicorn.*backend.main:app" >/dev/null; then
        log_warning "后端服务仍在运行"
        services_running=true
    else
        log_success "后端服务已停止"
    fi
    
    # 检查前端服务
    if pgrep -f "npm.*dev\|vite" >/dev/null; then
        log_warning "前端服务仍在运行"
        services_running=true
    else
        log_success "前端服务已停止"
    fi
    
    # 检查Celery Worker
    if pgrep -f "celery.*worker" >/dev/null; then
        log_warning "Celery Worker仍在运行"
        services_running=true
    else
        log_success "Celery Worker已停止"
    fi
    
    if [[ "$services_running" == true ]]; then
        log_warning "部分服务仍在运行，可能需要手动停止"
        echo ""
        echo "仍在运行的进程:"
        pgrep -f "uvicorn.*backend.main:app\|npm.*dev\|vite\|celery.*worker" | while read pid; do
            ps -p "$pid" -o pid,ppid,cmd --no-headers 2>/dev/null || true
        done
    else
        log_success "所有AutoClip服务已完全停止"
    fi
}

# 显示日志信息
show_log_info() {
    log_header "日志文件信息"
    
    if [[ -d "$LOG_DIR" ]]; then
        echo "日志文件位置:"
        ls -la "$LOG_DIR"/*.log 2>/dev/null | while read line; do
            echo "  $line"
        done
        echo ""
        echo "查看最新日志:"
        echo "  后端日志: tail -f $LOG_DIR/backend.log"
        echo "  前端日志: tail -f $LOG_DIR/frontend.log"
        echo "  Celery日志: tail -f $LOG_DIR/celery.log"
    else
        log_info "日志目录不存在"
    fi
}

# =============================================================================
# 主函数
# =============================================================================

main() {
    log_header "AutoClip 系统停止器 v2.0"
    
    # 停止所有服务
    stop_all_processes
    
    # 清理临时文件
    cleanup_temp_files
    
    # 显示系统状态
    show_system_status
    
    # 显示日志信息
    show_log_info
    
    echo ""
    log_success "AutoClip 系统已完全停止"
    echo ""
    echo "如需重新启动，请运行: ./start_autoclip.sh"
}

# 运行主函数
main "$@"
