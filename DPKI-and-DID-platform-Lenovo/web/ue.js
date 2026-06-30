// UE管理页面JavaScript

// 全局变量
const API_BASE_URL = `${window.location.protocol}//${window.location.host}/api`;

// 时延统计类
class TimingTracker {
    constructor() {
        this.timings = {};
    }
    
    start(operationId) {
        this.timings[operationId] = Date.now();
        this.updateDisplay(operationId, (window.languageManager ? window.languageManager.getText('timing') : '计时中...'), true);
    }
    
    end(operationId, backendTiming = null) {
        if (this.timings[operationId]) {
            const frontendDuration = Date.now() - this.timings[operationId];
            // 如果有后端时延信息，优先使用后端时延
            const displayTiming = backendTiming || `${frontendDuration}ms`;
            this.updateDisplay(operationId, displayTiming, false);
            delete this.timings[operationId];
            return frontendDuration;
        }
        return 0;
    }
    
    updateDisplay(operationId, text, isActive = false) {
        const displayElement = document.getElementById(`timing-${operationId}`);
        if (displayElement) {
            displayElement.textContent = text;
            if (isActive) {
                displayElement.classList.add('timing-active');
            } else {
                displayElement.classList.remove('timing-active');
            }
        }
    }
    
    // 从后端输出中提取时延信息
    extractBackendTiming(output, timingKey) {
        if (!output) return null;
        
        // 匹配时延格式：request Time: 64.105ms, authenticationreq Time: 40.375ms 等
        const regex = new RegExp(`${timingKey}:\\s*([\\d.]+(?:ms|s))`, 'i');
        const match = output.match(regex);
        return match ? match[1] : null;
    }
}

// 创建时延统计实例
const timingTracker = new TimingTracker();

// DOM元素
let ueStatusEl, caListEl, ueListEl, ueSystemLogsEl, ueResponseArea;

document.addEventListener('DOMContentLoaded', function() {
    // 获取DOM元素
    ueStatusEl = document.getElementById('ueStatus');
    caListEl = document.getElementById('caList');
    ueListEl = document.getElementById('ueList');
    ueSystemLogsEl = document.getElementById('ueSystemLogs');
    ueResponseArea = document.getElementById('ueResponseArea');
    
    // 获取按钮元素
    const startUeBtn = document.getElementById('startUeBtn');
    const stopUeBtn = document.getElementById('stopUeBtn');
    const updateListBtn = document.getElementById('updateListBtn');
    const requestCsrBtn = document.getElementById('requestCsrBtn');
    const authRequestBtn = document.getElementById('authRequestBtn');
    
    // 添加事件监听器
    if (startUeBtn) startUeBtn.addEventListener('click', () => startServer('ue'));
    if (stopUeBtn) stopUeBtn.addEventListener('click', () => stopServer('ue'));
    if (updateListBtn) updateListBtn.addEventListener('click', updateUEAddressList);
    if (requestCsrBtn) requestCsrBtn.addEventListener('click', requestCSR);
    if (authRequestBtn) authRequestBtn.addEventListener('click', authenticationRequest);
    
    // 初始化页面
    initializePage();
});

