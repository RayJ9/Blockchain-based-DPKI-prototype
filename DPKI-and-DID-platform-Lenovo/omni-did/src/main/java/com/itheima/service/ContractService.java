package com.itheima.service;

import com.google.gson.Gson;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import lombok.extern.slf4j.Slf4j;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.web3j.abi.FunctionEncoder;
import org.web3j.abi.FunctionReturnDecoder;
import org.web3j.abi.TypeReference;
import org.web3j.abi.datatypes.Function;
import org.web3j.abi.datatypes.Type;
import org.web3j.abi.datatypes.Utf8String;
import org.web3j.crypto.Credentials;
import org.web3j.crypto.RawTransaction;
import org.web3j.crypto.TransactionEncoder;
import org.web3j.protocol.Web3j;
import org.web3j.protocol.core.DefaultBlockParameterName;
import org.web3j.protocol.core.methods.request.Transaction;
import org.web3j.protocol.core.methods.response.*;
import org.web3j.protocol.exceptions.TransactionException;
import org.web3j.protocol.http.HttpService;
import org.web3j.tx.response.PollingTransactionReceiptProcessor;
import org.web3j.tx.response.TransactionReceiptProcessor;
import org.web3j.utils.Convert;
import org.web3j.utils.Numeric;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Arrays;
import java.util.Collections;
import java.util.Optional;
import java.util.concurrent.ExecutionException;

/**
 * ClassName: ContractService
 * Package: com.itheima.service
 * Description:
 *
 * @Create 2025/2/10 19:14
 */
@Service
public class ContractService {
    
    private static final Logger log = LoggerFactory.getLogger(ContractService.class);
    
    @Value("${contract.address}")
    private String contractAddress;

    @Value("${blockchain.provider.url}")
    private String blockchainProviderUrl;

    @Value("${blockchain.private.key}")
    private String blockchainPrivateKey;

    public void createOrUpdateDidDocument(String did, String didDocument)
            throws IOException, InterruptedException, ExecutionException, TransactionException {

        Web3j web3 = Web3j.build(new HttpService(blockchainProviderUrl));

        // 加载部署合约所需的凭证，用私钥
        Credentials credentials = Credentials.create(blockchainPrivateKey);

        // 获取chainid
        BigInteger chainId = web3.ethChainId().send().getChainId();

        //String contractAddress = "0x9182f3d5cddb7521cdda844591e9f565de830d2e";

        uploadDidDocument(web3, credentials, contractAddress, chainId, did, didDocument);

    }


    private static void uploadDidDocument(Web3j web3, Credentials credentials, String contractAddress, BigInteger chainId, String did, String didDocument)
            throws IOException, InterruptedException, ExecutionException, TransactionException {
        // 获取nonce，交易笔数
        BigInteger nonce = web3
                .ethGetTransactionCount(credentials.getAddress(), DefaultBlockParameterName.LATEST)
                .send().getTransactionCount();
        // 手续费
        EthGasPrice ethGasPrice = web3.ethGasPrice().sendAsync().get();
        BigInteger gasPrice = ethGasPrice.getGasPrice();
        BigInteger gasLimit = BigInteger.valueOf(500000L);
        // 合约参数
        Function function = new Function("createOrUpdateDidDocument",
                Arrays.asList(new Utf8String(did), new Utf8String(didDocument)),
                Collections.emptyList());
        // 创建合约交易对象
        String encodedFunction = FunctionEncoder.encode(function);
        RawTransaction rawTransaction = RawTransaction.createTransaction(nonce, gasPrice, gasLimit, contractAddress,
                encodedFunction);
        // 签名Transaction，这里要对交易做签名
        byte[] signMessage = TransactionEncoder.signMessage(rawTransaction, chainId.longValue(), credentials);
        String hexValue = Numeric.toHexString(signMessage);
        // 发送交易
        EthSendTransaction ethSendTransaction = web3.ethSendRawTransaction(hexValue).sendAsync().get();
        Gson gson = new Gson();
        String tx = gson.toJson(ethSendTransaction);
        JsonObject jo = JsonParser.parseString(tx).getAsJsonObject();
        String txHash = jo.get("result").getAsString();
        log.info("transaction hash value :{}",txHash);
        // 等待交易确认
        // 使用轮询处理器等待交易回执
        TransactionReceiptProcessor receiptProcessor = new PollingTransactionReceiptProcessor(
                web3,
                50, // 轮询间隔50ms
                40    // 最多尝试40次（总超时2秒）
        );

        // 等待直到获得回执或超时
        TransactionReceipt receipt;
        try {
            receipt = receiptProcessor.waitForTransactionReceipt(txHash);
        } catch (IOException e) {
            throw new RuntimeException("Failed to get transaction receipt", e);
        }

        // 检查交易是否成功
        if (!receipt.isStatusOK()) {
            throw new RuntimeException("Transaction failed: " + txHash);
        }

        log.info("Transaction confirmed in block: {}", receipt.getBlockNumber());
    }


    public String getDidDocument(String did) throws IOException {
        Web3j web3 = Web3j.build(new HttpService(blockchainProviderUrl));

        // 加载部署合约所需的凭证，用私钥
        Credentials credentials = Credentials.create(blockchainPrivateKey);

        // 获取chainid
        BigInteger chainId = web3.ethChainId().send().getChainId();

        //String contractAddress = "0x9182f3d5cddb7521cdda844591e9f565de830d2e";

        String didDocument = callContract(web3, credentials, contractAddress, did);
        return didDocument;
    }

    private static String callContract(Web3j web3, Credentials credentials, String contractAddress, String did)
            throws IOException {
        // 合约参数
        Function function = new Function(
                "getDidDocument",
                Arrays.asList(new Utf8String(did)),
                Collections.singletonList(new TypeReference<Utf8String>() {})
        );
        // 编码函数调用
        String encodedFunction = FunctionEncoder.encode(function);
        // 创建调用请求
        Transaction transaction = Transaction.createEthCallTransaction(
                credentials.getAddress(),
                contractAddress,
                encodedFunction
        );
        // 发送调用请求
        EthCall ethCall = web3.ethCall(transaction, DefaultBlockParameterName.LATEST).send();
        // 解码返回值
        java.util.List<Type> decoded = FunctionReturnDecoder.decode(
                ethCall.getValue(),
                function.getOutputParameters()
        );
        if (!decoded.isEmpty()) {
            Utf8String result = (Utf8String) decoded.get(0);
            return result.getValue();
        }
        return null;
    }


}
