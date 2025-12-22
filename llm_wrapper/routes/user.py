from llm_wrapper.types import BalanceResponse

def get_balance(wrapper) -> BalanceResponse:
    """
    Get user balance information.
    
    Compatible with DeepSeek API: /user/balance
    Uses GET method and standard Authorization header.
    """
    url = f"{wrapper.config.base_url}/{wrapper.config.balance_service}"
    
    # Send GET request
    # request_builder.build_headers ensures 'Authorization: Bearer <api_key>' is present
    response = wrapper.request_sender.send_request(
        wrapper.session,
        "GET",
        url,
        headers=wrapper.request_builder.build_headers(wrapper.token, wrapper.config.api_key),
        timeout=wrapper.config.timeout
    )
    
    data = wrapper.response_handler.handle_response(response)
    return BalanceResponse(**data)
