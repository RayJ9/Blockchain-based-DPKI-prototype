class LanguageManager {
    constructor() {
        // 从localStorage获取保存的语言设置，默认为中文
        this.currentLanguage = localStorage.getItem('selectedLanguage') || 'zh';
        this.translations = {
            'zh': {
                // 导航栏
                'platform_title': 'DPKI管理平台',
                'nav_home': '首页',
                'nav_ca': 'CA管理',
                'nav_ue': 'UE管理',
                'nav_did': 'DID平台',
                
                // 页面标题
                'home_title': 'DPKI管理平台 - 分布式公钥基础设施管理系统',
                'welcome_title': '欢迎使用DPKI平台',
                'welcome_desc': '基于区块链的分布式公钥基础设施管理系统，提供安全可靠的数字证书管理和身份认证服务。',
                'page_title_index': 'DPKI管理平台',
                'page_title_ca': 'CA管理 - DPKI平台',
                'page_title_ue': 'UE管理 - DPKI平台',
                'page_title_did': 'DID平台 - DPKI平台',
                
                // 按钮文本
                'generate_did': '生成新DID',
                'query_did': '查询DID文档',
                'issue_vc': '签发VC',
                'parse_verify_vc': '解析验证VC',
                'revoke_vc': '撤销VC',
                'copy_did': '复制DID',
                'copy_vc': '复制VC',
                'generate_did_button': '生成新DID',
                'copy_button': '复制',
                'query_did_button': '查询文档',
                'generate_vc_button': '签发VC',
                'parse_verify_vc_button': '解析验证VC',
                'revoke_vc_button': '撤销VC',
                
                // 标签文本
                'did_generation': 'DID生成',
                'did_query': 'DID文档查询',
                'vc_issuance': 'VC签发',
                'vc_display': 'VC展示',
                'vc_parse_verify': 'VC解析验证',
                'vc_revoke': 'VC撤销',
                'input_did': '输入DID：',
                'did_label': 'DID：',
                'operator_permission': '操作员权限：',
                'vc_jwt_label': 'VC JWT：',
                'revoke_vc_jwt': '要撤销的VC JWT：',
                'did_generation_title': '🆔 DID生成',
                'did_query_title': '🔍 DID文档查询',
                'vc_generation_title': '📜 可验证凭证(VC)签发',
                'vc_verification_title': '🔐 VC解析验证',
                'vc_revocation_title': '🚫 VC撤销管理',
                
                // 占位符文本
                'did_query_placeholder': '请输入要查询的DID',
                'vc_did_placeholder': '请输入DID',
                'vc_jwt_placeholder': '请粘贴VC JWT字符串',
                'vc_jwt_revoke_placeholder': '请粘贴要撤销的VC JWT字符串',
                'vc_generation_result_placeholder': 'VC将在此处显示',
                'ca_name_placeholder': 'CA名称/标签',
                'ue_name_placeholder': 'UE名称',
                
                // 结果和状态
                'no_did_data': '暂无DID数据',
                'generate_did_vc_first': '请先生成DID和VC',
                'no_associated_vc': '暂无关联的VC',
                'cert_revoke_success': '证书撤销成功',
                'ue_auth_success': 'UE认证成功 - 验证通过',
                'ue_auth_failed': 'UE认证失败 - 未找到成功验证信息',
                'auth_result_success': '认证结果: 成功',
                'auth_result_failed': '认证结果: 失败',
                'cert_update_success': '证书更新成功: {0}',
                'revoked': '已撤销',
                'success': '成功',
                'failed': '失败',
                'verification failed': '验证失败',
                'csr_request_success_msg': 'CSR请求成功！\n{0}',
                'csr_request_failed_msg': 'CSR请求失败！\n{0}',
                'auth_success_verification_passed': 'UE认证成功 - 验证通过',
                'auth_failed_no_success_info': 'UE认证失败 - 未找到成功验证信息',
                'please_fill_ue_name_error': '请填写UE名称',
                'please_fill_ca_name_error': '请填写CA名称',
                'please_fill_ca_ue_name_error': '请填写CA名称和UE名称',
                'auth_result_label': '认证结果',
                'address_list_update_success_msg': '地址列表更新成功: {0}',
                'did_must_contain_omni': 'DID invalid',
                
                // DID platform title
                'did_platform_title': '去中心化身份管理平台',
                
                // 日志消息
                'messages': {
                    'log_messages': {
                        'ca_init_success': 'CA证书初始化成功: {0}',
                        'ca_init_failed': 'CA证书初始化失败: {0}',
                        'cert_register_success': '证书注册成功: {0}',
                        'cert_register_failed': '证书注册失败: {0}',
                        'cert_revoke_success': '证书撤销成功: {0}',
                        'cert_revoke_failed': '证书撤销失败: {0}',
                        'cert_sign_success': '证书签署成功: {0}',
                        'cert_sign_failed': '证书签署失败: {0}',
                        'cert_update_success': '证书更新成功: {0}',
                        'cert_update_failed': '证书更新失败: {0}',
                        'ue_auth_success': 'UE认证成功 - 验证通过',
                        'ue_auth_failed': 'UE认证失败 - 未找到成功验证信息',
                        'csr_request_success': 'CSR请求发送成功: {0}',
                        'csr_request_failed': 'CSR请求失败: {0}',
                        'auth_request_success': '认证请求成功: {0} -> {1}',
                        'auth_request_failed': '认证请求失败: {0}',
                        'ue_address_update_success': 'UE地址列表更新成功',
                        'ue_address_update_failed': 'UE地址列表更新失败: {0}',
                        'api_request_failed': 'API请求失败: {0}',
                        'csr_success_received': 'CSR请求成功 - CSR已被接收',
                        'csr_failed_not_received': 'CSR请求失败 - 未检测到CSR received',
                        'server_start_failed': '启动{0}服务器失败: {1}',
                        'server_stop_failed': '停止{0}服务器失败: {1}',
                        'server_starting': '正在启动 {0} 服务器...',
                        'server_stopping': '正在停止 {0} 服务器...',
                        'server_stopped': '{0} 服务器已停止',
                        'ca_initializing': '正在初始化CA证书: {0}',
                        'cert_signing': '正在签署证书: CA={0}, UE={1}',
                        'cert_updating': '正在更新证书: CA={0}, UE={1}',
                        'cert_revoking': '正在撤销证书: {0}',
                        'csr_requesting': '正在发起CSR请求: {0}',
                        'ue_address_updating': '正在更新UE地址列表...',
                        'auth_requesting': '正在发起认证请求: {0} -> {1}',
                        'csr_success_received': 'CSR请求成功 - CSR已被接收',
                        'csr_failed_not_received': 'CSR请求失败 - 未检测到CSR received',
                        'please_fill_ca_name': '请填写CA名称',
                        'please_fill_ca_ue_name': '请填写CA名称和UE名称',
                        'please_fill_ue_name': '请填写UE名称',
                        'please_fill_ca_name_label': '请填写CA名称和标签',
                        'please_fill_revoke_ue_name': '请填写要撤销的UE名称',
                        'please_fill_local_target_ue': '请填写本地UE名称和目标UE名称',
                        'ca_page_loaded': 'CA管理页面已加载',
                        'ue_page_loaded': 'UE管理页面已加载'
                    }
                },
                
                // DID/VC相关
                'did_vc_relationship_title': '📊 DID/VC 关系展示',
                'vc_did_label': 'DID：',
                'vc_permission_label': '操作权限：',
                'permission_read': '读取',
                'permission_write': '写入',
                'permission_admin': '管理员',
                'vc_jwt_label': 'VC JWT：',
                'revoke_vc_jwt': '要撤销的VC JWT：',
                
                // 首页卡片
                'dpki_platform_card_title': 'DPKI平台',
                'dpki_platform_card_desc': '分布式公钥基础设施管理，提供CA和UE证书管理功能',
                'did_platform_card_title': 'DID平台',
                'did_platform_card_desc': '去中心化身份管理，支持DID生成和可验证凭证签发',
                
                // CA页面
                'dpki_platform_title': 'DPKI管理平台',
                'ca_list_title': 'CA列表',
                'ue_list_title': 'UE列表',
                'loading': '加载中...',
                'ca_server_control': 'CA服务器控制',
                'ca_server_status': 'CA服务器状态: ',
                'checking': '检查中...',
                'start_ca_server': '启动CA服务器',
                'stop_ca_server': '停止CA服务器',
                'ca_functions': 'CA功能',
                'init_root_cert': '初始化根证书',
                'waiting_operation': '等待操作',
                'init_ca': '初始化CA',
                'sign_ue_cert': '签署UE证书',
                'sign_cert': '签署证书',
                'update_cert': '更新证书',
                'update_cert_btn': '更新证书',
                'revoke_cert': '撤销证书',
                'revoke_cert_btn': '撤销证书',
                'operation_receipt': '操作回执',
                'operation_time': '操作时间',
                'operation_result_placeholder': '操作结果将在此显示...',
                'ca_system_logs': 'CA系统日志',
                'deploy_smart_contract': '部署智能合约',
                'warning': '警告：',
                'deploy_warning': '部署智能合约后将清空所有证书库数据，包括CA和UE的所有证书文件！',
                'deploy_contract_btn': '🚀 部署智能合约',
                'deploy_contract_desc': '部署DPKI智能合约到区块链网络，并自动更新配置文件中的合约地址',
                
                // UE页面
                'update_ue_address_list': '更新UE地址列表',
                'update_address_list': '更新地址列表',
                'ue_server_control': 'UE服务器控制',
                'ue_server_status': 'UE服务器状态: ',
                'start_ue_server': '启动UE服务器',
                'stop_ue_server': '停止UE服务器',
                'ue_functions': 'UE功能',
                'initiate_csr_request': '发起CSR请求',
                'initiate_csr': '发起CSR请求',
                'ue_authentication': 'UE间认证',
                'initiate_auth_request': '发起认证请求',
                'ue_system_logs': 'UE系统日志',
                
                'click_generate_did': '点击"生成新DID"按钮开始',
                'query_result_here': '查询结果将在此处显示',
                'vc_display_here': 'VC将在此处显示',
                'parse_verify_result_here': '解析验证结果将在此处显示',
                'revoke_result_here': '撤销结果将在此处显示',
                'did_generation_placeholder': '点击"生成新DID"按钮开始',
                'did_query_result_placeholder': '查询结果将在此处显示',
                'vc_verification_result_placeholder': '解析验证结果将在此处显示',
                'vc_revocation_result_placeholder': '撤销结果将在此处显示',
                
                // 系统日志相关翻译
                'system_logs': {
                    'no_system_logs': '暂无系统日志',
                    'no_ca_system_logs': '暂无CA系统日志',
                    'no_ue_system_logs': '暂无UE系统日志',
                    'load_ca_logs_failed': '加载CA系统日志失败',
                    'load_ue_logs_failed': '加载UE系统日志失败',
                    'load_logs_failed': '加载日志失败',
                    'api_request_failed': 'API请求失败',
                    'platform_loaded': 'DPKI管理平台已加载',
                    'platform_started': 'DPKI管理平台已启动',
                    'select_management_page': '请选择CA管理或UE管理进入相应功能页面',
                    'logs_cleared': '日志已清空'
                },
                
                // VC签发相关翻译
                'vc_did_required': '请填写DID标识符',
                'vc_did_format_error': '错误：DID格式不正确，必须以"did:omni:"开头',
                'vc_validating_did': '正在验证DID...',
                'generating_csr': '正在发起CSR请求...',
                'sending_auth_request': '正在发起认证请求...',
                'updating_ue_list': '正在更新UE地址列表...',
                'initializing_ca': '正在初始化CA...',
                'signing_cert': '正在签署证书...',
                'updating_cert': '正在更新证书...',
                'revoking_cert': '正在撤销证书...',
                'command_timeout': '命令执行超时',
                'vc_did_not_exist': '错误：输入的DID不存在或无效，无法生成VC',
                
                // 状态翻译
                'initialized': '已初始化',
                'issued': '已签发',
                'pending_operation': '待签署'
            },
            'en': {
                // 导航栏
                'platform_title': 'DPKI Management Platform',
                'nav_home': 'Home',
                'nav_ca': 'CA Management',
                'nav_ue': 'UE Management',
                'nav_did': 'DID Platform',
                
                // 页面标题
                'home_title': 'DPKI Management Platform - Distributed Public Key Infrastructure Management System',
                'welcome_title': 'Welcome to DPKI Platform',
                'welcome_desc': 'Blockchain-based distributed public key infrastructure management system, providing secure and reliable digital certificate management and identity authentication services.',
                'page_title_index': 'DPKI Management Platform',
                'page_title_ca': 'CA Management - DPKI Platform',
                'page_title_ue': 'UE Management - DPKI Platform',
                'page_title_did': 'DID Platform - DPKI Platform',
                
                // 按钮文本
                'generate_did': 'Generate New DID',
                'query_did': 'Query DID Document',
                'issue_vc': 'Issue VC',
                'parse_verify_vc': 'Parse & Verify VC',
                'revoke_vc': 'Revoke VC',
                'copy_did': 'Copy DID',
                'copy_vc': 'Copy VC',
                'generate_did_button': 'Generate New DID',
                'copy_button': 'Copy',
                'query_did_button': 'Query Document',
                'generate_vc_button': 'Issue VC',
                'parse_verify_vc_button': 'Parse & Verify VC',
                'revoke_vc_button': 'Revoke VC',
                
                // 标签文本
                'did_generation': 'DID Generation',
                'did_query': 'DID Document Query',
                'vc_issuance': 'VC Issuance',
                'vc_display': 'VC Display',
                'vc_parse_verify': 'VC Parse & Verify',
                'vc_revoke': 'VC Revocation',
                'input_did': 'Input DID:',
                'did_label': 'DID:',
                'operator_permission': 'Operator Permission:',
                'vc_jwt_label': 'VC JWT:',
                'revoke_vc_jwt': 'VC JWT to Revoke:',
                'did_generation_title': '🆔 DID Generation',
                'did_query_title': '🔍 DID Document Query',
                'vc_generation_title': '📜 Verifiable Credential (VC) Issuance',
                'vc_verification_title': '🔐 VC Parse & Verification',
                'vc_revocation_title': '🚫 VC Revocation Management',
                
                // 占位符文本
                'did_query_placeholder': 'Enter DID to query',
                'vc_did_placeholder': 'Enter DID',
                'vc_jwt_placeholder': 'Paste VC JWT string',
                'vc_jwt_revoke_placeholder': 'Paste VC JWT string to revoke',
                'vc_generation_result_placeholder': 'VC will be displayed here',
                'ca_name_placeholder': 'CA Name/Label',
                'ue_name_placeholder': 'UE Name',
                
                // 结果和状态
                'no_did_data': 'No DID data available',
                'generate_did_vc_first': 'Please generate DID and VC first',
                'no_associated_vc': 'No associated VCs',
                'cert_revoke_success': 'Certificate revocation successful',
                'ue_auth_success': 'UE authentication successful - verification passed',
                'ue_auth_failed': 'UE authentication failed - no successful verification found',
                'auth_result_success': 'Authentication result: Success',
                'auth_result_failed': 'Authentication result: Failed',
                'cert_update_success': 'Certificate update successful: {0}',
                'revoked': 'Revoked',
                'success': 'Success',
        'failed': 'Failed',
                'verification failed': 'Verification Failed',
                'csr_request_success_msg': 'CSR request successful!\n{0}',
                'csr_request_failed_msg': 'CSR request failed!\n{0}',
                'auth_success_verification_passed': 'UE authentication successful - verification passed',
                'auth_failed_no_success_info': 'UE authentication failed - no successful verification information found',
                'please_fill_ue_name_error': 'Please fill in UE name',
                'please_fill_ca_name_error': 'Please fill in CA name',
                'please_fill_ca_ue_name_error': 'Please fill in CA name and UE name',
                'auth_result_label': 'Authentication Result',
                'address_list_update_success_msg': 'Address list updated successfully: {0}',
                'did_must_contain_omni': 'DID invalid',
                
                // DID/VC相关
                'did_vc_relationship_title': '📊 DID/VC Relationship Display',
                'vc_did_label': 'DID:',
                'vc_permission_label': 'Operation Permission:',
                'permission_read': 'Read',
                'permission_write': 'Write',
                'permission_admin': 'Admin',
                'vc_jwt_label': 'VC JWT:',
                'revoke_vc_jwt': 'VC JWT to Revoke:',
                
                // 首页卡片
                'dpki_platform_card_title': 'DPKI Platform',
                'dpki_platform_card_desc': 'Distributed Public Key Infrastructure management, providing CA and UE certificate management functions',
                'did_platform_card_title': 'DID Platform',
                'did_platform_card_desc': 'Decentralized Identity Management, supporting DID generation and verifiable credential issuance',
                
                // CA页面
                'dpki_platform_title': 'DPKI Management Platform',
                'ca_list_title': 'CA List',
                'ue_list_title': 'UE List',
                'loading': 'Loading...',
                'ca_server_control': 'CA Server Control',
                'ca_server_status': 'CA Server Status: ',
                'checking': 'Checking...',
                'start_ca_server': 'Start CA Server',
                'stop_ca_server': 'Stop CA Server',
                'ca_functions': 'CA Functions',
                'init_root_cert': 'Initialize Root Certificate',
                'waiting_operation': 'Waiting for Operation',
                'init_ca': 'Initialize CA',
                'sign_ue_cert': 'Sign UE Certificate',
                'sign_cert': 'Sign Certificate',
                'update_cert': 'Update Certificate',
                'update_cert_btn': 'Update Certificate',
                'revoke_cert': 'Revoke Certificate',
                'revoke_cert_btn': 'Revoke Certificate',
                'operation_receipt': 'Operation Receipt',
                'operation_time': 'Operation Time',
                'operation_result_placeholder': 'Operation results will be displayed here...',
                'ca_system_logs': 'CA System Logs',
                'deploy_smart_contract': 'Deploy Smart Contract',
                'warning': 'Warning:',
                'deploy_warning': 'Deploying smart contract will clear all certificate store data, including all certificate files of CA and UE!',
                'deploy_contract_btn': '🚀 Deploy Smart Contract',
                'deploy_contract_desc': 'Deploy DPKI smart contract to blockchain network and automatically update contract address in configuration file',
                
                // UE页面
                'update_ue_address_list': 'Update UE Address List',
                'update_address_list': 'Update Address List',
                'ue_server_control': 'UE Server Control',
                'ue_server_status': 'UE Server Status: ',
                'start_ue_server': 'Start UE Server',
                'stop_ue_server': 'Stop UE Server',
                'ue_functions': 'UE Functions',
                'initiate_csr_request': 'Initiate CSR Request',
                'initiate_csr': 'Initiate CSR Request',
                'ue_authentication': 'UE Authentication',
                'initiate_auth_request': 'Initiate Authentication Request',
                'ue_system_logs': 'UE System Logs',
                
                // DID platform title
                'did_platform_title': 'Decentralized Identity Management Platform',
                
                // 日志消息
                'messages': {
                    'log_messages': {
                        'ca_init_success': 'CA certificate initialization successful: {0}',
                        'ca_init_failed': 'CA certificate initialization failed: {0}',
                        'cert_register_success': 'Certificate registration successful: {0}',
                        'cert_register_failed': 'Certificate registration failed: {0}',
                        'cert_revoke_success': 'Certificate revocation successful: {0}',
                        'cert_revoke_failed': 'Certificate revocation failed: {0}',
                        'cert_sign_success': 'Certificate signing successful: {0}',
                        'cert_sign_failed': 'Certificate signing failed: {0}',
                        'cert_update_success': 'Certificate update successful: {0}',
                        'cert_update_failed': 'Certificate update failed: {0}',
                        'ue_auth_success': 'UE authentication successful - verification passed',
                        'ue_auth_failed': 'UE authentication failed - no successful verification found',
                        'csr_request_success': 'CSR request sent successfully: {0}',
                        'csr_request_failed': 'CSR request failed: {0}',
                        'auth_request_success': 'Authentication request successful: {0} -> {1}',
                        'auth_request_failed': 'Authentication request failed: {0}',
                        'ue_address_update_success': 'UE address list updated successfully',
                        'ue_address_update_failed': 'UE address list update failed: {0}',
                        'api_request_failed': 'API request failed: {0}',
                        'csr_success_received': 'CSR request successful - CSR received',
                        'csr_failed_not_received': 'CSR request failed - CSR received not detected',
                        'server_start_failed': 'Failed to start {0} server: {1}',
                        'server_stop_failed': 'Failed to stop {0} server: {1}',
                        'server_starting': 'Starting {0} server...',
                        'server_stopping': 'Stopping {0} server...',
                        'server_stopped': '{0} server stopped',
                        'ca_initializing': 'Initializing CA certificate: {0}',
                        'cert_signing': 'Signing certificate: CA={0}, UE={1}',
                        'cert_updating': 'Updating certificate: CA={0}, UE={1}',
                        'cert_revoking': 'Revoking certificate: {0}',
                        'csr_requesting': 'Initiating CSR request: {0}',
                        'ue_address_updating': 'Updating UE address list...',
                        'auth_requesting': 'Initiating authentication request: {0} -> {1}',
                        'csr_success_received': 'CSR request successful - CSR received',
                        'csr_failed_not_received': 'CSR request failed - CSR received not detected',
                        'please_fill_ca_name': 'Please fill in CA name',
                        'please_fill_ca_ue_name': 'Please fill in CA name and UE name',
                        'please_fill_ue_name': 'Please fill in UE name',
                        'please_fill_ca_name_label': 'Please fill in CA name and label',
                        'please_fill_revoke_ue_name': 'Please fill in UE name to revoke',
                        'please_fill_local_target_ue': 'Please fill in local UE name and target UE name',
                        'ca_page_loaded': 'CA management page loaded',
                        'ue_page_loaded': 'UE management page loaded'
                    }
                },
                
                'click_generate_did': 'Click "Generate New DID" button to start',
                'query_result_here': 'Query results will be displayed here',
                'vc_display_here': 'VC will be displayed here',
                'parse_verify_result_here': 'Parse and verification results will be displayed here',
                'revoke_result_here': 'Revocation results will be displayed here',
                'did_generation_placeholder': 'Click "Generate New DID" button to start',
                'did_query_result_placeholder': 'Query results will be displayed here',
                'vc_verification_result_placeholder': 'Parse and verification results will be displayed here',
                'vc_revocation_result_placeholder': 'Revocation results will be displayed here',
                
                // 系统日志相关翻译
                'system_logs': {
                    'no_system_logs': 'No system logs available',
                    'no_ca_system_logs': 'No CA system logs available',
                    'no_ue_system_logs': 'No UE system logs available',
                    'load_ca_logs_failed': 'Failed to load CA system logs',
                    'load_ue_logs_failed': 'Failed to load UE system logs',
                    'load_logs_failed': 'Failed to load logs',
                    'api_request_failed': 'API request failed',
                    'platform_loaded': 'DPKI management platform loaded',
                    'platform_started': 'DPKI management platform started',
                    'select_management_page': 'Please select CA management or UE management to access the corresponding function page',
                    'logs_cleared': 'Logs cleared'
                },
                
                // VC签发相关翻译
                'vc_did_required': 'Please enter DID identifier',
                'vc_did_format_error': 'Error: Invalid DID format, must start with "did:omni:"',
                'vc_validating_did': 'Validating DID...',
                'generating_csr': 'Generating CSR request...',
                'sending_auth_request': 'Sending authentication request...',
                'updating_ue_list': 'Updating UE address list...',
                'initializing_ca': 'Initializing CA...',
                'signing_cert': 'Signing certificate...',
                'updating_cert': 'Updating certificate...',
                'revoking_cert': 'Revoking certificate...',
                'command_timeout': 'Command execution timeout',
                'vc_did_not_exist': 'Error: The entered DID does not exist or is invalid, cannot generate VC',
                
                // 状态翻译
                'initialized': 'Initialized',
                'issued': 'Issued',
                'pending_operation': 'Pending Operation'
            }
        };
    }

    getText(key, ...params) {
        let text = this.translations[this.currentLanguage][key] || key;
        
        // 如果有参数，进行占位符替换
        if (params.length > 0) {
            params.forEach((param, index) => {
                text = text.replace(`{${index}}`, param);
            });
        }
        
        return text;
    }

    setLanguage(lang) {
        if (this.translations[lang]) {
            this.currentLanguage = lang;
            // 保存语言设置到localStorage
            localStorage.setItem('selectedLanguage', lang);
            this.updatePageTexts();
            // 刷新页面以确保所有内容都能正确更新
            setTimeout(() => {
                window.location.reload();
            }, 100);
        }
    }

    updatePageTexts() {
        // 更新页面中所有带有 data-lang-key 属性的元素
        const elements = document.querySelectorAll('[data-lang-key]');
        elements.forEach(element => {
            const key = element.getAttribute('data-lang-key');
            const text = this.getText(key);
            
            if (element.tagName === 'INPUT' && element.type === 'text') {
                element.placeholder = text;
            } else {
                element.textContent = text;
            }
        });

        // 更新带有 data-lang-placeholder 属性的输入框占位符
        const placeholderElements = document.querySelectorAll('[data-lang-placeholder]');
        placeholderElements.forEach(element => {
            const key = element.getAttribute('data-lang-placeholder');
            const text = this.getText(key);
            element.placeholder = text;
        });

        // 更新页面标题
        const titleKey = document.body.getAttribute('data-page');
        if (titleKey) {
            document.title = this.getText(titleKey);
        }
    }

    getCurrentLanguage() {
        return this.currentLanguage;
    }
}

