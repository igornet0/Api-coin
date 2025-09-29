#!/usr/bin/python
# -*- coding:utf-8 -*-

import asyncio
import json
import requests
import hmac
import hashlib
import base64
import time
import aiohttp
from uuid import uuid1
from urllib.parse import urljoin
import socket

from requests import Session

try:
    import pkg_resources
    version = 'v' + pkg_resources.get_distribution("kucoin-python").version
except (ModuleNotFoundError, NameError):
    version = 'v1.0.0'


class KucoinBaseRestApi(object):


    def __init__(self, key='', secret='', passphrase='', url='', is_v1api=False, max_concurrent=50):
        """
        https://docs.kucoin.com

        :param key: Api Token Id  (Mandatory)
        :type key: string
        :param secret: Api Secret  (Mandatory)
        :type secret: string
        :param passphrase: Api Passphrase used to create API  (Mandatory)
        :type passphrase: string
        """

        if url:
            self.url = url
        else:
            self.url = 'https://api.kucoin.com'

        self.key = key
        self.secret = secret
        self.passphrase = passphrase
        self.is_v1api = is_v1api
        self.TCP_NODELAY = 0
        self._session = None
        self._async_session = None
        self.semaphore = asyncio.Semaphore(max_concurrent)

    @property
    def session(self) -> Session:
        return self._session
    
    @property
    def async_session(self) -> aiohttp.ClientSession:
        return self._async_session
    
    @session.setter
    def session(self, session: Session):
        self._session = session

    @async_session.setter
    def async_session(self, session: aiohttp.ClientSession):
        self._async_session = session

    def _request(self, method, uri, timeout=5, auth=True, params=None):
        uri_path = uri
        data_json = ''
        if method in ['GET', 'DELETE']:
            if params:
                strl = []
                for key in sorted(params):
                    strl.append("{}={}".format(key, params[key]))
                data_json += '&'.join(strl)
                uri += '?' + data_json
                uri_path = uri
        else:
            if params:
                data_json = json.dumps(params)

                uri_path = uri + data_json

        headers = {}
        if auth:
            now_time = int(time.time()) * 1000
            str_to_sign = str(now_time) + method + uri_path
            sign = base64.b64encode(
                hmac.new(self.secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest())
            if self.is_v1api:
                headers = {
                    "KC-API-SIGN": sign,
                    "KC-API-TIMESTAMP": str(now_time),
                    "KC-API-KEY": self.key,
                    "KC-API-PASSPHRASE": self.passphrase,
                    "Content-Type": "application/json"
                }
            else:
                passphrase = base64.b64encode(
                    hmac.new(self.secret.encode('utf-8'), self.passphrase.encode('utf-8'), hashlib.sha256).digest())
                headers = {
                    "KC-API-SIGN": sign,
                    "KC-API-TIMESTAMP": str(now_time),
                    "KC-API-KEY": self.key,
                    "KC-API-PASSPHRASE": passphrase,
                    "Content-Type": "application/json",
                    "KC-API-KEY-VERSION": "2"
                }
        headers["User-Agent"] = "kucoin-python-sdk/" + version
        url = urljoin(self.url, uri)
        if not self.session:
            self.session = requests.Session()
            if self.TCP_NODELAY == 1:
                adapter = requests.adapters.HTTPAdapter()
                adapter.socket_options = [
                    (socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                ]
                self.session.mount('https://', adapter)
        if method in ['GET', 'DELETE']:
            response_data = self.session.request(method, url, headers=headers, timeout=timeout)
        else:
            response_data = self.session.request(method, url, headers=headers, data=data_json,
                                                 timeout=timeout)
            
        return self.check_response_data(response_data)

    async def _request_async(self, method, uri, timeout=5, auth=True, params=None):
        uri_path = uri
        data_json = ''
        if method in ['GET', 'DELETE']:
            if params:
                strl = []
                for key in sorted(params):
                    strl.append("{}={}".format(key, params[key]))
                data_json += '&'.join(strl)
                uri += '?' + data_json
                uri_path = uri
        else:
            if params:
                data_json = json.dumps(params)

                uri_path = uri + data_json

        headers = {}
        if auth:
            now_time = int(time.time()) * 1000
            str_to_sign = f"{now_time}{method}{uri_path}{data_json}"  # Добавляем тело для POST/PUT
            # Генерация подписи с декодированием в строку
            sign = base64.b64encode(
                hmac.new(self.secret.encode(), str_to_sign.encode(), hashlib.sha256).digest()
            ).decode('utf-8')  # Декодируем байты в строку
            
            if self.is_v1api:
                headers = {
                    "KC-API-SIGN": sign,
                    "KC-API-TIMESTAMP": str(now_time),
                    "KC-API-KEY": self.key,
                    "KC-API-PASSPHRASE": self.passphrase,
                    "Content-Type": "application/json"
                }
            else:
                # passphrase = base64.b64encode(
                #     hmac.new(self.secret.encode('utf-8'), self.passphrase.encode('utf-8'), hashlib.sha256).digest())
                passphrase = base64.b64encode(
                    hmac.new(self.secret.encode(), self.passphrase.encode(), hashlib.sha256).digest()
                ).decode('utf-8')
                headers = {
                    "KC-API-SIGN": sign,
                    "KC-API-TIMESTAMP": str(now_time),
                    "KC-API-KEY": self.key,
                    "KC-API-PASSPHRASE": passphrase,
                    "Content-Type": "application/json",
                    "KC-API-KEY-VERSION": "2"
                }
        # headers["User-Agent"] = "kucoin-python-sdk/" + version

        url = urljoin(self.url, uri)

        if not self._async_session:
            self._async_session = aiohttp.ClientSession

        """Выполняет асинхронный запрос и сохраняет результат"""
        try:
            async with self._async_session() as session:
                async with self.semaphore:
                    async with session.request(
                        method,
                        url,
                        headers=headers,
                        data=data_json if method not in ['GET', 'DELETE'] else None,
                        timeout=timeout
                    ) as response:
                        response.raise_for_status()
                        response = await response.json()
                        return response['data']
                    
        except Exception as e:
            raise Exception(f"Error during HTTP request: {e}")
        except asyncio.TimeoutError:
            raise Exception("HTTP request timed out")
        if not response_data:
            raise Exception("No response data received")

        return self.check_response_data(response_data)

    @staticmethod
    def check_response_data(response_data):
        if response_data.status_code == 200:
            try:
                data = response_data.json()
            except ValueError:
                raise Exception(response_data.content)
            
            else:
                if data and data.get('code'):
                    if data.get('code') == '200000':
                        if data.get('data'):
                            return data['data']
                        else:
                            return data
                    else:
                        raise Exception("{}-{}".format(response_data.status_code, response_data.text))
        else:
            raise Exception("{}-{}".format(response_data.status_code, response_data.text))

    @property
    def return_unique_id(self):
        return ''.join([each for each in str(uuid1()).split('-')])
