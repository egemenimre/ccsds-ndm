import reader

x = reader.Xml("src\\sample_xml\\cdm_example_section4.xml")

l = x.find_('COMMENT')
for i in range(len(l)):
    print("line: ",l[i].line)
    print("content: ",l[i].content)
    print("list of attributes: ",l[i].attr)

k = x.find_("CD_AREA_OVER_MASS")
for i in range(len(k)):
    print("line: ",k[i].line)
    print("content: ",k[i].content)
    print("list of attributes: ",k[i].attr)
    print("dictionary of attributes: ",k[i].attributes)
    print("units value: ",k[i].attributes['units'])