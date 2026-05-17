from 合同审查.app.core.http_client import springboot_get
from 合同审查.app.utils.context import set_current_token


def get_contract_list():
    """
    获取系统中所有合同列表

    :return: 所有合同列表
    """
    # 设置测试用的 JWT Token
    # 注意：请替换为有效的 token
    test_token = "eyJhbGciOiJIUzI1NiJ9.eyJ1c2VySWQiOjksInJvbGUiOiJBRE1JTiIsInVzZXJuYW1lIjoiYWRtaW4iLCJleHAiOjE3Nzg5MjI1Mzh9.Q9bVPNTrazqW9rHdo3I-MsuNYNVEyqmq_s1CfnmkOjg"

    # 设置当前线程的 token
    set_current_token(test_token)

    try:
        response = springboot_get(
            "/contract/list",
            token=test_token
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


if __name__ == '__main__':
    result = get_contract_list()
    print(result)
