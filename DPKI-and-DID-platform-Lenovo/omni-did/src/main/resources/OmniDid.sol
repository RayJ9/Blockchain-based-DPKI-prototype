// SPDX-License-Identifier: MIT
pragma solidity ^0.5.12;

contract OmniDid {
    mapping(string => string ) private didToDocument;
    function createOrUpdateDidDocument(string memory _did, string memory _didDocument) public {
        didToDocument[_did] = _didDocument;
    }

    function getDidDocument(string memory _did) public view returns(string memory) {
        return didToDocument[_did];
    }

}