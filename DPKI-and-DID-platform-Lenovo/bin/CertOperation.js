const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { exec } = require('child_process');
const { keccak256 } = require('js-sha3');
// const { createClientConnection, handleClientEvents } = require('./client');

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

//生成rootCA的config文件，视作服务器执行
function generateRootConfig(ca_name, root_dir) {
  const filename = path.join(root_dir, `${ca_name}.cnf`);

  const dirs = [
    root_dir,
    path.join(root_dir, 'certs'),
    path.join(root_dir, 'private_key'),
    path.join(root_dir, 'crl'),
  ];
  dirs.forEach((dir) => {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  });

  const rootConfigData = `
[ ca ]
default_ca = root_CA

[ root_CA ]
dir               = ${root_dir}
new_certs_dir     = $dir/certs
certificate       = $dir/${ca_name}.crt
database          = $dir/index_${ca_name}.txt
serial            = $dir/serial
crl               = $dir/crl/${ca_name}.crl
crl_dir           = $dir/crl
crlnumber         = $dir/crl/crlnumber
private_key       = $dir/private_key/${ca_name}.key
default_crl_days  = 30
default_days      = 365
default_md        = sha256
policy            = root_policy
name_opt          = ca_default
cert_opt          = ca_default
copy_extensions   = copy

[ root_policy ]
countryName             = optional
stateOrProvinceName     = optional
localityName            = optional
organizationName        = optional
organizationalUnitName  = optional
commonName              = supplied

[ req ]
default_bits       = 4096
prompt             = no
default_md         = sha256
distinguished_name = set_unique

[ set_unique ]
C=CN
ST=JS
L=NJ
O=PLM
OU=1216
emailAddress = jiangrui1505@163.com
CN = localhost
CN = ${ca_name}

[ v3_ca ]
basicConstraints = critical, CA:TRUE, pathlen:10
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer

[ v3_intermediate_ca ]
basicConstraints = critical, CA:TRUE, pathlen:10
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
`;

  fs.writeFileSync(filename, rootConfigData);
  console.log(`Configuration file generated: ${filename}`);
  return filename;
}


//生成UE的config文件,视作终端执行
function generateUEConfig(ue_name, ue_dir, ue_psw) {
  const filename = path.join(ue_dir, `${ue_name}.cnf`);

// 生成文件夹
  const dirs = [
    ue_dir,
    path.join(ue_dir, 'certs'),
    path.join(ue_dir, 'private_key'),
  ];
  dirs.forEach((dir) => {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  });

  const rootConfigData = `
[ req ]
default_bits       = 4096
prompt             = no
default_md         = sha256
distinguished_name = alsoCN
attributes         = psw

[ alsoCN ]
C=CN
ST=JS
L=NJ
O=PLM
OU=1216
emailAddress=NON
CN = ${ue_name}

[ psw ]
challengePassword = ${ue_psw}
`;

fs.writeFileSync(filename, rootConfigData);
  console.log(`Configuration file generated: ${filename}`);
  return filename;
}

//CA证书生成，视作服务器执行
async function caCertgeneration(ca_name, root_dir) {
  const configFile = generateRootConfig(ca_name, root_dir);
  //注意，openssl生成的key文件包含sk和pk，所以要把sk抓出来
  const privateKeyPath = path.join(root_dir, `private_key`, `${ca_name}.key`);
  const certPath = path.join(root_dir, `certs`, `${ca_name}.crt`);

  try {
    // await runCommand(`openssl genpkey -algorithm RSA -out ${privateKeyPath} -aes256 -pass pass:mysecret -pkeyopt rsa_keygen_bits:4096`);
    await runCommand(`openssl ecparam -genkey -name secp256k1 -out ${privateKeyPath}`);
    console.log(`Private key saved to: ${privateKeyPath}`);
    const hexPrivateKeyOutput = await runCommand(`openssl ec -in ${privateKeyPath} -text -noout`);
    const privateKeyMatch = hexPrivateKeyOutput.match(/priv:\s*([\da-f\s:]+)/i);
    
    if (privateKeyMatch) {
      const privateKeyHex = privateKeyMatch[1].replace(/\s+/g, '').replace(/:/g, '');
      HEXsk = `0x${privateKeyHex}`;
      console.log('HEXsk:', HEXsk);
    } else {
      console.error('generation failed');
    }

    await runCommand(`openssl req -new -x509 -key ${privateKeyPath} -out ${certPath} -days 365 -config ${configFile} -passin pass:mysecret`);
    console.log(`Certificate saved to: ${certPath}`);
    } catch (err) {
        console.error('Error:', err);
      }
    }

