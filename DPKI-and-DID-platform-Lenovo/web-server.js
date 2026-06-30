const express = require('express');
const cors = require('cors');
const path = require('path');
const { spawn, exec } = require('child_process');
const fs = require('fs');

const app = express();
const PORT = 3001;

// 日志文件路径
const CA_LOG_FILE = path.join(__dirname, 'logs', 'ca-system.log');
const UE_LOG_FILE = path.join(__dirname, 'logs', 'ue-system.log');

// 确保日志目录存在
function ensureLogDirectory() {
    const logDir = path.join(__dirname, 'logs');
    if (!fs.existsSync(logDir)) {
        fs.mkdirSync(logDir, { recursive: true });
    }
}

// 写入日志到指定文件
function writeLog(message, level = 'INFO', logType = 'general') {
    ensureLogDirectory();
    const timestamp = new Date().toISOString();
    const logEntry = `[${timestamp}] [${level}] ${message}\n`;
    
    let logFile;
    switch (logType) {
        case 'ca':
            logFile = CA_LOG_FILE;
            break;
        case 'ue':
            logFile = UE_LOG_FILE;
            break;
        default:
            // 对于通用日志，同时写入CA和UE日志
            try {
                fs.appendFileSync(CA_LOG_FILE, logEntry);
                fs.appendFileSync(UE_LOG_FILE, logEntry);
            } catch (error) {
                console.error('写入日志失败:', error);
            }
            return;
    }
    
    try {
        fs.appendFileSync(logFile, logEntry);
    } catch (error) {
        console.error('写入日志失败:', error);
    }
}

// 读取指定类型的最新日志条目
function getRecentLogs(count = 5, logType = 'ca') {
    try {
        const logFile = logType === 'ca' ? CA_LOG_FILE : UE_LOG_FILE;
        
        if (!fs.existsSync(logFile)) {
            return [];
        }
        
        const logContent = fs.readFileSync(logFile, 'utf8');
        const lines = logContent.trim().split('\n').filter(line => line.trim());
        
        // 返回最新的几条日志
        return lines.slice(-count).map(line => {
            const match = line.match(/^\[([^\]]+)\] \[([^\]]+)\] (.+)$/);
            if (match) {
                return {
                    timestamp: match[1],
                    level: match[2],
                    message: match[3]
                };
            }
            return { timestamp: '', level: 'INFO', message: line };
        });
    } catch (error) {
        console.error('读取日志失败:', error);
        return [];
    }
}

// 解析区块链信息的函数
function parseBlockchainInfo(output) {
    const blockchainInfo = {};
    
    if (!output) return blockchainInfo;
    
    // 解析交易哈希
    const txHashMatch = output.match(/交易哈希[：:]\s*([a-fA-F0-9]+)/);
    if (txHashMatch) {
        blockchainInfo['交易哈希'] = txHashMatch[1];
    }
    
    // 解析区块高度
    const blockHeightMatch = output.match(/区块高度[：:]\s*(\d+)/);
    if (blockHeightMatch) {
        blockchainInfo['区块高度'] = blockHeightMatch[1];
    }
    
    // 解析Gas费用
    const gasFeeMatch = output.match(/Gas费用[：:]\s*([\d.]+)/);
    if (gasFeeMatch) {
        blockchainInfo['Gas费用'] = gasFeeMatch[1];
    }
    
    // 解析时间戳
    const timestampMatch = output.match(/时间戳[：:]\s*(\d+)/);
    if (timestampMatch) {
        const timestamp = parseInt(timestampMatch[1]);
        blockchainInfo['时间戳'] = new Date(timestamp * 1000).toLocaleString();
    }
    
    // 解析合约地址
    const contractMatch = output.match(/合约地址[：:]\s*([a-fA-F0-9x]+)/);
    if (contractMatch) {
        blockchainInfo['合约地址'] = contractMatch[1];
    }
    
    return blockchainInfo;
}

// 中间件
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'web')));

// 全局变量存储进程
let caServerProcess = null;
let ueServerProcess = null;

// 工具函数
function executeCommand(command, args = [], options = {}) {
    return new Promise((resolve, reject) => {
        const process = spawn(command, args, {
            cwd: __dirname,
            ...options
        });
        
        let stdout = '';
        let stderr = '';
        
        process.stdout?.on('data', (data) => {
            stdout += data.toString();
        });
        
        process.stderr?.on('data', (data) => {
            stderr += data.toString();
        });
        
        process.on('close', (code) => {
            if (code === 0) {
                resolve({ stdout, stderr, code });
            } else {
                reject(new Error(`命令执行失败: ${stderr || stdout}`));
            }
        });
        
        process.on('error', (error) => {
            reject(new Error(`进程启动失败: ${error.message}`));
        });
    });
}

