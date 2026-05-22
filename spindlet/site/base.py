import json.decoder
from typing import Literal, TypeAlias
from urllib.parse import urlparse, urlunparse

import requests
from loguru import logger


class SiteConnectionError(Exception):
    pass


class SiteRequestError(Exception):
    pass


class SiteResponseError(Exception):
    pass


class SiteResponseFormatError(Exception):
    pass


class SiteError(Exception):
    pass


TimeoutType: TypeAlias = float | tuple[float, float]
_DEFAULT_TIMEOUT: TimeoutType = (3.03, 20)


class SiteBase:
    NAME = ''
    AUTHOR = ''
    SCHEME = 'HTTP'
    NETLOC = ''
    BASE_ROUTE = ''
    TIMEOUT = _DEFAULT_TIMEOUT
    DEBUG = False
    _session: requests.Session | None = None

    def __setattr__(self, key, value):
        if key in ('NAME', 'AUTHOR', 'SCHEME', 'NETLOC', 'BASE_ROUTE'):
            raise SiteError(f'{key} 属性不可修改')
        else:
            super().__setattr__(key, value)

    def _get_path(self, route: str) -> str:
        return '/'.join((self.BASE_ROUTE.strip('/'), route.strip('/'))).strip('/')

    def _get_url(self, route: str) -> str:
        return urlparse(urlunparse((self.SCHEME, self.NETLOC, self._get_path(route), '', '', ''))).geturl()

    def _resolve_timeout(self, timeout: TimeoutType | None) -> TimeoutType:
        return timeout or self.TIMEOUT or _DEFAULT_TIMEOUT

    def _get_session(self) -> requests.Session:
        session = getattr(self, '_session', None)
        if session is None:
            session = requests.Session()
            self._session = session
        return session

    def close(self) -> None:
        session = getattr(self, '_session', None)
        if session is not None:
            session.close()
            self._session = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def request(self, method: Literal['POST', 'GET', 'PUT'], route: str = '',
                timeout: TimeoutType = _DEFAULT_TIMEOUT,
                rsp_mode: Literal['JSON', 'TEXT', 'ORIGIN'] = 'JSON',
                **param) -> dict | str | requests.Response:
        site = self.__class__.__name__
        path = self._get_path(route)
        url = self._get_url(route)
        timeout = self._resolve_timeout(timeout)
        session = self._get_session()
        method = method.upper()
        try:
            rsp = session.request(method=method, url=url, timeout=timeout, **param)
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout):
            raise SiteConnectionError(
                f'{site} 连接超时，请检查 NETLOC<{self.NETLOC}> 状态是否正常。Site Author: <{self.AUTHOR}>'
            ) from None
        except requests.exceptions.ConnectionError:
            raise SiteConnectionError(
                f'{site} 连接建立失败，请检查 NETLOC<{self.NETLOC}> 状态是否正常。Site Author: <{self.AUTHOR}>'
            ) from None
        except requests.exceptions.Timeout:
            raise SiteConnectionError(
                f'{site} 请求超时，请检查 NETLOC<{self.NETLOC}> 状态是否正常。Site Author: <{self.AUTHOR}>'
            ) from None
        except requests.exceptions.RequestException as exc:
            raise SiteRequestError(f'{site} 请求异常：{exc}') from exc
        else:
            # 请求信息打印
            if self.DEBUG:
                logger.debug(f'{method}: {url} {rsp}')
                try:
                    logger.debug(f'Request Headers: {rsp.request.headers}')
                    _content_types = (_.strip() for _ in rsp.request.headers.get('Content-Type', '').split(';'))
                    if method != 'GET' and 'application/json' in _content_types:
                        if isinstance(_body := rsp.request.body, bytes):
                            try:
                                body_for_log = _body.decode('utf-8')
                            except UnicodeDecodeError:
                                body_for_log = _body.decode('unicode-escape', errors='ignore')
                        else:
                            body_for_log = _body
                        logger.debug(f'Request Body: {body_for_log}')
                except json.decoder.JSONDecodeError:
                    logger.debug('无法输出请求详情')
            # 响应信息打印
            if rsp.status_code == 401:
                raise SiteConnectionError(f'{site}: {path} 没有权限<401>，请检查')
            elif rsp.status_code == 404:
                raise SiteConnectionError(f'{site}: {path} 不存在<404>, 请检查')
            elif str(rsp.status_code).startswith('5'):
                raise SiteResponseError(f'{site}: {path} 响应异常<{rsp.status_code}>：{rsp.text}')
            else:
                if self.DEBUG:
                    logger.debug(f'Response Headers: {rsp.headers}')
                    logger.debug(f'Response Body: {rsp.text}')
                if rsp_mode == 'JSON':
                    try:
                        return rsp.json()
                    except json.decoder.JSONDecodeError:
                        raise SiteResponseFormatError(rsp.text)
                elif rsp_mode == 'TEXT':
                    return rsp.text
                else:
                    return rsp
