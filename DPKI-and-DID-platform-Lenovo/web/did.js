// DID管理页面JavaScript

// 时延统计类
class TimingTracker {
    constructor() {
        this.timings = {};
    }
    
    start(operationId) {
        this.timings[operationId] = {
            startTime: Date.now(),
            endTime: null,
            duration: null
        };
        this.updateDisplay(operationId, (window.languageManager ? window.languageManager.getText('timing') : '计时中...'), true);
    }
    
    end(operationId, backendTiming = null) {
        if (this.timings[operationId]) {
            this.timings[operationId].endTime = Date.now();
            this.timings[operationId].duration = this.timings[operationId].endTime - this.timings[operationId].startTime;
            // 如果有后端时延信息，优先使用后端时延，否则使用前端计时
            const displayTiming = backendTiming || `${this.timings[operationId].duration}ms`;
            this.updateDisplay(operationId, displayTiming, false);
        }
    }
    
    updateDisplay(operationId, text, isActive) {
        const displayElement = document.getElementById(`${operationId}Timing`);
        if (displayElement) {
            displayElement.textContent = text;
            if (isActive) {
                displayElement.classList.add('timing-active');
            } else {
                displayElement.classList.remove('timing-active');
            }
        }
    }
    
    // 从后端输出中提取时延信息（为了保持一致性，虽然DID服务目前不返回时延）
    extractBackendTiming(output, timingKey) {
        if (!output) return null;
        
        // 匹配时延格式：generateDid Time: 100ms, queryDid Time: 50ms 等
        const regex = new RegExp(`${timingKey}:\\s*([\\d.]+(?:ms|s))`, 'i');
        const match = output.match(regex);
        return match ? match[1] : null;
    }
}

// 创建时延统计实例
const timingTracker = new TimingTracker();

// 全局变量
const API_BASE_URL = `${window.location.protocol}//${window.location.host}/api`;

// DOM元素
let didResult, vcResult, vcVerifyResult, serviceStatus;

// 存储数据
let didHistory = [];
let vcHistory = [];

document.addEventListener('DOMContentLoaded', function() {
    // 获取DOM元素
    didResult = document.getElementById('didResult');
    vcResult = document.getElementById('vcResult');
    vcVerifyResult = document.getElementById('vcVerifyResult');
    serviceStatus = document.getElementById('serviceStatus');
    
    // 初始化页面
    initializePage();
});

// 初始化页面
function initializePage() {
    updateServiceStatus();
}

// 更新服务状态
function updateServiceStatus() {
    if (!serviceStatus) return;
    
    serviceStatus.innerHTML = `
        <span class="status-indicator status-success"></span>
        DID服务已就绪，可以开始操作
    `;
}

