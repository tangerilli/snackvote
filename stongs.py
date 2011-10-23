"""
deli->cheese->blue cheeses (class 12, product group 35, product id 138)
deli->crackers->Gone Crackers (class 12, product group 61, product id 522)
dairy->cheese->baking cheese (class 11, product group id 34, product id 1548)

Category structure is:

Top-level category (class id)
 -> Sub-category (product group id)
   -> Brand category (product id)
     -> product (id?)

"""

import logging
log = logging.getLogger("stongs")
import requests
import pickle
import os
import re
from BeautifulSoup import BeautifulSoup

COOKIEFILE = '/tmp/stongcookies.lwp'
INDEX_URL = "http://www.stongs.com/index.cfm?fuseaction=content&page_id=1"
PRODUCTS_URL = "http://www.stongs.com/index.cfm?fuseaction=order&class=%s&product_group_id=%s&product_id=%s"
CACHEFILE = '/tmp/stongs.cache'
cache = {}

class ParseError(Exception): pass

class Category(object):
    def __init__(self, name, id, parent=None):
        self.name = name
        self.id = id
        self.children = []
        self.parent = parent
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return str(self)
        
    def slugified(self):
        return self.name.lower().replace(" ", "_").replace("/", "_")
        
    def as_url(self):
        components = [self.slugified()]
        parent = self.parent
        while parent:
            components.append(parent.slugified())
            parent = parent.parent
        components.reverse()
        return "/".join(components)
        
    def find_child(self, child_name):
        for child in self.children:
            if child.slugified() == child_name:
                return child
        return None
        
    def get_parents(self):
        parents = [self]
        parent = self.parent
        while parent:
            parents.append(parent)
            parent = parent.parent
        parents.reverse()
        return parents
        
def _get_page(url):
    cached_pages = cache.setdefault("cached_pages", {})
    # TODO: Add expiration times
    if url in cached_pages:
        return cached_pages[url]
    log.info("Opening %s" % url)
    r = requests.get(url)
    cached_pages[url] = r.content
    cache["cached_pages"] = cached_pages
    return r.content
    
def _persist_cache():
    log.info("Saving cache")
    f = open(CACHEFILE, "w")
    pickle.dump(cache, f)
    f.close()
    
def load_cache():
    if os.path.exists(CACHEFILE):
        global cache
        log.info("Loading cache")
        f = open(CACHEFILE, "r")
        cache = pickle.load(f)
        f.close()
    
def get_category_list():
    category_list = []
    page = _get_page(INDEX_URL)
    
    category_id_match = re.search("classes = Array\((.*?)\)\;", page)
    category_match = re.search("classes_names = Array\((.*?)\)\;", page)
    if not category_match:
        raise ParseError("Could not find top-level category list")
    cat_data = category_match.groups(0)[0]
    cat_id_data = category_id_match.groups(0)[0]
    categories = [c.replace("'", "").replace("\\", "") for c in cat_data.split("','")]
    category_ids = cat_id_data.split(",")
    for name, id in zip(categories, category_ids):
        category = Category(name, id)
        category_list.append(category)
    
    group_list = []    
    groups_id_match = re.search("groups_class = Array\((.*?)\)\;", page)
    groups_match = re.search("groups_names = Array\((.*?)\)\;", page)
    if not groups_match:
        raise ParseError("Could not find groups list")
    groups_data = groups_match.groups(0)[0]
    groups_id_data = groups_id_match.groups(0)[0]
    groups = [c.replace("'", "").replace("\\", "") for c in groups_data.split("','")]
    group_ids = groups_id_data.split("','")
    for idx, (name_list, id_list) in enumerate(zip(groups, group_ids)):
        parent_cat = category_list[idx]
        for name, id in zip(name_list.split("|"), id_list.split(",")):
            category = Category(name, id, parent=parent_cat)
            parent_cat.children.append(category)
            group_list.append(category)

    products_id_match = re.search("products_groups = Array\((.*?)\)\;", page)
    products_match = re.search("products_groups_names = Array\((.*?)\)\;", page)
    if not products_match:
        raise ParseError("Could not find products list")
    products_data = products_match.groups(0)[0]
    products_id_data = products_id_match.groups(0)[0]
    products = [c.replace("'", "").replace("\\", "") for c in products_data.split("','")]
    products_ids = products_id_data.split("','")
    for idx, (name_list, id_list) in enumerate(zip(products, products_ids)):
        parent_cat = group_list[idx]
        for name, id in zip(name_list.split("|"), id_list.split(",")):
            category = Category(name, id, parent=parent_cat)
            parent_cat.children.append(category)
        
    return category_list
    
def get_products(category):
    products = []
    products_id = category.id
    groups_id = category.parent.id
    class_id = category.parent.parent.id
    url = PRODUCTS_URL % (class_id, groups_id, products_id)
    page = _get_page(url)
    soup = BeautifulSoup(page)
    form = soup.find("form", {"id":"orderForm"})
    table = form.parent
    for row in table.findAll("tr", {"valign":"top"}):
        cells = row.findAll("td")
        title = cells[1].b.string
        if cells[2].string:
            price = cells[2].string.strip()
        else:
            price = "NA"
        order_input = cells[3].input
        product_id = int(order_input['id'].replace("sub_", ""))
        products.append((title, price, product_id, url))
    return products
    
if __name__=="__main__":
    logging.basicConfig()
    for handler in logging.getLogger().handlers:
        handler.setFormatter(logging.Formatter("%(asctime)s %(name)-8s %(levelname)-7s - %(message)s"))
    formatter = logging.Formatter('%(name)s: %(levelname)s %(message)s')
    logging.getLogger().setLevel(logging.INFO)
    
    
    load_cache()
    cat_list = get_category_list()
    deli = cat_list[12]
    print deli
    print deli.children
    cheese = deli.children[0]
    print cheese
    print cheese.children
    asiago = cheese.children[0]
    print get_products(asiago)
    _persist_cache()