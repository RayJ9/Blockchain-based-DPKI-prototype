package com.itheima.controller;

import com.fasterxml.jackson.databind.JsonNode;
import com.itheima.pojo.Result;
import com.itheima.service.DidService;
import lombok.extern.slf4j.Slf4j;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.web3j.protocol.exceptions.TransactionException;

import java.io.IOException;
import java.net.URI;
import java.util.concurrent.ExecutionException;

/**
 * did Controller
 */
@RequestMapping("/did")
@RestController
public class DidController {

    private static final Logger log = LoggerFactory.getLogger(DidController.class);

    @Autowired
    private DidService didService;

    /**
     * 生成did
     * @return
     */
    //@RequestMapping(value = "/depts",method = RequestMethod.GET) //指定请求方式为GET
    @GetMapping
    public Result createDid() {
        long startTime = System.currentTimeMillis();
        log.info("Create DID request received");

        try {
            URI did = didService.createDid();
            return Result.success(did);
        } catch (Exception e) {
            log.error("Failed to create DID", e);
            return Result.error("Failed to create DID: " + e.getMessage());
        } finally {
            long duration = System.currentTimeMillis() - startTime;
            log.info("create DID delay: {}ms", duration);
        }
    }


    /**
     * 获取did文档
     * @return
     */
    @GetMapping("/{did}")
    public Result getDidDocument(@PathVariable URI did) throws IOException {
//        log.info("Query DID documents on omnichain, {}",did);
//
//        JsonNode diddoc= didService.getDidDocument(did);
//        return Result.success(diddoc);
        long startTime = System.currentTimeMillis();
        log.info("Query DID Documents on omnichain, {}", did);

        try {
            JsonNode diddoc = didService.getDidDocument(did);
            return Result.success(diddoc);
        } finally {
            long duration = System.currentTimeMillis() - startTime;
            log.info("Get DID Document delay | did={} | {}ms", did, duration);
        }
    }


}
