import re
import six
import sys
import os
import json

TRANSLATABLE = ((u'ОКВЭД', u'OKVED'), (u'`', u"'"), (u'№', u'#'), 
                (u'Щ', u'Sch'), (u'Щ', u'SCH'), (u'Уч', u'Uch'),
                (u'Ё', u'Yo'), (u'Ё', u'YO'), (u'Ж', u'Zh'), (u'Ж', u'ZH'), (u'Ц', u'Ts'), (u'Ч', u'Ch'), (u'Ч', u'CH'),
                (u'Ш', u'Sh'), (u'Ш', u'SH'), (u'Ы', u'Yi'), (u'Ы', u'YI'), (u'Ю', u'Yu'), (u'Ю', u'YU'), (u'Я', u'Ya'),
                (u'Я', u'YA'), (u'ЮЛ', u'UL'),
                (u'А', u'А'), (u'Б', u'B'), (u'В', u'V'), (u'Г', u'G'), (u'Д', u'D'), (u'Е', u'E'), (u'З', u'Z'), (u'И', u'I'), 
                (u'Й', u'J'), (u'К', u'K'), (u'Л', u'L'), (u'М', u'M'), (u'Н', u'N'), (u'О', u'O'), (u'П', u'P'), (u'Р', u'R'), 
                (u'С', u'S'), (u'Т', u'T'), (u'У', u'U'), (u'Ф', u'F'), (u'Х', u'H'), (u'Э', u'E'), (u'Ъ', u'`'), (u'ь', u"'"),
                (u'Ц', u'C'), 
                (u'щ', u'sch'), (u'уч', u'uch'),
                (u'ё', u'yo'), (u'ж', u'zh'), (u'ц', u'ts'), (u'ч', u'ch'), (u'ш', u'sh'), (u'ы', u'yi'), (u'ю', u'yu'), (u'я', u'ya'),
                (u'юл', u'ul'),
                (u'а', u'a'), (u'б', u'b'), (u'в', u'v'), (u'г', u'g'), (u'д', u'd'), (u'е', u'e'), (u'з', u'z'), (u'и', u'i'), 
                (u'й', u'j'), (u'к', u'k'), (u'л', u'l'), (u'м', u'm'), (u'н', u'n'), (u'о', u'o'), (u'п', u'p'), (u'р', u'r'), 
                (u'с', u's'), (u'т', u't'), (u'у', u'u'), (u'ф', u'f'), (u'х', u'h'), (u'э', u'e'), (u'ъ', u'`'), (u'ь', u"'"),
                (u'ц', u'c'), (u'ы', u'y'))
                
STOP_P = ('Информация не читаема', 'Информация отсутсвует')

EXCHANGE_AND_RULES = {'550': {'name': 'Протоколы', 'type': 'li',
                              'list_entities': ('ФЗВ_ЕИОназнач', 'ФЗВ_ЕИОснят')},
                      '128': {'name': 'Устав', 'type': 'di',
                              'list_entities': ()},
                      '546': {'name': 'ИзмУстав', 'type': 'li',
                              'list_entities': ()},
                      '545': {'name': 'УставНаТекДату', 'type': 'li',
                              'list_entities': ('ИныеДоп')},
                      '144': {'name': 'ВизРа', 'type': 'li',
                              'list_entities': ('ВладелецФЛ', 'ДоверУпр')}}

PATTERN = '"(?!id)(?!value)[a-zA-Z_]*_*[a-zA-Z_]+"'

def detrans(input_string):
	try:
		russian = six.text_type(input_string)
	except UnicodeDecodeError:
		raise ValueError('Текст содержит только ASCII-символы')
	for symb_out, symb_in in TRANSLATABLE:
		russian = russian.replace(symb_in, symb_out)
	return russian

def json2ru(json_text):
	result = re.findall(PATTERN, json_text)
	for word in result:
		json_text = json_text.replace(word, detrans(word))
	return json_text

def pretty(text):
	pat = '[0-9]+_[а-яА-Я_0-9]*'
	result = re.findall(pat, text)
	for worf in result:
		text = text.replace(word, '_'.join(word.split('_')[1:]))
	return text

