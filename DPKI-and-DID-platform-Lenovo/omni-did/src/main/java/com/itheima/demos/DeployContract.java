package com.itheima.demos;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.security.InvalidAlgorithmParameterException;
import java.security.NoSuchAlgorithmException;
import java.security.NoSuchProviderException;
import java.util.Arrays;
import java.util.Collections;
import java.util.Optional;
import java.util.concurrent.ExecutionException;

import org.web3j.abi.FunctionEncoder;
import org.web3j.abi.FunctionReturnDecoder;
import org.web3j.abi.TypeReference;
import org.web3j.abi.datatypes.Address;
import org.web3j.abi.datatypes.Function;
import org.web3j.abi.datatypes.Type;
import org.web3j.abi.datatypes.Utf8String;
import org.web3j.abi.datatypes.generated.Uint256;
import org.web3j.crypto.Credentials;
import org.web3j.crypto.RawTransaction;
import org.web3j.crypto.TransactionEncoder;
import org.web3j.protocol.Web3j;
import org.web3j.protocol.core.DefaultBlockParameterName;
import org.web3j.protocol.core.methods.request.Transaction;
import org.web3j.protocol.core.methods.response.EthCall;
import org.web3j.protocol.core.methods.response.EthGasPrice;
import org.web3j.protocol.core.methods.response.EthGetTransactionReceipt;
import org.web3j.protocol.core.methods.response.EthSendTransaction;
import org.web3j.protocol.core.methods.response.TransactionReceipt;
import org.web3j.protocol.http.HttpService;
import org.web3j.utils.Convert;
import org.web3j.utils.Numeric;

import com.google.gson.Gson;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

/**
 * 部署和调用合约
 *
 */
public class DeployContract {
    public static void main(String[] args) throws IOException, InterruptedException, ExecutionException {

        // 读取合约二进制代码
        Path binPath = Paths.get(
                System.getProperty("user.dir"),
                "src/main/resources/OmniDid.code"
        );
        String contractBin = Files.readString(binPath, StandardCharsets.UTF_8);

        // 部署智能合约
        Web3j web3 = Web3j.build(new HttpService("http://192.168.5.23:8545"));

        // 加载部署合约所需的凭证，用私钥
        Credentials credentials = Credentials
                .create("0x73e66f099144f820753aa3a5e131785b528081da572e16339fcd02de05de719e");

        // 获取chainid
        BigInteger chainId = web3.ethChainId().send().getChainId();
        System.out.println("chainId:"+chainId);

        // 部署合约
        String txHash = deployContract(web3, credentials, contractBin, chainId);


        // 等待交易确认
        Thread.sleep(5000);

        // 从交易回执行获取合约地址
        String contractAddress = getContractAddress(web3, txHash);
        // String contractAddress = "0x9182f3d5cddb7521cdda844591e9f565de830d2e";
        // 调用合约
        // DID和DID文档
        String did = "did:example:123";
        String didDocument = "{\"@context\": \"https://www.w3.org/ns/did/v1\", \"id\": \"did:example:123\"}";
        // 调用合约
        callContract(web3, credentials, contractAddress, chainId, did, didDocument);
        // 等待交易确认
        //Thread.sleep(10000);
        String didDocument1 = callContract(web3, credentials, contractAddress, did);
        System.out.println("DID Document: " + didDocument1);

        // 查询账户下NFT数量和uri等信息
        //queryNFTInfo(web3, contractAddress, tokenId);
    }

    /**
     * 部署合约
     *
     //      * @return
     //      * @throws IOException
     //      * @throws ExecutionException
     //      * @throws InterruptedException
     //      */
    private static String deployContract(Web3j web3, Credentials credentials, String contractBin, BigInteger chainId)
            throws IOException, InterruptedException, ExecutionException {

        BigInteger nonce = web3
                .ethGetTransactionCount("0xab7F5238cbEfB02062241cf979e4994b656FB944", DefaultBlockParameterName.LATEST)
                .send().getTransactionCount();

        EthGasPrice ethGasPrice = web3.ethGasPrice().sendAsync().get();
        BigInteger gasPrice = ethGasPrice.getGasPrice();
        BigInteger gasLimit = BigInteger.valueOf(5000000L);

        String encodedConstructor = FunctionEncoder
                .encodeConstructor(Arrays.asList(new org.web3j.abi.datatypes.Utf8String("init ERC1155")));
        BigInteger value = Convert.toWei("0", Convert.Unit.ETHER).toBigInteger();

        RawTransaction rawTransaction = RawTransaction.createContractTransaction(nonce, gasPrice, gasLimit, value,
                contractBin + encodedConstructor);

        byte[] signMessage = TransactionEncoder.signMessage(rawTransaction, chainId.longValue(), credentials);
        String hexValue = Numeric.toHexString(signMessage);

        EthSendTransaction ethSendTransaction = web3.ethSendRawTransaction(hexValue).sendAsync().get();
        Gson gson = new Gson();
        String tx = gson.toJson(ethSendTransaction);
        JsonObject jo = JsonParser.parseString(tx).getAsJsonObject();
        String txHash = jo.get("result").getAsString();
        System.out.println("部署合约交易hash值:" + txHash);
        return txHash;
    }

    /**
     * 根据交易hash获取合约地址
     *
     * @param txHash
     * @return
     * @throws IOException
     * @throws InterruptedException
     * @throws ExecutionException
     */
    private static String getContractAddress(Web3j web3, String txHash)
            throws InterruptedException, ExecutionException {
        // 根据hash获取合约地址
        EthGetTransactionReceipt transaction = web3.ethGetTransactionReceipt(txHash).sendAsync().get();
        Optional<TransactionReceipt> optionalTransaction = transaction.getTransactionReceipt();
        TransactionReceipt transactionInfo = new TransactionReceipt();
        if (optionalTransaction.isPresent()) {
            transactionInfo = optionalTransaction.get();
        }
        String contractAddress = transactionInfo.getContractAddress();
        System.out.println("contract address:" + contractAddress + "\r\n");
        return contractAddress;
    }

    /**
     * 调用合约
     *
     * @param web3
     * @param credentials
     * @param contractAddress
     * @param chainId

     * @throws IOException
     * @throws InterruptedException
     * @throws ExecutionException
     */

    private static void callContract(Web3j web3, Credentials credentials, String contractAddress, BigInteger chainId, String did, String didDocument)
            throws IOException, InterruptedException, ExecutionException {
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
        System.out.println("调用合约交易hash值:" + txHash);
        // 等待交易确认
        Thread.sleep(5000);
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