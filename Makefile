PACKAGE_VERSION=0.0.1
prefix=/usr

all:

clean:
	fixme

install:
	install -d -m 0755 "$(DESTDIR)/$(prefix)/lib/wrtd/plugins"
	cp -r wct-pppoe "$(DESTDIR)/$(prefix)/lib/wrtd/plugins"
	find "$(DESTDIR)/$(prefix)/lib/wrtd/plugins/wct-pppoe" -type f | xargs chmod 644
	find "$(DESTDIR)/$(prefix)/lib/wrtd/plugins/wct-pppoe" -type d | xargs chmod 755

uninstall:
	rm -rf "$(DESTDIR)/$(prefix)/lib/wrtd/plugins/wct-pppoe"

.PHONY: all clean install uninstall
