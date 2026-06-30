const net = require('net');
const { verifyAll } = require('./DPKI-UE');
const CertGenerate = require('./CertOperation');

const Web3 = require('web3');
const fs = require('fs');
const path = require('path');
const { ecsign, toBuffer, bufferToHex } = require('ethereumjs-util');
const { keccak256 } = require('js-sha3');
const { exec } = require('child_process');


const exeDir = process.pkg ? path.dirname(process.execPath) : __dirname;
const nodesDir = path.join(exeDir, '..', 'nodes');

const config = JSON.parse(fs.readFileSync(path.join(exeDir, '..', 'config', 'DPKI-config.json')).toString());

// const account = config.ethereum.account; //目前配置似乎不能是创世之外的地址
// const privateKey = config.Blockchain.privateKey; //对应私钥
const contractAddress = config.contract.address;

// const verifyAll = async (contractAddress, signedAssertion, message, label, certAddress, inputCert) => {
//     try {
//         const contract = new web3.eth.Contract(abi, contractAddress);

//         const allValid = await contract.methods.verifyAll(signedAssertion, message, label, certAddress, inputCert).call();
//         console.log('验证结果是:', allValid);
//         return allValid;

//     } catch (err) {
//         console.error('寄了:', err);
//     }
// };

const PORT = 12348;
const HOST = '0.0.0.0';

const server = net.createServer((socket) => {
    console.log('New client connected:', socket.remoteAddress, socket.remotePort);
    let receivedData = '';
    socket.on('data', (chunk) => {
        receivedData += chunk.toString();
         try {
            const message = JSON.parse(receivedData);
            console.log (message);
            if (message.type === 'CRT') {
                const ueName = message.ue_name;
                console.log(ueName);
                const crtContent = message.crt_content;
                console.log(crtContent);
                const crtDir = path.join(nodesDir, 'UE', `${ueName}`, `certs`, `${ueName}.crt`);
             
                fs.writeFile(crtDir, crtContent, (err) => {
                    if (err) {
                        console.error('Store crt failed:', err);
                        socket.write('Store crt failed');
                    } else {
                        console.log(`Crt received to:${crtDir}`);
                        socket.write('Crt received');
                    }
                });

            } else if (message.type === 'AuthReq') {           
                const ueName = message.ue_name;
                console.log(ueName);
                const Assertion = message.signedAssertion;
                console.log(Assertion);
                const certContent = message.crt_content;
                console.log(certContent);

                const crtDir1 = path.join(nodesDir, 'temp', `auth_${ueName}`);
                
                if (!fs.existsSync(crtDir1)) {
                    fs.mkdirSync(crtDir1, { recursive: true });
                }

                const crtDir2 = path.join(crtDir1, `certs`);
                if (!fs.existsSync(crtDir2)) {
                    fs.mkdirSync(crtDir2);
                }

                const filePath = path.join(crtDir2, `${ueName}.crt`);
                fs.writeFile(filePath, certContent, (err) => {
                        if (err) {
                            console.error('Store failed:', err);
                        } else {
                            (async () => {
                                const certdetails = await CertGenerate.getCertificateDetails(crtDir1, ueName);
                                address = certdetails.ethereumAddress;
                                console.log ()
                                result = await verifyAll(contractAddress, Assertion, address, ueName, address, certContent);
                                socket.write(result);
                        })();
                    }
                });

                // getaddress(crtDir1, ueName)
                

                // verifyAll(contractAddress, Assertion, certdetails.ethereumAddress, certdetails.ethereumAddress)
                
                // let response = verifyAll(contractAddress, Assertion, certdetails.ethereumAddress, certdetails.ethereumAddress);
                // console.log(response);
                // if (typeof response !== 'string') {
                //     response = JSON.stringify(response);
                //   }      
                // socket.write(response);
            };

        } catch (err) {
            console.error('Error processing message:', err);
        }
    });

    socket.on('end', () => {
        console.log('Client disconnected');
    });

    socket.on('error', (err) => {
        console.error('Socket error:', err.message);
    });
});

// async function getaddress(dir, name){
//     const certdetails = CertGenerate.getCertificateDetails(dir, name);
//     console.log('Ethereum Address:', certdetails.ethereumAddress);
//     console.log('certcontent:', certdetails.CertContent);
//     console.log('Validity:', certdetails.notBefore);
//     console.log('Validity:', certdetails.notAfter);
// }

server.listen(PORT, HOST, () => {
    console.log(`Server listening on ${HOST}:${PORT}`);
});

// getaddress(path.join(__dirname, `auth_ty`), ty);
// verifyAll(contractAddress, `0x04186ec5881fe659e824f39a039b53029ac2dbadfb3bf2ca7c9d4eba99e762cf4143227152a72897f1bfbfa1f51d48d03e9c855c15e42c7d3c6ad9f80197154fd0`, )
