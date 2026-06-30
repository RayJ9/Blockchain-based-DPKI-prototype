// CA管理页面JavaScript

// 全局变量
const API_BASE_URL = `${window.location.protocol}//${window.location.host}/api`;

// 时延统计工具函数
class TimingTracker {
    constructor() {
        this.timers = new Map();
    }
    
    start(operationId) {
        this.timers.set(operationId, Date.now());
        this.updateDisplay(operationId, (window.languageManager ? window.languageManager.getText('executing') : '执行中...'), true);
    }
    
    end(operationId, backendTiming = null) {
        const startTime = this.timers.get(operationId);
        if (startTime) {
            const frontendDuration = Date.now() - startTime;
            // 如果有后端时延信息，优先使用后端时延
            const displayTiming = backendTiming || `${frontendDuration}ms`;
            this.updateDisplay(operationId, displayTiming, false);
            this.timers.delete(operationId);
            return frontendDuration;
        }
        return 0;
    }
    
    updateDisplay(operationId, text, isActive = false) {
        const element = document.getElementById(`${operationId}Timing`);
        if (element) {
            element.textContent = text;
            if (isActive) {
                element.classList.add('timing-active');
            } else {
                element.classList.remove('timing-active');
            }
        }
    }
    
    // 从后端输出中提取时延信息
    extractBackendTiming(output, timingKey) {
        if (!output) return null;
        
        // 匹配时延格式：Initial Time: 1.184s, register Time: 1.086s 等
        const regex = new RegExp(`${timingKey}:\\s*([\\d.]+(?:ms|s))`, 'i');
        const match = output.match(regex);
        return match ? match[1] : null;
    }
}

// 创建全局时延跟踪器
const timingTracker = new TimingTracker();

// DOM元素
let caStatusEl, caListEl, ueListEl, caSystemLogsEl, caResponseArea;

document.addEventListener('DOMContentLoaded', function() {
    // 获取DOM元素
    caStatusEl = document.getElementById('caStatus');
    caListEl = document.getElementById('caList');
    ueListEl = document.getElementById('ueList');
    caSystemLogsEl = document.getElementById('caSystemLogs');
    caResponseArea = document.getElementById('caResponseArea');
    
    // 初始化页面
    initializePage();
    
    // 初始化部署合约按钮
    const deployContractBtn = document.getElementById('deployContractBtn');
    if (deployContractBtn) {
        deployContractBtn.addEventListener('click', deployContract);
    }
});

// 添加响应到右侧区域
function addResponse(content, type = 'info', blockchainInfo = null) {
    if (!caResponseArea) return;
    
    // 清空之前的回执
    caResponseArea.innerHTML = '';
    
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
    } else {
        receiptDiv.style.color = '#495057';
    }
    
    receiptDiv.textContent = content;
    responseItem.appendChild(receiptDiv);
    
    caResponseArea.appendChild(responseItem);
    caResponseArea.scrollTop = caResponseArea.scrollHeight;
}

// 服务器控制按钮
const startCaBtn = document.getElementById('startCaBtn');
const stopCaBtn = document.getElementById('stopCaBtn');

// CA功能按钮
const initCaBtn = document.getElementById('initCaBtn');
const signCertBtn = document.getElementById('signCertBtn');
const updateCertBtn = document.getElementById('updateCertBtn');
const revokeCertBtn = document.getElementById('revokeCertBtn');

