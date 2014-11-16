from ckan.lib.munge import munge_title_to_name

import re

def parse_datajson_entry(datajson, package, defaults, schema_version):
	# three fields (tag, license, resources) need extra handling.
	# 1. package["tags"]
	package["tags"] = [ { "name": munge_title_to_name(t) } for t in
		package.get("tags", "") if t.strip() != ""]

	# 2. package["license"]
	licenses = {
		'Creative Commons Attribution':'cc-by',
		'Creative Commons Attribution Share-Alike':'cc-by-sa',
		'Creative Commons CCZero':'cc-zero',
		'Creative Commons Non-Commercial (Any)':'cc-nc',
		'GNU Free Documentation License':'gfdl',
		'License Not Specified':'notspecified',
		'Open Data Commons Attribution License':'odc-by',
		'Open Data Commons Open Database License (ODbL)':'odc-odbl',
		'Open Data Commons Public Domain Dedication and License (PDDL)':'odc-pddl',
		'Other (Attribution)':'other-at',
		'Other (Non-Commercial)':'other-nc',
		'Other (Not Open)':'other-closed',
		'Other (Open)':'other-open',
		'Other (Public Domain)':'other-pd',
		'UK Open Government Licence (OGL)':'uk-ogl',
	}

	if not datajson.get("license", ""):
		package["license_id"] = licenses.get("License Not Specified", "");
	elif licenses.get(datajson.get("license", ""), ""):
		package["license_id"] = licenses.get(datajson.get("license", ""), "")

	# 3. package["resources"]
	# if distribution is empty, assemble it with root level accessURL and format.
	# but firstly it can be an ill-formated dict.
	distribution = datajson.get("distribution", [])
	if isinstance(distribution, dict): distribution = [distribution]
	if not isinstance(distribution, list): distribution = []

	downloadurl_key = "downloadURL"
	acccessurl_key = "accessURL"
	webservice_key = "webService"
	if datajson.get("processed_how", []) and "lowercase" in datajson.get("processed_how", []):
		acccessurl_key = acccessurl_key.lower()
		webservice_key = webservice_key.lower()

	if not distribution:
		for url in (acccessurl_key, webservice_key):
			if datajson.get(url, "") and datajson.get(url, "").strip():
				d = {
					url: datajson.get(url, ""),
					"format": datajson.get("format", ""),
					"mimetype": datajson.get("format", ""),
				}
				distribution.append(d)

	datajson["distribution"] = distribution

	for d in datajson.get("distribution", []):
		downloadurl_value = d.get(downloadurl_key, "").strip()
		acccessurl_value = d.get(acccessurl_key, "").strip()
		webservice_value = d.get(webservice_key, "").strip()

		which_value = (acccessurl_value or webservice_value) if schema_version == '1.0' else (acccessurl_value or downloadurl_value)

		if which_value:
			r = {}
			r['url'] = which_value
			r['format'] = d.get("format", "")
			r['mimetype'] = d.get("format", "") if schema_version == '1.0' else d.get("mediaType", "")
			r['description'] = d.get('description', '')
			r['name'] = d.get('title', '')

			package["resources"].append(r)
	
def extra(package, key, value):
	if not value: return
	package.setdefault("extras", []).append({ "key": key, "value": value })
	
def normalize_format(format, raise_on_unknown=False):
	if format is None: return
	# Format should be a file extension. But sometimes Socrata outputs a MIME type.
	format = format.lower()
	m = re.match(r"((application|text)/(\S+))(; charset=.*)?", format)
	if m:
		if m.group(1) == "text/plain": return "Text"
		if m.group(1) == "application/zip": return "ZIP"
		if m.group(1) == "application/vnd.ms-excel": return "XLS"
		if m.group(1) == "application/x-msaccess": return "Access"
		if raise_on_unknown: raise ValueError() # caught & ignored by caller
		return "Other"
	if format == "text": return "Text"
	if raise_on_unknown and "?" in format: raise ValueError() # weird value we should try to filter out; exception is caught & ignored by caller
	return format.upper() # hope it's one of our formats by converting to upprecase
