"""
  Walk a mailing list archive and index it
"""

import tralchemy
import mailbox

from tralchemy.nmo import Message
from tralchemy.nco import Contact

# Delete all messages
count = 0
for m in Message.get():
    count = count + 1
    m.delete()

print "Deleted %d messages" % count

# Inject some messages
count = 0
mbox = mailbox.mbox("~/Desktop/2009-April.txt")
for mail in mbox:
    count = count + 1
    m = Message.create(commit=False)

    for field, value in mail.items():
        if field == 'To':
            m.to = Contact.create(fullname=value)
        elif field == 'From':
            #from is a reserved word
            pass
        elif field == 'CC':
            m.cc = Contact.create(fullname=value)
        elif field == 'Bcc':
            m.bcc = Contact.create(fullname=value)

    m.commit()

print "Injected %d messages" % count
