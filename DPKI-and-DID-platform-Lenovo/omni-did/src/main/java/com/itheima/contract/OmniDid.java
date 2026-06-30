package com.itheima.contract;

import java.math.BigInteger;
import java.util.Arrays;
import java.util.Collections;
import org.web3j.abi.TypeReference;
import org.web3j.abi.datatypes.Function;
import org.web3j.abi.datatypes.Type;
import org.web3j.crypto.Credentials;
import org.web3j.protocol.Web3j;
import org.web3j.protocol.core.RemoteCall;
import org.web3j.protocol.core.methods.response.TransactionReceipt;
import org.web3j.tx.Contract;
import org.web3j.tx.TransactionManager;
import org.web3j.tx.gas.ContractGasProvider;

/**
 * <p>Auto generated code.
 * <p><strong>Do not modify!</strong>
 * <p>Please use the <a href="https://docs.web3j.io/command_line.html">web3j command line tools</a>,
 * or the org.web3j.codegen.SolidityFunctionWrapperGenerator in the 
 * <a href="https://github.com/web3j/web3j/tree/master/codegen">codegen module</a> to update.
 *
 * <p>Generated with web3j version 3.6.0.
 */
public class OmniDid extends Contract {
    private static final String BINARY = "6080604052348015600e575f80fd5b506107428061001c5f395ff3fe608060405234801561000f575f80fd5b5060043610610034575f3560e01c806391ab489914610038578063d43f1d0014610068575b5f80fd5b610052600480360381019061004d91906102ad565b610084565b60405161005f9190610354565b60405180910390f35b610082600480360381019061007d9190610374565b610131565b005b60605f826040516100959190610424565b908152602001604051809103902080546100ae90610467565b80601f01602080910402602001604051908101604052809291908181526020018280546100da90610467565b80156101255780601f106100fc57610100808354040283529160200191610125565b820191905f5260205f20905b81548152906001019060200180831161010857829003601f168201915b50505050509050919050565b805f836040516101419190610424565b9081526020016040518091039020908161015b919061063d565b505050565b5f604051905090565b5f80fd5b5f80fd5b5f80fd5b5f80fd5b5f601f19601f8301169050919050565b7f4e487b71000000000000000000000000000000000000000000000000000000005f52604160045260245ffd5b6101bf82610179565b810181811067ffffffffffffffff821117156101de576101dd610189565b5b80604052505050565b5f6101f0610160565b90506101fc82826101b6565b919050565b5f67ffffffffffffffff82111561021b5761021a610189565b5b61022482610179565b9050602081019050919050565b828183375f83830152505050565b5f61025161024c84610201565b6101e7565b90508281526020810184848401111561026d5761026c610175565b5b610278848285610231565b509392505050565b5f82601f83011261029457610293610171565b5b81356102a484826020860161023f565b91505092915050565b5f602082840312156102c2576102c1610169565b5b5f82013567ffffffffffffffff8111156102df576102de61016d565b5b6102eb84828501610280565b91505092915050565b5f81519050919050565b5f82825260208201905092915050565b8281835e5f83830152505050565b5f610326826102f4565b61033081856102fe565b935061034081856020860161030e565b61034981610179565b840191505092915050565b5f6020820190508181035f83015261036c818461031c565b905092915050565b5f806040838503121561038a57610389610169565b5b5f83013567ffffffffffffffff8111156103a7576103a661016d565b5b6103b385828601610280565b925050602083013567ffffffffffffffff8111156103d4576103d361016d565b5b6103e085828601610280565b9150509250929050565b5f81905092915050565b5f6103fe826102f4565b61040881856103ea565b935061041881856020860161030e565b80840191505092915050565b5f61042f82846103f4565b915081905092915050565b7f4e487b71000000000000000000000000000000000000000000000000000000005f52602260045260245ffd5b5f600282049050600182168061047e57607f821691505b6020821081036104915761049061043a565b5b50919050565b5f819050815f5260205f209050919050565b5f6020601f8301049050919050565b5f82821b905092915050565b5f600883026104f37fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff826104b8565b6104fd86836104b8565b95508019841693508086168417925050509392505050565b5f819050919050565b5f819050919050565b5f61054161053c61053784610515565b61051e565b610515565b9050919050565b5f819050919050565b61055a83610527565b61056e61056682610548565b8484546104c4565b825550505050565b5f90565b610582610576565b61058d818484610551565b505050565b5b818110156105b0576105a55f8261057a565b600181019050610593565b5050565b601f8211156105f5576105c681610497565b6105cf846104a9565b810160208510156105de578190505b6105f26105ea856104a9565b830182610592565b50505b505050565b5f82821c905092915050565b5f6106155f19846008026105fa565b1980831691505092915050565b5f61062d8383610606565b9150826002028217905092915050565b610646826102f4565b67ffffffffffffffff81111561065f5761065e610189565b5b6106698254610467565b6106748282856105b4565b5f60209050601f8311600181146106a5575f8415610693578287015190505b61069d8582610622565b865550610704565b601f1984166106b386610497565b5f5b828110156106da578489015182556001820191506020850194506020810190506106b5565b868310156106f757848901516106f3601f891682610606565b8355505b6001600288020188555050505b50505050505056fea26469706673582212208f57d334c326ff8669582c593dd50edc36c83af76f981b82a2472ffe0b38809564736f6c634300081a0033";