// 工具函数
function addLog(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry log-${type}`;
    logEntry.innerHTML = `<span class="log-time">[${timestamp}]</span> ${message}`;
    if (caSystemLogsEl) {
        caSystemLogsEl.appendChild(logEntry);
        caSystemLogsEl.scrollTop = caSystemLogsEl.scrollHeight;
    }
    
    // 根据日志消息更新服务器状态
    updateServerStatusFromLog(message);
}

// 加载CA系统日志
async function loadCASystemLogs() {
    try {
        const response = await fetch(`${API_BASE_URL}/logs`);
        if (response.ok) {
            const data = await response.json();
            const logs = data.logs || [];
            displayCASystemLogs(logs);
        }
    } catch (error) {
        console.error((window.languageManager ? window.languageManager.getText('system_logs.load_ca_logs_failed') : '加载CA系统日志失败') + ':', error);
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
            pattern: /UE CSR请求成功:\s*(.+)；证书注册成功；UE认证成功 - 验证通过/,
            replacement: 'UE CSR request successful: $1; Certificate registration successful; UE authentication successful - verification passed'
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

// 显示CA系统日志
function displayCASystemLogs(logs) {
    if (!caSystemLogsEl) return;
        
        caSystemLogsEl.innerHTML = '';
        
        if (logs.length === 0) {
            caSystemLogsEl.innerHTML = '<div class="log-entry">' + (window.languageManager ? window.languageManager.getText('system_logs.no_ca_system_logs') : '暂无CA系统日志') + '</div>';
            return;
        }
    
    logs.forEach(log => {
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        logEntry.innerHTML = `
            <div class="log-timestamp">${log.timestamp}</div>
            <div class="log-message">${translateLogMessage(log.message)}</div>
        `;
        caSystemLogsEl.appendChild(logEntry);
    });
}

function updateServerStatusFromLog(message) {
    // 检查CA服务器状态相关的日志消息
    if (message.includes('CA服务器启动成功') || message.includes('CA服务器已在运行')) {
        if (caStatusEl) {
            caStatusEl.textContent = '在线';
            caStatusEl.className = 'status-indicator online';
        }
        // 暂停定时检查，避免冲突
        window.statusCheckPaused = true;
        setTimeout(() => {
            window.statusCheckPaused = false;
        }, 3000);
    } else if (message.includes('CA服务器退出') || message.includes('CA服务器未运行')) {
        if (caStatusEl) {
            caStatusEl.textContent = '离线';
            caStatusEl.className = 'status-indicator offline';
        }
        // 暂停定时检查，避免冲突
        window.statusCheckPaused = true;
        setTimeout(() => {
            window.statusCheckPaused = false;
        }, 3000);
    }
}

function updateServerStatus(caOnline, ueOnline) {
    // CA页面只更新CA服务器状态
    if (caStatusEl) {
        caStatusEl.textContent = caOnline ? '在线' : '离线';
        caStatusEl.className = `status-indicator ${caOnline ? 'online' : 'offline'}`;
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
        addLog(`启动${type}服务器失败: ${error.message || '网络错误'}`, 'error', 'server_start_failed', [type, error.message || '网络错误']);
    }
}

async function stopServer(type) {
    try {
        const response = await makeApiRequest(`/server/stop/${type}`, { method: 'POST' });
        addLog(response.message, 'success');
        setTimeout(checkServerStatus, 1000);
    } catch (error) {
        console.error(`停止${type}服务器失败:`, error);
        addLog(`停止${type}服务器失败: ${error.message || '网络错误'}`, 'error', 'server_stop_failed', [type, error.message || '网络错误']);
    }
}

// CA功能函数
async function initializeCA() {
    const caName = document.getElementById('caName').value.trim();
    
    if (!caName) {
        addResponse(window.languageManager ? window.languageManager.getText('please_fill_ca_name_error') : '请填写CA名称', 'error');
        addLog(window.languageManager ? window.languageManager.getText('please_fill_ca_name') : '请填写CA名称', 'error', 'please_fill_ca_name');
        return;
    }
    
    // 自动为CA名称添加"CA-"前缀（如果还没有的话）
    const finalCaName = caName.startsWith('CA-') ? caName : `CA-${caName}`;
    
    // 开始计时
    timingTracker.start('initCa');
    
    try {
        addResponse(window.languageManager ? window.languageManager.getText('initializing_ca') : '正在初始化CA...', 'info');
        const response = await makeApiRequest('/ca/initial', {
            method: 'POST',
            body: JSON.stringify({ caName: finalCaName, caLabel: finalCaName })
        });
        
        // 从后端响应中提取时延信息
        const backendTiming = timingTracker.extractBackendTiming(response.output, 'Initial Time');
        
        // 结束计时
        timingTracker.end('initCa', backendTiming);
        
        // 显示完整的后端输出
        addResponse(response.output || response.message, 'success');
        addLog(window.languageManager ? window.languageManager.getText('ca_init_success', finalCaName) : `CA certificate initialization successful: ${finalCaName}`, 'success', 'ca_init_success', finalCaName);
        
        // 清空输入框
        document.getElementById('caName').value = '';
        
        setTimeout(() => {
            loadCAList();
            loadUEList();
        }, 1000);
    } catch (error) {
        // 结束计时（即使出错也要结束）
        timingTracker.end('initCa');
        addResponse(`初始化CA失败: ${error.message}`, 'error');
        addLog(`初始化CA失败: ${error.message}`, 'error', 'ca_init_failed', error.message);
    }
}

async function signCertificate() {
    const caName = document.getElementById('signCaName').value.trim();
    const ueName = document.getElementById('signUeName').value.trim();
    
    if (!caName || !ueName) {
        addResponse(window.languageManager ? window.languageManager.getText('please_fill_ca_ue_name_error') : '请填写CA名称和UE名称', 'error');
        addLog(window.languageManager ? window.languageManager.getText('please_fill_ca_ue_name') : '请填写CA名称和UE名称', 'error', 'please_fill_ca_ue_name');
        return;
    }
    
    // 自动为CA名称添加"CA-"前缀（如果还没有的话）
    const finalCaName = caName.startsWith('CA-') ? caName : `CA-${caName}`;
    
    // 开始计时
    timingTracker.start('signCert');
    
    try {
        addResponse(window.languageManager ? window.languageManager.getText('signing_cert') : '正在签署证书...', 'info');
        const response = await makeApiRequest('/ca/register', {
            method: 'POST',
            body: JSON.stringify({ caName: finalCaName, ueName })
        });
        
        // 从后端响应中提取时延信息
        const backendTiming = timingTracker.extractBackendTiming(response.output, 'register Time');
        
        // 结束计时
        timingTracker.end('signCert', backendTiming);
        
        // 显示完整的后端输出
        addResponse(response.output || response.message, 'success');
        addLog(window.languageManager ? window.languageManager.getText('cert_update_success', ueName) : `Certificate update successful: ${ueName}`, 'success', 'cert_update_success', ueName);
        
        // 清空输入框
        document.getElementById('signCaName').value = '';
        document.getElementById('signUeName').value = '';
        
        setTimeout(() => {
            loadCAList();
            loadUEList();
        }, 1000);
    } catch (error) {
        // 结束计时（即使出错也要结束）
        timingTracker.end('signCert');
        addResponse(`签署证书失败: ${error.message}`, 'error');
        addLog(`签署证书失败: ${error.message}`, 'error', 'cert_sign_failed', error.message);
    }
}

async function updateCertificate() {
    const caName = document.getElementById('updateCaName').value.trim();
    const ueName = document.getElementById('updateUeName').value.trim();
    
    if (!caName || !ueName) {
        addResponse(window.languageManager ? window.languageManager.getText('please_fill_ca_ue_name_error') : '请填写CA名称和UE名称', 'error');
        addLog(window.languageManager ? window.languageManager.getText('please_fill_ca_ue_name') : '请填写CA名称和UE名称', 'error', 'please_fill_ca_ue_name');
        return;
    }
    
    // 开始计时
    timingTracker.start('updateCert');
    
    try {
        addResponse(window.languageManager ? window.languageManager.getText('updating_cert') : '正在更新证书...', 'info');
        const response = await makeApiRequest('/ca/update', {
            method: 'POST',
            body: JSON.stringify({ caName, ueName })
        });
        
        // 从后端响应中提取时延信息
        const backendTiming = timingTracker.extractBackendTiming(response.output, 'update Time');
        
        // 结束计时
        timingTracker.end('updateCert', backendTiming);
        
        // 显示完整的后端输出
        addResponse(response.output || response.message, 'success');
        addLog(response.message, 'success');
        
        // 清空输入框
        document.getElementById('updateCaName').value = '';
        document.getElementById('updateUeName').value = '';
        
        setTimeout(() => {
            loadCAList();
            loadUEList();
        }, 1000);
    } catch (error) {
        // 结束计时（即使出错也要结束）
        timingTracker.end('updateCert');
        addResponse(`更新证书失败: ${error.message}`, 'error');
        addLog(`更新证书失败: ${error.message}`, 'error', 'cert_update_failed', error.message);
    }
}

async function revokeCertificate() {
    const ueName = document.getElementById('revokeUeName').value.trim();
    
    if (!ueName) {
        addResponse(window.languageManager ? window.languageManager.getText('please_fill_ue_name_error') : '请填写UE名称', 'error');
        addLog(window.languageManager ? window.languageManager.getText('please_fill_revoke_ue_name') : '请填写要撤销的UE名称', 'error', 'please_fill_revoke_ue_name');
        return;
    }
    
    // 开始计时
    timingTracker.start('revokeCert');
    
    try {
        addResponse(window.languageManager ? window.languageManager.getText('revoking_cert') : '正在撤销证书...', 'info');
        const response = await makeApiRequest('/ca/revoke', {
            method: 'POST',
            body: JSON.stringify({ ueName })
        });
        
        // 从后端响应中提取时延信息
        const backendTiming = timingTracker.extractBackendTiming(response.output, 'revoke Time');
        
        // 结束计时
        timingTracker.end('revokeCert', backendTiming);
        
        // 显示完整的后端输出
        addResponse(response.output || response.message, 'success');
        addLog(response.message, 'success');
        
        // 清空输入框
        document.getElementById('revokeUeName').value = '';
        
        setTimeout(() => {
            loadCAList();
            loadUEList();
        }, 1000);
    } catch (error) {
        // 结束计时（即使出错也要结束）
        timingTracker.end('revokeCert');
        addResponse(`撤销证书失败: ${error.message}`, 'error');
        addLog(`撤销证书失败: ${error.message}`, 'error', 'cert_revoke_failed', error.message);
    }
}

// 初始化页面函数
function initializePage() {
    addLog('CA管理页面已加载', 'info', 'ca_page_loaded');
    checkServerStatus();
    loadCAList();
    loadUEList();
    
    // 延迟加载CA系统日志，确保语言管理器已初始化
    setTimeout(() => {
        loadCASystemLogs();
    }, 500);
    
    // 定期刷新列表（每10秒），但如果之前失败则不再刷新
    window.caListInterval = setInterval(() => {
        if (window.caListInterval) loadCAList();
    }, 10000);
    
    window.ueListInterval = setInterval(() => {
        if (window.ueListInterval) loadUEList();
    }, 10000);
    
    // 定期刷新CA系统日志（每30秒）
    window.caLogsInterval = setInterval(() => {
        loadCASystemLogs();
    }, 30000);
}

// 事件监听器
document.addEventListener('DOMContentLoaded', () => {
    // 获取按钮元素
    const startCaBtn = document.getElementById('startCaBtn');
    const stopCaBtn = document.getElementById('stopCaBtn');
    const initCaBtn = document.getElementById('initCaBtn');
    const signCertBtn = document.getElementById('signCertBtn');
    const updateCertBtn = document.getElementById('updateCertBtn');
    const revokeCertBtn = document.getElementById('revokeCertBtn');
    
    // 添加事件监听器
    if (startCaBtn) startCaBtn.addEventListener('click', () => startServer('ca'));
    if (stopCaBtn) stopCaBtn.addEventListener('click', () => stopServer('ca'));
    if (initCaBtn) initCaBtn.addEventListener('click', initializeCA);
    if (signCertBtn) signCertBtn.addEventListener('click', signCertificate);
    if (updateCertBtn) updateCertBtn.addEventListener('click', updateCertificate);
    if (revokeCertBtn) revokeCertBtn.addEventListener('click', revokeCertificate);
});

// 部署合约功能
async function deployContract() {
    const deployStatus = document.getElementById('deployStatus');
    const deployBtn = document.getElementById('deployContractBtn');
    
    deployStatus.innerHTML = `<span style="color: orange;">${window.languageManager.getText('deploying_contract')}</span>`;
    deployBtn.disabled = true;
    
    // 开始计时
    timingTracker.start('deployContract');
    
    try {
        const response = await fetch('/api/deploy-contract', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        // 检查响应是否为JSON格式
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            throw new Error(`服务器返回非JSON响应: ${text.substring(0, 200)}`);
        }
        
        const result = await response.json();
        
        // 结束计时
        timingTracker.end('deployContract');
        
        if (result.success) {
            deployStatus.innerHTML = `<span style="color: green;">${window.languageManager.getText('deploy_success', result.contractAddress)}</span>`;
            // 刷新CA系统日志
            setTimeout(() => {
                loadCASystemLogs();
            }, 1000);
        } else {
            deployStatus.innerHTML = `<span style="color: red;">${window.languageManager.getText('deploy_failed', result.error)}</span>`;
        }
    } catch (error) {
        // 结束计时（即使出错也要结束）
        timingTracker.end('deployContract');
        console.error('部署合约错误:', error);
        deployStatus.innerHTML = `<span style="color: red;">${window.languageManager.getText('deploy_error', error.message)}</span>`;
    } finally {
        deployBtn.disabled = false;
    }
}