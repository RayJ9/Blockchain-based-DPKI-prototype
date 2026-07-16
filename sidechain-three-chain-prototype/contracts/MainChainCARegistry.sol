// SPDX-License-Identifier: MIT
pragma solidity ^0.5.17;

contract MainChainCARegistry {
    struct CARecord {
        address operator;
        bytes32 metadataHash;
        bool active;
        uint256 updatedAt;
    }

    struct SidechainCheckpoint {
        bytes32 caId;
        bytes32 stateRoot;
        uint256 sideHeight;
        address submitter;
        uint256 submittedAt;
    }

    mapping(bytes32 => CARecord) public certificateAuthorities;
    mapping(bytes32 => SidechainCheckpoint) public checkpoints;

    event CARegistered(bytes32 indexed caId, address indexed operator, bytes32 metadataHash);
    event CAStatusChanged(bytes32 indexed caId, bool active);
    event CheckpointSubmitted(
        bytes32 indexed sidechainId,
        bytes32 indexed caId,
        bytes32 stateRoot,
        uint256 sideHeight,
        address submitter
    );

    function registerCA(bytes32 caId, address operator, bytes32 metadataHash) public {
        require(caId != bytes32(0), "missing CA id");
        require(operator != address(0), "missing CA operator");
        certificateAuthorities[caId] = CARecord(operator, metadataHash, true, block.timestamp);
        emit CARegistered(caId, operator, metadataHash);
    }

    function setCAStatus(bytes32 caId, bool active) public {
        CARecord storage record = certificateAuthorities[caId];
        require(record.operator != address(0), "unknown CA");
        require(msg.sender == record.operator, "only CA operator");
        record.active = active;
        record.updatedAt = block.timestamp;
        emit CAStatusChanged(caId, active);
    }

    function submitCheckpoint(
        bytes32 sidechainId,
        bytes32 caId,
        bytes32 stateRoot,
        uint256 sideHeight
    ) public {
        CARecord memory record = certificateAuthorities[caId];
        require(record.active, "inactive CA");
        require(msg.sender == record.operator, "only CA operator");
        require(stateRoot != bytes32(0), "missing state root");
        checkpoints[sidechainId] = SidechainCheckpoint(
            caId,
            stateRoot,
            sideHeight,
            msg.sender,
            block.timestamp
        );
        emit CheckpointSubmitted(sidechainId, caId, stateRoot, sideHeight, msg.sender);
    }
}
