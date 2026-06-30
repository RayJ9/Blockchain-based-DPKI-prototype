package com.itheima.demos;

import com.danubetech.verifiablecredentials.CredentialSubject;
import com.danubetech.verifiablecredentials.VerifiableCredential;
import com.danubetech.verifiablecredentials.jsonld.VerifiableCredentialContexts;
import com.danubetech.verifiablecredentials.jwt.FromJwtConverter;
import com.danubetech.verifiablecredentials.jwt.JwtVerifiableCredential;
import com.danubetech.verifiablecredentials.jwt.ToJwtConverter;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.nimbusds.jose.JOSEException;
import foundation.identity.jsonld.JsonLDUtils;
import org.apache.commons.codec.DecoderException;
import org.apache.commons.codec.binary.Hex;

import java.io.File;
import java.io.IOException;
import java.net.URI;
import java.text.ParseException;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * ClassName: VCDemo
 * Package: com.itheima
 * Description:
 *
 * @Create 2025/1/2 17:10
 */
public class VCDemo {
    public static void main(String[] args) throws DecoderException, JOSEException, ParseException, IOException {
        Map<String, Object> claims = new LinkedHashMap<>();
        Map<String, Object> degree = new LinkedHashMap<>();
        degree.put("name", "Bachelor of Science and Arts");
        degree.put("type", "BachelorDegree");
        claims.put("college", "Test University");
        claims.put("degree", degree);

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
        System.out.println(verifiableCredential.toJson(true));
        ObjectMapper objectMapper = new ObjectMapper();

        try {
            // 指定要保存的文件路径，使用 .jsonld 扩展名
            File file = new File("output.jsonld");

            // 将 JSON-LD 对象写入文件，使用美化输出
            objectMapper.writerWithDefaultPrettyPrinter().writeValue(file, verifiableCredential);

            System.out.println("JSON-LD 对象已成功保存到文件：" + file.getAbsolutePath());
        } catch (IOException e) {
            System.err.println("保存 JSON-LD 对象到文件时发生错误：" + e.getMessage());
        }

        byte[] testEd25519PrivateKey = Hex.decodeHex("984b589e121040156838303f107e13150be4a80fc5088ccba0b0bdc9b1d89090de8777a28f8da1a74e7a13090ed974d879bf692d001cddee16e4cc9f84b60580".toCharArray());

        JwtVerifiableCredential jwtVerifiableCredential = ToJwtConverter.toJwtVerifiableCredential(verifiableCredential);

        String jwtPayload = jwtVerifiableCredential.getPayload().toString();
       // System.out.println(claims);
        System.out.println(jwtPayload);

        String jwtString = jwtVerifiableCredential.sign_Ed25519_EdDSA(testEd25519PrivateKey);
        System.out.println(jwtString);
        System.out.println();
        System.out.println();



        byte[] testEd25519PublicKey = Hex.decodeHex("de8777a28f8da1a74e7a13090ed974d879bf692d001cddee16e4cc9f84b60580".toCharArray());

        String jwt = "eyJhbGciOiJFZERTQSJ9.eyJzdWIiOiJkaWQ6ZXhhbXBsZTplYmZlYjFmNzEyZWJjNmYxYzI3NmUxMmVjMjEiLCJuYmYiOjE1NjA3MTE0MTksImlzcyI6ImRpZDpleGFtcGxlOjc2ZTEyZWM3MTJlYmM2ZjFjMjIxZWJmZWIxZiIsImV4cCI6MTU2MDc5NzgxOSwidmMiOnsiQGNvbnRleHQiOlsiaHR0cHM6Ly93d3cudzMub3JnLzIwMTgvY3JlZGVudGlhbHMvdjEiLCJodHRwczovL3d3dy53My5vcmcvMjAxOC9jcmVkZW50aWFscy9leGFtcGxlcy92MSJdLCJ0eXBlIjpbIlZlcmlmaWFibGVDcmVkZW50aWFsIiwiVW5pdmVyc2l0eURlZ3JlZUNyZWRlbnRpYWwiXSwiY3JlZGVudGlhbFN1YmplY3QiOnsiY29sbGVnZSI6IlRlc3QgVW5pdmVyc2l0eSIsImRlZ3JlZSI6eyJuYW1lIjoiQmFjaGVsb3Igb2YgU2NpZW5jZSBhbmQgQXJ0cyIsInR5cGUiOiJCYWNoZWxvckRlZ3JlZSJ9fX0sImp0aSI6Imh0dHA6Ly9leGFtcGxlLmVkdS9jcmVkZW50aWFscy8zNzMyIn0.GDpCOlxiZ2isBQn151i5Pj2e-kUgkNg_wzxCPAfxLxtdOz4fpDimg81mNw3LsnO0G56AOTvD4SuzSQyj1cP3Bg";
        JwtVerifiableCredential jwtVerifiableCredential1 = JwtVerifiableCredential.fromCompactSerialization(jwt);
        // 验证
        System.out.println(jwtVerifiableCredential1.verify_Ed25519_EdDSA(testEd25519PublicKey));

        String jwtPayload1 = jwtVerifiableCredential1.getPayload().toString();
        String jwtPayloadVerifiableCredential = jwtVerifiableCredential1.getPayloadObject().toJson(true);
        System.out.println(jwtPayload1);
        System.out.println(jwtPayloadVerifiableCredential);

        VerifiableCredential verifiableCredential1 = FromJwtConverter.fromJwtVerifiableCredential(jwtVerifiableCredential1);
        System.out.println(verifiableCredential1.toJson(true));
    }



}
