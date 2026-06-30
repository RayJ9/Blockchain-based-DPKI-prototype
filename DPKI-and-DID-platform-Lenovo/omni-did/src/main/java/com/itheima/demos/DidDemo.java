package com.itheima.demos;

import com.danubetech.verifiablecredentials.CredentialSubject;
import com.danubetech.verifiablecredentials.VerifiableCredential;
import com.danubetech.verifiablecredentials.VerifiablePresentation;
import com.danubetech.verifiablecredentials.jsonld.VerifiableCredentialContexts;
import foundation.identity.did.DIDDocument;
import foundation.identity.did.Service;
import foundation.identity.did.VerificationMethod;
import foundation.identity.jsonld.JsonLDException;
import foundation.identity.jsonld.JsonLDUtils;
import info.weboftrust.ldsignatures.LdProof;
import info.weboftrust.ldsignatures.jsonld.LDSecurityKeywords;
import info.weboftrust.ldsignatures.signer.Ed25519Signature2018LdSigner;
import info.weboftrust.ldsignatures.verifier.Ed25519Signature2018LdVerifier;
import org.apache.commons.codec.DecoderException;
import org.apache.commons.codec.binary.Hex;

import java.io.FileReader;
import java.io.IOException;
import java.net.URI;
import java.security.GeneralSecurityException;
import java.util.Date;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * ClassName: DidDemo
 * Package: testnodej
 * Description:
 *
 * @Create 2024/11/5 17:17
 */
public class DidDemo {
    public static void main(String[] args) throws DecoderException, JsonLDException, GeneralSecurityException, IOException {
        URI did = URI.create("did:ex:1234");

        Service service = Service.builder()
                .type("ServiceEndpointProxyService")
                .serviceEndpoint("https://myservice.com/myendpoint")
                .build();

        VerificationMethod verificationMethod = VerificationMethod.builder()
                .id(URI.create(did + "#key-1"))
                .type("Ed25519VerificationKey2018")
                .publicKeyBase58("FyfKP2HvTKqDZQzvyL38yXH7bExmwofxHf2NR5BrcGf1")
                .build();

        DIDDocument diddoc = DIDDocument.builder()
                .id(did)
                .service(service)
                .verificationMethod(verificationMethod)
                .build();

        System.out.println(diddoc.toJson(true));


        Map<String, Object> claims = new LinkedHashMap<>();
        Map<String, Object> degree = new LinkedHashMap<>();
        degree.put("name", "Bachelor of Science and Arts");
        degree.put("type", "BachelorDegree");
        claims.put("organization", "Test University");
        claims.put("User Attribute VC", degree);

        CredentialSubject credentialSubject = CredentialSubject.builder()
                .id(URI.create("did:example:ebfeb1f712ebc6f1c276e12ec21"))
                .claims(claims)
                .build();

        VerifiableCredential verifiableCredential = VerifiableCredential.builder()
                .context(VerifiableCredentialContexts.JSONLD_CONTEXT_W3C_2018_CREDENTIALS_EXAMPLES_V1)
                .type("UniversityDegreeCredential")
                .id(URI.create("http://example.edu/credentials/3732"))
                .issuer(URI.create("did:example:76e12ec712ebc6f1c221ebfeb1f"))
                .issuanceDate(JsonLDUtils.stringToDate("2019-06-16T18:56:59Z"))
                .expirationDate(JsonLDUtils.stringToDate("2019-06-17T18:56:59Z"))
                .credentialSubject(credentialSubject)
                .build();

        byte[] testEd25519PrivateKey = Hex.decodeHex("984b589e121040156838303f107e13150be4a80fc5088ccba0b0bdc9b1d89090de8777a28f8da1a74e7a13090ed974d879bf692d001cddee16e4cc9f84b60580".toCharArray());

        Ed25519Signature2018LdSigner signer = new Ed25519Signature2018LdSigner(testEd25519PrivateKey);
        signer.setCreated(new Date());
        signer.setProofPurpose(LDSecurityKeywords.JSONLD_TERM_ASSERTIONMETHOD);
        signer.setVerificationMethod(URI.create("did:example:76e12ec712ebc6f1c221ebfeb1f#keys-1"));
        LdProof ldProof = signer.sign(verifiableCredential);

        System.out.println(verifiableCredential.toJson(true));
        VerifiablePresentation verifiablePresentation = VerifiablePresentation.builder()
                .verifiableCredential(verifiableCredential)
                .holder(URI.create("did:key:z6MkwBZ6oiJ71ovCohPfdsgBrQinMXnFn6wJxVZHpZEpSh8x"))
                .build();

        byte[] testEd25519PrivateKey2 = Hex.decodeHex("984b589e121040156838303f107e13150be4a80fc5088ccba0b0bdc9b1d89090de8777a28f8da1a74e7a13090ed974d879bf692d001cddee16e4cc9f84b60580".toCharArray());

        Ed25519Signature2018LdSigner signer2 = new Ed25519Signature2018LdSigner(testEd25519PrivateKey2);
        signer2.setCreated(new Date());
        signer2.setProofPurpose(LDSecurityKeywords.JSONLD_TERM_AUTHENTICATION);
        signer2.setVerificationMethod(URI.create("did:key:z6MkwBZ6oiJ71ovCohPfdsgBrQinMXnFn6wJxVZHpZEpSh8x#z6MkwBZ6oiJ71ovCohPfdsgBrQinMXnFn6wJxVZHpZEpSh8x"));
        signer2.setDomain("example.com");
        signer2.setNonce("343s$FSFDa-");
        LdProof ldProof2 = signer2.sign(verifiablePresentation);

        System.out.println(verifiablePresentation.toJson(true));


//        byte[] testEd25519PublicKey = Hex.decodeHex("de8777a28f8da1a74e7a13090ed974d879bf692d001cddee16e4cc9f84b60580".toCharArray());
//
//        VerifiableCredential verifiableCredential1 = VerifiableCredential.fromJson(new FileReader("input.jsonld"));
//        Ed25519Signature2018LdVerifier verifier = new Ed25519Signature2018LdVerifier(testEd25519PublicKey);
//        System.out.println(verifier.verify(verifiableCredential1));
//        System.out.println(verifiableCredential1.toJson(true));

        byte[] testEd25519PublicKey = Hex.decodeHex("f890ab605908a65b89b926fba3b540c0132ce147e3dc5da9fbe7f1445d7279e5".toCharArray());

        VerifiablePresentation verifiablePresentation1 = VerifiablePresentation.fromJson(new FileReader("input.jsonld"));
        Ed25519Signature2018LdVerifier verifier = new Ed25519Signature2018LdVerifier(testEd25519PublicKey);
        System.out.println(verifier.verify(verifiablePresentation1));


    }
}