// 添加响应到右侧区域
function addResponse(content, type = 'info', blockchainInfo = null, authResult = null) {
    if (!ueResponseArea) return;
    
    // 清空之前的回执
    ueResponseArea.innerHTML = '';
    
    const responseItem = document.createElement('div');
    responseItem.style.marginBottom = '20px';
    responseItem.style.padding = '15px';
    responseItem.style.border = '1px solid #ddd';
    responseItem.style.borderRadius = '8px';
    responseItem.style.backgroundColor = '#fff';
    responseItem.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
    
    const timestamp = new Date().toLocaleString();
    
    // 操作回执标题
    const titleDiv = document.createElement('div');
    titleDiv.style.fontSize = '16px';
    titleDiv.style.fontWeight = 'bold';
    titleDiv.style.marginBottom = '15px';
    titleDiv.style.color = '#333';
    titleDiv.textContent = window.languageManager ? window.languageManager.getText('operation_receipt') : '操作回执';
    responseItem.appendChild(titleDiv);
    
    // 操作时间
    const timeDiv = document.createElement('div');
    timeDiv.style.marginBottom = '15px';
    timeDiv.style.color = '#666';
    const operationTimeText = window.languageManager ? window.languageManager.getText('operation_time') : '操作时间';
    timeDiv.innerHTML = `<strong>${operationTimeText}:</strong> ${timestamp}`;
    responseItem.appendChild(timeDiv);
    
    // 认证结果（如果提供）
    if (authResult) {
        const resultDiv = document.createElement('div');
        resultDiv.style.marginBottom = '15px';
        resultDiv.style.color = '#666';
        const authResultText = window.languageManager ? window.languageManager.getText('auth_result_label') : '认证结果';
        resultDiv.innerHTML = `<strong>${authResultText}:</strong> ${authResult}`;
        responseItem.appendChild(resultDiv);
    }
    
    // 原始回执内容
    const receiptDiv = document.createElement('div');
    receiptDiv.style.padding = '12px';
    receiptDiv.style.background = '#f8f9fa';
    receiptDiv.style.border = '1px solid #dee2e6';
    receiptDiv.style.borderRadius = '6px';
    receiptDiv.style.fontFamily = 'monospace';
    receiptDiv.style.fontSize = '12px';
    receiptDiv.style.lineHeight = '1.4';
    receiptDiv.style.whiteSpace = 'pre-wrap';
    receiptDiv.style.wordBreak = 'break-all';
    receiptDiv.style.maxHeight = '400px';
    receiptDiv.style.overflowY = 'auto';
    
    // 根据类型设置颜色
    if (type === 'error') {
        receiptDiv.style.color = '#721c24';
        receiptDiv.style.backgroundColor = '#f8d7da';
        receiptDiv.style.borderColor = '#f5c6cb';
    } else if (type === 'success') {
        receiptDiv.style.color = '#155724';
        receiptDiv.style.backgroundColor = '#d4edda';
        receiptDiv.style.borderColor = '#c3e6cb';
    } else {
        receiptDiv.style.color = '#495057';
    }
    
    // 处理内容显示
    let displayContent;
    if (typeof content === 'object' && content !== null) {
        displayContent = JSON.stringify(content, null, 2);
    } else {
        displayContent = String(content);
    }
    
    // 处理换行符，确保正确显示
    displayContent = displayContent.replace(/\\n/g, '\n');
    
    receiptDiv.textContent = displayContent;
    responseItem.appendChild(receiptDiv);
    
    ueResponseArea.appendChild(responseItem);
    ueResponseArea.scrollTop = ueResponseArea.scrollHeight;
}

