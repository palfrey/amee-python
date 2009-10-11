from urlgrab.URLTimeout import URLTimeoutError
from urlgrab.GetURL import GetURL
from xml.etree.ElementTree import fromstring, ElementTree, tostring
from xml.parsers.expat import ExpatError
from types import ListType, DictType
import pprint
from os.path import join

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
		try:
			xml = fromstring(data)
		except ExpatError:
			open("dump","w").write(data)
			raise
		return ElementTree(xml).getroot()

	def DataCategory(self, path = None):
		if path == None:
			xml = self._get_authed("data/")
		else:
			assert path[0] == "/"
			pth = "data" + path
			xml = self._get_authed(pth)
		return DataCategory(xml,path)

	def DataItem(self, path):
		assert path[0] == "/"
		pth = "data" + path
		xml = self._get_authed(pth)
		return DataItem(xml, path)

class XMLDictionary(dict):
	def __init__(self, top):
		self.tag = top.tag[top.tag.find("}")+1:]
		for (k,v) in top.items():
			self[k] = v
		for k in top.getchildren():
			c = XMLDictionary(k)
			if k.text!=None:
				if c.keys() == []:
					assert not self.has_key(c.tag)
					self[c.tag] = k.text
					continue
				else:
					c["_text"] = k.text
			if len(c.keys()) == 0:
				continue
			if self.has_key(c.tag):
				orig = self[c.tag]
				if type(orig) != ListType:
					orig = [orig]
				orig.append(c)
				self[c.tag] = orig
			else:
				self[c.tag] = c

class ResourceDictionary(XMLDictionary):
	_Prefix = None
	def __init__(self, top, path):
		XMLDictionary.__init__(self,top)
		assert self._Prefix!=None
		if path == None:
			self.path = "/"
		else:
			self.path = path
		assert self._Prefix + "Resource" in self

		assert self._Prefix in self[self._Prefix + "Resource"],self
		for k in self[self._Prefix + "Resource"]:
			self[k] = self[self._Prefix + "Resource"][k]
		del self[self._Prefix + "Resource"]
		
		if "Children" in self:
			for k in self["Children"]:
				if len(self["Children"][k]) == 1:
					self["Children"][k] = self["Children"][k][self["Children"][k].keys()[0]]

class DataCategory(ResourceDictionary):
	_Prefix = "DataCategory"
	def _get_uid(self):
		return self["DataCategory"]["uid"]
	uid = property(_get_uid, None)

	def join(self, sub_path):
		return join(self.path, sub_path)

	def cat_paths(self):
		if "Children" not in self or "DataCategories" not in self["Children"]:
			return []
		if type(self["Children"]["DataCategories"]) == ListType:
			return [self.join(x["Path"]) for x in self["Children"]["DataCategories"]]
		else:
			return [self.join(self["Children"]["DataCategories"]["Path"])]
	
	def item_paths(self):
		if "Children" not in self or "DataItems" not in self["Children"]:
			return []
		print self
		if type(self["Children"]["DataItems"]) == ListType:
			return [(x["label"],self.join(x["path"])) for x in self["Children"]["DataItems"]]
		else:
			return [(self["Children"]["DataItems"]["label"],self.join(self["Children"]["DataItems"]["path"]))]

class DataItem(ResourceDictionary):
	_Prefix = "DataItem"

if __name__ == "__main__":
	(u,p) = [x.strip() for x in open("config").readlines() if x.strip()!=""]
	a = AMEE("stage.amee.com", u,p)
	dc = a.DataCategory()
	while True:
		print dc.uid
		cp = dc.cat_paths()
		print cp
		if len(cp)>0:
			dc = a.DataCategory(cp[0])
		else:
			ip = dc.item_paths()
			print ip
			dc = a.DataItem(ip[0][1])
			break

	pp = pprint.PrettyPrinter()
	pp.pprint(dc)
