// SPDX-License-Identifier: MIT
pragma solidity ^0.5.17;
pragma experimental ABIEncoderV2;

contract DPKIExperiment {
    uint8 public constant STATE_NONE = 0;
    uint8 public constant STATE_VALID = 1;
    uint8 public constant STATE_REVOKED = 2;

    struct Certificate {
        bytes32 domainId;
        bytes32 subjectId;
        address subjectAddress;
        bytes32 certHash;
        uint8 state;
        uint256 notBefore;
        uint256 notAfter;
        uint256 updatedAt;
    }

    struct AuthRecord {
        bytes32 sourceDomainId;
        bytes32 targetDomainId;
        bytes32 sourceSubjectId;
        bytes32 targetSubjectId;
        bytes32 certHash;
        bytes32 nonceHash;
        address sourceAddress;
        uint256 timestamp;
        bool crossDomain;
        bool exists;
    }

    mapping(bytes32 => Certificate) public certificates;
    mapping(bytes32 => bytes32) public domainRoots;
    mapping(bytes32 => AuthRecord) public authRecords;
    mapping(bytes32 => address) public authRecordSigners;
    mapping(bytes32 => bytes32) public authRecordSignatureHashes;

    event DomainRootUpdated(bytes32 indexed domainId, bytes32 repoRoot);
    event CertificateStored(bytes32 indexed certKey, bytes32 indexed domainId, bytes32 indexed subjectId, bytes32 certHash, uint8 state);
    event CertificateRevoked(bytes32 indexed certKey);
    event AuthRecordStored(bytes32 indexed requestId, bytes32 indexed sourceDomainId, bytes32 indexed targetDomainId, bool crossDomain);

    function putDomainRoot(bytes32 domainId, bytes32 repoRoot) public {
        domainRoots[domainId] = repoRoot;
        emit DomainRootUpdated(domainId, repoRoot);
    }

    function putCertificate(
        bytes32 certKey,
        bytes32 domainId,
        bytes32 subjectId,
        address subjectAddress,
        bytes32 certHash,
        uint256 notBefore,
        uint256 notAfter
    ) public {
        certificates[certKey] = Certificate(
            domainId,
            subjectId,
            subjectAddress,
            certHash,
            STATE_VALID,
            notBefore,
            notAfter,
            block.timestamp
        );
        emit CertificateStored(certKey, domainId, subjectId, certHash, STATE_VALID);
    }

    function putCertificateAndDomainRoot(
        bytes32 certKey,
        bytes32 domainId,
        bytes32 subjectId,
        address subjectAddress,
        bytes32 certHash,
        uint256 notBefore,
        uint256 notAfter,
        bytes32 repoRoot
    ) public {
        certificates[certKey] = Certificate(
            domainId,
            subjectId,
            subjectAddress,
            certHash,
            STATE_VALID,
            notBefore,
            notAfter,
            block.timestamp
        );
        domainRoots[domainId] = repoRoot;
        emit CertificateStored(certKey, domainId, subjectId, certHash, STATE_VALID);
        emit DomainRootUpdated(domainId, repoRoot);
    }

    function revokeCertificate(bytes32 certKey) public {
        require(certificates[certKey].state == STATE_VALID, "certificate is not valid");
        certificates[certKey].state = STATE_REVOKED;
        certificates[certKey].updatedAt = block.timestamp;
        emit CertificateRevoked(certKey);
    }

    function verifyCertificate(bytes32 certKey, bytes32 certHash) public view returns (bool) {
        return _isCertificateValid(certKey, certHash);
    }

    function authenticate(
        bytes32 requestId,
        bytes32 sourceDomainId,
        bytes32 targetDomainId,
        bytes32 sourceSubjectId,
        bytes32 targetSubjectId,
        bytes32 nonceHash,
        address sourceAddress,
        uint256 timestamp,
        bool crossDomain,
        bytes32[] memory certKeys,
        bytes32[] memory certHashes
    ) public {
        require(certKeys.length > 0, "missing certificate checks");
        require(certKeys.length == certHashes.length, "bad certificate checks length");
        for (uint256 i = 0; i < certKeys.length; i++) {
            require(_isCertificateValid(certKeys[i], certHashes[i]), "certificate is not valid");
        }
        _putAuthRecord(
            requestId,
            sourceDomainId,
            targetDomainId,
            sourceSubjectId,
            targetSubjectId,
            certHashes[0],
            nonceHash,
            sourceAddress,
            timestamp,
            crossDomain
        );
    }

    function authenticateSigned(
        bytes32[8] memory data,
        address sourceAddress,
        uint256 timestamp,
        bool crossDomain,
        address serviceSigner,
        bytes32 serviceSignatureHash
    ) public {
        require(serviceSigner != address(0), "missing service signer");
        require(serviceSignatureHash != bytes32(0), "missing service signature");
        require(_isCertificateValid(data[6], data[7]), "certificate is not valid");
        _putAuthRecord(
            data[0],
            data[1],
            data[2],
            data[3],
            data[4],
            data[7],
            data[5],
            sourceAddress,
            timestamp,
            crossDomain
        );
        authRecordSigners[data[0]] = serviceSigner;
        authRecordSignatureHashes[data[0]] = serviceSignatureHash;
    }

    function _isCertificateValid(bytes32 certKey, bytes32 certHash) internal view returns (bool) {
        Certificate memory cert = certificates[certKey];
        return cert.state == STATE_VALID
            && cert.certHash == certHash
            && now >= cert.notBefore
            && now <= cert.notAfter;
    }

    function putAuthRecord(
        bytes32 requestId,
        bytes32 sourceDomainId,
        bytes32 targetDomainId,
        bytes32 sourceSubjectId,
        bytes32 targetSubjectId,
        bytes32 certHash,
        bytes32 nonceHash,
        address sourceAddress,
        uint256 timestamp,
        bool crossDomain
    ) public {
        _putAuthRecord(
            requestId,
            sourceDomainId,
            targetDomainId,
            sourceSubjectId,
            targetSubjectId,
            certHash,
            nonceHash,
            sourceAddress,
            timestamp,
            crossDomain
        );
    }

    function _putAuthRecord(
        bytes32 requestId,
        bytes32 sourceDomainId,
        bytes32 targetDomainId,
        bytes32 sourceSubjectId,
        bytes32 targetSubjectId,
        bytes32 certHash,
        bytes32 nonceHash,
        address sourceAddress,
        uint256 timestamp,
        bool crossDomain
    ) internal {
        authRecords[requestId] = AuthRecord(
            sourceDomainId,
            targetDomainId,
            sourceSubjectId,
            targetSubjectId,
            certHash,
            nonceHash,
            sourceAddress,
            timestamp,
            crossDomain,
            true
        );
        emit AuthRecordStored(requestId, sourceDomainId, targetDomainId, crossDomain);
    }

    function authRecordExists(bytes32 requestId) public view returns (bool) {
        return authRecords[requestId].exists;
    }

    function getAuthRecordSignatureCommitment(bytes32 requestId) public view returns (address, bytes32) {
        return (authRecordSigners[requestId], authRecordSignatureHashes[requestId]);
    }
}
