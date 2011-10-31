Snackvote
---------

A reddit-inspired site to vote on snack food for an office.  Currently only works for products from stongs (http://stongs.com).

To run, setup a virtualenv environment with the included requirements.txt (virtualenv env; . env/bin/activate; pip install -r requirements.txt). Then run "python site.py".  Users for the site are extracted from the Authorization header, so it is assumed that the cherrypy site will be sitting behind a reverse proxy, such as nginx or apache, that is providing HTTP auth.  If this is not the case, modify get_username in site.py.

A local sqlite database named votes.db will be created.  Change this in site.py:main() as required.