// 页面加载完成后初始化语言管理器
document.addEventListener('DOMContentLoaded', function() {
    window.languageManager = new LanguageManager();
    
    // 只在首页显示语言切换开关
    const isHomePage = window.location.pathname === '/' || window.location.pathname.endsWith('/index.html') || window.location.pathname.endsWith('/web/');
    
    if (isHomePage) {
        // 创建语言切换开关
        const languageToggle = document.createElement('div');
        languageToggle.className = 'language-toggle';
        languageToggle.innerHTML = `
            <label class="switch">
                <input type="checkbox" id="languageSwitch">
                <span class="slider round"></span>
            </label>
            <span class="language-label">中/EN</span>
        `;
        
        // 添加样式
        const style = document.createElement('style');
        style.textContent = `
            .language-toggle {
                position: fixed;
                top: 20px;
                right: 20px;
                display: flex;
                align-items: center;
                gap: 10px;
                z-index: 1000;
                background: rgba(255, 255, 255, 0.9);
                padding: 10px;
                border-radius: 25px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            }
            
            .switch {
                position: relative;
                display: inline-block;
                width: 60px;
                height: 34px;
            }
            
            .switch input {
                opacity: 0;
                width: 0;
                height: 0;
            }
            
            .slider {
                position: absolute;
                cursor: pointer;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background-color: #ccc;
                transition: .4s;
            }
            
            .slider:before {
                position: absolute;
                content: "";
                height: 26px;
                width: 26px;
                left: 4px;
                bottom: 4px;
                background-color: white;
                transition: .4s;
            }
            
            input:checked + .slider {
                background-color: #2196F3;
            }
            
            input:focus + .slider {
                box-shadow: 0 0 1px #2196F3;
            }
            
            input:checked + .slider:before {
                transform: translateX(26px);
            }
            
            .slider.round {
                border-radius: 34px;
            }
            
            .slider.round:before {
                border-radius: 50%;
            }
            
            .language-label {
                font-size: 14px;
                font-weight: bold;
                color: #333;
            }
        `;
        document.head.appendChild(style);
        
        // 将语言切换开关添加到页面
        document.body.appendChild(languageToggle);
        
        // 绑定切换事件
        const languageSwitch = document.getElementById('languageSwitch');
        
        // 根据保存的语言设置初始化开关状态
        languageSwitch.checked = window.languageManager.getCurrentLanguage() === 'en';
        
        languageSwitch.addEventListener('change', function() {
            const newLang = this.checked ? 'en' : 'zh';
            window.languageManager.setLanguage(newLang);
        });
    }
    
    // 初始化页面文本
    window.languageManager.updatePageTexts();
});