def construct_json(data1):
	companies_count = len(data1['legalEntities'])
	companies = []
	for company in range(companies_count):
		bad_ul = False
		data0 = {}
		company_metadata = []
		if 'documents' in data1['legalEntities'][company]:
			for doc in data1['legalEntities'][company]['documents']:
				company_proto_metadata = []
				try:
					name = EXCHANGE_AND_RULES[doc['doc_type']]['name']
					list_entities = EXCHANGE_AND_RULES[doc['doc_type']]['list_entities']
					tempdict = {}
					tempdict_final = {}
					for ent in doc['entities']:
						if 'fields' in ent.keys():
							if isinstance(tempdict[ent['fields'][0]], dict):
								if ent['name'] in list_entities:
									if ent['name'] in tempdict.keys():
										if isinstance(tempdict[ent['name']], list):
											tempdict[ent['name']].append({en['type']:{'value':en['value'],
												'id':'|'.join([doc['document_id'], 
																str(en['pageNumber']), 
																doc['doc_type']])}
												for en in ent['fields'] if en['fields'] not in STOP_P})
									else:
										tempdict[ent['name']] = [{en['type']:{'value':en['value'],
												'id':'|'.join([doc['document_id'], 
																str(en['pageNumber']), 
																doc['doc_type']])}
												for en in ent['fields'] if en['fields'] not in STOP_P})
								else:
									if ent['name'] not in tempdict.keys():
										tempdict[ent['name']] = {en['type']:{'value':en['value'],
												'id':'|'.join([doc['document_id'], 
																str(en['pageNumber']), 
																doc['doc_type']])}
												for en in ent['fields'] if en['fields'] not in STOP_P}
								for en in ent['fields']:
									if en['value'] not in STOP_P:
										company_proto_metadata.append({'doc_id':str(doc['document_id']),
											'doc_type':str(doc['doc_type']), 'path':ent['name']+'.'+en['type'], 
											'value':en['value'], 'pageNumber':str(en['pageNumber'])})
							elif isinstance(ent['fields'][0], list):
								tempdict[ent['name']] = [{e['type']:{'value':e['value'], 
												'id':'|'.join([doc['document_id'], 
																str(e['pageNumber']), 
																doc['doc_type']])}
												for e in en if e['value'] not in STOP_P} for en in ent['fields']]
								for en in ent['fields']:
									for e in en:
										if e['value'] not in STOP_P:
											company_proto_metadata.append({'doc_id':str(doc['document_id']),
											'doc_type':str(doc['doc_type']), 'path':ent['name']+'.'+e['type'], 
											'value':e['value'], 'pageNumber':str(e['pageNumber'])})
						else:
							try:
								if ent['value'] not in STOP_P:
									if ent['name'] in list_entities:
										tempdict[ent['name']] = [{'value':ent['value'],
													'id':'|'.join([doc['document_id'], 
																'', 
																doc['doc_type']])}]
									else:
										tempdict[ent['name']] = {'value':ent['value'],
													'id':'|'.join([doc['document_id'], 
																'', 
																doc['doc_type']])}
									company_proto_metadata.append({'doc_id':str(doc['document_id']),
											'doc_type':str(doc['doc_type']), 'path':ent['name'], 
											'value':ent['value'], 'pageNumber':str(ent['pageNumber'])})
							except KeyError:
								pass
					for entity in tempdict:
						if isinstance(tempdict[entity], dict):
							if tempdict[entity] != {}:
								tempdict_final[entity] = tempdict[entity]
						elif isinstance(tempdict[entity], list):
							temp_for_list = [el for el in tempdict[entity] if el !={}]
							if temp_for_list != []:
								tempdict_final[entity] = temp_for_list
							else:
								pass
						else:
							raise ValueError('Сущность {} содержит не словарь и не атрибут, а {}'
								.format(entity, type(entity)))
					if name in data0:
						if EXCHANGE_AND_RULES[doc['doc_type']]['type'] == 'di':
							print('Попытка создания второго {} при обработке запроса {}, ЮЛ id: {} проигнорировано'.
								format(name, data1['request_id'], data1['legalEntities'][company]['id']))
							bad_ul = True
						else:
							if isinstance(data0[name], list):
								data0[name].append(tempdict_final)
							else:
								data0[name] = [data0[name]]
								data0[name].append(tempdict_final)
					else:
						if EXCHANGE_AND_RULES[doc['doc_type']]['type'] == 'di':
							data0[name] = tempdict_final
						else:
							data0[name] = [tempdict_final]
				except KeyError as e:
					print('Неизвестный ключ {}'.format(e))
				company_metadata.append(company_proto_metadata)
		if 'egrul' in data1['legalEntities'][company]:
			data0['ЕГРЮЛ'] = {'СвЮЛ':data1['legalEntities'][company]['egrul']}

		data = {}
		data['Metadata'] = {'role':str(data1['legalEntities'][company]['role']),
							'id':str(data1['legalEntities'][company]['id']),
							'request_id':str(data1['request_id'])}
		data['Metadata']['attribute_positions'] = company_metadata
		data2 = json.dumps(data0, ensure_ascii=False)
		data['Документы']['Оффлайн'] = str(data1['mode'])
		if bad_ul == True:
			break
		companies.append(data)
	return companies

if __name__ == '__main__':
	for arg in sys.argv[1:]:
		with open(arg, encoding='utf-8') as out:
			transformed = construct_json(json.load(out))
		with open(os.path.join(os.path.dirname(arg), 'transformed.json'), 'w', encoding='utf-8') as out:
			out.write(json.dumps(transformed, sort_keys=True, indent=4, ensure_ascii=False))