// 全局变量
let caServerProcess = null;
let ueServerProcess = null;
const API_BASE_URL = `${window.location.protocol}//${window.location.host}/api`;

// DOM元素
const elements = {
    // 状态指示器
    caStatus: document.getElementById('ca-status'),
    ueStatus: document.getElementById('ue-status'),
    
    // 服务器控制按钮
    startCaServer: document.getElementById('start-ca-server'),
    startUeServer: document.getElementById('start-ue-server'),
    stopCaServer: document.getElementById('stop-ca-server'),
    stopUeServer: document.getElementById('stop-ue-server'),
    
    // CA功能输入框和按钮
    caName: document.getElementById('ca-name'),
    caLabel: document.getElementById('ca-label'),
    caInitial: document.getElementById('ca-initial'),
    
    caRegisterName: document.getElementById('ca-register-name'),
    ueRegisterName: document.getElementById('ue-register-name'),
    caRegister: document.getElementById('ca-register'),
    
    caUpdateName: document.getElementById('ca-update-name'),
    ueUpdateName: document.getElementById('ue-update-name'),
    caUpdate: document.getElementById('ca-update'),
    
    ueRevokeName: document.getElementById('ue-revoke-name'),
    caRevoke: document.getElementById('ca-revoke'),
    
    // UE功能输入框和按钮
    ueRequestName: document.getElementById('ue-request-name'),
    ueRequest: document.getElementById('ue-request'),
    
    ueUpdatelist: document.getElementById('ue-updatelist'),
    
    ueAuthName: document.getElementById('ue-auth-name'),
    ueTargetName: document.getElementById('ue-target-name'),
    ueAuth: document.getElementById('ue-auth'),
    
    // 日志
    logOutput: document.getElementById('log-output'),
    clearLog: document.getElementById('clear-log')
};

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

// 工具函数
function addLog(message, type = 'info', logKey = null, params = null) {
    const timestamp = new Date().toLocaleTimeString();
    const logClass = `log-${type}`;
    
    // 如果提供了logKey，使用多语言版本
    let finalMessage = message;
    if (logKey && window.languageManager) {
        finalMessage = window.languageManager.getText(`messages.log_messages.${logKey}`);
        // 如果有参数，替换占位符
        if (params) {
            if (Array.isArray(params)) {
                params.forEach((param, index) => {
                    finalMessage = finalMessage.replace(`{${index}}`, param);
                });
            } else {
                finalMessage = finalMessage.replace('{0}', params);
            }
        }
    } else {
        // 如果没有提供logKey或languageManager不可用，使用翻译函数
        finalMessage = translateLogMessage(message);
    }
    
    const logMessage = `[${timestamp}] ${finalMessage}\n`;
    
    const logElement = document.createElement('span');
    logElement.className = logClass;
    logElement.textContent = logMessage;
    
    elements.logOutput.appendChild(logElement);
    elements.logOutput.scrollTop = elements.logOutput.scrollHeight;
}

function updateServerStatus(server, status) {
    const statusElement = server === 'ca' ? elements.caStatus : elements.ueStatus;
    statusElement.textContent = status ? '在线' : '离线';
    statusElement.className = `status-indicator ${status ? 'online' : 'offline'}`;
    
    if (server === 'ca') {
        elements.startCaServer.disabled = status;
        elements.stopCaServer.disabled = !status;
    } else {
        elements.startUeServer.disabled = status;
        elements.stopUeServer.disabled = !status;
    }
}

async function makeApiRequest(endpoint, method = 'POST', data = null) {
    try {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            }
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || '请求失败');
        }
        
        return result;
    } catch (error) {
        addLog(`API请求失败: ${error.message}`, 'error', 'api_request_failed', error.message);
        throw error;
    }
}

// 服务器控制函数
async function startServer(serverType) {
    try {
        addLog(`正在启动 ${serverType.toUpperCase()} 服务器...`, 'info', 'server_starting', serverType.toUpperCase());
        const result = await makeApiRequest(`/server/start/${serverType}`);
        
        if (result.success) {
            updateServerStatus(serverType, true);
            addLog(`${serverType.toUpperCase()} 服务器启动成功`, 'success', `${serverType}_server_start_success`);
        }
    } catch (error) {
        addLog(`启动 ${serverType.toUpperCase()} 服务器失败: ${error.message}`, 'error', 'server_start_failed', [serverType.toUpperCase(), error.message]);
    }
}

