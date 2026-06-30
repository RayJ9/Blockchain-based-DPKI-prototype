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

const web3 = new Web3(new Web3.providers.HttpProvider(config.Blockchain.providerUrl)); //主机ip

// var abi = JSON.parse(fs.readFileSync(path.join(__dirname, "./authentication.abi")).toString())
// var bytecode = fs.readFileSync(path.join(__dirname, "./authentication.code")).toString()

// const account = '0xab7F5238cbEfB02062241cf979e4994b656FB944'; //目前配置似乎不能是创世之外的地址
// const privateKey = '0x73e66f099144f820753aa3a5e131785b528081da572e16339fcd02de05de719e'; //对应私钥

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

// var abi = JSON.parse(fs.readFileSync(path.join(__dirname, config.contract.abiPath)).toString());
// var bytecode = fs.readFileSync(path.join(__dirname, config.contract.bytecodePath)).toString();

const account = config.Blockchain.account; //目前配置似乎不能是创世之外的地址
const privateKey = config.Blockchain.privateKey; //对应私钥

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
    throw new Error(`args miss: ${key}`);
}

const registerCertificate = async (contractAddress, label, certAddress, certData, notBefore, notAfter) => {
    try {
        const contract = new web3.eth.Contract(abi, contractAddress);

        const gasEstimate = await contract.methods.registerCertificate(label, certAddress, certData, notBefore, notAfter)
            .estimateGas({ from: account });

        const signedTx = await web3.eth.accounts.signTransaction(
            {
                to: contractAddress,
                data: contract.methods.registerCertificate(label, certAddress, certData, notBefore, notAfter).encodeABI(),
                gas: gasEstimate,
                from: account
            },
            privateKey
        );

        const receipt = await web3.eth.sendSignedTransaction(signedTx.rawTransaction);
        console.log('Certificate saved:', receipt);
        return receipt;

    } catch (err) {
        console.error('error:', err);
    }
};

const updateCertificate = async (contractAddress, label, certAddress, certData, notBefore, notAfter) => {
    try {
        const contract = new web3.eth.Contract(abi, contractAddress);

        const gasEstimate = await contract.methods.updateCertificate(label, certAddress, certData, notBefore, notAfter)
            .estimateGas({ from: account });

        const signedTx = await web3.eth.accounts.signTransaction(
            {
                to: contractAddress,
                data: contract.methods.updateCertificate(label, certAddress, certData, notBefore, notAfter).encodeABI(),
                gas: gasEstimate,
                from: account
            },
            privateKey
        );
        const receipt = await web3.eth.sendSignedTransaction(signedTx.rawTransaction);
        console.log('Certificate updated:', receipt);
        return receipt;

    } catch (err) {
        console.error('error:', err);
    }
};

const revokeCertificate = async (contractAddress, label) => {
    try {
        const contract = new web3.eth.Contract(abi, contractAddress);

        const gasEstimate = await contract.methods.revokeCertificate(label)
            .estimateGas({ from: account });

        const signedTx = await web3.eth.accounts.signTransaction(
            {
                to: contractAddress,
                data: contract.methods.revokeCertificate(label).encodeABI(),
                gas: gasEstimate,
                from: account
            },
            privateKey
        );

        const receipt = await web3.eth.sendSignedTransaction(signedTx.rawTransaction);
        console.log('Certificate revoked:', receipt);
        return receipt;

    } catch (err) {
        console.error('error:', err);
    }
};

const verifyAll = async (contractAddress, signedAssertion, message, label, certAddress, inputCert) => {
    try {
        const contract = new web3.eth.Contract(abi, contractAddress);

        const allValid = await contract.methods.verifyAll(signedAssertion, message, label, certAddress, inputCert).call();
        console.log('Verification result:', allValid);
        return allValid;

    } catch (err) {
        console.error('error:', err);
    }
};

const deployContract = async () => {
    try {
     const contract = new web3.eth.Contract(abi);
   
     const contractdeploy = contract.deploy({
       data: bytecode,
       arguments: ["a"],
     });
 
   const createTransaction = await web3.eth.accounts.signTransaction(
     {
       data: contractdeploy.encodeABI(),
       gas: await contractdeploy.estimateGas({from: "0xab7F5238cbEfB02062241cf979e4994b656FB944"}),
     },
     "0x73e66f099144f820753aa3a5e131785b528081da572e16339fcd02de05de719e"
   );
 
    const createReceipt = await web3.eth.sendSignedTransaction(createTransaction.rawTransaction);
    console.log(createReceipt);
       } catch (err) {
   console.error(err);
    }
 }

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

// const certFilePath = path.join(rootDir, 'certs', `${caName}.crt`);
// const certContent = fs.readFileSync(certFilePath, 'utf8');
// console.log('证书已加载:', certContent);

// 部署合约
// deployContract();
// const contractAddress = '0x99c7FDb06Bf5832Ef13dCA9aa67Da8EfBE2Cba35';

