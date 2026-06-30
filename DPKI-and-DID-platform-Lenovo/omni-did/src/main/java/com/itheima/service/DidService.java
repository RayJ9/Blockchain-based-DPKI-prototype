package com.itheima.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.type.ResolvedRecursiveType;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import foundation.identity.did.DIDDocument;
import foundation.identity.did.VerificationMethod;
import lombok.extern.slf4j.Slf4j;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.web3j.protocol.exceptions.TransactionException;

import java.io.IOException;
import java.net.URI;
import java.util.*;
import java.util.concurrent.ExecutionException;

/**
 * ClassName: DidService
 * Package: com.itheima.service
 * Description:
 *
 * @Create 2024/12/25 14:43
 */
@Service
public class DidService {

    private static final Logger log = LoggerFactory.getLogger(DidService.class);

    @Autowired
    private ContractService contractService;

    public URI createDid() throws IOException, ExecutionException, InterruptedException, TransactionException {
        // 生成did
        URI did = generateDid();
        log.info("new did created:{}",did);
        // 生成did文档
        DIDDocument didDoc=generateDidDocument(did);

        String entityDidDoc=generateEntityDidDocument(didDoc);

        log.info("new did document generated");
        // did and didDoc上链
        contractService.createOrUpdateDidDocument(did.toString(),entityDidDoc);
        return did;
    }

    private String generateEntityDidDocument(DIDDocument didDoc) {
        String originalJson = didDoc.toString();
        try {
            ObjectMapper mapper = new ObjectMapper();
            JsonNode rootNode = mapper.readTree(originalJson);

            // 将 JsonNode 转换为 LinkedHashMap 以保持顺序
            LinkedHashMap<String, Object> map = mapper.convertValue(rootNode, LinkedHashMap.class);

            // 在 "id" 字段之后插入新字段
            LinkedHashMap<String, Object> newMap = new LinkedHashMap<>();
            for (Map.Entry<String, Object> entry : map.entrySet()) {
                newMap.put(entry.getKey(), entry.getValue());
                if ("id".equals(entry.getKey())) {
                    newMap.put("entityType", "individual user");
                    newMap.put("device", "User equipment/IoT device");

                    // 创建 entityAssociationIdentifiers 数组
                    List<Map<String, String>> entityAssociationIdentifiers = new ArrayList<>();
                    Map<String, String> identifier = new HashMap<>();
                    // 这里的 ... 部分需要你根据实际情况填充
                    identifier.put("Username", "exampleUsername");
                    identifier.put("User equipment identifier", "exampleIdentifier");
                    entityAssociationIdentifiers.add(identifier);
                    newMap.put("entityAssociationIdentifiers", entityAssociationIdentifiers);
                }
            }

            // 将 LinkedHashMap 转换回 JsonNode
            rootNode = mapper.valueToTree(newMap);

            String newJson = mapper.writerWithDefaultPrettyPrinter().writeValueAsString(rootNode);
            return newJson;
        } catch (IOException e) {
            e.printStackTrace();
        }
        return "something wrong when generateEntityDidDocument";
    }

    public static URI generateDid() {
        UUID uuid = UUID.randomUUID();
        String uuidStr = uuid.toString().replace("-", "");
        // 截取前面18位
        uuidStr = uuidStr.substring(0, 18);
        // 将可能存在的大写字母转为小写字母
        uuidStr = uuidStr.toLowerCase();
        String didString="did:omni:"+uuidStr;
        URI did = URI.create(didString);
        return did;
    }
    DIDDocument generateDidDocument(URI did){

        foundation.identity.did.Service service = foundation.identity.did.Service.builder()
                .type("ServiceEndpointProxyService")
                .serviceEndpoint("https://myservice.com/myendpoint")
                .build();

        VerificationMethod verificationMethod = VerificationMethod.builder()
                .controller(did)
                .id(URI.create(did + "#key-1"))
                .type("Ed25519VerificationKey2018")
                .publicKeyBase58("FyfKP2HvTKqDZQzvyL38yXH7bExmwofxHf2NR5BrcGf1")
                .build();

        DIDDocument diddoc = DIDDocument.builder()
                .id(did)
                .service(service)
                .verificationMethod(verificationMethod)
                .build();
        return diddoc;
    }

    public JsonNode getDidDocument(URI did) throws IOException {
        // 链上查询获取did文档
        String didDocument= contractService.getDidDocument(did.toString());
        ObjectMapper objectMapper = new ObjectMapper();
        // 将 JSON 字符串转换为 JsonNode 对象
        JsonNode jsonNode = objectMapper.readTree(didDocument);

        return jsonNode;

    }
}
