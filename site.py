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

import framework
from models import Product, User, Vote

import stongs
    
class browse(object):
    def __init__(self):
        self.categories = stongs.get_category_list()
    
    def find_category(self, category_name):
        for category in self.categories:
            if category.slugified() == category_name:
                return category
        return None
        
    def get_user(self, username):
        user = cherrypy.request.db.query(User).filter(User.username == username).first()
        if user is None:
            user = User(username)
            cherrypy.request.db.add(user)
        return user

    def get_product(self, product_info):
        product_name, price, product_id, url = product_info
        product = cherrypy.request.db.query(Product).filter(Product.id == product_id).first()
        if product is None:
            product = Product(product_id, product_name, url)
            cherrypy.request.db.add(product)
        return product

    def get_vote(self, product_id, user):
        return cherrypy.request.db.query(Vote).filter(Vote.user == user).filter(Vote.product_id == product_id).first()

    def get_vote_count(self, product_id):
        count = 0
        for vote in cherrypy.request.db.query(Vote).filter(Vote.product_id == product_id):
            count += vote.value
        return count
            
    def handle_vote(self, product_info, direction, vote_type):
        # TODO: Get an actual user
        username = "tony"
        user = self.get_user(username)
        product = self.get_product(product_info)
        vote = cherrypy.request.db.query(Vote).filter(Vote.user == user).filter(Vote.product == product).first()
        if vote is None:
            vote = Vote(product, user, 0)
            cherrypy.request.db.add(vote)
        if vote_type == "remove":
            cherrypy.request.db.delete(vote)
            direction = ""
        else:
            if direction == "up":
                vote.value = 1
            else:
                vote.value = -1
        
        response = {"vote_status":direction, "vote_count":self.get_vote_count(product.id)}
        return simplejson.dumps(response)

    def find_product_info(self, product_id, products):
        for product_name, price, id, url in products:
            if str(id) == str(product_id):
                return (product_name, price, id, url)
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
                products = stongs.get_products(product_category)
                product_info = self.find_product_info(product_id, products)
                if product_info is None:
                    raise cherrypy.HTTPError(404, "Unknown product id %s" % product_id)
                return self.handle_vote(product_info, direction, vote_type)                
            else:
                # TODO: Could return the number of votes or other info about this product for GET
                raise cherrypy.HTTPError(404, "Invalid method")
            
        else:
            lookup = TemplateLookup(directories=['templates'])
            template = Template(filename="templates/categories.html", disable_unicode=True, lookup=lookup)
            if product_category:
                template = Template(filename="templates/products.html", disable_unicode=True, lookup=lookup)
                products = stongs.get_products(product_category)
                user = self.get_user("tony")
                full_products = []
                for product_name, price, product_id, url in products:
                    # TODO: Ignore votes for this user older than a week or so
                    vote = self.get_vote(product_id, user)
                    if vote:
                        if vote.value > 0:
                            vote_class = "up"
                        elif vote.value < 0:
                            vote_class = "down"
                        else:
                            vote_class = ""
                    else:
                        vote_class = ""
                    full_products.append((product_name, price, product_id, url, vote_class, self.get_vote_count(product_id)))
                return template.render(products=full_products, current=product_category)
            elif subcategory:
                return template.render(categories=subcategory.children, current=subcategory)
            else:
                return template.render(categories=category.children, current=category)
        return "Found nothing"
    default.exposed = True

class top(object):
    def index(self):
        lookup = TemplateLookup(directories=['templates'])
        template = Template(filename="templates/products.html", disable_unicode=True, lookup=lookup)
        products = []
        # TODO: Take vote age into account (i.e. weight more recent votes more)
        # TODO: Show vote for current user, if any
        # TODO: Cache price
        for product in cherrypy.request.db.query(Product).join(Vote).filter(Vote.value > 0):
            products.append((product.name, "0", product.id, product.url, "", len(product.votes)))
            
        def cmp_products(x, y):    
            name, price, id, url, vote_type, x_votes = x
            name, price, id, url, vote_type, y_votes = y
            return cmp(x_votes, y_votes)
        products.sort(cmp_products)
        return template.render(products=products, current=None)
    index.exposed = True

class snacks(object):
    browse = browse()
    top = top()

def main(argv):
    stongs.load_cache()
    
    db_path = os.path.abspath(os.path.join(os.curdir, 'votes.db'))
    url = 'sqlite:///%s' % db_path

    framework.SAEnginePlugin(cherrypy.engine, url).subscribe()
    cherrypy.tools.db = framework.SATool()
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    conf = {'/static': {'tools.staticdir.on': True,
                        'tools.staticdir.dir': os.path.join(current_dir, 'static')},
            '/' : {'tools.db.on': True}}
    # Start the web server
    cherrypy.quickstart(snacks(), config=conf)

if __name__=="__main__":
    sys.exit(main(sys.argv))
    