// 生成DID
async function generateDID() {
    timingTracker.start('generateDid');
    try {
        document.getElementById('didResult').textContent = '正在生成新的DID...';
        
        const response = await fetch(`/api/did/create`, {
            method: 'GET'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.code === 1) {
            document.getElementById('didResult').textContent = result.data;
            
            // 添加到历史记录
            didHistory.unshift({
                did: result.data,
                timestamp: new Date().toLocaleString(),
                type: 'generated'
            });
            timingTracker.end('generateDid');
        } else {
            document.getElementById('didResult').textContent = `DID生成失败: ${result.msg}`;
            timingTracker.end('generateDid');
        }
    } catch (error) {
        console.error('创建DID失败:', error);
        document.getElementById('didResult').textContent = `DID生成失败: ${error.message}`;
        timingTracker.end('generateDid');
    }
}

// 查询DID文档
async function queryDIDDocument() {
    const didInput = document.getElementById('queryDID').value.trim();
    
    if (!didInput) {
        document.getElementById('didDocResult').textContent = '请输入要查询的DID';
        return;
    }
    
    timingTracker.start('queryDid');
    try {
        document.getElementById('didDocResult').textContent = '正在查询DID文档...';
        
        // 添加200ms前端间隔
        await new Promise(resolve => setTimeout(resolve, 200));
        
        const response = await fetch(`${API_BASE_URL}/did/query/${encodeURIComponent(didInput)}`, {
            method: 'GET'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.code === 1) {
            document.getElementById('didDocResult').textContent = `DID文档查询成功！\n\n${JSON.stringify(result.data, null, 2)}`;
            
            // 添加到历史记录
            didHistory.unshift({
                did: didInput,
                document: result.data,
                timestamp: new Date().toLocaleString(),
                type: 'queried'
            });
            timingTracker.end('queryDid');
        } else {
            document.getElementById('didDocResult').textContent = `DID查询失败: ${result.msg}`;
            timingTracker.end('queryDid');
        }
    } catch (error) {
        console.error('查询DID失败:', error);
        document.getElementById('didDocResult').textContent = `DID查询失败: ${error.message}`;
        timingTracker.end('queryDid');
    }
}

// 验证DID是否存在于已生成的DID列表中
function validateDID(did) {
    // 检查DID是否在didHistory中
    const isInHistory = didHistory.some(item => item.did === did);
    
    // 检查DID是否在didVcData中（如果在HTML页面中）
    const isInVcData = typeof didVcData !== 'undefined' && didVcData.hasOwnProperty(did);
    
    return isInHistory || isInVcData;
}

// 生成VC
async function generateVC() {
    const didInput = document.getElementById('vcDID').value.trim();
    const permissionInput = document.getElementById('operatorPermission').value.trim();
    // 固定启用状态为true（有效）
    const enabledInput = 'true';
    
    if (!didInput) {
        document.getElementById('vcResult').value = window.languageManager ? window.languageManager.getText('vc_did_required') : '请填写DID标识符';
        return;
    }
    
    // 验证DID格式是否正确（必须包含did:omni:前缀）
    if (!didInput.startsWith('did:omni:')) {
        document.getElementById('vcResult').value = window.languageManager ? window.languageManager.getText('vc_did_format_error') : '错误：DID格式不正确，必须以"did:omni:"开头';
        return;
    }
    
    // 验证DID是否存在
    document.getElementById('vcResult').value = window.languageManager ? window.languageManager.getText('vc_validating_did') : '正在验证DID...';
    const isValidDID = validateDID(didInput);
    if (!isValidDID) {
        document.getElementById('vcResult').value = 'DID not valid';
        return;
    }
    
    timingTracker.start('generateVc');
    try {
        document.getElementById('vcResult').value = '正在签发可验证凭证...';
        
        const response = await fetch(`/api/vc/user-attribute?did=${encodeURIComponent(didInput)}&operatorPermission=${encodeURIComponent(permissionInput)}&enabled=${encodeURIComponent(enabledInput)}`, {
            method: 'GET'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.code === 1) {
            document.getElementById('vcResult').value = result.data;
            
            // 添加到VC历史记录
            vcHistory.unshift({
                did: didInput,
                permission: permissionInput,
                enabled: enabledInput,
                jwt: result.data,
                timestamp: new Date().toLocaleString(),
                type: 'created'
            });
            timingTracker.end('generateVc');
        } else {
            document.getElementById('vcResult').value = `VC签发失败: ${result.msg}`;
            timingTracker.end('generateVc');
        }
    } catch (error) {
        console.error('签发VC失败:', error);
        document.getElementById('vcResult').value = `VC签发失败: ${error.message}`;
        timingTracker.end('generateVc');
    }
}

// 生成DID
async function generateDID() {
    timingTracker.start('generateDid');
    try {
        document.getElementById('didResult').textContent = '正在生成新的DID...';
        
        const response = await fetch(`/api/did/create`, {
            method: 'GET'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.code === 1) {
            document.getElementById('didResult').textContent = result.data;
            
            // 添加到历史记录
            didHistory.unshift({
                did: result.data,
                timestamp: new Date().toLocaleString(),
                type: 'generated'
            });
            timingTracker.end('generateDid');
        } else {
            document.getElementById('didResult').textContent = `DID生成失败: ${result.msg}`;
            timingTracker.end('generateDid');
        }
    } catch (error) {
        console.error('创建DID失败:', error);
        document.getElementById('didResult').textContent = `DID生成失败: ${error.message}`;
        timingTracker.end('generateDid');
    }
}