function executeDPKICommand(scriptName, args = []) {
    return new Promise((resolve, reject) => {
        // 在Windows上使用.exe文件
        const command = path.join(__dirname, 'bin', `${scriptName}.exe`);
        
        // 设置超时时间（30秒）
        const timeout = 30000;
        let timeoutId;
        
        // 检查文件是否存在
        if (!fs.existsSync(command)) {
            // 如果.exe不存在，尝试使用node执行.js文件
            const jsFile = path.join(__dirname, 'bin', `${scriptName}.js`);
            if (fs.existsSync(jsFile)) {
                const process = spawn('node', [jsFile, ...args], {
                    cwd: __dirname  // 改为项目根目录
                });
                
                let stdout = '';
                let stderr = '';
                
                // 设置超时
                timeoutId = setTimeout(() => {
                    process.kill('SIGTERM');
                    reject(new Error('命令执行超时（30秒）'));
                }, timeout);
                
                process.stdout.on('data', (data) => {
                    stdout += data.toString();
                });
                
                process.stderr.on('data', (data) => {
                    stderr += data.toString();
                });
                
                process.on('close', (code) => {
                    clearTimeout(timeoutId);
                    if (code === 0) {
                        resolve({ stdout, stderr, code });
                    } else {
                        reject(new Error(`命令执行失败: ${stderr || stdout}`));
                    }
                });
                
                process.on('error', (error) => {
                    clearTimeout(timeoutId);
                    reject(new Error(`进程启动失败: ${error.message}`));
                });
            } else {
                reject(new Error(`找不到可执行文件: ${scriptName}`));
            }
        } else {
            // 使用.exe文件
            const process = spawn(command, args, {
                cwd: __dirname  // 改为项目根目录
            });
            
            let stdout = '';
            let stderr = '';
            
            // 设置超时
            timeoutId = setTimeout(() => {
                process.kill('SIGTERM');
                reject(new Error('命令执行超时（30秒）'));
            }, timeout);
            
            process.stdout.on('data', (data) => {
                stdout += data.toString();
            });
            
            process.stderr.on('data', (data) => {
                stderr += data.toString();
            });
            
            process.on('close', (code) => {
                clearTimeout(timeoutId);
                if (code === 0) {
                    resolve({ stdout, stderr, code });
                } else {
                    reject(new Error(`命令执行失败: ${stderr || stdout}`));
                }
            });
            
            process.on('error', (error) => {
                clearTimeout(timeoutId);
                reject(new Error(`进程启动失败: ${error.message}`));
            });
        }
    });
}

// API路由

// 服务器启动API
app.post('/api/server/start/:type', (req, res) => {
    const { type } = req.params;
    let responseHandled = false;
    
    try {
        if (type === 'ca') {
            if (caServerProcess && !caServerProcess.killed) {
                return res.json({ success: false, message: 'CA服务器已在运行' });
            }
            
            // 启动CA服务器
            const caCommand = path.join(__dirname, 'bin', 'Server-CA.exe');
            if (fs.existsSync(caCommand)) {
                caServerProcess = spawn(caCommand, [], { cwd: path.join(__dirname, 'bin') });
                console.log('启动CA服务器 (exe):', caCommand);
            } else {
                const jsCommand = path.join(__dirname, 'bin', 'Server-CA.js');
                if (fs.existsSync(jsCommand)) {
                    caServerProcess = spawn('node', ['Server-CA.js'], { cwd: path.join(__dirname, 'bin') });
                    console.log('启动CA服务器 (js):', jsCommand);
                } else {
                    return res.json({ success: false, message: '找不到CA服务器文件' });
                }
            }
            
            caServerProcess.on('error', (error) => {
                console.error('CA服务器启动失败:', error);
                caServerProcess = null;
                if (!responseHandled) {
                    responseHandled = true;
                    res.json({ success: false, message: `CA服务器启动失败: ${error.message}` });
                }
            });
            
            caServerProcess.on('exit', (code) => {
                console.log('CA服务器退出，代码:', code);
                caServerProcess = null;
                if (!responseHandled && code !== 0) {
                    responseHandled = true;
                    res.json({ success: false, message: `CA服务器启动失败，退出代码: ${code}` });
                }
            });
            
            // 给进程一点时间启动
            setTimeout(() => {
                if (!responseHandled) {
                    responseHandled = true;
                    if (caServerProcess && !caServerProcess.killed) {
                        res.json({ success: true, message: 'CA服务器启动成功' });
                    } else {
                        res.json({ success: false, message: 'CA服务器启动失败' });
                    }
                }
            }, 1000);
            
        } else if (type === 'ue') {
            if (ueServerProcess && !ueServerProcess.killed) {
                return res.json({ success: false, message: 'UE服务器已在运行' });
            }
            
            // 启动UE服务器
            const ueCommand = path.join(__dirname, 'bin', 'Server-UE.exe');
            if (fs.existsSync(ueCommand)) {
                ueServerProcess = spawn(ueCommand, [], { cwd: path.join(__dirname, 'bin') });
                console.log('启动UE服务器 (exe):', ueCommand);
            } else {
                const jsCommand = path.join(__dirname, 'bin', 'Server-UE.js');
                if (fs.existsSync(jsCommand)) {
                    ueServerProcess = spawn('node', ['Server-UE.js'], { cwd: path.join(__dirname, 'bin') });
                    console.log('启动UE服务器 (js):', jsCommand);
                } else {
                    return res.json({ success: false, message: '找不到UE服务器文件' });
                }
            }
            
            ueServerProcess.on('error', (error) => {
                console.error('UE服务器启动失败:', error);
                ueServerProcess = null;
                if (!responseHandled) {
                    responseHandled = true;
                    res.json({ success: false, message: `UE服务器启动失败: ${error.message}` });
                }
            });
            
            ueServerProcess.on('exit', (code) => {
                console.log('UE服务器退出，代码:', code);
                ueServerProcess = null;
                if (!responseHandled && code !== 0) {
                    responseHandled = true;
                    res.json({ success: false, message: `UE服务器启动失败，退出代码: ${code}` });
                }
            });
            
            // 给进程一点时间启动
            setTimeout(() => {
                if (!responseHandled) {
                    responseHandled = true;
                    if (ueServerProcess && !ueServerProcess.killed) {
                        res.json({ success: true, message: 'UE服务器启动成功' });
                    } else {
                        res.json({ success: false, message: 'UE服务器启动失败' });
                    }
                }
            }, 1000);
            
        } else {
            res.json({ success: false, message: '无效的服务器类型' });
        }
    } catch (error) {
        console.error('服务器启动错误:', error);
        if (!responseHandled) {
            res.json({ success: false, message: error.message });
        }
    }
});

