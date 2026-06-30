// 主页面JavaScript

// 全局变量
const API_BASE_URL = `${window.location.protocol}//${window.location.host}/api`;

// 页面加载时初始化设置
document.addEventListener('DOMContentLoaded', function() {
    // DOM元素
    const logOutputEl = document.getElementById('logOutput');
    
    // 初始化部署合约按钮
    const deployContractBtn = document.getElementById('deployContractBtn');
    if (deployContractBtn) {
        deployContractBtn.addEventListener('click', deployContract);
    }
    
    // 加载系统日志
    loadSystemLogs();
});

// 加载系统日志
async function loadSystemLogs() {
    try {
        const response = await fetch(`${API_BASE_URL}/logs`);
        
        // 检查响应是否成功
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // 检查响应内容类型
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            console.warn('Response is not JSON, possibly HTML error page');
            const logsContainer = document.getElementById('systemLogs');
            if (logsContainer) {
                logsContainer.innerHTML = '<div class="log-entry">' + (window.languageManager ? window.languageManager.getText('system_logs.api_not_available') : 'API服务暂不可用') + '</div>';
            }
            return;
        }
        
        const data = await response.json();
        
        if (data.success && data.logs) {
            const logsContainer = document.getElementById('systemLogs');
            if (logsContainer) {
                logsContainer.innerHTML = '';
                
                if (data.logs.length === 0) {
                    logsContainer.innerHTML = '<div class="log-entry">' + (window.languageManager ? window.languageManager.getText('system_logs.no_system_logs') : '暂无系统日志') + '</div>';
                } else {
                    data.logs.forEach(log => {
                        const logEntry = document.createElement('div');
                        logEntry.className = 'log-entry';
                        
                        const timestamp = new Date(log.timestamp).toLocaleString();
                        logEntry.innerHTML = `
                            <span class="log-timestamp">${timestamp}</span>
                            <span class="log-message">[${log.level}] ${log.message}</span>
                        `;
                        
                        logsContainer.appendChild(logEntry);
                    });
                }
            }
        }
    } catch (error) {
        console.error((window.languageManager ? window.languageManager.getText('system_logs.load_ca_logs_failed') : '加载系统日志失败') + ':', error);
        const logsContainer = document.getElementById('systemLogs');
        if (logsContainer) {
            logsContainer.innerHTML = '<div class="log-entry">' + (window.languageManager ? window.languageManager.getText('system_logs.load_logs_failed') : '加载日志失败') + '</div>';
        }
    }
}

// 工具函数
function addLog(message, type = 'info') {
    const logOutputEl = document.getElementById('logOutput');
    if (logOutputEl) {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry log-${type}`;
        logEntry.innerHTML = `<span class="log-time">[${timestamp}]</span> ${message}`;
        logOutputEl.appendChild(logEntry);
        logOutputEl.scrollTop = logOutputEl.scrollHeight;
    }
}

function addLog(message, type = 'info') {
    const logOutputEl = document.getElementById('logOutput');
    if (logOutputEl) {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry log-${type}`;
        logEntry.innerHTML = `<span class="log-time">[${timestamp}]</span> ${message}`;
        logOutputEl.appendChild(logEntry);
        logOutputEl.scrollTop = logOutputEl.scrollHeight;
    }
}

async function makeApiRequest(url, options = {}) {
    try {
        const response = await fetch(`${API_BASE_URL}${url}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || `HTTP ${response.status}`);
        }
        
        return data;
    } catch (error) {
        addLog((window.languageManager ? window.languageManager.getText('system_logs.api_request_failed') : 'API请求失败') + `: ${error.message}`, 'error');
        throw error;
    }
}

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', () => {
    addLog(window.languageManager ? window.languageManager.getText('system_logs.platform_loaded') : 'DPKI管理平台已加载', 'info');
    addLog(window.languageManager ? window.languageManager.getText('system_logs.select_management_page') : '请选择CA管理或UE管理进入相应功能页面', 'info');
});

document.addEventListener('DOMContentLoaded', function() {
    addLog(window.languageManager ? window.languageManager.getText('system_logs.platform_loaded') : 'DPKI管理平台已加载', 'info');
    addLog(window.languageManager ? window.languageManager.getText('system_logs.select_management_page') : '请选择CA管理或UE管理进入相应功能页面', 'info');
});