package com.itheima.service;

import com.danubetech.verifiablecredentials.CredentialSubject;
import com.danubetech.verifiablecredentials.VerifiableCredential;
import com.danubetech.verifiablecredentials.credentialstatus.CredentialStatus;
import com.danubetech.verifiablecredentials.jwt.FromJwtConverter;
import com.danubetech.verifiablecredentials.jwt.JwtVerifiableCredential;
import com.danubetech.verifiablecredentials.jwt.ToJwtConverter;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.nimbusds.jose.JOSEException;
import info.weboftrust.ldsignatures.LdProof;
import lombok.extern.slf4j.Slf4j;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.apache.commons.codec.DecoderException;
import org.apache.commons.codec.binary.Hex;
import org.springframework.stereotype.Service;


import java.io.File;
import java.io.IOException;
import java.net.URI;
import java.text.ParseException;
import java.util.Calendar;
import java.util.Date;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * ClassName: VcService
 * Package: com.itheima.service
 * Description:
 *
 * @Create 2024/12/25 14:43
 */

@Service
public class VcService {

    private static final Logger log = LoggerFactory.getLogger(VcService.class);

    public String  createAttributeCredential(String did, String operatorPermission, String enabled) throws DecoderException, JOSEException {
        Map<String, Object> claims = new LinkedHashMap<>();
        Map<String, Object> degree = new LinkedHashMap<>();

        claims.put("organization", "PLMNa");
//        claims.put("organization", "PLMNa");

        degree.put("operator permission", operatorPermission);
        degree.put("enabled", enabled);
        claims.put("cross network access", degree);
//        degree.put("name", "Bachelor of Science and Arts");
//        degree.put("type", "BachelorDegree");
//        claims.put("college", "Test University");
//        claims.put("degree", degree);

        CredentialSubject credentialSubject = CredentialSubject.builder()
                .id(URI.create(did))
                .claims(claims)
                .build();



        Date currentDate=new Date();
        Calendar calendar = Calendar.getInstance();
        calendar.setTime(currentDate);
        calendar.add(Calendar.YEAR, 2);
        // 获取两年后的时间
        Date dateTwoYearsLater = calendar.getTime();

        LdProof ldProof=LdProof.builder()
                .type("ServiceAccessCredential")
                .creator(URI.create("did:omni:76e12ec712ebc6f1c221ebfeb1f"))
                .created(currentDate)
                .jws("eyJhbGciOiJFZERTQSIsImI2NCI6ZmFsc2UsImNyaXQiOlsiYjY0Il19g5l7d5W7r4g4h6G7j6Z")
                .build();

        VerifiableCredential verifiableCredential = VerifiableCredential.builder()
//                .context(VerifiableCredentialContexts.JSONLD_CONTEXT_W3C_2018_CREDENTIALS_EXAMPLES_V1)
                .context(URI.create("https://www.w3.org/ns/credentials/v2"))
                .type("ServiceAccessCredential")
//                .id(URI.create("http://example.edu/credentials/3732"))
                .id(URI.create("https:://w3id.org/citizenship/v3"))

                .issuer(URI.create("did:omni:76e12ec712ebc6f1c221ebfeb1f"))
//                .issuanceDate(JsonLDUtils.stringToDate("2019-06-16T18:56:59Z"))
                .issuanceDate(currentDate)
                .expirationDate(dateTwoYearsLater)
                .credentialSubject(credentialSubject)
                .ldProof(ldProof)
                .build();

        ObjectMapper objectMapper = new ObjectMapper();

        try {
            // 指定要保存的文件路径，使用 .jsonld 扩展名
            File file = new File("verifiable_credential.jsonld");

            // 将 JSON-LD 对象写入文件，使用美化输出
            objectMapper.writerWithDefaultPrettyPrinter().writeValue(file, verifiableCredential);

            log.info("The JSON - LD object has been successfully saved to the file: {}",file.getAbsolutePath());
        } catch (IOException e) {
            log.info("An error occurred while saving the JSON - LD object to the file: {}" ,e.getMessage());
        }

        byte[] testEd25519PrivateKey = Hex.decodeHex("984b589e121040156838303f107e13150be4a80fc5088ccba0b0bdc9b1d89090de8777a28f8da1a74e7a13090ed974d879bf692d001cddee16e4cc9f84b60580".toCharArray());

        JwtVerifiableCredential jwtVerifiableCredential = ToJwtConverter.toJwtVerifiableCredential(verifiableCredential);

//        String jwtPayload = jwtVerifiableCredential.getPayload().toString();
//        System.out.println(claims);
//        System.out.println(jwtPayload);

        String jwtString = jwtVerifiableCredential.sign_Ed25519_EdDSA(testEd25519PrivateKey);
        return  jwtString;
    }

    public boolean verifyCredential(String jwtString) throws DecoderException {
        return verify(jwtString);
    }

    public boolean verify(String jwtString) throws DecoderException {
        byte[] testEd25519PublicKey = Hex.decodeHex("de8777a28f8da1a74e7a13090ed974d879bf692d001cddee16e4cc9f84b60580".toCharArray());

        JwtVerifiableCredential jwtVerifiableCredential = null;
        try {
            jwtVerifiableCredential = JwtVerifiableCredential.fromCompactSerialization(jwtString);
        } catch (ParseException e) {
            log.info("verify result: false");
            return false;
        }

        boolean res=false;


        // 验证
        try {
            res=jwtVerifiableCredential.verify_Ed25519_EdDSA(testEd25519PublicKey);
        } catch (JOSEException e) {
            log.info("verify result: false");
            return false;
        }
        log.info("verify result:{}",res);
        return res;
    }


    public Object getCredential(String jwtString) throws DecoderException, ParseException {
        boolean verifyResult=verify(jwtString);
        if(verifyResult==false){
            return "wrong jwt!";
        }
        JwtVerifiableCredential jwtVerifiableCredential = JwtVerifiableCredential.fromCompactSerialization(jwtString);
        String jwtPayloadVerifiableCredential = jwtVerifiableCredential.getPayloadObject().toJson(true);

        VerifiableCredential verifiableCredential = FromJwtConverter.fromJwtVerifiableCredential(jwtVerifiableCredential);
        return verifiableCredential;

    }
}
