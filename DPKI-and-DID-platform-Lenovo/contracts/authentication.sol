// SPDX-License-Identifier: MIT
pragma solidity ^0.5.12;

contract DPKIAuth {

    address public issuer;
    
    struct Certificate {
        string certData;
        address certaddress;
        bool valid;
        uint256 notBefore;
        uint256 notAfter;
    }

    mapping(string => Certificate) public certificates;

    function registerCertificate(string memory _label, address _certaddress, string memory _certData, uint256 _notBefore, uint256 _notAfter) public {
        require(bytes(certificates[_label].certData).length == 0 || !certificates[_label].valid, "Cert already exists, register failed");
        certificates[_label] = Certificate(_certData, _certaddress, true, _notBefore, _notAfter);
    }


    function updateCertificate(string memory _label, address _certaddress, string memory _certData, uint256 _notBefore, uint256 _notAfter) public {
        require(bytes(certificates[_label].certData).length != 0, "Cert not exists, update failed");
        certificates[_label] = Certificate(_certData, _certaddress, true, _notBefore, _notAfter);
    }


    function revokeCertificate(string memory _label) public {
        require(bytes(certificates[_label].certData).length != 0, "Cert not exists, revoke failed");
        certificates[_label].valid = false;
    }


    // 验证证书是否在链上，会有type错误出现所以哈希了一下，很麻烦，懒得改
    function verifyCertificate(string memory _label, string memory _inputCert) public view returns (bool) {
        require(bytes(certificates[_label].certData).length != 0, "Cert not exists, verify failed");
        string memory storedCert = certificates[_label].certData;
        return (keccak256(abi.encodePacked(storedCert)) == keccak256(abi.encodePacked(_inputCert)));
    }


    function verifyCertificateTimestamp(string memory _label) public view returns (bool) {
         require(bytes(certificates[_label].certData).length != 0, "Cert not exists, verify failed");
        uint256 currentTime = block.timestamp;
        return (currentTime >= certificates[_label].notBefore && currentTime <= certificates[_label].notAfter);
    }


    function recoverSigner(bytes32 _hash, bytes memory _signature) internal pure returns (address) {
        bytes32 r;
        bytes32 s;
        uint8 v;
        require(_signature.length == 65, "invalid signature length");
        assembly {
            r := mload(add(_signature, 0x20))
            s := mload(add(_signature, 0x40))
            v := byte(0, mload(add(_signature, 0x60)))
        }
        return ecrecover(_hash, v, r, s);
    }

    //独立检验用的，一般不调用
    function verifySignedAssertion(bytes calldata _signedAssertion, address _certaddress, string calldata message) external pure returns (bool) {
        bytes memory messageBytes = bytes(message);
        bytes32 assertionHash = keccak256(messageBytes);
        address recoveredAddress = recoverSigner(assertionHash, _signedAssertion);
        return (recoveredAddress == _certaddress);
    }


    function verifyAll(bytes calldata _signedAssertion, string calldata message, string calldata _label, address _certaddress, string calldata _inputCert) external view returns (string memory) {
        
        if (!verifyCertificate(_label, _inputCert)) {
            return "verify falied, target certificate not match";
        }

        if (!certificates[_label].valid) {
            return "verify falied, certificate is not valid";
        }

        // 验证证书时间戳
        if (!verifyCertificateTimestamp(_label)) {
            return "verify falied, certificate is out of validity";
        }

        // 验证地址是否匹配，即相当于进行了challenge的过程？存疑
        bytes memory messageBytes = bytes(message);
        bytes32 assertionHash = keccak256(messageBytes);
        address recoveredAddress = recoverSigner(assertionHash, _signedAssertion);
        if (recoveredAddress != _certaddress) {
            return "verify falied, the challenge-response failed";
        }
        return "verify successful!";
    }

}