// 工具函数
function addLog(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry log-${type}`;
    logEntry.innerHTML = `<span class="log-time">[${timestamp}]</span> ${message}`;
    if (ueSystemLogsEl) {
        ueSystemLogsEl.appendChild(logEntry);
        ueSystemLogsEl.scrollTop = ueSystemLogsEl.scrollHeight;
    }
    
    // 根据日志消息更新服务器状态
    updateServerStatusFromLog(message);
}

// 加载UE系统日志
async function loadUESystemLogs() {
    try {
        const response = await fetch(`${API_BASE_URL}/logs`);
        if (response.ok) {
            const data = await response.json();
            const logs = data.logs || [];
            displayUESystemLogs(logs);
        }
    } catch (error) {
        console.error((window.languageManager ? window.languageManager.getText('system_logs.load_ue_logs_failed') : '加载UE系统日志失败') + ':', error);
    }
}

// 翻译日志消息
function translateLogMessage(message) {
    // 确保languageManager已经初始化
    if (!window.languageManager) {
        return message; // 如果languageManager未初始化，返回原消息
    }
    
    const currentLang = window.languageManager.getCurrentLanguage();
    if (currentLang === 'zh') {
        return message; // 中文模式下直接返回原消息
    }
    
    // 英文翻译映射
    const logTranslations = {
        // 服务器状态相关
        'CA服务器启动成功': 'CA server started successfully',
        'CA服务器已在运行': 'CA server is already running',
        'CA服务器停止成功': 'CA server stopped successfully',
        'CA服务器未运行': 'CA server is not running',
        'CA服务器自动启动成功': 'CA server auto-started successfully',
        'UE服务器启动成功': 'UE server started successfully',
        'UE服务器已在运行': 'UE server is already running',
        'UE服务器停止成功': 'UE server stopped successfully',
        'UE服务器未运行': 'UE server is not running',
        'UE服务器自动启动成功': 'UE server auto-started successfully',
        
        // 初始化相关
        'CA-1 initialized': 'CA-1 initialized',
        'UE-1 initialized': 'UE-1 initialized',
        '初始化CA成功': 'CA initialization successful',
        '初始化CA失败': 'CA initialization failed',
        '初始化UE成功': 'UE initialization successful',
        '初始化UE失败': 'UE initialization failed',
        
        // 证书操作相关
        '证书签发成功': 'Certificate issuance successful',
        '证书签发失败': 'Certificate issuance failed',
        '证书签署成功': 'Certificate signing successful',
        '证书签署失败': 'Certificate signing failed',
        '证书更新成功': 'Certificate update successful',
        '证书更新失败': 'Certificate update failed',
        '证书撤销成功': 'Certificate revocation successful',
        '证书撤销失败': 'Certificate revocation failed',
        '证书请求成功': 'Certificate request successful',
        '证书请求失败': 'Certificate request failed',
        '证书验证成功': 'Certificate verification successful',
        '证书验证失败': 'Certificate verification failed',
        '证书注册成功': 'Certificate registration successful',
        '证书注册失败': 'Certificate registration failed',
        
        // 智能合约相关
        '智能合约部署成功': 'Smart contract deployment successful',
        '智能合约部署失败': 'Smart contract deployment failed',
        '智能合约调用成功': 'Smart contract call successful',
        '智能合约调用失败': 'Smart contract call failed',
        
        // 根证书相关
        '根证书初始化成功': 'Root certificate initialization successful',
        '根证书初始化失败': 'Root certificate initialization failed',
        
        // 页面加载相关
        'CA管理页面已加载': 'CA management page loaded',
        'UE管理页面已加载': 'UE management page loaded',
        'DPKI管理平台已加载': 'DPKI management platform loaded',
        'DPKI管理平台已启动': 'DPKI management platform started',
        
        // 用户操作相关
        '用户注册成功': 'User registration successful',
        '用户注册失败': 'User registration failed',
        '用户认证成功': 'User authentication successful',
        '用户认证失败': 'User authentication failed',
        
        // CSR相关
        'CSR请求成功 - CSR已被接收': 'CSR request successful - CSR received',
        'CSR请求失败 - 未检测到CSR received': 'CSR request failed - CSR received not detected',
        
        // 地址列表相关
        '地址列表更新成功': 'Address list updated successfully',
        'UE地址列表更新成功': 'UE address list updated successfully',
        
        // 认证相关
        'UE认证成功 - 验证通过': 'UE authentication successful - verification passed',
        'UE认证失败 - 未找到成功验证信息': 'UE authentication failed - no successful verification found',
        
        // 错误消息相关
        '请填写CA名称': 'Please enter CA name',
        '请填写UE名称': 'Please enter UE name',
        '请填写CA名称和标签': 'Please enter CA name and label',
        '请填写CA名称和UE名称': 'Please enter CA name and UE name',
        '请填写要撤销的UE名称': 'Please enter UE name to revoke',
        '请填写本地UE名称和目标UE名称': 'Please enter local UE name and target UE name',
        
        // 操作进行中
        '正在初始化CA...': 'Initializing CA...',
        '正在更新UE地址列表...': 'Updating UE address list...',
        
        // 日志清空
        '日志已清空': 'Logs cleared',
        
        // 选择提示
        '请选择CA管理或UE管理进入相应功能页面': 'Please select CA Management or UE Management to enter the corresponding function page'
    };
    
    // 处理包含动态内容的日志消息
    const dynamicPatterns = [
        {
            pattern: /UE服务器退出，代码:\s*(\d+)/,
            replacement: 'UE server exited with code: $1'
        },
        {
            pattern: /CA服务器退出，代码:\s*(\d+)/,
            replacement: 'CA server exited with code: $1'
        },
        {
            pattern: /DPKI Web服务器启动，端口:\s*(\d+)，监听所有网络接口/,
            replacement: 'DPKI Web server started on port: $1, listening on all network interfaces'
        },
        {
            pattern: /DPKI Web服务器启动，端口:\s*(\d+)/,
            replacement: 'DPKI Web server started on port: $1'
        },
        {
            pattern: /服务器启动在端口\s*(\d+)/,
            replacement: 'Server started on port $1'
        },
        {
            pattern: /API请求失败:\s*(.+)/,
            replacement: 'API request failed: $1'
        },
        {
            pattern: /启动(.+)服务器失败:\s*(.+)/,
            replacement: 'Failed to start $1 server: $2'
        },
        {
            pattern: /停止(.+)服务器失败:\s*(.+)/,
            replacement: 'Failed to stop $1 server: $2'
        },
        {
            pattern: /初始化CA失败:\s*(.+)/,
            replacement: 'CA initialization failed: $1'
        },
        {
            pattern: /签署证书失败:\s*(.+)/,
            replacement: 'Certificate signing failed: $1'
        },
        {
            pattern: /更新证书失败:\s*(.+)/,
            replacement: 'Certificate update failed: $1'
        },
        {
            pattern: /撤销证书失败:\s*(.+)/,
            replacement: 'Certificate revocation failed: $1'
        },
        {
            pattern: /发起CSR请求失败:\s*(.+)/,
            replacement: 'CSR request failed: $1'
        },
        {
            pattern: /发起认证请求失败:\s*(.+)/,
            replacement: 'Authentication request failed: $1'
        },
        {
            pattern: /更新地址列表失败:\s*(.+)/,
            replacement: 'Address list update failed: $1'
        },
        {
            pattern: /正在启动\s*(.+)\s*服务器\.\.\./,
            replacement: 'Starting $1 server...'
        },
        {
            pattern: /正在停止\s*(.+)\s*服务器\.\.\./,
            replacement: 'Stopping $1 server...'
        },
        {
            pattern: /(.+)\s*服务器启动成功/,
            replacement: '$1 server started successfully'
        },
        {
            pattern: /(.+)\s*服务器已停止/,
            replacement: '$1 server stopped'
        },
        {
            pattern: /正在初始化CA证书:\s*(.+)/,
            replacement: 'Initializing CA certificate: $1'
        },
        {
            pattern: /CA证书初始化成功:\s*(.+)/,
            replacement: 'CA certificate initialization successful: $1'
        },
        {
            pattern: /CA证书初始化失败:\s*(.+)/,
            replacement: 'CA certificate initialization failed: $1'
        },
        {
            pattern: /正在签署证书:\s*CA=(.+),\s*UE=(.+)/,
            replacement: 'Signing certificate: CA=$1, UE=$2'
        },
        {
            pattern: /证书签署成功:\s*(.+)/,
            replacement: 'Certificate signing successful: $1'
        },
        {
            pattern: /正在更新证书:\s*CA=(.+),\s*UE=(.+)/,
            replacement: 'Updating certificate: CA=$1, UE=$2'
        },
        {
            pattern: /证书更新成功:\s*(.+)/,
            replacement: 'Certificate update successful: $1'
        },
        {
            pattern: /正在撤销证书:\s*(.+)/,
            replacement: 'Revoking certificate: $1'
        },
        {
            pattern: /证书撤销成功:\s*(.+)/,
            replacement: 'Certificate revocation successful: $1'
        },
        {
            pattern: /正在发起CSR请求:\s*(.+)/,
            replacement: 'Initiating CSR request: $1'
        },
        {
            pattern: /CSR请求发送成功:\s*(.+)/,
            replacement: 'CSR request sent successfully: $1'
        },
        {
            pattern: /正在发起认证请求:\s*(.+)\s*->\s*(.+)/,
            replacement: 'Initiating authentication request: $1 -> $2'
        },
        {
            pattern: /认证请求成功:\s*(.+)\s*->\s*(.+)/,
            replacement: 'Authentication request successful: $1 -> $2'
        },
        
        // 新增的复杂日志消息模式
        {
            pattern: /开始UE CSR请求:\s*(.+)/,
            replacement: 'Starting UE CSR request: $1'
        },
        {
            pattern: /UE CSR请求成功:\s*(.+)/,
            replacement: 'UE CSR request successful: $1'
        },
        {
            pattern: /UE CSR请求失败:\s*(.+)/,
            replacement: 'UE CSR request failed: $1'
        },
        {
            pattern: /CA证书注册成功:\s*(.+)\s*->\s*(.+)/,
            replacement: 'CA certificate registration successful: $1 -> $2'
        },
        {
            pattern: /CA证书注册失败:\s*(.+)/,
            replacement: 'CA certificate registration failed: $1'
        },
        {
            pattern: /开始UE认证请求:\s*(.+)\s*->\s*(.+)/,
            replacement: 'Starting UE authentication request: $1 -> $2'
        },
        {
            pattern: /UE认证请求成功:\s*(.+)\s*->\s*(.+)/,
            replacement: 'UE authentication request successful: $1 -> $2'
        },
        {
            pattern: /UE认证请求失败:\s*(.+)/,
            replacement: 'UE authentication request failed: $1'
        },
        {
            pattern: /UE地址列表更新失败:\s*(.+)/,
            replacement: 'UE address list update failed: $1'
        },
        {
            pattern: /智能合约部署成功，地址:\s*(.+)/,
            replacement: 'Smart contract deployed successfully, address: $1'
        },
        {
            pattern: /智能合约部署失败:\s*(.+)/,
            replacement: 'Smart contract deployment failed: $1'
        },
        {
            pattern: /已删除失败的UE节点文件夹:\s*(.+)/,
            replacement: 'Deleted failed UE node folder: $1'
        },
        {
            pattern: /已删除异常的UE节点文件夹:\s*(.+)/,
            replacement: 'Deleted abnormal UE node folder: $1'
        },
        {
            pattern: /删除失败的UE节点文件夹时出错:\s*(.+)/,
            replacement: 'Error deleting failed UE node folder: $1'
        },
        {
            pattern: /删除异常的UE节点文件夹时出错:\s*(.+)/,
            replacement: 'Error deleting abnormal UE node folder: $1'
        },
        {
            pattern: /UE CSR请求异常:\s*(.+)/,
            replacement: 'UE CSR request exception: $1'
        },
        {
            pattern: /CA服务器自动启动失败:\s*(.+)/,
            replacement: 'CA server auto-start failed: $1'
        },
        {
            pattern: /CA服务器自动启动异常:\s*(.+)/,
            replacement: 'CA server auto-start exception: $1'
        },
        {
            pattern: /UE服务器自动启动失败:\s*(.+)/,
            replacement: 'UE server auto-start failed: $1'
        },
        {
            pattern: /UE服务器自动启动异常:\s*(.+)/,
            replacement: 'UE server auto-start exception: $1'
        },
        {
            pattern: /更新UE配置文件失败:\s*(.+)/,
            replacement: 'Failed to update UE config file: $1'
        },
        
        // 处理复合消息（包含分号分隔的多个状态）
        {
            pattern: /UE CSR请求成功:\s*(.+)；证书注册成功；UE认证成功 - 验证通过/,
            replacement: 'UE CSR request successful: $1; Certificate registration successful; UE authentication successful - verification passed'
        },
        {
            pattern: /(.+)；证书注册成功/,
            replacement: '$1; Certificate registration successful'
        },
        {
            pattern: /(.+)；UE认证成功 - 验证通过/,
            replacement: '$1; UE authentication successful - verification passed'
        }
    ];
    
    // 首先尝试动态模式匹配
    for (const {pattern, replacement} of dynamicPatterns) {
        if (pattern.test(message)) {
            return message.replace(pattern, replacement);
        }
    }
    
    // 尝试完全匹配
    if (logTranslations[message]) {
        return logTranslations[message];
    }
    
    // 部分匹配翻译
    for (const [chineseText, englishText] of Object.entries(logTranslations)) {
        if (message.includes(chineseText)) {
            return message.replace(chineseText, englishText);
        }
    }
    
    return message; // 如果没有匹配的翻译，返回原消息
}

// 显示UE系统日志
function displayUESystemLogs(logs) {
    if (!ueSystemLogsEl) return;
        
        ueSystemLogsEl.innerHTML = '';
        
        if (logs.length === 0) {
            ueSystemLogsEl.innerHTML = '<div class="log-entry">' + (window.languageManager ? window.languageManager.getText('system_logs.no_ue_system_logs') : '暂无UE系统日志') + '</div>';
            return;
        }
    
    logs.forEach(log => {
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        logEntry.innerHTML = `
            <div class="log-timestamp">${log.timestamp}</div>
            <div class="log-message">${translateLogMessage(log.message)}</div>
        `;
        ueSystemLogsEl.appendChild(logEntry);
    });
}

function updateServerStatusFromLog(message) {
    // 检查UE服务器状态相关的日志消息
    if (message.includes('UE服务器启动成功') || message.includes('UE服务器已在运行')) {
        if (ueStatusEl) {
            ueStatusEl.textContent = '在线';
            ueStatusEl.className = 'status-indicator online';
        }
        // 暂停定时检查，避免冲突
        window.statusCheckPaused = true;
        setTimeout(() => {
            window.statusCheckPaused = false;
        }, 3000);
    } else if (message.includes('UE服务器退出') || message.includes('UE服务器未运行')) {
        if (ueStatusEl) {
            ueStatusEl.textContent = '离线';
            ueStatusEl.className = 'status-indicator offline';
        }
        // 暂停定时检查，避免冲突
        window.statusCheckPaused = true;
        setTimeout(() => {
            window.statusCheckPaused = false;
        }, 3000);
    }
}

function updateServerStatus(caOnline, ueOnline) {
    // UE页面只更新UE服务器状态
    if (ueStatusEl) {
        ueStatusEl.textContent = ueOnline ? '在线' : '离线';
        ueStatusEl.className = `status-indicator ${ueOnline ? 'online' : 'offline'}`;
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
        addLog(`API请求失败: ${error.message}`, 'error', 'api_request_failed', error.message);
        throw error;
    }
}

// 加载CA列表
async function loadCAList() {
    try {
        const response = await makeApiRequest('/ca/list');
        const caListEl = document.getElementById('caList');
        
        if (response.success && response.caList) {
            caListEl.innerHTML = response.caList.map(ca => `
                <div class="list-item">
                    <span class="item-name">${ca.name}</span>
                    <span class="item-status status-${ca.status}">${ca.status === 'initialized' ? window.languageManager.getText('initialized') : '已创建'}</span>
                </div>
            `).join('');
        } else {
            caListEl.innerHTML = '<div class="list-item">暂无CA实例</div>';
        }
    } catch (error) {
        const caListEl = document.getElementById('caList');
        caListEl.innerHTML = '<div class="list-item error">' + (window.languageManager ? window.languageManager.getText('messages.load_ca_list_failed') : '加载CA列表失败') + '</div>';
        // 停止定时刷新
        if (window.caListInterval) {
            clearInterval(window.caListInterval);
            window.caListInterval = null;
        }
    }
}

// 加载UE列表
async function loadUEList() {
    try {
        const response = await makeApiRequest('/ue/list');
        const ueListEl = document.getElementById('ueList');
        
        if (response.success && response.ueList) {
            ueListEl.innerHTML = response.ueList.map(ue => `
                <div class="list-item">
                    <span class="item-name">${ue.name}</span>
                    <span class="item-status status-${ue.status}">
                        ${ue.status === 'certified' ? window.languageManager.getText('issued') : 
                          ue.status === 'pending' ? window.languageManager.getText('pending_operation') : '已创建'}
                    </span>
                    ${ue.host ? `<span class="item-info">${ue.host}:${ue.port}</span>` : ''}
                </div>
            `).join('');
        } else {
            ueListEl.innerHTML = '<div class="list-item">暂无UE实例</div>';
        }
    } catch (error) {
        const ueListEl = document.getElementById('ueList');
        ueListEl.innerHTML = '<div class="list-item error">' + (window.languageManager ? window.languageManager.getText('messages.load_ue_list_failed') : '加载UE列表失败') + '</div>';
        // 停止定时刷新
        if (window.ueListInterval) {
            clearInterval(window.ueListInterval);
            window.ueListInterval = null;
        }
    }
}

// 显示CA列表
function displayCAList(caList) {
    if (caList.length === 0) {
        caListEl.innerHTML = '<div class="list-item"><div class="item-name">暂无CA</div></div>';
        return;
    }
    
    caListEl.innerHTML = caList.map(ca => `
        <div class="list-item">
            <div class="item-name">${ca.name}</div>
            <div class="item-status ${ca.hasCert ? 'status-active' : 'status-inactive'}">
                ${ca.hasCert ? '已激活' : '未激活'}
            </div>
            <div class="item-path">${ca.path}</div>
        </div>
    `).join('');
}

// 显示UE列表
function displayUEList(ueList) {
    if (ueList.length === 0) {
        ueListEl.innerHTML = '<div class="list-item"><div class="item-name">暂无UE</div></div>';
        return;
    }
    
    ueListEl.innerHTML = ueList.map(ue => `
        <div class="list-item">
            <div class="item-name">${ue.name}</div>
            <div class="item-status status-${ue.status}">
                ${getStatusText(ue.status)}
            </div>
            <div class="item-path">${ue.path}</div>
        </div>
    `).join('');
}

function getStatusText(status) {
    const statusMap = {
        'certified': '已签发',
        'pending': '待签署',
        'created': '已创建'
    };
    return statusMap[status] || status;
}

// 检查服务器状态
async function checkServerStatus() {
    // 如果状态检查被暂停，跳过此次检查
    if (window.statusCheckPaused) {
        return;
    }
    
    // 服务器状态检查功能已移除
    updateServerStatus(false, false);
}

// 服务器控制函数
async function startServer(type) {
    try {
        const response = await makeApiRequest(`/server/start/${type}`, { method: 'POST' });
        addLog(response.message, 'success');
        setTimeout(checkServerStatus, 1000);
    } catch (error) {
        console.error(`启动${type}服务器失败:`, error);
        addLog(`启动${type}服务器失败: ${error.message || '网络错误'}`, 'error', 'server_start_failed', type, error.message || '网络错误');
    }
}

async function stopServer(type) {
    try {
        const response = await makeApiRequest(`/server/stop/${type}`, { method: 'POST' });
        addLog(response.message, 'success');
        setTimeout(checkServerStatus, 1000);
    } catch (error) {
        console.error(`停止${type}服务器失败:`, error);
        addLog(`停止${type}服务器失败: ${error.message || '网络错误'}`, 'error', 'server_stop_failed', type, error.message || '网络错误');
    }
}

// UE功能函数
async function updateAddressList() {
    try {
        const response = await makeApiRequest('/ue/updatelist', { method: 'POST' });
        addLog(response.message, 'success');
        setTimeout(() => {
            loadCAList();
            loadUEList();
        }, 1000);
    } catch (error) {
        addLog(`更新地址列表失败: ${error.message}`, 'error', 'ue_address_update_failed', error.message);
    }
}

async function requestCSR() {
    const ueName = document.getElementById('csrUeName').value.trim();
    
    if (!ueName) {
        addResponse(window.languageManager ? window.languageManager.getText('please_fill_ue_name_error') : '请填写UE名称', 'error');
        addLog(window.languageManager ? window.languageManager.getText('please_fill_ue_name') : 'Please enter UE name', 'error', 'please_fill_ue_name');
        return;
    }
    
    // 开始计时
    timingTracker.start('requestCsr');
    
    try {
        addResponse(window.languageManager ? window.languageManager.getText('generating_csr') : '正在发起CSR请求...', 'info');
        const response = await makeApiRequest('/ue/request', {
            method: 'POST',
            body: JSON.stringify({ ueName })
        });
        
        // 从后端输出中提取时延信息
        const backendTiming = timingTracker.extractBackendTiming(response.output, 'request Time');
        
        // 结束计时，使用后端时延
        timingTracker.end('requestCsr', backendTiming);
        
        // 根据CSR received检测结果显示不同的消息
        if (response.success && response.csrReceived) {
            addResponse(window.languageManager ? window.languageManager.getText('csr_request_success_msg', response.output || response.message) : `CSR请求成功！\n${response.output || response.message}`, 'success');
            addLog(window.languageManager ? window.languageManager.getText('csr_success_received') : 'CSR请求成功 - CSR已被接收', 'success', 'csr_success_received');
        } else {
            addResponse(window.languageManager ? window.languageManager.getText('csr_request_failed_msg', response.output || response.message) : `CSR请求失败！\n${response.output || response.message}`, 'error');
            addLog('CSR请求失败 - 未检测到CSR received', 'error', 'csr_failed_not_received');
            
            // CSR请求失败时立即刷新列表，确保失败的节点不显示
            setTimeout(() => {
                loadCAList();
                loadUEList();
            }, 500);
        }
        
        // 清空输入框
        document.getElementById('csrUeName').value = '';
        
        // 成功时也刷新列表
        if (response.success && response.csrReceived) {
            setTimeout(() => {
                loadCAList();
                loadUEList();
            }, 1000);
        }
    } catch (error) {
        // 结束计时（即使出错也要结束）
        timingTracker.end('requestCsr');
        addResponse(`发起CSR请求失败: ${error.message}`, 'error');
        addLog(`发起CSR请求失败: ${error.message}`, 'error', 'csr_request_failed', error.message);
        
        // 异常情况下也立即刷新列表，确保失败的节点不显示
        setTimeout(() => {
            loadCAList();
            loadUEList();
        }, 500);
    }
}

async function authenticationRequest() {
    const ueName = document.getElementById('authUeName').value.trim();
    const target = ueName; // 使用同一个值作为目标
    
    if (!ueName) {
        addResponse(window.languageManager ? window.languageManager.getText('please_fill_ue_name_error') : '请填写UE名称', 'error');
        addLog(window.languageManager ? window.languageManager.getText('please_fill_ue_name') : 'Please enter UE name', 'error', 'please_fill_ue_name');
        return;
    }
    
    // 开始计时
    timingTracker.start('authRequest');
    
    try {
        addResponse(window.languageManager ? window.languageManager.getText('sending_auth_request') : '正在发起认证请求...', 'info');
        const response = await makeApiRequest('/ue/auth', {
            method: 'POST',
            body: JSON.stringify({ ueName, target })
        });
        
        // 从后端输出中提取时延信息
        const backendTiming = timingTracker.extractBackendTiming(response.output, 'authenticationreq Time');
        
        // 结束计时，使用后端时延
        timingTracker.end('authRequest', backendTiming);
        
        // 显示完整的后端输出
        const outputContent = response.output || response.message;
        
        // 检查认证是否成功 - 确保outputContent是字符串类型
        const outputString = String(outputContent || '');
        const isAuthSuccess = outputString.includes('Message received: verify successful!');
        
        let authResult;
        if (isAuthSuccess) {
            authResult = window.languageManager ? window.languageManager.getText('success') : '成功';
            addResponse(outputContent, 'success', null, authResult);
            addLog(window.languageManager ? window.languageManager.getText('ue_auth_success') : 'UE认证成功 - 验证通过', 'success', 'ue_auth_success');
        } else {
            // 提取失败原因 - 查找"Message received:"之后的内容
            const messageMatch = outputString.match(/Message received:\s*(.+)/);
            const failureReason = messageMatch ? messageMatch[1].trim() : '未知错误';
            const failedText = window.languageManager ? window.languageManager.getText('failed') : '失败';
            authResult = `${failedText}（${failureReason}）`;
            addResponse(outputContent, 'error', null, authResult);
            addLog(window.languageManager ? window.languageManager.getText('ue_auth_failed') : 'UE authentication failed - no successful verification found', 'error', 'ue_auth_failed');
        }
        
        // 清空输入框
        document.getElementById('authUeName').value = '';
        
        setTimeout(() => {
            loadCAList();
            loadUEList();
        }, 1000);
    } catch (error) {
        // 结束计时（即使出错也要结束）
        timingTracker.end('authRequest');
        addResponse(`发起认证请求失败: ${error.message}`, 'error');
        addLog(`发起认证请求失败: ${error.message}`, 'error', 'auth_request_failed', error.message);
    }
}

async function updateUEAddressList() {
    try {
        addResponse(window.languageManager ? window.languageManager.getText('updating_ue_list') : '正在更新UE地址列表...', 'info');
        const response = await makeApiRequest('/ue/updatelist', {
            method: 'POST'
        });
        
        addResponse(window.languageManager ? window.languageManager.getText('address_list_update_success_msg', response.message) : `地址列表更新成功: ${response.message}`, 'success', response.blockchainInfo);
        addLog(response.message, 'success');
        
        setTimeout(() => {
            loadCAList();
            loadUEList();
        }, 1000);
    } catch (error) {
        addResponse(`更新地址列表失败: ${error.message}`, 'error');
        addLog(`更新地址列表失败: ${error.message}`, 'error', 'ue_address_update_failed', error.message);
    }
}

// 初始化页面函数
function initializePage() {
    addLog('UE管理页面已加载', 'info', 'ue_page_loaded');
    checkServerStatus();
    loadCAList();
    loadUEList();
    
    // 延迟加载UE系统日志，确保语言管理器已初始化
    setTimeout(() => {
        loadUESystemLogs();
    }, 500);
    
    // 定期刷新列表（每10秒），但如果之前失败则不再刷新
    window.caListInterval = setInterval(() => {
        if (window.caListInterval) loadCAList();
    }, 10000);
    
    window.ueListInterval = setInterval(() => {
        if (window.ueListInterval) loadUEList();
    }, 10000);
    
    // 定期刷新UE系统日志（每30秒）
    window.ueLogsInterval = setInterval(() => {
        loadUESystemLogs();
    }, 30000);
}