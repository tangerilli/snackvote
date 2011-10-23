"""
URL structure:

GET /deli/cheese
 - Returns page with a list of subcategories (asiago, etc..)

GET /deli/cheese/asiago
 - Returns page with list of asiago cheeses with voting arrows

GET /deli/cheese/asiago/3930
 - Invalid?
 
POST /deli/cheese/asiago/3930
 - Should include vote type, returns json data containing vote count

TODO: Add current category to page title
"""
import sys
import os

from mako.template import Template
from mako.lookup import TemplateLookup
import cherrypy
import simplejson

import stongs
    
class browse(object):
    def __init__(self):
        self.categories = stongs.get_category_list()
    
    def find_category(self, category_name):
        for category in self.categories:
            if category.slugified() == category_name:
                return category
        return None
        
    def index(self):
        lookup = TemplateLookup(directories=['templates'])
        template = Template(filename="templates/categories.html", disable_unicode=True, lookup=lookup)
        return template.render(categories=self.categories, current=None)
    index.exposed = True

    def default(self, category_name, subcategory_name=None, product_category_name=None, product_id=None, direction=None, vote_type=None):
        category = self.find_category(category_name)
        if category is None:
            raise cherrypy.HTTPError(404, "Unknown category %s" % category_name)
        
        if subcategory_name:
            subcategory = category.find_child(subcategory_name)
            if subcategory is None:
                raise cherrypy.HTTPError(404, "Unknown category %s" % subcategory_name)
        else:
            subcategory = None
            
        if product_category_name:
            product_category = subcategory.find_child(product_category_name)
            if product_category is None:
                raise cherrypy.HTTPError(404, "Unknown category %s" % product_category_name)
        else:
            product_category = None

        if product_id:
            if cherrypy.request.method.upper() == "POST":
                print "Handling vote for %s" % product_id
                if vote_type == "add":
                    modifier = "mod"
                else:
                    modifier = ""
                response = {"vote_status":direction}
                return simplejson.dumps(response)
            else:
                # TODO: Could return the number of votes or other info about this product for GET
                raise cherrypy.HTTPError(404, "Invalid method")
            
        else:
            lookup = TemplateLookup(directories=['templates'])
            template = Template(filename="templates/categories.html", disable_unicode=True, lookup=lookup)
            if product_category:
                template = Template(filename="templates/products.html", disable_unicode=True, lookup=lookup)
                products = stongs.get_products(product_category)
                return template.render(products=products, current=product_category)
            elif subcategory:
                return template.render(categories=subcategory.children, current=subcategory)
            else:
                return template.render(categories=category.children, current=category)
        return "Found nothing"
    default.exposed = True

class snacks(object):
    browse = browse()

def main(argv):
    stongs.load_cache()
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    conf = {'/static': {'tools.staticdir.on': True,
                          'tools.staticdir.dir': os.path.join(current_dir, 'static')}}
    # Start the web server
    cherrypy.quickstart(snacks(), config=conf)

if __name__=="__main__":
    sys.exit(main(sys.argv))
    