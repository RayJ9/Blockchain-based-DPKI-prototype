module.exports = {
  mechanism: "traditional-pki",
  requestClasses: ["management", "intra-auth", "cross-auth"],

  async execute({ row, ctx, label, helpers }) {
    const {
      issue,
      assertion,
      certificateVerification,
      ocspVerify,
    } = helpers;

    if (row.requestClass === "management") {
      await issue(row, ctx.openssl, 1);
      await assertion(row, ctx.openssl, 2);
      return;
    }

    if (row.requestClass === "intra-auth") {
      await certificateVerification(row, ctx.openssl, 1);
      await ocspVerify(row, ctx.services, 1, label);
      await assertion(row, ctx.openssl, 1);
      return;
    }

    if (row.requestClass === "cross-auth") {
      for (let i = 0; i < 4; i += 1) {
        await certificateVerification(row, ctx.openssl, 1);
        await ocspVerify(row, ctx.services, 1, `${label}:hop${i}`);
        await assertion(row, ctx.openssl, 1);
      }
      return;
    }

    throw new Error(`Unsupported request class for traditional-pki: ${row.requestClass}`);
  },
};
