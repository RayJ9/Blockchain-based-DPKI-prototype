module.exports = {
  mechanism: "proposed-dpki",
  requestClasses: ["management", "intra-off-chain", "intra-on-chain", "cross-on-chain"],

  async execute({ row, ctx, label, requestId, helpers }) {
    const {
      issue,
      assertion,
      certificateVerification,
      mptVerify,
      chainRecord,
      chainStateRead,
      proposedCertificateStorageBytes,
      authRecordStorageBytes,
      keccakBytes32,
    } = helpers;

    const chain = ctx.chain;

    if (row.requestClass === "management") {
      const issueArtifact = await issue(row, ctx.openssl, 1, {
        persistMode: "none",
        persistStatus: false,
        countOffchainStorage: false,
      });
      await chainRecord(row, chain, "chainRecord", chain
        ? chain.contract.methods.putProposedCertificateBundleAndDomainRoot(
          keccakBytes32(chain.web3, `dpki-cert:${row.index}`),
          chain.source.domainId,
          keccakBytes32(chain.web3, `dpki-subject:${row.index}`),
          chain.source.subjectAddress,
          keccakBytes32(chain.web3, `dpki-cert-hash:${row.index}`),
          0,
          chain.notAfter,
          keccakBytes32(chain.web3, `dpki-root:${row.index}`),
          `0x${issueArtifact.certBuffer.toString("hex")}`,
        )
        : null,
      {
        onChainStorageBytes: proposedCertificateStorageBytes(issueArtifact.certBytes),
      });
      await assertion(row, ctx.openssl, 2);
      return;
    }

    if (row.requestClass === "intra-off-chain") {
      await certificateVerification(row, ctx.openssl, 1);
      await mptVerify(row, ctx.services, chain, 1, label);
      await assertion(row, ctx.openssl, 1);
      return;
    }

    if (row.requestClass === "intra-on-chain" || row.requestClass === "cross-on-chain") {
      await certificateVerification(row, ctx.openssl, 1);
      await mptVerify(row, ctx.services, chain, row.requestClass === "cross-on-chain" ? 2 : 1, label);
      await chainRecord(row, chain, "chainRecord", chain.contract.methods.putAuthRecord(
        requestId,
        chain.source.domainId,
        chain.target.domainId,
        chain.source.subjectId,
        chain.target.subjectId,
        chain.source.certHash,
        keccakBytes32(chain.web3, `nonce:${label}`),
        chain.source.subjectAddress,
        Math.floor(Date.now() / 1000),
        row.requestClass === "cross-on-chain",
      ), {
        onChainStorageBytes: authRecordStorageBytes(),
      });
      await chainStateRead(row, chain, requestId);
      await assertion(row, ctx.openssl, 1);
      return;
    }

    throw new Error(`Unsupported request class for proposed-dpki: ${row.requestClass}`);
  },
};