//UE证书请求生成，视作终端执行
async function ueCSRgenerate(ue_name, ue_dir, ue_psw) {
  const configFile = generateUEConfig(ue_name, ue_dir, ue_psw);
  //注意，openssl生成的key文件包含sk和pk，所以要把sk抓出来
  const privateKeyPath = path.join(ue_dir, `private_key`, `${ue_name}.key`);
  const csrPath = path.join(ue_dir, `certs`, `${ue_name}.csr`);
    
    try {
      // await runCommand(`openssl genpkey -algorithm RSA -out ${privateKeyPath} -aes256 -pass pass:mysecret -pkeyopt rsa_keygen_bits:4096`);
      await runCommand(`openssl ecparam -genkey -name secp256k1 -out ${privateKeyPath}`);
      console.log(`Private key saved to: ${privateKeyPath}`);
      const hexPrivateKeyOutput = await runCommand(`openssl ec -in ${privateKeyPath} -text -noout`);
      const privateKeyMatch = hexPrivateKeyOutput.match(/priv:\s*([\da-f\s:]+)/i);
    
    if (privateKeyMatch) {
      const privateKeyHex = privateKeyMatch[1].replace(/\s+/g, '').replace(/:/g, '');
      HEXsk = `0x${privateKeyHex}`;
      console.log('HEXsk:', HEXsk);
    } else {
      console.error('generation failed');
    }
 
    await runCommand(`openssl req -new -key ${privateKeyPath} -config ${configFile} -out ${csrPath}`);
    console.log(`CSR file saved to: ${csrPath}`);
  } catch (err) {
    console.error('Error:', err);
  }
}

//UE证书生成，视作服务器执行
async function ueCertSignature(ca_name, root_dir, ue_name, ue_dir) {

  const csrPath = path.join(ue_dir, `certs`, `${ue_name}.csr`);
  const CRTpath = path.join(ue_dir, `certs`, `${ue_name}.crt`)
  const privateKeyPath = path.join(root_dir, `private_key`, `${ca_name}.key`);
  const config = path.join(root_dir, `${ca_name}.cnf`);
  const CAPath = path.join(root_dir, `certs`, `${ca_name}.crt`);

  if (!fs.existsSync(root_dir)) {
    console.log("cant find verifier");
    return;
  }

  if (!fs.existsSync(ue_dir)) {
    console.log("cant find issuer");
    return;
  }

  if (!fs.existsSync(path.join(root_dir, `certs`, `${ca_name}.crt`))) {
    console.log("issuer is not a valid ca");
    return;
  }

  if (!fs.existsSync(csrPath)) {
    console.log("cant find .csr file");
    return;
  }

  if (fs.existsSync(CRTpath)) {
    console.log("already exist certificate!");
    return;
  }

 
// 签名开始
  try {
  await runCommand(`openssl x509 -req -in ${csrPath} -CA ${CAPath} -CAkey ${privateKeyPath} -out ${CRTpath} -days 365 -extfile ${config}`);

// openssl x509 -req -in ${csrPath} -CA ${CAPath} -CAkey ${privateKeyPath} -out ${CRTpath} \
// -startdate "$(date -u +%Y%m%d%H%M%SZ)" \
// -enddate "$(date -u -d '+10 minutes' +%Y%m%d%H%M%SZ)" \
// -extfile ${config}


  console.log('creat succeed')
  } catch (err) {
  console.error('Error:', err);
  }

  if (fs.existsSync(CRTpath)) {
    console.log(`Issurance successful, ${ue_name} is issued by ${ca_name}`);
  } else {
    console.log("cant find certificate");
  }
}

