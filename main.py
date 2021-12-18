import feedparser
import pdfkit
import re
import os
from datetime import datetime, timedelta
#config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe') #needed on windows but not on pi

options = {'enable-local-file-access':None}

feeds = ['https://rss.app/feeds/Ft4D8XEer3UHVrlu.xml', 'https://sandsvendor100.tumblr.com/rss', 'https://rss.app/feeds/OZ6PcsgstPae8bM4.xml']
post_limit = 5
nook_root_dir = '/mnt/My Files'


def get_last_checked():
    with open('last_checked.txt', 'r') as f:
        return datetime.strptime(f.read(), '%Y-%m-%d %H:%M:%S.%f').timestamp()


def process_username(url):
    if 'tumblr.com' in url:
        username = re.findall(r'//([\d\w]+)\.', url)[0]
    #todo: add more platforms
    elif ('twitter.com' in url) or ('pinterest.com' in url):
        username = re.findall(r'com/([\d\w_]+)', url)[0] #this may not capture all usernames, i'm not familiar with what kinds of characters twitter allows
    else:
        username = re.findall(r'//(?:www.)?([\d\w]+)\.', url)[0]
    #print('username: ', username)
    return username


def make_test_checked(): #for testing, pretend posts were last gotten 5 years ago (for instance the dezeenb tumblr makes nice dummy data but has not been updated in 3 years)
    with open('./last_checked.txt', 'w') as f:
        last_week = datetime.now() - timedelta(days=1800)
        f.write(str(last_week))


def make_pdf(posts_list):
    for poster in posts_list:
        title = list(poster.keys())[0]#this is the username
        for post in poster[title]:
            #link = post['link']
            try: #look for images
                image = '<img src=\"'+str(post['img']['src'])+'\"/><br>'
            except KeyError:
                try: image = '<img src=\"'+str(post['media_content'][0]['url'])+'\"/><br>'
                except KeyError:pass
                pass
            content = str(post['summary'])
            # tumblr seems to add excessive line breaks
            content = content.replace('<br /> <br />', '') 
            content = content.replace('"', '\"')
            date = str(post['published'])
            # add the other info to the html
            try:
                content = image + content
            except UnboundLocalError:#no image
                pass
            # if there's more than one image, use only the first
            imeges = re.findall('<img src=\"[^>]+/>', content)
            if len(imeges)>1:
                for imege in imeges[1:]:
                    content = content.replace(imege, '')
            content = ('<h3>' + date + '</h3>') + content
            content = ('<h1>' + title + '</h1>') + content
            content = '<head><meta charset="UTF-8"></head>' + content
            with open('./'+title+str(poster[title].index(post))+'output.html', 'w') as f:
                f.write(content)

    # todo: make sure posts are added in chronological order
    # create the front page
    with open('aaaaaaaafrontpage.html', 'w') as f:
        f.write('<style>font-family: "Times New Roman", Times, serif;</style><h1>NEW POSTS FOR '+str(datetime.strftime(datetime.now(),'%m/%d/%Y'))+'</h1><br><h3>retrieved at '+datetime.strftime(datetime.now(),'%I:%M'))

    # make pdf and clean up the files
    file_list = [file for file in os.listdir('./') if '.html' in file]
    if file_list:
        # make sure the 'cover' page is first by swapping it
        old_first = file_list[0]
        indexof_cover = file_list.index('aaaaaaaafrontpage.html')
        file_list[0] = 'aaaaaaaafrontpage.html'
        file_list[indexof_cover] = old_first
        try:
            pdfkit.from_file(file_list, options=options, verbose=True, output_path=nook_root_dir+'/posts.pdf')
        except OSError: #nook not connected
            pdfkit.from_file(file_list, options=options, verbose=True, output_path='.\posts.pdf')
    else:
        try:
            pdfkit.from_string('<h1>NO NEW POSTS FOR TODAY :D </h1>',output_path=nook_root_dir+'/posts.pdf')
        except OSError:#nook not connected
            pdfkit.from_string('<h1>NO NEW POSTS FOR TODAY :D </h1>', output_path='.\posts.pdf')

    for file in file_list:
        os.remove(file)


def get_feeds(feeds):
    posts = []
    last_updated = get_last_checked()
    for feed in feeds:
        #todo: figure out what the number of posts returned is determined by.
        newsfeed = feedparser.parse(feed)
        #pprint.pprint(newsfeed['feed'])
        title = newsfeed['feed']['link']
        title = process_username(title)
        posts_to_check = newsfeed.entries
        checked_posts = []
        added_this_round = 0
        for post in posts_to_check:
            if added_this_round>=post_limit:
                continue
            #make sure they are new
            try:
            	published_date = datetime.strptime(post['published'], '%a, %d %b %Y %H:%M:%S %z').timestamp()
            except ValueError:
                published_date = datetime.strptime(post['published'], '%a, %d %b %Y %H:%M:%S %Z').timestamp()
            #make sure its not a duplicate
            #post_contents = [poste['summary'] for poste in checked_posts]
            #print(post_contents)
            #print(post['summary'])
            if (published_date>last_updated): #and (post['summary'] not in post_contents):
                checked_posts.append(post)
                added_this_round +=1
        #posts_to_check = [post for post in posts_to_check if ]
        postss = {title:checked_posts}
        posts.append(postss)
    make_pdf(posts)
    with open ('./last_checked.txt', 'w') as f:
        f.write(str(datetime.now()))


#make_test_checked()
get_feeds(feeds)
