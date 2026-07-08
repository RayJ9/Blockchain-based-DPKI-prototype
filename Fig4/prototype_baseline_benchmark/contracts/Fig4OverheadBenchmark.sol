// SPDX-License-Identifier: MIT
pragma solidity ^0.5.17;
pragma experimental ABIEncoderV2;

contract Fig4OverheadBenchmark {
    uint8 public constant STATE_NONE = 0;
    uint8 public constant STATE_VALID = 1;
    uint8 public constant STATE_REVOKED = 2;
    uint256 public constant MAX_ASSERTION_AGE = 600;
    uint256 public constant MAX_ASSERTION_CLOCK_SKEW = 60;

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

    struct ThresholdEvidence {
        bytes certPem;
        bytes committeeSignatures;
        uint8 quorumK;
        uint8 signerCount;
        bool exists;
    }

    struct ProposedCertificateMaterial {
        bytes certPem;
        bool exists;
    }

    struct FullCertificateMaterial {
        bytes csrPem;
        bytes certPem;
        bytes statusBlob;
        bool exists;
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
    mapping(bytes32 => ProposedCertificateMaterial) public proposedCertificates;
    mapping(bytes32 => ThresholdEvidence) public thresholdEvidences;
    mapping(bytes32 => FullCertificateMaterial) public fullCertificates;
    mapping(bytes32 => AuthRecord) public authRecords;
    mapping(bytes32 => address) public authRecordSigners;
    mapping(bytes32 => bytes32) public authRecordSignatureHashes;

    mapping(address => bool) public isThresholdValidator;
    address[] public thresholdValidators;

    event DomainRootUpdated(bytes32 indexed domainId, bytes32 repoRoot);
    event CertificateStored(bytes32 indexed certKey, bytes32 indexed domainId, bytes32 indexed subjectId, bytes32 certHash, uint8 state);
    event ProposedCertificateStored(bytes32 indexed certKey, uint256 certBytes);
    event ThresholdCertificateStored(bytes32 indexed certKey, uint8 quorumK, uint8 signerCount, uint256 certBytes, uint256 signatureBytes);
    event FullCertificateStored(bytes32 indexed certKey, uint256 csrBytes, uint256 certBytes, uint256 statusBytes);
    event AuthRecordStored(bytes32 indexed requestId, bytes32 indexed sourceDomainId, bytes32 indexed targetDomainId, bool crossDomain);

    constructor(address[] memory validators) public {
        for (uint256 i = 0; i < validators.length; i++) {
            address validator = validators[i];
            if (validator != address(0) && !isThresholdValidator[validator]) {
                isThresholdValidator[validator] = true;
                thresholdValidators.push(validator);
            }
        }
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
        _storeCertificate(certKey, domainId, subjectId, subjectAddress, certHash, notBefore, notAfter);
        domainRoots[domainId] = repoRoot;
        emit DomainRootUpdated(domainId, repoRoot);
    }

    function putProposedCertificateBundleAndDomainRoot(
        bytes32 certKey,
        bytes32 domainId,
        bytes32 subjectId,
        address subjectAddress,
        bytes32 certHash,
        uint256 notBefore,
        uint256 notAfter,
        bytes32 repoRoot,
        bytes memory certPem
    ) public {
        require(certPem.length > 0, "missing certPem");
        _storeCertificate(certKey, domainId, subjectId, subjectAddress, certHash, notBefore, notAfter);
        domainRoots[domainId] = repoRoot;
        proposedCertificates[certKey] = ProposedCertificateMaterial(certPem, true);
        emit DomainRootUpdated(domainId, repoRoot);
        emit ProposedCertificateStored(certKey, certPem.length);
    }

    function putThresholdCertificateBundleAndDomainRoot(
        bytes32 certKey,
        bytes32 domainId,
        bytes32 subjectId,
        address subjectAddress,
        bytes32 certHash,
        uint256 notBefore,
        uint256 notAfter,
        bytes32 repoRoot,
        bytes memory certPem,
        bytes memory committeeSignatures,
        uint8 quorumK
    ) public {
        require(quorumK > 0, "bad quorumK");
        require(certPem.length > 0, "missing certPem");
        uint256 signerCount = _verifyThresholdCommittee(
            certKey,
            domainId,
            subjectId,
            subjectAddress,
            certHash,
            notBefore,
            notAfter,
            repoRoot,
            committeeSignatures
        );
        require(signerCount >= quorumK, "insufficient threshold signatures");

        _storeCertificate(certKey, domainId, subjectId, subjectAddress, certHash, notBefore, notAfter);
        domainRoots[domainId] = repoRoot;
        thresholdEvidences[certKey] = ThresholdEvidence(
            certPem,
            committeeSignatures,
            quorumK,
            uint8(signerCount),
            true
        );
        emit DomainRootUpdated(domainId, repoRoot);
        emit ThresholdCertificateStored(certKey, quorumK, uint8(signerCount), certPem.length, committeeSignatures.length);
    }

    function putFullCertificateBundleAndDomainRoot(
        bytes32 certKey,
        bytes32 domainId,
        bytes32 subjectId,
        address subjectAddress,
        bytes32 certHash,
        uint256 notBefore,
        uint256 notAfter,
        bytes32 repoRoot,
        bytes memory csrPem,
        bytes memory certPem,
        bytes memory statusBlob
    ) public {
        require(certPem.length > 0, "missing certPem");
        _storeCertificate(certKey, domainId, subjectId, subjectAddress, certHash, notBefore, notAfter);
        domainRoots[domainId] = repoRoot;
        fullCertificates[certKey] = FullCertificateMaterial(csrPem, certPem, statusBlob, true);
        emit DomainRootUpdated(domainId, repoRoot);
        emit FullCertificateStored(certKey, csrPem.length, certPem.length, statusBlob.length);
    }

    function verifyCertificate(bytes32 certKey, bytes32 certHash) public view returns (bool) {
        return _isCertificateValid(certKey, certHash);
    }

    function authenticateSigned(
        bytes32[6] memory data,
        address sourceAddress,
        uint256 timestamp,
        bool crossDomain,
        bytes32[] memory certKeys,
        bytes32[] memory certHashes,
        address serviceSigner,
        bytes memory serviceSignature
    ) public {
        require(serviceSigner != address(0), "missing service signer");
        require(serviceSignature.length == 65, "bad service signature length");
        require(certKeys.length > 0, "missing certificate checks");
        require(certKeys.length == certHashes.length, "bad certificate checks length");
        require(timestamp <= now + MAX_ASSERTION_CLOCK_SKEW, "assertion timestamp from future");
        require(timestamp + MAX_ASSERTION_AGE >= now, "assertion expired");
        for (uint256 i = 0; i < certKeys.length; i++) {
            require(_isCertificateValid(certKeys[i], certHashes[i]), "certificate is not valid");
        }
        require(
            _recoverEthereumSigned(authAssertionDigest(data, sourceAddress, timestamp, crossDomain, certKeys, certHashes), serviceSignature)
                == serviceSigner,
            "bad assertion signature"
        );
        _putAuthRecord(
            data[0],
            data[1],
            data[2],
            data[3],
            data[4],
            certHashes[0],
            data[5],
            sourceAddress,
            timestamp,
            crossDomain
        );
        authRecordSigners[data[0]] = serviceSigner;
        authRecordSignatureHashes[data[0]] = keccak256(serviceSignature);
    }

    function authAssertionDigest(
        bytes32[6] memory data,
        address sourceAddress,
        uint256 timestamp,
        bool crossDomain,
        bytes32[] memory certKeys,
        bytes32[] memory certHashes
    ) public view returns (bytes32) {
        return keccak256(
            abi.encodePacked(
                address(this),
                data[0],
                data[1],
                data[2],
                data[3],
                data[4],
                data[5],
                sourceAddress,
                timestamp,
                crossDomain,
                keccak256(abi.encode(certKeys, certHashes))
            )
        );
    }

    function thresholdCertificateDigest(
        bytes32 certKey,
        bytes32 domainId,
        bytes32 subjectId,
        address subjectAddress,
        bytes32 certHash,
        uint256 notBefore,
        uint256 notAfter,
        bytes32 repoRoot
    ) public view returns (bytes32) {
        return keccak256(
            abi.encodePacked(
                address(this),
                "threshold-cert",
                certKey,
                domainId,
                subjectId,
                subjectAddress,
                certHash,
                notBefore,
                notAfter,
                repoRoot
            )
        );
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

    function authRecordExists(bytes32 requestId) public view returns (bool) {
        return authRecords[requestId].exists;
    }

    function getAuthRecordSignatureCommitment(bytes32 requestId) public view returns (address, bytes32) {
        return (authRecordSigners[requestId], authRecordSignatureHashes[requestId]);
    }

    function _storeCertificate(
        bytes32 certKey,
        bytes32 domainId,
        bytes32 subjectId,
        address subjectAddress,
        bytes32 certHash,
        uint256 notBefore,
        uint256 notAfter
    ) internal {
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

    function _isCertificateValid(bytes32 certKey, bytes32 certHash) internal view returns (bool) {
        Certificate memory cert = certificates[certKey];
        return cert.state == STATE_VALID
            && cert.certHash == certHash
            && now >= cert.notBefore
            && now <= cert.notAfter;
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
        require(!authRecords[requestId].exists, "auth record already exists");
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

    function _verifyThresholdCommittee(
        bytes32 certKey,
        bytes32 domainId,
        bytes32 subjectId,
        address subjectAddress,
        bytes32 certHash,
        uint256 notBefore,
        uint256 notAfter,
        bytes32 repoRoot,
        bytes memory committeeSignatures
    ) internal view returns (uint256) {
        require(committeeSignatures.length > 0, "missing threshold signatures");
        require(committeeSignatures.length % 65 == 0, "bad threshold signature blob");

        bytes32 digest = thresholdCertificateDigest(
            certKey,
            domainId,
            subjectId,
            subjectAddress,
            certHash,
            notBefore,
            notAfter,
            repoRoot
        );

        uint256 count = committeeSignatures.length / 65;
        address[] memory seen = new address[](count);
        uint256 validCount = 0;

        for (uint256 i = 0; i < count; i++) {
            address signer = _recoverEthereumSigned(digest, _sliceSignature(committeeSignatures, i * 65));
            require(isThresholdValidator[signer], "unexpected threshold signer");
            for (uint256 j = 0; j < validCount; j++) {
                require(seen[j] != signer, "duplicate threshold signer");
            }
            seen[validCount] = signer;
            validCount += 1;
        }
        return validCount;
    }

    function _sliceSignature(bytes memory blob, uint256 offset) internal pure returns (bytes memory) {
        bytes memory out = new bytes(65);
        for (uint256 i = 0; i < 65; i++) {
            out[i] = blob[offset + i];
        }
        return out;
    }

    function _recoverEthereumSigned(bytes32 digest, bytes memory signature) internal pure returns (address) {
        bytes32 r;
        bytes32 s;
        uint8 v;
        assembly {
            r := mload(add(signature, 32))
            s := mload(add(signature, 64))
            v := byte(0, mload(add(signature, 96)))
        }
        if (v < 27) {
            v += 27;
        }
        require(v == 27 || v == 28, "bad signature v");
        bytes32 ethDigest = keccak256(abi.encodePacked("\x19Ethereum Signed Message:\n32", digest));
        return ecrecover(ethDigest, v, r, s);
    }
}
