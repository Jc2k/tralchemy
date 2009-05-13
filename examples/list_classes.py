
import tralchemy
from tralchemy.rdfs import Class

for c in Class.get():
    print c.uri
