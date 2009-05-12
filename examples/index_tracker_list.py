"""
  Walk a mailing list archive and index it
"""

import tralchemy
import mailbox

Message = tralchemy.types.get_class("nmo:Message")

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
    m = Message("http://localhost/message/"+str(count))

    for field, value in mail.items():
        if field == 'To':
            m.to = value
        elif field == 'From':
            #from is a reserved word
            pass
        elif field == 'CC':
            m.cc = value
        elif field == 'Bcc':
            m.bcc = value

    m.commit()

print "Injected %d messages" % count
