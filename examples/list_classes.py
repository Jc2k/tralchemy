
import tralchemy

Class = tralchemy.types.get_class("rdfs:Class")
for c in Class.get():
    print c.uri
