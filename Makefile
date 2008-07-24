NAME = portage-mod_jabber
VERSION = 0.0.5.2-dev
PLUGIN_FILE = mod_jabber.py

snapshot: clean
	mkdir /tmp/$(NAME)-$(VERSION)
	cp * /tmp/$(NAME)-$(VERSION)
	cd /tmp && tar --exclude=".svn" --exclude="Makefile" -jcf $(NAME)-$(VERSION).tar.bz2 $(NAME)-$(VERSION)
	mv /tmp/$(NAME)-$(VERSION).tar.bz2 .
	md5sum $(NAME)-$(VERSION).tar.bz2 > $(NAME)-$(VERSION).md5
	sha512sum $(NAME)-$(VERSION).tar.bz2 > $(NAME)-$(VERSION).sha512
	rm -rf /tmp/$(NAME)-$(VERSION)

release: snapshot
	scp $(NAME)-$(VERSION).* milch:websites/software.usrportage.de/htdocs/$(NAME)

testinstall:
	python $(PLUGIN_FILE)
	sudo cp $(PLUGIN_FILE) /usr/lib64/portage/pym/portage/elog/$(PLUGIN_FILE)

clean:
	rm -rf *~ *.tar.bz2 *.sha512 *.md5 *.pyc
