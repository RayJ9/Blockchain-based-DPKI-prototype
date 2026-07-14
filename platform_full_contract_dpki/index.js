module.exports = {
  mechanism: "full-contract-onchain",
  requestClasses: ["management", "intra-on-chain", "cross-on-chain"],

  async execute({ row, ctx, label, requestId, helpers }) {
    const {
      issue,
      assertion,
      ocspVerify,
      chainRecord,
      signContractAssertion,
      signedAuthRecordStorageBytes,
      fullCertificateStorageBytes,
      addCertStatusChecks,
      keccakBytes32,
    } = helpers;

    const chain = ctx.chain;

    await assertion(row, ctx.openssl, row.requestClass === "management" ? 2 : 1);

    if (row.requestClass === "management") {
      const issueArtifact = await issue(row, ctx.openssl, 1, {
        persistMode: "none",
        persistStatus: false,
        countOffchainStorage: false,
      });
      await chainRecord(row, chain, "contractExecution", chain
        ? chain.contract.methods.putFullCertificateBundleAndDomainRoot(
          keccakBytes32(chain.web3, `full-cert:${row.index}`),
          chain.source.domainId,
          keccakBytes32(chain.web3, `full-subject:${row.index}`),
          chain.source.subjectAddress,
          keccakBytes32(chain.web3, `full-cert-hash:${row.index}`),
          0,
          chain.notAfter,
          keccakBytes32(chain.web3, `full-root:${row.index}`),
          `0x${issueArtifact.csrBuffer.toString("hex")}`,
          `0x${issueArtifact.certBuffer.toString("hex")}`,
          `0x${issueArtifact.statusBuffer.toString("hex")}`,
        )
        : null,
      {
        onChainStorageBytes: fullCertificateStorageBytes(
          issueArtifact.csrBytes,
          issueArtifact.certBytes,
          issueArtifact.statusBytes,
        ),
      });
      return;
    }

    const crossDomain = row.requestClass === "cross-on-chain";
    addCertStatusChecks(row, crossDomain ? 2 : 1);
    if (crossDomain) {
      await ocspVerify(row, ctx.services, 1, `${label}:counterparty-ca`);
    }
    const certs = crossDomain ? [chain.source, chain.service] : [chain.source];
    const timestamp = Math.floor(Date.now() / 1000);
    const signed = signContractAssertion(chain, requestId, crossDomain, certs, timestamp);
    await chainRecord(row, chain, "contractExecution", chain.contract.methods.authenticateSigned(
      signed.data,
      chain.source.subjectAddress,
      timestamp,
      crossDomain,
      signed.certKeys,
      signed.certHashes,
      chain.service.subjectAddress,
      signed.signature,
    ), {
      onChainStorageBytes: signedAuthRecordStorageBytes(),
      onChainSigVerifyOps: 1,
    });
  },
};
