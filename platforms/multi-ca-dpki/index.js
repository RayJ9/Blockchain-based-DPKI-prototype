module.exports = {
  mechanism: "threshold-validation-dpki",
  requestClasses: ["management", "intra-auth", "cross-auth"],

  async execute({ row, ctx, label, helpers }) {
    const {
      issue,
      assertion,
      ocspVerify,
      thresholdValidate,
      thresholdManagementCeremony,
      signThresholdCertificateBundle,
      thresholdCertificateStorageBytes,
      chainRecord,
      keccakBytes32,
      measure,
      postJson,
    } = helpers;

    const chain = ctx.chain;

    if (row.requestClass === "management") {
      const thresholdCertKey = keccakBytes32(chain.web3, `threshold-cert:${row.index}`);
      const thresholdSubjectId = keccakBytes32(chain.web3, `threshold-subject:${row.index}`);
      const thresholdCertHash = keccakBytes32(chain.web3, `threshold-cert-hash:${row.index}`);
      const thresholdRoot = keccakBytes32(chain.web3, `threshold-root:${row.index}`);
      const issueArtifact = await issue(row, ctx.openssl, 1, {
        persistMode: "none",
        persistStatus: false,
        countOffchainStorage: false,
      });

      if (ctx.args.actualOverhead) {
        await thresholdManagementCeremony(row, ctx.services, ctx.args, label);
      } else {
        await measure(row, "thresholdIssue", async () => {
          await Promise.all(Array.from({ length: ctx.args.thresholdN }, (_, i) =>
            postJson(18343, "/threshold", {
              nodeId: i,
              cert: `${label}:issue`,
              nonce: `${label}:issue:${i}`,
            }).catch(() => null),
          ));
        });
      }

      const committee = signThresholdCertificateBundle(
        chain,
        thresholdCertKey,
        chain.source.domainId,
        thresholdSubjectId,
        chain.source.subjectAddress,
        thresholdCertHash,
        0,
        chain.notAfter,
        thresholdRoot,
        ctx.args.thresholdK,
      );

      await chainRecord(row, chain, "chainRecord", chain
        ? chain.contract.methods.putThresholdCertificateBundleAndDomainRoot(
          thresholdCertKey,
          chain.source.domainId,
          thresholdSubjectId,
          chain.source.subjectAddress,
          thresholdCertHash,
          0,
          chain.notAfter,
          thresholdRoot,
          `0x${issueArtifact.certBuffer.toString("hex")}`,
          committee.blobHex,
          committee.quorumK,
        )
        : null,
      {
        onChainStorageBytes: thresholdCertificateStorageBytes(issueArtifact.certBytes, committee.blob.length),
        onChainSigVerifyOps: committee.signerCount,
      });
      await assertion(row, ctx.openssl, 2);
      return;
    }

    if (row.requestClass === "intra-auth") {
      await thresholdValidate(row, ctx.services, ctx.args, label);
      await assertion(row, ctx.openssl, 1);
      return;
    }

    if (row.requestClass === "cross-auth") {
      await thresholdValidate(row, ctx.services, ctx.args, label);
      await ocspVerify(row, ctx.services, 1, `${label}:counterparty-ca`);
      await assertion(row, ctx.openssl, 2);
      return;
    }

    throw new Error(`Unsupported request class for threshold-validation-dpki: ${row.requestClass}`);
  },
};
