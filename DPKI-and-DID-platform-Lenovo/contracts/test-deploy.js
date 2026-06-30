const Web3 = require('web3');
const fs = require('fs');
const path = require('path');

const exeDir = process.pkg ? path.dirname(process.execPath) : __dirname;
const config = JSON.parse(fs.readFileSync(path.join(exeDir, '..', 'config', 'DPKI-config.json')).toString());
const web3 = new Web3(new Web3.providers.HttpProvider(config.Blockchain.providerUrl));

let abi;
let bytecode;

try {
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

    console.log('ABI loaded successfully, length:', abi.length);
    console.log('Bytecode loaded successfully, length:', bytecode.length);

    const account = config.Blockchain.account;
    const privateKey = config.Blockchain.privateKey;

    console.log('Account:', account);
    console.log('Private key length:', privateKey.length);

    const deployContract = async () => {
        try {
            console.log('Creating contract instance...');
            const contract = new web3.eth.Contract(abi);
            
            console.log('Preparing deployment...');
            const contractdeploy = contract.deploy({
                data: bytecode,
                arguments: ["DPKI Contract"],
            });
            
            console.log('Estimating gas...');
            const gasEstimate = await contractdeploy.estimateGas({from: account});
            console.log('Gas estimate:', gasEstimate);
            
            console.log('Signing transaction...');
            const createTransaction = await web3.eth.accounts.signTransaction(
                {
                    data: contractdeploy.encodeABI(),
                    gas: gasEstimate,
                },
                privateKey
            );
            
            console.log('Sending signed transaction...');
            const createReceipt = await web3.eth.sendSignedTransaction(createTransaction.rawTransaction);
            console.log('Contract deployed at:', createReceipt.contractAddress);
            
            // 更新配置文件
            config.contract.address = createReceipt.contractAddress;
            fs.writeFileSync(path.join(exeDir, '..', 'config', 'DPKI-config.json'), JSON.stringify(config, null, 2));
            
            return createReceipt.contractAddress;
        } catch (err) {
            console.error('Deployment error details:', err);
            throw err;
        }
    };

    deployContract().then(address => {
        console.log('SUCCESS:' + address);
    }).catch(err => {
        console.error('ERROR:' + err.message);
    });

} catch (err) {
    console.error('Initialization error:', err.message);
    console.error('ERROR:' + err.message);
}