const Web3 = require('web3');
const fs = require('fs');
const path = require('path');
const CertGenerate = require('./CertOperation');
const { createClientConnection, handleClientEvents } = require('./client');
const { ecsign, toBuffer, bufferToHex } = require('ethereumjs-util');
const { keccak256 } = require('js-sha3');
const { exec } = require('child_process');

const exeDir = process.pkg ? path.dirname(process.execPath) : __dirname;
const nodesDir = path.join(exeDir, '..', 'nodes');

const config = JSON.parse(fs.readFileSync(path.join(exeDir, '..', 'config', 'DPKI-config.json')).toString());

console.log (config);

const web3 = new Web3(new Web3.providers.HttpProvider(config.Blockchain.providerUrl)); //主机ip

let abi;
let bytecode;

if (process.pkg) {
    const abiPath = path.join(path.dirname(process.execPath), 'contracts', 'authentication.abi');
    const bytecodePath = path.join(path.dirname(process.execPath), 'contracts', 'authentication.code');
    abi = JSON.parse(fs.readFileSync(abiPath, 'utf8'));
    bytecode = fs.readFileSync(bytecodePath, 'utf8');
} else {
    const abiPath = path.join(exeDir, config.contract.abiPath);
    const bytecodePath = path.join(exeDir, config.contract.bytecodePath);
    abi = JSON.parse(fs.readFileSync(abiPath, 'utf8'));
    bytecode = fs.readFileSync(bytecodePath, 'utf8');
}

// const account = config.ethereum.account; //目前配置似乎不能是创世之外的地址
// const privateKey = config.Blockchain.privateKey; //对应私钥
const contractAddress = config.contract.address;

//openssl工具箱需要用cmd执行（js没有原生的包好像），载体
function runCommand(command) {
    return new Promise((resolve, reject) => {
      exec(command, (error, stdout, stderr) => {
        if (error) {
          reject(`Error: ${stderr}`);
        } else {
          resolve(stdout);
        }
      });
    });
}

//执行输入的逻辑
function getArgValue(key) {
    const index = process.argv.indexOf(key);
    if (index > -1 && process.argv.length > index + 1) {
        return process.argv[index + 1];
    }
    throw new Error(`Miss arg: ${key}`);
}

const verifyAll = async (contractAddress, signedAssertion, message, label, certAddress, inputCert) => {
    try {
        const contract = new web3.eth.Contract(abi, contractAddress);

        const allValid = await contract.methods.verifyAll(signedAssertion, message, label, certAddress, inputCert).call();
        console.log('Result is:', allValid);
        return allValid;

    } catch (err) {
        console.error('error:', err);
    }
};

async function generateSignature(dir, name, address) {
    try{
    const skpath = path.join(dir, `private_key`, `${name}.key`);
    const stdout = await runCommand(`openssl ec -in ${skpath} -text -noout`);

    const privateKeyMatch = stdout.match(/priv:\s*([\da-f\s:]+)/i);
    let privateKeyHex = `0x${privateKeyMatch[1].replace(/\s+/g, '').replace(/:/g, '')}`;
    const privateKeyBuffer = Buffer.from(privateKeyHex.slice(2), 'hex');
    console.log (privateKeyBuffer);
    const messageHash = Buffer.from(keccak256(address), 'hex');
    const { r, s, v } = ecsign(messageHash, privateKeyBuffer);
    const signature = Buffer.concat([r, s, Buffer.from([v])]);
    return bufferToHex(signature);
    } catch (err) {
        console.error(err);
    }
}

// const certFilePath = path.join(rootDir, 'certs', `${caName}.crt`);gnhfbg cvgcn
// const certContent = fs.readFileSync(certFilePath, 'utf8');
// console.log('证书已加载:', certContent);

(async () => {
    const action = process.argv[2];
    //server的端口和地址
    const PORT = config.Servernetwork.serverPort;
    const HOST = config.Servernetwork.serverHost;

    if (action === 'request') {
        console.time('request Time');
        // const label = getArgValue('-ue_label');
        // const caName = getArgValue('-ca_name');
        const ueName = getArgValue('-ue_name');

              
        const ueDir = path.join(nodesDir, 'UE', ueName);
        const uepasswd = '123456';
        const csrPath = path.join(ueDir, `certs`, `${ueName}.csr`);

        await CertGenerate.ueCSRgenerate(ueName, ueDir, uepasswd);
        const csrContent = fs.readFileSync(csrPath, 'utf8');

        const client = createClientConnection(PORT, HOST);
        handleClientEvents(client);

        const message = JSON.stringify({
        type: "CSR",
        ue_name: ueName,
        private_key: HEXsk,
        csr_content: csrContent
        }, null, 2);
        client.write(`${message}`);
        console.timeEnd('request Time');

    } else if (action === 'authenticationreq') {
        console.time('authenticationreq Time');
        const ueName = getArgValue('-ue_name');
        const targetName = getArgValue('-target');
        const uePORT = config[targetName].uePort;
        const ueHOST = config[targetName].ueHost;

        const ueDir = path.join(nodesDir, 'UE', ueName);
        const certdetails = await CertGenerate.getCertificateDetails(ueDir, ueName);
        const signedAssertion = await generateSignature(ueDir, ueName, certdetails.ethereumAddress);
        const crtpath = path.join(ueDir, `certs`, `${ueName}.crt`);
        const crtContent = fs.readFileSync(crtpath, 'utf8');

        const message = JSON.stringify({
        type: "AuthReq",
        ue_name: ueName,
        crt_content: crtContent,
        signedAssertion: signedAssertion
        }, null, 2);

        console.log (message)

        const client = createClientConnection(uePORT, ueHOST);
        handleClientEvents(client);

        client.write(`${message}`);
        console.timeEnd('authenticationreq Time');


    } else if (action === 'updatelist') {
        const client = createClientConnection(PORT, HOST);
        handleClientEvents(client);

        const message = JSON.stringify({
        type: "updatelist",
        }, null, 2);
        client.write(`${message}`);


    } 
    //    else if (action === 'assertion') {
    //     const ueName = getArgValue('-ue_name');
    //     const ueDir = path.join(__dirname, ueName);
    //     const signedAssertion = await generateSignature (ueDir, ueName, certdetails.ethereumAddress);
    //     console.log (signedAssertion);

    // }
})();

module.exports = {
    verifyAll
  };
  

//解锁钱包，如果没有钱包需要先创建钱包，bash命令如下：

//不解锁的话不能创建账户
//这里和etehrum不同，第二个字段在链33里变成了label，所以账户不能重名
// 创建账户，但是暂时看来不会进行UE的认证，链上操作全部由主节点完成，11.1去掉
// web3.eth.personal.importRawKey(HEXsk, 'ca1').then(console.log);