//从公钥中提取可用的以太坊地址，视作服务器执行
function pkToAddress(publicKeyHex) {
  const publicKeyWithoutPrefix = publicKeyHex.slice(4);
  const publicKeyBuffer = Buffer.from(publicKeyWithoutPrefix, 'hex');
  const hashedPublicKey = keccak256(publicKeyBuffer);
  return `0x${hashedPublicKey.slice(-40)}`;
}

//将pem格式的数字证书转化为可读格式，视作服务器执行
async function getCertificateDetails(dir, name) {
  const CRTpath = path.join(dir, `certs`, `${name}.crt`);
  console.log(CRTpath);
  try {
      const CertContent = fs.readFileSync(CRTpath, 'utf8');
      const stdout = await runCommand(`openssl x509 -in ${CRTpath} -text -noout`);
      const parsedDetails = parseCertificate(stdout);
      console.log(parsedDetails)
      return {
        CertContent: CertContent,
        ethereumAddress: parsedDetails.ethereumAddress,
        notBefore: parsedDetails.notBefore,
        notAfter: parsedDetails.notAfter
      };
  } catch (error) {
      console.error("error:", error);
      throw error;
  }
}

//提取证书中的字段
function parseCertificate(opensslOutput) {
  const publicKeyMatch = /Public-Key:\s*\((\d+)\sbit\)\s*[\s\S]*?pub:\s*([\s\S]*?)\s*ASN1 OID:/m;
  const validityMatch = /Not Before:\s*(.*? GMT).*?Not After :\s*(.*? GMT)/s;

  const publicKeyResult = publicKeyMatch.exec(opensslOutput);
  const validityResult = validityMatch.exec(opensslOutput);

  if (!publicKeyResult || !validityResult) {
      throw new Error("Failed.");
  }

  //转化成可读格式的256公钥
  const publicKeyHex = `0x${publicKeyResult[2].replace(/[:\s]/g, '')}`;
  console.log (publicKeyHex)

  //转换
  const ethereumAddress = pkToAddress(publicKeyHex);

  //日期分界
  const notBefore = new Date(validityResult[1]).getTime() / 1000;
  const notAfter = new Date(validityResult[2]).getTime() / 1000;

  return {
      ethereumAddress,
      notBefore: Math.floor(notBefore),
      notAfter: Math.floor(notAfter)
  };
}

// const caName = 'root_CA';
// const ueName = 'UE';
// const uepasswd = '123456';
// const rootDir = path.join(`__dirname`, caName);
// const ueDir = path.join(__dirname, ueName);

// ueCSRgenerate(ueName, ueDir, uepasswd, 12346, '121.248.53.204');


// (async () => {
//   try {
//       await UECSRgenerate(ueName, ueDir, uepasswd);
//       await ueCertSignature(caName, rootDir, ueName, ueDir);
//       const details = await getCertificateDetails(ueDir, ueName);
//       console.log('Ethereum Address:', details.ethereumAddress);
//       console.log('Validity:', details.validity);
//   } catch (error) {
//       console.error('Error:', error);
//   }
// })();

module.exports = {
  caCertgeneration,
  ueCSRgenerate,
  ueCertSignature,
  getCertificateDetails
};


//CA 一步到位
// caCertgeneration(caName, rootDir);

//UE暂时分两步（客户端分离）
// UECSRgenerate(ueName, ueDir, uepasswd);
// ueCertSignature(caName, rootDir, ueName, ueDir);