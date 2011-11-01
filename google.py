import urllib
import requests
import simplejson

# Return a list of urls to images (len = 4)
# Example is from here - http://code.google.com/apis/imagesearch/v1/jsondevguide.html#json_snippets_python
# Google requires an API key which I have generated with 'https://development.sparkintegration.com'
# This probably can refactor alot instead of copy and pasting
def get_product_images(product_name):
    query = product_name.strip()
    query = urllib.quote(query)
    
    # print product_name
    # print query
    
    url = ('https://ajax.googleapis.com/ajax/services/search/images?' +
        'v=1.0&q=' + query +
        '&key=ABQIAAAACmdH40ypgsbXr33Vko_f8hRK5p-Y_hq-RWraBX1SaR3vezWLVRThH-i3FqBui10i7eO_mon3i-dJmA&userip=192.168.1.11')

    request = requests.get(url)
    results = simplejson.loads(request.content)
    if len(results['responseData']['results']) < 4:
        print "query %s failed!" % query
    else:
        images = []
        for image in results['responseData']['results']:
            images.append(image['url'])
        return images
    
    images = []
    #If orginal query does not return anything, I am going to try to split the query string using '-' 
    queries = query.split("-")
    # cannot split
    if len(queries) < 2:
        return images   
    url = ('https://ajax.googleapis.com/ajax/services/search/images?' +
        'v=1.0&q=' + queries[0].strip() +
        '&key=ABQIAAAACmdH40ypgsbXr33Vko_f8hRK5p-Y_hq-RWraBX1SaR3vezWLVRThH-i3FqBui10i7eO_mon3i-dJmA&userip=192.168.1.11')
    request = requests.get(url)
    results = simplejson.loads(request.content)
    if len(results['responseData']['results']) < 4:
        print "query %s failed!" % queries[0].strip()
        images.append("")
        images.append("")
    else:
        images.append(results['responseData']['results'][0]['url'])
        images.append(results['responseData']['results'][1]['url'])
    
    #Doing the second query 
    url = ('https://ajax.googleapis.com/ajax/services/search/images?' +
        'v=1.0&q=' + queries[1].strip() +
        '&key=ABQIAAAACmdH40ypgsbXr33Vko_f8hRK5p-Y_hq-RWraBX1SaR3vezWLVRThH-i3FqBui10i7eO_mon3i-dJmA&userip=192.168.1.11')
    request = requests.get(url)
    results = simplejson.loads(request.content)
    if len(results['responseData']['results']) < 4:
        print "query %s failed!" % queries[1].strip()
        images.append("")
        images.append("")
    else:
        images.append(results['responseData']['results'][0]['url'])
        images.append(results['responseData']['results'][1]['url'])  
    return images  
    