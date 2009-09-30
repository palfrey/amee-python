from urlgrab.URLTimeout import URLTimeoutError
from urlgrab.GetURL import GetURL
from xml.etree.ElementTree import fromstring, ElementTree

class AMEE:
	def __init__(self, server, username = None, password = None):
		self.server = server
		self.username = username
		self.password = password
		self.token = None
		self.cache = GetURL(debug=True)
		self._auth()
	
	def _auth(self, refresh = False):
		assert self.username!=None and self.password != None
		if refresh:
			max_age = 0
		else:
			max_age = -1
		data = self.cache.get("http://%s/auth"%self.server, data={"username":self.username,"password":self.password},headers={"Accept":"application/xml"}, max_age = max_age)
		self.token = data.headers.cookies()["authToken"]
		return True

	def _get_authed(self,uri):
		try:
			assert self.token != None
			data = self.cache.get("http://%s/%s"%(self.server,uri),headers={"Accept":"application/xml","Authtoken":self.token}, max_age = -1).read()
		except URLTimeoutError, e:
			if e.code == 401: # only do t
				self._auth(refresh=True)
				assert self.token != None
				data = self.cache.get("http://%s/%s"%(self.server,uri),headers={"Accept":"application/xml","Authtoken":self.token}, max_age = -1).read()
			else:
				raise
		xml = fromstring(data)
		return ElementTree(xml)

	def DataCategory(self, path = None):
		if path == None:
			return self._get_authed("data")
		else:
			return self._get_authed("data/%s"%path)
	
if __name__ == "__main__":
	(u,p) = [x.strip() for x in open("config").readlines() if x.strip()!=""]
	a = AMEE("stage.amee.com", u,p)
	print a.DataCategory()
