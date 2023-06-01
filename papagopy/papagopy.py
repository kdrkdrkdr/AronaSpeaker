import requests
import time
import random
import json

from . import constants as CONST
from . import auth as AUTH
from . import utils as UTIL
from .version import version as VERSION

class Papagopy:
	'''
	api(dict): `{"clientId":"cliendSecret", ...}`. You can get this values from [here](https://developers.naver.com/main)

	debug(bool): if `True`, it logs a lot more information on terminal using `print` function.

	retry(int): a retry value for web api calls

	requestTimeout(int): a requests call timeout value

	sleepMaxMS(int): a sleep time between web api calls

	proxy(object): proxy options for requests calls. check also [here](https://docs.python-requests.org/en/latest/user/advanced/#proxies)
	'''
	def __init__(self, api={}, debug=False, retry=5, requestTimeout=3, sleepMaxMS=4321, proxy={}):
		self.api = api
		self.debug = debug
		self.retry = retry
		self.proxy = proxy
		self.requestTimeout = requestTimeout
		self.sleepMaxMS = sleepMaxMS
		self.uuid = None
		self.time = None
		self.auth = {}
		self.headers = {
			'web': {},
			'api': {},
		}
		self.papagoVersion = None
		self.version = VERSION
		self.setAuth()


	def setAuth(self):
		self.uuid = AUTH.getUUID()
		self.time = AUTH.getTimeString()
		self.papagoVersion = AUTH.getVersion(proxy=self.proxy)
		self.auth = {
			key: AUTH.getAuthorization(
				url = CONST.url['web'][key],
				version = self.papagoVersion,
				uuid = self.uuid,
				time = self.time
				) for key in CONST.url['web']
		}
		self.headers['web'] = {
			key: {
				'authorization': self.auth[key],
				'timestamp': self.time,
        'sec-ch-ua': '"Chromium";v="86", "\"Not\\A;Brand";v="99", "Whale";v="2"',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Whale/2.9.115.16 Safari/537.36',
			} for key in CONST.url['web']
		}
		self.headers['api'] = {
			clientId:{
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Naver-Client-Id": clientId,
        'X-Naver-Client-Secret': self.api[clientId],
      } for clientId in self.api
		}

	'''
	options={
		"method": '', # dect, n2mt, nsmt, tts

		# for n2mt, nsmt
		sourceCode?
		targetCode?

		# for tts
		alpha?
		speed?
		speaker?
		pitch?
	}
	'''
	def request(self, source, options):
		response = None
		method = options['method']
		data = {
			"api": {},
			"web": {},
		}

		if method == 'dect':
			data['api'] = {"query": source}
			data['web'] = {"query": source}
		elif method == 'tts':
			data['web'] = {
				"alpha": options['alpha'],
				"pitch": options['pitch'],
				"speed": options['speed'],
				"speaker": options['speaker'],
				"text": source,
			}
		elif (method == 'nsmt' or method == 'n2mt'): # for translate
			data['api'] = {
				"source": options['sourceCode'],
				"target": options['targetCode'],
				"text": source,
			}
			data['web'] = {
				'deviceId': self.uuid,
				'locale': options['targetCode'],
				'honorific': options['honorific'],
				'dict': 'false',
				'instant': 'false',
				'paging': 'false',
				'source': options['sourceCode'],
				'target': options['targetCode'],
				'text': source,
				'authorization': self.auth[method],
				'timestamp': self.time
			}
		else:
			raise Exception(f'Not supported method: {options}')

		# use api
		if method == 'dect' or (method == 'n2mt' and UTIL.isAPIusable(options['sourceCode'], options['targetCode'])):
			for clientId in self.api:
				try:
					response = requests.post(
						url = CONST.url['api'][method],
						data = data['api'],
						headers = self.headers['api'][clientId],
						timeout = self.requestTimeout,
						proxies = self.proxy,
					)
				except requests.exceptions.Timeout:
					if self.debug:
						print(f"[Pypago.request][{method}][API][{clientId}] try timeout for source: {UTIL.makePrintableString(source)}")
					time.sleep(random.randrange(1100, self.sleepMaxMS)/1000)
					continue
				if response.status_code == 200:
					if self.debug:
						print(f"[Pypago.request][{method}][API][{clientId}] successed for source: {UTIL.makePrintableString(source)}")
					break
				else:
					print(f"[Pypago.request][{method}][API][{clientId}] failed for source: {UTIL.makePrintableString(source)}. Try other clientIds or use web api")
					print(f"{response.json()}")

		
		# use web
		if response == None or response.status_code != 200:
			if len(self.api) > 0 and self.debug:
				print(f"[Pypago.request][{method}][API] request failed for source: {UTIL.makePrintableString(source)}")
			
			for i in range(self.retry):
				try:
					response = requests.post(
						url = CONST.url['web'][method],
						data = data['web'],
						headers = self.headers['web'][method],
						timeout = self.requestTimeout,
						proxies = self.proxy,
					)
				except requests.exceptions.Timeout:
					if self.debug:
						print(f"[Pypago.request][{method}][web][{str(i+1)}-th] timeout for source: {UTIL.makePrintableString(source)}")
					time.sleep(random.randrange(1100, self.sleepMaxMS)/1000)
					continue
				if response.status_code == 200:
					if self.debug:
						print(f"[Pypago.request][{method}][web][{str(i+1)}] successed for source: {UTIL.makePrintableString(source)}")
					break
				else:
					print(f"[Pypago.request][{method}][web][{str(i+1)}] failed for source: {UTIL.makePrintableString(source)}")
					print(f"It will sleep for a few seconds and change headers")
					print(response.text)
					print(f"{response.json()}")
					time.sleep(random.randrange(1100, self.sleepMaxMS)/1000)
					self.setAuth()
		
		if response == None or response.status_code != 200:
			raise Exception(f"[Pypago.request][{method}] failed for source: {UTIL.makePrintableString(source)} with reason {response.text}. check ip ban also")
		if self.debug:
			print(f"[Pypago.request][{method}] return value: {UTIL.makePrintableString(response.text)}")
		return response


	def detectLang(self, source, returnRaw=False):
		''' 
		source(str): a text to be used to detect a language.

		returnRaw(bool): if `True`, it returns a JSON object received from papago server. if `False`, it returns only a language code.
		'''
		source = str(source).strip()
		if len(source) == 0:
			return source

		chunks = UTIL.splitLongText(source, size=500, forLangDetection=True, debug=self.debug)
		result = None
		for chunk in chunks:
			response = self.request(chunk, options={"method": "dect"})
			res = json.loads(response.text)
			if response.status_code == 200 and 'langCode' in res and res['langCode'] != 'unk':
				result = res
				break
		if self.debug:
			print(f"[Pypago.detectLang] language code for source({UTIL.makePrintableString(source)}) is {result}")
		if result['langCode'] == 'py':
			result['langCode'] = 'zh-CN'
		if returnRaw:
			return result
		else:
			return result['langCode']
		

	def translate(self, source, targetCode, sourceCode='', method='n2mt', honorific=False, returnRaw=False):
		'''
		source(str): a text to be translated.

		targetCode(str): a language code of translated text. check [here](https://github.com/k123s456h/papagopy/blob/main/papagopy/constants.py#L2).

		sourceCode(str): a language code of source. if not set, papagopy will automatically set it using it's internal `detectLang` method.

		method(str): a translation method. You can set `n2mt` or `nsmt`, but I recommend to use `n2mt`. `n2mt` means `Naver Neural Machine Translation` and `nsmt` means `Naver Statistical Machine Translation`. Some language does not support `n2mt` method, then it automatically use `nsmt` method.

		honorific(bool): use honorific words in translated text, especially in korean language. 

		returnRaw(bool): similar as a `returnRaw` argument in `detectLang` method.
		'''
		
		# source = str(source).strip()
		source = str(source)
		if len(source) == 0:
			return source

		if len(sourceCode) == 0:
			sourceCode = self.detectLang(source)
		if len(targetCode) == 0:
			raise Exception(f"[Pypago.translate] You must specify target language code.")
		if not UTIL.isValidCode(sourceCode):
			raise Exception(f"[Pypago.translate] {sourceCode} is not a valid code.")
		if not UTIL.isValidCode(targetCode):
			raise Exception(f"[Pypago.translate] {targetCode} is not a valid code.")
		if sourceCode == targetCode:
			return source
		if UTIL.useNSMT(sourceCode, targetCode):
			method = 'nsmt'
		if not UTIL.canTranslateDirectly(sourceCode, targetCode):
			if self.debug:
				print(f"[Pypago.translate] {sourceCode} language cannot directly translated to {targetCode}")
				print(f"pypago will translate source({sourceCode}) to english and translate to target({targetCode}) using web nsmt method.")
			source = self.translate(source, 'en', sourceCode=sourceCode)
			sourceCode = 'en'
		
		preprocessedSources = UTIL.splitLongText(source, debug=self.debug)
		options = {
			'method': method,
			'sourceCode': sourceCode,
			'targetCode': targetCode,
			'honorific': honorific,
		}

		result = [self.request(source=chunk, options=options) for chunk in preprocessedSources]
		result = [json.loads(response.text) for response in result]




		if returnRaw:
			result = [
				res['message']['result'] if 'message' in res else res 
				for res in result
			]
		else:
			result = [
				res['message']['result']['translatedText'] if 'message' in res else res['translatedText'] 
				for res in result
      		]
		
		if self.debug:
			for res in result:
				print(f"[Pypago.translate] result length {str(len(res))} : {UTIL.makePrintableString(res)}")
		
		if not returnRaw:
			result = '\n'.join(result)
		return result


	def tts(self, text, sex=True, speed=0, alpha=0, pitch=0, save=False):
		'''
		text(str): a text to be converted to audio file.

		sex(bool): if `True`, it will use a male voice. if `False`, it will use a female voice.

		speed(int): a integer value -5(slow) to 5(fast). 0 is normal speed.

		alpha(int): a integer value -5 to 5.

		pitch(int): a integer value -5 to 5.

		save(bool): if `True`, it will save `mp3` file to your current working directory. else it returns dict object that contains url to audio file.
		'''
		text = str(text).strip()
		if len(text) == 0:
			return {}

		sexString = 'male' if sex else 'female' 
		langCode = self.detectLang(text)
		if CONST.tts[sexString][langCode] == "":
			print(f"[Pypago.tts] {UTIL.makePrintableString}({langCode}) currently not supported by papago.")
			return
		
		chunks = UTIL.splitLongText(text, debug=self.debug)
		result = {}
		filename = ''

		for i in range(0, len(chunks)):
			voiceFilePath = None
			voiceFile = None
			options = {
				'method': 'tts',
				"alpha": alpha,
				"pitch": pitch,
				"speed": speed,
				"speaker": CONST.tts[sexString][langCode],
			}
			response = self.request(chunks[i], options=options)
			voiceFilePath = json.loads(response.text)['id']
			voiceFile = f"https://papago.naver.com/apis/tts/{voiceFilePath}"
			result[str(i)] = voiceFile
			if save:
				if len(filename) < 1:
					filename = voiceFilePath
				UTIL.downloadAudio(voiceFile, filename=filename)

		if self.debug:
			print(f"[Pypago.tts] result: {result}")
			if save:
				print(f"[Pypago.tts] tts audio saved as {filename}.mp3")
		return result

