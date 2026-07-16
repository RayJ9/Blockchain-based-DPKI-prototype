// SPDX-License-Identifier: MIT
pragma solidity ^0.5.17;

contract SidechainDPKI {
    uint8 public constant STATE_VALID = 1;
    uint8 public constant STATE_REVOKED = 2;

    struct CertificateRecord {
        bytes32 subjectId;
        bytes32 certHash;
        bytes32 publicKeyHash;
        uint8 state;
        uint256 notBefore;
        uint256 notAfter;
        uint256 updatedAt;
    }

    struct CrossDomainResult {
        bytes32 sourceChainId;
        bytes32 sourceCertId;
        bytes32 sourceCertHash;
        bytes32 mainChainCheckpoint;
        bool accepted;
        uint256 recordedAt;
    }

    bytes32 public sidechainId;
    bytes32 public governingCaId;
    bytes32 public stateRoot;

    mapping(bytes32 => CertificateRecord) public certificates;
    mapping(bytes32 => CrossDomainResult) public crossDomainResults;

    event CertificateIssued(bytes32 indexed certId, bytes32 indexed subjectId, bytes32 certHash);
    event CertificateRevoked(bytes32 indexed certId);
    event StateRootUpdated(bytes32 indexed stateRoot);
    event CrossDomainAuthenticationRecorded(
        bytes32 indexed requestId,
        bytes32 indexed sourceChainId,
        bytes32 indexed sourceCertId,
        bool accepted
    );

    constructor(bytes32 _sidechainId, bytes32 _governingCaId) public {
        sidechainId = _sidechainId;
        governingCaId = _governingCaId;
    }

    function issueCertificate(
        bytes32 certId,
        bytes32 subjectId,
        bytes32 certHash,
        bytes32 publicKeyHash,
        uint256 notBefore,
        uint256 notAfter
    ) public {
        require(certId != bytes32(0), "missing certificate id");
        require(notAfter > notBefore, "bad validity window");
        certificates[certId] = CertificateRecord(
            subjectId,
            certHash,
            publicKeyHash,
            STATE_VALID,
            notBefore,
            notAfter,
            block.timestamp
        );
        emit CertificateIssued(certId, subjectId, certHash);
    }

    function revokeCertificate(bytes32 certId) public {
        require(certificates[certId].state == STATE_VALID, "certificate is not valid");
        certificates[certId].state = STATE_REVOKED;
        certificates[certId].updatedAt = block.timestamp;
        emit CertificateRevoked(certId);
    }

    function updateStateRoot(bytes32 newStateRoot) public {
        require(newStateRoot != bytes32(0), "missing state root");
        stateRoot = newStateRoot;
        emit StateRootUpdated(newStateRoot);
    }

    function verifyCertificate(bytes32 certId, bytes32 certHash) public view returns (bool) {
        CertificateRecord memory record = certificates[certId];
        return record.state == STATE_VALID
            && record.certHash == certHash
            && now >= record.notBefore
            && now <= record.notAfter;
    }

    function recordCrossDomainAuthentication(
        bytes32 requestId,
        bytes32 sourceChainId,
        bytes32 sourceCertId,
        bytes32 sourceCertHash,
        bytes32 mainChainCheckpoint,
        bool accepted
    ) public {
        crossDomainResults[requestId] = CrossDomainResult(
            sourceChainId,
            sourceCertId,
            sourceCertHash,
            mainChainCheckpoint,
            accepted,
            block.timestamp
        );
        emit CrossDomainAuthenticationRecorded(requestId, sourceChainId, sourceCertId, accepted);
    }
}