// 停止服务器
app.post('/api/server/stop/:type', (req, res) => {
    const { type } = req.params;
    
    try {
        if (type === 'ca') {
            if (caServerProcess && !caServerProcess.killed) {
                caServerProcess.kill();
                caServerProcess = null;
                console.log('CA服务器已停止');
                res.json({ success: true, message: 'CA服务器已停止' });
            } else {
                console.log('CA服务器未运行，无需停止');
                res.json({ success: false, message: 'CA服务器未运行' });
            }
        } else if (type === 'ue') {
            if (ueServerProcess && !ueServerProcess.killed) {
                ueServerProcess.kill();
                ueServerProcess = null;
                console.log('UE服务器已停止');
                res.json({ success: true, message: 'UE服务器已停止' });
            } else {
                console.log('UE服务器未运行，无需停止');
                res.json({ success: false, message: 'UE服务器未运行' });
            }
        } else {
            console.log('无效的服务器类型:', type);
            res.json({ success: false, message: '无效的服务器类型' });
        }
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// CA功能API

// CA初始化
app.post('/api/ca/initial', async (req, res) => {
    try {
        const { caName, caLabel } = req.body;
        
        if (!caName || !caLabel) {
            writeLog(`CA初始化失败: 缺少必要参数 (caName: ${caName}, caLabel: ${caLabel})`, 'ERROR', 'ca');
            return res.status(400).json({ error: '请提供CA名称和标签' });
        }
        
        writeLog(`开始初始化CA: ${caName} (${caLabel})`, 'INFO', 'ca');
        const result = await executeDPKICommand('DPKI-CA', ['initial', '-ca_name', caName, '-ca_label', caLabel]);
        
        // 解析区块链信息
        const blockchainInfo = parseBlockchainInfo(result.stdout);
        
        // 将CA信息写入DPKI-config.json
        try {
            const configPath = path.join(__dirname, 'config', 'DPKI-config.json');
            let config = {};
            
            // 读取现有配置
            if (fs.existsSync(configPath)) {
                config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
            }
            
            // 添加CA配置（CA通常作为服务器，使用默认端口12349）
            config[caName] = {
                "caHost": dpkiConfig.Servernetwork?.serverHost || "127.0.0.1",
                "caPort": 12349
            };
            
            // 写入配置文件
            fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
            console.log(`CA配置已更新: ${caName}`);
            
        } catch (configError) {
            console.error('更新配置文件失败:', configError);
            writeLog(`更新CA配置文件失败: ${configError.message}`, 'ERROR', 'ca');
            // 不影响主要功能，只记录错误
        }
        
        writeLog(`CA初始化成功: ${caName}`, 'SUCCESS', 'ca');
        res.json({ 
            success: true, 
            message: 'CA初始化成功', 
            output: result.stdout,
            blockchainInfo: blockchainInfo
        });
        
    } catch (error) {
        writeLog(`CA初始化失败: ${error.message}`, 'ERROR', 'ca');
        res.status(500).json({ error: error.message });
    }
});

// CA注册证书
app.post('/api/ca/register', async (req, res) => {
    try {
        const { caName, ueName } = req.body;
        
        if (!caName || !ueName) {
            writeLog('CA证书注册失败: 缺少必要参数', 'ERROR', 'ca');
            return res.status(400).json({ error: '请提供CA名称和UE名称' });
        }
        
        writeLog(`开始CA证书注册: ${caName} -> ${ueName}`, 'INFO', 'ca');
        const result = await executeDPKICommand('DPKI-CA', ['register', '-ca_name', caName, '-ue_name', ueName]);
        
        // 解析区块链信息
        const blockchainInfo = parseBlockchainInfo(result.stdout);
        
        writeLog(`CA证书注册成功: ${caName} -> ${ueName}`, 'SUCCESS', 'ca');
        res.json({ 
            success: true, 
            message: '证书注册成功', 
            output: result.stdout,
            blockchainInfo: blockchainInfo
        });
        
    } catch (error) {
        writeLog(`CA证书注册失败: ${error.message}`, 'ERROR', 'ca');
        res.status(500).json({ error: error.message });
    }
});

// CA更新证书
app.post('/api/ca/update', async (req, res) => {
    try {
        const { caName, ueName } = req.body;
        
        if (!caName || !ueName) {
            writeLog('CA证书更新失败: 缺少必要参数', 'ERROR', 'ca');
            return res.status(400).json({ error: '请提供CA名称和UE名称' });
        }
        
        writeLog(`开始CA证书更新: ${caName} -> ${ueName}`, 'INFO', 'ca');
        const result = await executeDPKICommand('DPKI-CA', ['update', '-ca_name', caName, '-ue_name', ueName]);
        
        // 解析区块链信息
        const blockchainInfo = parseBlockchainInfo(result.stdout);
        
        writeLog(`CA certificate update successful: ${caName} -> ${ueName}`, 'SUCCESS', 'ca');
        res.json({ 
            success: true, 
            message: 'Certificate update successful', 
            output: result.stdout,
            blockchainInfo: blockchainInfo
        });
        
    } catch (error) {
        writeLog(`CA证书更新失败: ${error.message}`, 'ERROR', 'ca');
        res.status(500).json({ error: error.message });
    }
});

// CA撤销证书
app.post('/api/ca/revoke', async (req, res) => {
    try {
        const { ueName } = req.body;
        
        if (!ueName) {
            writeLog('CA证书撤销失败: 缺少UE名称参数', 'ERROR', 'ca');
            return res.status(400).json({ error: '请提供UE名称' });
        }
        
        writeLog(`开始CA证书撤销: ${ueName}`, 'INFO', 'ca');
        const result = await executeDPKICommand('DPKI-CA', ['revoke', '-ue_name', ueName]);
        
        // 解析区块链信息
        const blockchainInfo = parseBlockchainInfo(result.stdout);
        
        writeLog(`CA certificate revocation successful: ${ueName}`, 'SUCCESS', 'ca');
        res.json({ 
            success: true, 
            message: 'Certificate revocation successful', 
            output: result.stdout,
            blockchainInfo: blockchainInfo
        });
        
    } catch (error) {
        writeLog(`CA证书撤销失败: ${error.message}`, 'ERROR', 'ca');
        res.status(500).json({ error: error.message });
    }
});

// UE功能API

// UE请求证书
app.post('/api/ue/request', async (req, res) => {
    try {
        const { ueName } = req.body;
        
        if (!ueName) {
            writeLog(`UE CSR请求失败: 缺少UE名称参数`, 'ERROR', 'ue');
            return res.status(400).json({ error: '请提供UE名称' });
        }
        
        writeLog(`开始UE CSR请求: ${ueName}`, 'INFO', 'ue');
        const result = await executeDPKICommand('DPKI-UE', ['request', '-ue_name', ueName]);
        
        // 检查输出中是否包含"CSR received"
        const csrReceived = result.stdout.includes('CSR received') || result.stdout.includes('received');
        
        // 解析区块链信息
        const blockchainInfo = parseBlockchainInfo(result.stdout);
        
        // 如果CSR请求成功，将UE信息写入DPKI-config.json
        if (csrReceived) {
            try {
                const configPath = path.join(__dirname, 'config', 'DPKI-config.json');
                let config = {};
                
                // 读取现有配置
                if (fs.existsSync(configPath)) {
                    config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
                }
                
                // 添加UE配置（UE通常使用默认端口12348）
                config[ueName] = {
                    "ueHost": dpkiConfig.Servernetwork?.serverHost || "127.0.0.1",
                    "uePort": 12348
                };
                
                // 写入配置文件
                fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
                console.log(`UE配置已更新: ${ueName}`);
                writeLog(`UE CSR请求成功: ${ueName}`, 'SUCCESS', 'ue');
                
            } catch (configError) {
                console.error('更新配置文件失败:', configError);
                writeLog(`更新UE配置文件失败: ${configError.message}`, 'ERROR', 'ue');
                // 不影响主要功能，只记录错误
            }
            
            res.json({ 
                success: true, 
                message: 'CSR请求成功 - CSR已被接收', 
                output: result.stdout,
                blockchainInfo: blockchainInfo,
                csrReceived: true
            });
        } else {
            writeLog(`UE CSR请求失败: 未检测到CSR received - ${ueName}`, 'ERROR', 'ue');
            
            // CSR请求失败时，删除nodes/UE中对应的节点文件夹
            try {
                const ueNodePath = path.join(__dirname, 'nodes', 'UE', ueName);
                if (fs.existsSync(ueNodePath)) {
                    fs.rmSync(ueNodePath, { recursive: true, force: true });
                    writeLog(`已删除失败的UE节点文件夹: ${ueNodePath}`, 'INFO', 'ue');
                    console.log(`已删除失败的UE节点文件夹: ${ueNodePath}`);
                }
            } catch (deleteError) {
                writeLog(`删除失败的UE节点文件夹时出错: ${deleteError.message}`, 'ERROR', 'ue');
                console.error('删除失败的UE节点文件夹时出错:', deleteError);
            }
            
            res.json({ 
                success: false, 
                message: 'CSR请求失败 - 未检测到CSR received', 
                output: result.stdout,
                blockchainInfo: blockchainInfo,
                csrReceived: false
            });
        }
        
    } catch (error) {
        writeLog(`UE CSR请求异常: ${error.message}`, 'ERROR', 'ue');
        
        // CSR请求异常时，也删除可能已创建的节点文件夹
        try {
            const { ueName } = req.body;
            if (ueName) {
                const ueNodePath = path.join(__dirname, 'nodes', 'UE', ueName);
                if (fs.existsSync(ueNodePath)) {
                    fs.rmSync(ueNodePath, { recursive: true, force: true });
                    writeLog(`已删除异常的UE节点文件夹: ${ueNodePath}`, 'INFO', 'ue');
                    console.log(`已删除异常的UE节点文件夹: ${ueNodePath}`);
                }
            }
        } catch (deleteError) {
            writeLog(`删除异常的UE节点文件夹时出错: ${deleteError.message}`, 'ERROR', 'ue');
            console.error('删除异常的UE节点文件夹时出错:', deleteError);
        }
        
        res.status(500).json({ error: error.message });
    }
});

// UE更新列表
app.post('/api/ue/updatelist', async (req, res) => {
    try {
        writeLog('开始UE地址列表更新', 'INFO', 'ue');
        const result = await executeDPKICommand('DPKI-UE', ['updatelist']);
        
        // 解析区块链信息
        const blockchainInfo = parseBlockchainInfo(result.stdout);
        
        writeLog('UE地址列表更新成功', 'SUCCESS', 'ue');
        res.json({ 
            success: true, 
            message: '地址列表更新成功', 
            output: result.stdout,
            blockchainInfo: blockchainInfo
        });
        
    } catch (error) {
        writeLog(`UE地址列表更新失败: ${error.message}`, 'ERROR', 'ue');
        res.status(500).json({ error: error.message });
    }
});

// UE认证请求
app.post('/api/ue/auth', async (req, res) => {
    try {
        const { ueName, target } = req.body;
        if (!ueName || !target) {
            writeLog('UE认证请求失败: 缺少必要参数', 'ERROR', 'ue');
            return res.status(400).json({ success: false, message: '缺少必要参数' });
        }

        writeLog(`开始UE认证请求: ${ueName} -> ${target}`, 'INFO', 'ue');
        const result = await executeDPKICommand('DPKI-UE', ['authenticationreq', '-ue_name', ueName, '-target', target]);
        
        // 解析区块链信息
        const blockchainInfo = parseBlockchainInfo(result.stdout);
        
        writeLog(`UE认证请求成功: ${ueName} -> ${target}`, 'SUCCESS', 'ue');
        res.json({ 
            success: true, 
            message: 'UE认证请求成功', 
            output: result.stdout,
            blockchainInfo: blockchainInfo
        });
    } catch (error) {
        writeLog(`UE认证请求失败: ${error.message}`, 'ERROR', 'ue');
        res.status(500).json({ success: false, message: `UE认证请求失败: ${error.message}` });
    }
});

// API路由 - 获取CA列表
app.get('/api/ca/list', async (req, res) => {
    try {
        const fs = require('fs');
        const path = require('path');
        
        // 读取DPKI配置文件
        let configData = {};
        try {
            const configPath = path.join(__dirname, 'config', 'DPKI-config.json');
            if (fs.existsSync(configPath)) {
                const configContent = fs.readFileSync(configPath, 'utf8');
                configData = JSON.parse(configContent);
            }
        } catch (error) {
            console.log('读取配置文件失败:', error.message);
        }
        
        // 扫描nodes/CA目录中的CA文件夹
        const caDir = path.join(__dirname, 'nodes', 'CA');
        const caList = [];
        
        if (fs.existsSync(caDir)) {
            const items = fs.readdirSync(caDir);
            
            for (const item of items) {
                const itemPath = path.join(caDir, item);
                if (fs.statSync(itemPath).isDirectory() && item.startsWith('CA')) {
                    // 检查是否是CA文件夹（包含.cnf文件）
                    const cnfFile = path.join(itemPath, `${item}.cnf`);
                    const certFile = path.join(itemPath, 'certs', `${item}.crt`);
                    
                    if (fs.existsSync(cnfFile)) {
                        const caInfo = {
                            name: item,
                            path: itemPath,
                            hasCert: fs.existsSync(certFile),
                            configFile: cnfFile,
                            status: fs.existsSync(certFile) ? 'initialized' : 'created'
                        };
                        
                        caList.push(caInfo);
                    }
                }
            }
        }
        
        res.json({ success: true, caList });
    } catch (error) {
        console.error('获取CA列表错误:', error);
        res.status(500).json({ success: false, message: `获取CA列表失败: ${error.message}` });
    }
});

// API路由 - 获取UE列表
app.get('/api/ue/list', async (req, res) => {
    try {
        const fs = require('fs');
        const path = require('path');
        
        // 读取DPKI配置文件
        let configData = {};
        try {
            const configPath = path.join(__dirname, 'config', 'DPKI-config.json');
            if (fs.existsSync(configPath)) {
                const configContent = fs.readFileSync(configPath, 'utf8');
                configData = JSON.parse(configContent);
            }
        } catch (error) {
            console.log('读取配置文件失败:', error.message);
        }
        
        // 扫描nodes/UE目录中的UE文件夹
        const ueDir = path.join(__dirname, 'nodes', 'UE');
        const ueList = [];
        
        if (fs.existsSync(ueDir)) {
            const items = fs.readdirSync(ueDir);
            
            for (const item of items) {
                const itemPath = path.join(ueDir, item);
                if (fs.statSync(itemPath).isDirectory()) {
                    // 检查是否是UE文件夹（包含.cnf文件）
                    const cnfFile = path.join(itemPath, `${item}.cnf`);
                    const csrFile = path.join(itemPath, 'certs', `${item}.csr`);
                    const certFile = path.join(itemPath, 'certs', `${item}.crt`);
                    
                    if (fs.existsSync(cnfFile)) {
                        const ueInfo = {
                            name: item,
                            path: itemPath,
                            hasCSR: fs.existsSync(csrFile),
                            hasCert: fs.existsSync(certFile),
                            configFile: cnfFile
                        };
                        
                        // 确定UE状态
                        if (ueInfo.hasCert) {
                            ueInfo.status = 'certified';
                        } else if (ueInfo.hasCSR) {
                            ueInfo.status = 'pending';
                        } else {
                            ueInfo.status = 'created';
                        }
                        
                        // 从配置文件读取网络信息
                        if (configData[item]) {
                            ueInfo.host = configData[item].ueHost;
                            ueInfo.port = configData[item].uePort;
                        }
                        
                        ueList.push(ueInfo);
                    }
                }
            }
        }
        
        res.json({ success: true, ueList });
    } catch (error) {
        console.error('获取UE列表错误:', error);
        res.status(500).json({ success: false, message: `获取UE列表失败: ${error.message}` });
    }
});

// 默认路由 - 提供前端页面
// 部署合约API
app.post('/api/deploy-contract', async (req, res) => {
    // 确保响应头设置为JSON
    res.setHeader('Content-Type', 'application/json');
    
    try {
        writeLog('Starting smart contract deployment', 'INFO');
        console.log('Starting smart contract deployment...');
        
        const Web3 = require('web3');
        
        // 读取配置文件
        const exeDir = process.pkg ? path.dirname(process.execPath) : __dirname;
        const config = JSON.parse(fs.readFileSync(path.join(exeDir, 'config', 'DPKI-config.json')).toString());
        const web3 = new Web3(new Web3.providers.HttpProvider(config.Blockchain.providerUrl));

        let abi;
        let bytecode;

        // 读取ABI和字节码
        if (process.pkg) {
            const abiPath = path.join(path.dirname(process.execPath), 'contracts', 'authentication.abi');
            const bytecodePath = path.join(path.dirname(process.execPath), 'contracts', 'authentication.code');
            abi = JSON.parse(fs.readFileSync(abiPath, 'utf8'));
            bytecode = fs.readFileSync(bytecodePath, 'utf8');
        } else {
            const abiPath = path.join(exeDir, 'contracts', config.contract.abiPath);
            const bytecodePath = path.join(exeDir, 'contracts', config.contract.bytecodePath);
            abi = JSON.parse(fs.readFileSync(abiPath, 'utf8'));
            bytecode = fs.readFileSync(bytecodePath, 'utf8');
        }

        const account = config.Blockchain.account;
        const privateKey = config.Blockchain.privateKey;

        console.log('创建合约实例...');
        const contract = new web3.eth.Contract(abi);
        
        console.log('准备部署...');
        const contractdeploy = contract.deploy({
            data: bytecode,
            arguments: ["DPKI Contract"],
        });
        
        console.log('估算Gas费用...');
        const gasEstimate = await contractdeploy.estimateGas({from: account});
        console.log('Gas估算:', gasEstimate);
        
        console.log('签名交易...');
        const createTransaction = await web3.eth.accounts.signTransaction(
            {
                data: contractdeploy.encodeABI(),
                gas: gasEstimate,
            },
            privateKey
        );
        
        console.log('发送签名交易...');
        const createReceipt = await web3.eth.sendSignedTransaction(createTransaction.rawTransaction);
        console.log('合约部署成功，地址:', createReceipt.contractAddress);
        
        // 更新配置文件
        config.contract.address = createReceipt.contractAddress;
        
        // 清理nodes目录下的所有节点文件夹内容（保留文件夹本身）
        const nodesDir = path.join(exeDir, 'nodes');
        const foldersToClean = ['CA', 'UE', 'temp'];
        
        writeLog('Starting node data cleanup', 'INFO');
        for (const folder of foldersToClean) {
            const folderPath = path.join(nodesDir, folder);
            if (fs.existsSync(folderPath)) {
                const items = fs.readdirSync(folderPath);
                for (const item of items) {
                    const itemPath = path.join(folderPath, item);
                    if (fs.statSync(itemPath).isDirectory()) {
                        fs.rmSync(itemPath, { recursive: true, force: true });
                    } else {
                        fs.unlinkSync(itemPath);
                    }
                }
            }
        }
        
        // 清理配置文件，只保留Blockchain、contract和Servernetwork配置
        const cleanConfig = {
            Blockchain: config.Blockchain,
            contract: config.contract,
            Servernetwork: config.Servernetwork
        };
        
        fs.writeFileSync(path.join(exeDir, 'config', 'DPKI-config.json'), JSON.stringify(cleanConfig, null, 2));
        
        writeLog(`智能合约部署成功，地址: ${createReceipt.contractAddress}`, 'SUCCESS');
        res.json({
            success: true,
            contractAddress: createReceipt.contractAddress,
            message: '合约部署成功，配置文件已更新，节点数据已清理'
        });
        
    } catch (error) {
        console.error('合约部署失败:', error);
        writeLog(`智能合约部署失败: ${error.message}`, 'ERROR');
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// 获取CA系统日志的API端点
app.get('/api/ca/logs', (req, res) => {
    try {
        const logs = getRecentLogs(5, 'ca');
        res.json({ success: true, logs });
    } catch (error) {
        console.error('获取CA日志失败:', error);
        res.status(500).json({ success: false, error: '获取CA日志失败' });
    }
});

// 获取UE系统日志的API端点
app.get('/api/ue/logs', (req, res) => {
    try {
        const logs = getRecentLogs(5, 'ue');
        res.json({ success: true, logs });
    } catch (error) {
        console.error('获取UE日志失败:', error);
        res.status(500).json({ success: false, error: '获取UE日志失败' });
    }
});

// 获取系统日志的API端点
app.get('/api/logs', (req, res) => {
    try {
        const logs = getRecentLogs(10, 'general');
        res.json({ success: true, logs });
    } catch (error) {
        console.error('获取系统日志失败:', error);
        res.status(500).json({ success: false, error: '获取系统日志失败' });
    }
});

// DID服务代理API
// 读取DPKI配置文件
const dpkiConfigPath = path.join(__dirname, 'config', 'DPKI-config.json');
let dpkiConfig = {};
try {
    const configData = fs.readFileSync(dpkiConfigPath, 'utf8');
    dpkiConfig = JSON.parse(configData);
} catch (error) {
    console.error('读取DPKI配置文件失败:', error);
    // 使用默认配置
    dpkiConfig = {
        Servernetwork: {
            serverHost: "localhost"
        }
    };
}

// DID服务配置
const DID_SERVICE_HOST = (dpkiConfig.DIDService && dpkiConfig.DIDService.host) || 'localhost';
const DID_SERVICE_PORT = (dpkiConfig.DIDService && dpkiConfig.DIDService.port) || 8080;
const DID_SERVICE_URL = `http://${DID_SERVICE_HOST}:${DID_SERVICE_PORT}`;

// 撤销的VC列表（在实际应用中应该使用数据库）
const revokedVCs = new Set();

// 生成DID
app.get('/api/did/create', async (req, res) => {
    try {
        const response = await fetch(`${DID_SERVICE_URL}/did`);
        const data = await response.json();
        res.json(data);
    } catch (error) {
        console.error('DID生成失败:', error);
        res.status(500).json({ code: 0, msg: 'DID服务连接失败', error: error.message });
    }
});

// 查询DID文档
app.get('/api/did/query/:did', async (req, res) => {
    try {
        const did = req.params.did;
        const response = await fetch(`${DID_SERVICE_URL}/did/${encodeURIComponent(did)}`);
        const data = await response.json();
        res.json(data);
    } catch (error) {
        console.error('DID查询失败:', error);
        res.status(500).json({ code: 0, msg: 'DID查询失败', error: error.message });
    }
});

// DID解析端点（POST方式）
app.post('/api/did/resolve', async (req, res) => {
    try {
        const { did } = req.body;
        if (!did) {
            return res.status(400).json({ code: 0, msg: '缺少DID参数' });
        }
        const response = await fetch(`${DID_SERVICE_URL}/did/${encodeURIComponent(did)}`);
        const data = await response.json();
        res.json(data);
    } catch (error) {
        console.error('DID解析失败:', error);
        res.status(500).json({ code: 0, msg: 'DID解析失败', error: error.message });
    }
});

// 创建用户属性VC
app.get('/api/vc/create', async (req, res) => {
    try {
        const { did, operatorPermission, enabled } = req.query;
        const response = await fetch(`${DID_SERVICE_URL}/vc/user-attribute?did=${encodeURIComponent(did)}&operatorPermission=${encodeURIComponent(operatorPermission)}&enabled=${encodeURIComponent(enabled)}`);
        const data = await response.json();
        res.json(data);
    } catch (error) {
        console.error('VC创建失败:', error);
        res.status(500).json({ code: 0, msg: 'VC创建失败', error: error.message });
    }
});

// 验证VC
app.get('/api/vc/verify', async (req, res) => {
    try {
        const { jwtString } = req.query;
        
        // 检查VC是否已被撤销
        if (revokedVCs.has(jwtString)) {
            return res.json({ 
                code: 0, 
                msg: 'VC验证失败：该VC已被撤销',
                data: {
                    valid: false,
                    reason: 'VC已被撤销'
                }
            });
        }
        
        const response = await fetch(`${DID_SERVICE_URL}/vc/verify-jwt?jwtString=${encodeURIComponent(jwtString)}`);
        const data = await response.json();
        res.json(data);
    } catch (error) {
        console.error('VC验证失败:', error);
        res.status(500).json({ code: 0, msg: 'VC验证失败', error: error.message });
    }
});

// 解析VC内容
app.get('/api/vc/parse', async (req, res) => {
    try {
        const { jwtString } = req.query;
        const response = await fetch(`${DID_SERVICE_URL}/vc/parse?jwtString=${encodeURIComponent(jwtString)}`);
        const data = await response.json();
        res.json(data);
    } catch (error) {
        console.error('VC解析失败:', error);
        res.status(500).json({ code: 0, msg: 'VC解析失败', error: error.message });
    }
});

// 用户属性VC创建（兼容旧路径）
app.get('/api/vc/user-attribute', async (req, res) => {
    try {
        const { did, operatorPermission, enabled } = req.query;
        const response = await fetch(`${DID_SERVICE_URL}/vc/user-attribute?did=${encodeURIComponent(did)}&operatorPermission=${encodeURIComponent(operatorPermission)}&enabled=${encodeURIComponent(enabled)}`);
        const data = await response.json();
        res.json(data);
    } catch (error) {
        console.error('VC创建失败:', error);
        res.status(500).json({ code: 0, msg: 'VC创建失败', error: error.message });
    }
});

// 撤销VC
app.post('/api/vc/revoke', async (req, res) => {
    try {
        const { vcJwt } = req.body;
        
        if (!vcJwt) {
            return res.status(400).json({ success: false, message: '缺少VC JWT参数' });
        }

        // 检查VC是否已经被撤销
        if (revokedVCs.has(vcJwt)) {
            return res.status(400).json({ success: false, message: '该VC已经被撤销' });
        }

        // 将VC添加到撤销列表
        revokedVCs.add(vcJwt);
        
        writeLog(`VC revoked: ${vcJwt.substring(0, 50)}...`, 'INFO');
        
        res.json({ 
            success: true, 
            message: 'VC撤销成功'
        });
    } catch (error) {
        console.error('VC撤销失败:', error);
        writeLog(`VC撤销失败: ${error.message}`, 'ERROR');
        res.status(500).json({ success: false, message: 'VC撤销失败', error: error.message });
    }
});

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'web', 'index.html'));
});

// 错误处理中间件
app.use((error, req, res, next) => {
    console.error('服务器错误:', error);
    res.status(500).json({ error: '内部服务器错误' });
});

// 自动启动CA和UE服务器的函数
function autoStartServers() {
    console.log('正在自动启动CA和UE服务器...');
    
    // 启动CA服务器
    try {
        if (!caServerProcess || caServerProcess.killed) {
            const caCommand = path.join(__dirname, 'bin', 'Server-CA.exe');
            if (fs.existsSync(caCommand)) {
                caServerProcess = spawn(caCommand, [], { cwd: path.join(__dirname, 'bin') });
                console.log('自动启动CA服务器 (exe):', caCommand);
            } else {
                const jsCommand = path.join(__dirname, 'bin', 'Server-CA.js');
                if (fs.existsSync(jsCommand)) {
                    caServerProcess = spawn('node', ['Server-CA.js'], { cwd: path.join(__dirname, 'bin') });
                    console.log('自动启动CA服务器 (js):', jsCommand);
                }
            }
            
            if (caServerProcess) {
                caServerProcess.on('error', (error) => {
                    console.error('CA服务器自动启动失败:', error);
                    writeLog(`CA服务器自动启动失败: ${error.message}`, 'ERROR', 'ca');
                });
                
                caServerProcess.on('exit', (code) => {
                    console.log('CA服务器退出，代码:', code);
                    writeLog(`CA服务器退出，代码: ${code}`, 'INFO', 'ca');
                    caServerProcess = null;
                });
                
                writeLog('CA服务器自动启动成功', 'INFO', 'ca');
            }
        }
    } catch (error) {
        console.error('CA服务器自动启动异常:', error);
        writeLog(`CA服务器自动启动异常: ${error.message}`, 'ERROR', 'ca');
    }
    
    // 启动UE服务器
    try {
        if (!ueServerProcess || ueServerProcess.killed) {
            const ueCommand = path.join(__dirname, 'bin', 'Server-UE.exe');
            if (fs.existsSync(ueCommand)) {
                ueServerProcess = spawn(ueCommand, [], { cwd: path.join(__dirname, 'bin') });
                console.log('自动启动UE服务器 (exe):', ueCommand);
            } else {
                const jsCommand = path.join(__dirname, 'bin', 'Server-UE.js');
                if (fs.existsSync(jsCommand)) {
                    ueServerProcess = spawn('node', ['Server-UE.js'], { cwd: path.join(__dirname, 'bin') });
                    console.log('自动启动UE服务器 (js):', jsCommand);
                }
            }
            
            if (ueServerProcess) {
                ueServerProcess.on('error', (error) => {
                    console.error('UE服务器自动启动失败:', error);
                    writeLog(`UE服务器自动启动失败: ${error.message}`, 'ERROR', 'ue');
                });
                
                ueServerProcess.on('exit', (code) => {
                    console.log('UE服务器退出，代码:', code);
                    writeLog(`UE服务器退出，代码: ${code}`, 'INFO', 'ue');
                    ueServerProcess = null;
                });
                
                writeLog('UE服务器自动启动成功', 'INFO', 'ue');
            }
        }
    } catch (error) {
        console.error('UE服务器自动启动异常:', error);
        writeLog(`UE服务器自动启动异常: ${error.message}`, 'ERROR', 'ue');
    }
}

// 启动服务器
app.listen(PORT, '0.0.0.0',() => {
    console.log(`DPKI Web服务器运行在 http://${dpkiConfig.Servernetwork?.serverHost || '127.0.0.1'}:${PORT}`);
    console.log(`局域网访问地址: http://192.168.5.23:${PORT}`);
    console.log('请在浏览器中打开上述地址访问管理界面');
    writeLog(`DPKI Web服务器启动，端口: ${PORT}，监听所有网络接口`, 'INFO');
    
    // 延迟2秒后自动启动CA和UE服务器
    setTimeout(() => {
        autoStartServers();
    }, 2000);
});

// 优雅关闭
process.on('SIGINT', () => {
    console.log('\n正在关闭服务器...');
    
    if (caServerProcess && !caServerProcess.killed) {
        caServerProcess.kill();
    }
    
    if (ueServerProcess && !ueServerProcess.killed) {
        ueServerProcess.kill();
    }
    
    process.exit(0);
});