async function stopServer(serverType) {
    try {
        addLog(`正在停止 ${serverType.toUpperCase()} 服务器...`, 'info', 'server_stopping', serverType.toUpperCase());
        const result = await makeApiRequest(`/server/stop/${serverType}`);
        
        if (result.success) {
            updateServerStatus(serverType, false);
            addLog(`${serverType.toUpperCase()} 服务器已停止`, 'warning', 'server_stopped', serverType.toUpperCase());
        }
    } catch (error) {
        addLog(`停止 ${serverType.toUpperCase()} 服务器失败: ${error.message}`, 'error', 'server_stop_failed', [serverType.toUpperCase(), error.message]);
    }
}

// CA功能函数
async function caInitial() {
    const caName = elements.caName.value.trim();
    const caLabel = elements.caLabel.value.trim();
    
    if (!caName || !caLabel) {
        addLog(window.languageManager ? window.languageManager.getText('please_fill_ca_name_label') : '请填写CA名称和标签', 'error', 'please_fill_ca_name_label');
        return;
    }
    
    try {
        addLog(`正在初始化CA证书: ${caName}`, 'info', 'ca_initializing', caName);
        const result = await makeApiRequest('/ca/initial', 'POST', {
            caName,
            caLabel
        });
        
        if (result.success) {
            addLog(`CA证书初始化成功: ${caName}`, 'success', 'ca_init_success', caName);
            elements.caName.value = '';
            elements.caLabel.value = '';
        }
    } catch (error) {
        addLog(`CA证书初始化失败: ${error.message}`, 'error', 'ca_init_failed', error.message);
    }
}

async function caRegister() {
    const caName = elements.caRegisterName.value.trim();
    const ueName = elements.ueRegisterName.value.trim();
    
    if (!caName || !ueName) {
        addLog(window.languageManager ? window.languageManager.getText('please_fill_ca_ue_name') : '请填写CA名称和UE名称', 'error', 'please_fill_ca_ue_name');
        return;
    }
    
    try {
        addLog(`正在签署证书: CA=${caName}, UE=${ueName}`, 'info', 'cert_signing', [caName, ueName]);
        const result = await makeApiRequest('/ca/register', 'POST', {
            caName,
            ueName
        });
        
        if (result.success) {
            addLog(`证书签署成功: ${ueName}`, 'success', 'cert_sign_success', ueName);
            elements.caRegisterName.value = '';
            elements.ueRegisterName.value = '';
        }
    } catch (error) {
        addLog(`证书签署失败: ${error.message}`, 'error', 'cert_sign_failed', error.message);
    }
}

async function caUpdate() {
    const caName = elements.caUpdateName.value.trim();
    const ueName = elements.ueUpdateName.value.trim();
    
    if (!caName || !ueName) {
        addLog(window.languageManager ? window.languageManager.getText('please_fill_ca_ue_name') : '请填写CA名称和UE名称', 'error', 'please_fill_ca_ue_name');
        return;
    }
    
    try {
        addLog(`正在更新证书: CA=${caName}, UE=${ueName}`, 'info', 'cert_updating', [caName, ueName]);
        const result = await makeApiRequest('/ca/update', 'POST', {
            caName,
            ueName
        });
        
        if (result.success) {
            addLog(window.languageManager ? window.languageManager.getText('cert_update_success', ueName) : `Certificate update successful: ${ueName}`, 'success', 'cert_update_success', ueName);
            elements.caUpdateName.value = '';
            elements.ueUpdateName.value = '';
        }
    } catch (error) {
        addLog(`证书更新失败: ${error.message}`, 'error', 'cert_update_failed', error.message);
    }
}

async function caRevoke() {
    const ueName = elements.ueRevokeName.value.trim();
    
    if (!ueName) {
        addLog('请填写要撤销的UE名称', 'error', 'please_fill_revoke_ue_name');
        return;
    }
    
    try {
        addLog(`正在撤销证书: ${ueName}`, 'info', 'cert_revoking', ueName);
        const result = await makeApiRequest('/ca/revoke', 'POST', {
            ueName
        });
        
        if (result.success) {
            addLog(window.languageManager ? window.languageManager.getText('cert_revoke_success', ueName) : `Certificate revocation successful: ${ueName}`, 'success', 'cert_revoke_success', ueName);
            elements.ueRevokeName.value = '';
        }
    } catch (error) {
        addLog(`证书撤销失败: ${error.message}`, 'error', 'cert_revoke_failed', error.message);
    }
}

