package com.example.contractreview.constant;


public class UserConstant {

    // 用户用户名注册验证码
    public static final String REGISTER_CAPTCHA_USERNAME = "captcha:register:user:";  // + captchaId
    // 用户手机号注册验证码
    public static final String REGISTER_CAPTCHA_PHONE = "captcha:register:phone:";   // + target
    // 用户邮箱注册验证码
    public static final String REGISTER_CAPTCHA_EMAIL = "captcha:register:email:";   // + target

    // 用户用户名登录
    public static final String LOGIN_CAPTCHA_USERNAME = "captcha:login:user:";  // + captchaId
    // 用户手机号登录验证码
    public static final String LOGIN_CAPTCHA_PHONE = "captcha:login:phone:";  // + target
    // 用户邮箱登录验证码
    public static final String LOGIN_CAPTCHA_EMAIL = "captcha:login:email:";  // + target
    // 忘记密码
    public static final String RESETPASSWORD_CAPTCHA_EMAIL = "captcha:resetPassword:email:";  // + target

    // 用户默认头像
    public static final String DEFAULT_AVATAR = "https://allenxjl.oss-cn-beijing.aliyuncs.com/avatar/3a7b1ac1b22a345ad56bc8a302cf3af775aa8372f4b7-1xJO27_fw1200webp.webp";

    // Token黑名单前缀（用于退出登录）
    public static final String TOKEN_BLACKLIST = "token:blacklist:";  // + token

    // 用户登录token映射（用于单点登录，一个用户只能在一个设备登录）
    public static final String USER_TOKEN_MAP = "user:token:";  // + userId
    // 用户信息
    public static final String USER_INFO = "user:info:";  // + userId
    // 用户列表
    public static final String USER_List = "user:list:";

    // 用户通知设置
    public static final String USER_NOTIFICATION_SETTINGS = "user:notification:settings:";

    // 验证码发送限流前缀
    public static final String RATE_LIMIT_PREFIX = "rate:limit:code:";

    // 验证码发送计数前缀
    public static final String RATE_COUNT_PREFIX = "rate:count:code:";

    // 用户会话列表
    public static final String CONVERSATION_LIST = "conversation:list:";  // + userId
    // 用户会话详细信息
    public static final String CONVERSATION_DETAIL = "conversation:detail:";  // + conversationId
}
