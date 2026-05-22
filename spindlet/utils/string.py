def escape_re(string: str) -> str:
    """
    保证字符串在正则表达式中表示原本的意思，对特殊字符进行转义
    :param string: 可能包含正则特殊字符的字符串
    :return: 转义替换后的字符串
    """
    for char in r'\/*.?+$^[](){}|':
        if char in string:
            string = string.replace(char, rf"\{char}")
    return string