// UE功能函数
async function ueRequest() {
    const ueName = elements.ueRequestName.value.trim();
    
    if (!ueName) {
        addLog(window.languageManager ? window.languageManager.getText('please_fill_ue_name') : 'Please enter UE name', 'error', 'please_fill_ue_name');
        return;
    }
    
    try {
        addLog(`正在发起CSR请求: ${ueName}`, 'info', 'csr_requesting', ueName);
        const result = await makeApiRequest('/ue/request', 'POST', {
            ueName
        });
        
        if (result.success) {
            addLog(`CSR请求发送成功: ${ueName}`, 'success', 'csr_request_success', ueName);
            elements.ueRequestName.value = '';
        }
    } catch (error) {
        addLog(`CSR请求失败: ${error.message}`, 'error', 'csr_request_failed', error.message);
    }
}

async function ueUpdatelist() {
    try {
        addLog('正在更新UE地址列表...', 'info', 'ue_address_updating');
        const result = await makeApiRequest('/ue/updatelist', 'POST');
        
        if (result.success) {
            addLog('UE地址列表更新成功', 'success', 'ue_address_update_success');
        }
    } catch (error) {
        addLog(`更新地址列表失败: ${error.message}`, 'error', 'ue_address_update_failed', error.message);
    }
}

async function ueAuth() {
    const ueName = elements.ueAuthName.value.trim();
    const targetName = elements.ueTargetName.value.trim();
    
    if (!ueName || !targetName) {
        addLog('请填写本地UE名称和目标UE名称', 'error', 'please_fill_local_target_ue');
        return;
    }
    
    try {
        addLog(`正在发起认证请求: ${ueName} -> ${targetName}`, 'info', 'auth_requesting', [ueName, targetName]);
        const result = await makeApiRequest('/ue/auth', 'POST', {
            ueName,
            targetName
        });
        
        if (result.success) {
            addLog(`认证请求成功: ${ueName} -> ${targetName}`, 'success', 'auth_request_success', [ueName, targetName]);
            elements.ueAuthName.value = '';
            elements.ueTargetName.value = '';
        }
    } catch (error) {
        addLog(`发起认证请求失败: ${error.message}`, 'error', 'auth_request_failed', error.message);
    }
}

// 事件监听器
function setupEventListeners() {
    // 服务器控制
    elements.startCaServer.addEventListener('click', () => startServer('ca'));
    elements.startUeServer.addEventListener('click', () => startServer('ue'));
    elements.stopCaServer.addEventListener('click', () => stopServer('ca'));
    elements.stopUeServer.addEventListener('click', () => stopServer('ue'));
    
    // CA功能
    elements.caInitial.addEventListener('click', caInitial);
    elements.caRegister.addEventListener('click', caRegister);
    elements.caUpdate.addEventListener('click', caUpdate);
    elements.caRevoke.addEventListener('click', caRevoke);
    
    // UE功能
    elements.ueRequest.addEventListener('click', ueRequest);
    elements.ueUpdatelist.addEventListener('click', ueUpdatelist);
    elements.ueAuth.addEventListener('click', ueAuth);
    
    // 日志清空
    elements.clearLog.addEventListener('click', () => {
        elements.logOutput.innerHTML = '';
        addLog(window.languageManager ? window.languageManager.getText('system_logs.logs_cleared') : '日志已清空', 'info');
    });
    
    // 自动填充CA标签
    elements.caName.addEventListener('input', (e) => {
        if (!elements.caLabel.value) {
            elements.caLabel.value = e.target.value;
        }
    });
}

// 定期检查服务器状态
async function checkServerStatus() {
    // 服务器状态检查功能已移除
    updateServerStatus('ca', false);
    updateServerStatus('ue', false);
}

// 初始化
function init() {
    setupEventListeners();
    addLog(window.languageManager ? window.languageManager.getText('system_logs.platform_started') : 'DPKI管理平台已启动', 'success');
    
    // 立即检查一次状态
    checkServerStatus();
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', init);