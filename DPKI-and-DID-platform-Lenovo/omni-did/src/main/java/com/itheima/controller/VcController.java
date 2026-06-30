package com.itheima.controller;

import com.danubetech.verifiablecredentials.VerifiableCredential;
import com.itheima.pojo.PageBean;
import com.itheima.pojo.Result;

import com.itheima.service.VcService;
import com.nimbusds.jose.JOSEException;
import foundation.identity.jsonld.JsonLDException;
import lombok.extern.slf4j.Slf4j;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.apache.commons.codec.DecoderException;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.io.IOException;
import java.security.GeneralSecurityException;
import java.text.ParseException;


/**
 * vc Controller
 */
@RestController
@RequestMapping("/vc")
public class VcController {

    private static final Logger log = LoggerFactory.getLogger(VcController.class);

    @Autowired
    private VcService vcService;

    /**
     * 创建User Attribute vc
     * @return
     */
    @GetMapping("/user-attribute")
    public Result createAttributeCredential(@RequestParam String did,
                       @RequestParam String operatorPermission,@RequestParam String enabled) throws DecoderException, JOSEException {
//        log.info("create User Attribute vc: {},{}",did,operatorPermission,enabled);
//
//
//        String jwtString = vcService.createAttributeCredential(did,operatorPermission,enabled);
//        return Result.success(jwtString);
        long startTime = System.currentTimeMillis();
        log.info("Create User Attribute VC | did={} | op={} | enabled={}",
                did, operatorPermission, enabled);

        try {
            String jwtString = vcService.createAttributeCredential(did, operatorPermission, enabled);
            return Result.success(jwtString);
        } finally {
            long duration = System.currentTimeMillis() - startTime;
            log.info("create Credential delay: {}ms", duration);
        }
    }

    /**
     * 验证vc
     * @return
     */
    @GetMapping("/verify-jwt")
    public Result verifyCredential(@RequestParam String jwtString) throws DecoderException {
        log.info("verify vc:{}",jwtString);
        return Result.success(vcService.verifyCredential(jwtString));
    }

    /**
     * 获取vc内容
     */
    @GetMapping("/get-credential")
    public Result getCredential(@RequestParam String jwtString) throws DecoderException, ParseException {
//        log.info("Obtain VC content: {}",jwtString);
//        Object jwtPayloadVerifiableCredential=vcService.getCredential(jwtString);
//        return Result.success(jwtPayloadVerifiableCredential);
        long startTime = System.currentTimeMillis();
        log.info("Obtain VC content: {}", jwtString);

        try {
            Object jwtPayloadVerifiableCredential = vcService.getCredential(jwtString);
            return Result.success(jwtPayloadVerifiableCredential); // 注意修正变量名拼写错误
        } finally {
            long duration = System.currentTimeMillis() - startTime;
            log.info("Obtain VC content delay {}ms", duration);
        }
    }

    /**
     * 解析vc内容 (前端调用的接口)
     */
    @GetMapping("/parse")
    public Result parseCredential(@RequestParam String jwtString) throws DecoderException, ParseException {
        long startTime = System.currentTimeMillis();
        log.info("Parse VC content: {}", jwtString);

        try {
            Object jwtPayloadVerifiableCredential = vcService.getCredential(jwtString);
            return Result.success(jwtPayloadVerifiableCredential);
        } finally {
            long duration = System.currentTimeMillis() - startTime;
            log.info("Parse VC content delay {}ms", duration);
        }
    }
}