(async () => {
    const action = process.argv[2];

    if (action === 'initial') {
        console.time('Initial Time');
        const caName = getArgValue('-ca_name');
        const root_label = getArgValue('-ca_label');
        const rootDir = path.join(nodesDir, 'CA', caName);

        await CertGenerate.caCertgeneration(caName, rootDir);
        const certdetails = await CertGenerate.getCertificateDetails(rootDir, caName);
  
        console.log('Ethereum Address:', certdetails.ethereumAddress);
        console.log('certcontent:', certdetails.CertContent);
        console.log('Validity:', certdetails.notBefore);
        console.log('Validity:', certdetails.notAfter);
  
        await registerCertificate(
          contractAddress,
          root_label,
          certdetails.ethereumAddress,
          certdetails.CertContent,
          certdetails.notBefore,
          certdetails.notAfter
        )
        console.timeEnd('Initial Time');

    } else if (action === 'register') {
        console.time('register Time');
        const caName = getArgValue('-ca_name');
        const ueName = getArgValue('-ue_name');

        // const PORT = 12348;
        // const HOST = '121.248.54.226';

        const uePORT = config[ueName].uePort;
        const ueHOST = config[ueName].ueHost;

        const rootDir = path.join(nodesDir, 'CA', caName);
        const ueDir = path.join(nodesDir, 'temp', `tempUE_${ueName}`);

        // await CertGenerate.ueCSRgenerate(ueName, ueDir, uepasswd);

        
        await CertGenerate.ueCertSignature(caName, rootDir, ueName, ueDir);

        const certFilePath = path.join(ueDir, `certs`, `${ueName}.crt`);

        const certdetails = await CertGenerate.getCertificateDetails(ueDir, ueName);

        console.log('Ethereum Address:', certdetails.ethereumAddress);
        console.log('certcontent:', certdetails.CertContent);
        console.log('Validity:', certdetails.notBefore);
        console.log('Validity:', certdetails.notAfter);

        await registerCertificate(
          contractAddress,
          ueName,
          certdetails.ethereumAddress,
          certdetails.CertContent,
          certdetails.notBefore,
          certdetails.notAfter
        )

        const crtContent = fs.readFileSync(certFilePath, 'utf8');

        const message = JSON.stringify({
            type: "CRT",
            ue_name: ueName,
            crt_content: crtContent
            }, null, 2);

        const client = createClientConnection(uePORT, ueHOST);
        handleClientEvents(client);
        client.write(`${message}`);
        console.timeEnd('register Time');
    

    } else if (action === 'update') {
        console.time('update Time');
        const caName = getArgValue('-ca_name');
        const ueName = getArgValue('-ue_name');

        const rootDir = path.join(nodesDir, 'CA', caName);
        const ueDir = path.join(nodesDir, 'temp', `tempUE_${ueName}`);

        await CertGenerate.ueCertSignature(caName, rootDir, ueName, ueDir);
        const certdetails = await CertGenerate.getCertificateDetails(ueDir, ueName);
  
        console.log('Ethereum Address:', certdetails.ethereumAddress);
        console.log('certcontent:', certdetails.CertContent);
        console.log('Validity:', certdetails.notBefore);
        console.log('Validity:', certdetails.notAfter);
  
        await updateCertificate(
          contractAddress,
          ueName,
          certdetails.ethereumAddress,
          certdetails.CertContent,
          certdetails.notBefore,
          certdetails.notAfter
        )
        console.timeEnd('update Time');

    } else if (action === 'revoke') {
        console.time('revoke Time');
        const label = getArgValue('-ue_name');
        await revokeCertificate(
            contractAddress,
            label
        )
        console.timeEnd('revoke Time');
    } else if (action === 'verify') {
        console.time('verify Time');
        const label = getArgValue('-ue_label');
        const ueName = getArgValue('-ue_name');

        const ueDir = path.join(nodesDir, 'UE', ueName);
        const certdetails = await CertGenerate.getCertificateDetails(ueDir, ueName);
        const signedAssertion = await generateSignature (ueDir, ueName, certdetails.ethereumAddress);
        console.log (signedAssertion);

        await verifyAll(
          contractAddress,
          signedAssertion,
          certdetails.ethereumAddress,
          label,
          certdetails.ethereumAddress,
          certdetails.CertContent
        )
        console.timeEnd('verify Time');
    }
})();


//解锁钱包，如果没有钱包需要先创建钱包，bash命令如下：
// .\chain33-cli seed generate -l 0
// .\chain33-cli seed save -s '生产的助记词' -p 密码（要有字母+数字，牢记，不然要干掉整个钱包）
// .\chain33-cli wallet unlock -p 密码 -t 0
//不解锁的话不能创建账户
//这里和etehrum不同，第二个字段在链33里变成了label，所以账户不能重名
// 创建账户，但是暂时看来不会进行UE的认证，链上操作全部由主节点完成，11.1去掉
// web3.eth.personal.importRawKey(HEXsk, 'ca1').then(console.log);