    public static final String FUNC_CREATEORUPDATEDIDDOCUMENT = "createOrUpdateDidDocument";

    public static final String FUNC_GETDIDDOCUMENT = "getDidDocument";

    @Deprecated
    protected OmniDid(String contractAddress, Web3j web3j, Credentials credentials, BigInteger gasPrice, BigInteger gasLimit) {
        super(BINARY, contractAddress, web3j, credentials, gasPrice, gasLimit);
    }

    protected OmniDid(String contractAddress, Web3j web3j, Credentials credentials, ContractGasProvider contractGasProvider) {
        super(BINARY, contractAddress, web3j, credentials, contractGasProvider);
    }

    @Deprecated
    protected OmniDid(String contractAddress, Web3j web3j, TransactionManager transactionManager, BigInteger gasPrice, BigInteger gasLimit) {
        super(BINARY, contractAddress, web3j, transactionManager, gasPrice, gasLimit);
    }

    protected OmniDid(String contractAddress, Web3j web3j, TransactionManager transactionManager, ContractGasProvider contractGasProvider) {
        super(BINARY, contractAddress, web3j, transactionManager, contractGasProvider);
    }

    public RemoteCall<TransactionReceipt> createOrUpdateDidDocument(String _did, String _didDocument) {
        final Function function = new Function(
                FUNC_CREATEORUPDATEDIDDOCUMENT, 
                Arrays.<Type>asList(new org.web3j.abi.datatypes.Utf8String(_did), 
                new org.web3j.abi.datatypes.Utf8String(_didDocument)), 
                Collections.<TypeReference<?>>emptyList());
        return executeRemoteCallTransaction(function);
    }

    public RemoteCall<TransactionReceipt> getDidDocument(String _did) {
        final Function function = new Function(
                FUNC_GETDIDDOCUMENT, 
                Arrays.<Type>asList(new org.web3j.abi.datatypes.Utf8String(_did)), 
                Collections.<TypeReference<?>>emptyList());
        return executeRemoteCallTransaction(function);
    }

    public static RemoteCall<OmniDid> deploy(Web3j web3j, Credentials credentials, ContractGasProvider contractGasProvider) {
        return deployRemoteCall(OmniDid.class, web3j, credentials, contractGasProvider, BINARY, "");
    }

    @Deprecated
    public static RemoteCall<OmniDid> deploy(Web3j web3j, Credentials credentials, BigInteger gasPrice, BigInteger gasLimit) {
        return deployRemoteCall(OmniDid.class, web3j, credentials, gasPrice, gasLimit, BINARY, "");
    }

    public static RemoteCall<OmniDid> deploy(Web3j web3j, TransactionManager transactionManager, ContractGasProvider contractGasProvider) {
        return deployRemoteCall(OmniDid.class, web3j, transactionManager, contractGasProvider, BINARY, "");
    }

    @Deprecated
    public static RemoteCall<OmniDid> deploy(Web3j web3j, TransactionManager transactionManager, BigInteger gasPrice, BigInteger gasLimit) {
        return deployRemoteCall(OmniDid.class, web3j, transactionManager, gasPrice, gasLimit, BINARY, "");
    }

    @Deprecated
    public static OmniDid load(String contractAddress, Web3j web3j, Credentials credentials, BigInteger gasPrice, BigInteger gasLimit) {
        return new OmniDid(contractAddress, web3j, credentials, gasPrice, gasLimit);
    }

    @Deprecated
    public static OmniDid load(String contractAddress, Web3j web3j, TransactionManager transactionManager, BigInteger gasPrice, BigInteger gasLimit) {
        return new OmniDid(contractAddress, web3j, transactionManager, gasPrice, gasLimit);
    }

    public static OmniDid load(String contractAddress, Web3j web3j, Credentials credentials, ContractGasProvider contractGasProvider) {
        return new OmniDid(contractAddress, web3j, credentials, contractGasProvider);
    }

    public static OmniDid load(String contractAddress, Web3j web3j, TransactionManager transactionManager, ContractGasProvider contractGasProvider) {
        return new OmniDid(contractAddress, web3j, transactionManager, contractGasProvider);
    }
}
