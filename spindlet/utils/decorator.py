import functools
import time


class RetryException(Exception):
    pass


def delay(seconds):
    """ 延迟执行装饰器 """

    def _wrapper_outer(func):
        @functools.wraps(func)
        def _wrapper_inner(self, *args, **kwargs):
            self.logger.info(f"函数延迟执行 {seconds}s，函数名：{func.__name__}，参数：args={args} kwargs={kwargs}")
            time.sleep(seconds)
            return func(self, *args, **kwargs)

        return _wrapper_inner

    return _wrapper_outer


def _fibonacci_delay(retry_count: int, base_delay: int) -> int:
    """ 计算斐波那契数列延迟时间 """
    if retry_count <= 1:
        return base_delay

    fib_a, fib_b = 1, 1
    for _ in range(retry_count - 1):
        fib_a, fib_b = fib_b, fib_a + fib_b

    return base_delay * fib_b


def _calculate_total_fibonacci_wait_time(reruns: int, base_delay: int) -> int:
    """ 预计算斐波那契数列的总等待时间 """
    total_time = 0
    for i in range(1, reruns + 1):
        total_time += _fibonacci_delay(i, base_delay)
    return total_time


def retry(reruns: int, reruns_delay: int, backoff_strategy: str = "fixed", exception=AssertionError):
    """
    重试装饰器
    :param reruns: 函数重试次数，n 表示函数在第一次失败后会再执行 n 次
    :param reruns_delay: 函数重试间隔延时，单位：秒
    :param backoff_strategy: 退避策略，支持 "fixed"（固定延迟）和 "fibonacci"（斐波那契数列延迟），默认为 "fixed"
    :param exception: 支持捕获的失败异常，默认为 AssertionError
    """
    if not reruns and reruns_delay:
        raise RetryException(f"重试次数和重试间隔必须大于0")
    if backoff_strategy not in ("fixed", "fibonacci"):
        raise RetryException(f"退避策略必须为 'fixed' 或 'fibonacci'，当前值：{backoff_strategy}")
    if reruns / reruns_delay > 2:
        raise RetryException(f"重试间隔设置不合理！重试次数 / 重试间隔 : {reruns} / {reruns_delay} 需小于等于 2")

    max_wait_time = 3600
    if backoff_strategy == "fibonacci":
        total_fibonacci_time = _calculate_total_fibonacci_wait_time(reruns, reruns_delay)
        if total_fibonacci_time > max_wait_time:
            raise RetryException(
                f"斐波那契数列模式下的总等待时间 {total_fibonacci_time}s 超过最大限制 {max_wait_time}s（60分钟）！"
                f"请减少重试次数或基础延迟时间。"
            )

    def _wrapper_outer(func):
        @functools.wraps(func)
        def _wrapper_inner(self, *args, **kwargs):
            _error = None
            total_wait_time = 0
            for current_retry in range(1, reruns + 1):
                try:
                    return func(self, *args, **kwargs)
                except exception as err:
                    self.logger.error(err)
                    self.logger.info(
                        f"函数重试第 {current_retry} 次，函数名：{func.__name__}，参数：args={args} kwargs={kwargs}")

                    if backoff_strategy == "fibonacci":
                        delay_time = _fibonacci_delay(current_retry, reruns_delay)
                        total_wait_time += delay_time
                        if total_wait_time > max_wait_time:
                            self.logger.error(f"已达到最大等待时间 {max_wait_time}s，停止重试！")
                            raise _error
                    else:
                        delay_time = reruns_delay

                    self.logger.info(f"waiting... {delay_time}s")
                    time.sleep(delay_time)
                    _error = err

            self.logger.error("已达到最大重试次数！")
            raise _error

        return _wrapper_inner

    return _wrapper_outer
