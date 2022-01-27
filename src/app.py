from flask import Flask, render_template, request, flash
import re
import requests
import justext
from bs4 import BeautifulSoup
import urllib.parse


from dotenv import load_dotenv,find_dotenv
load_dotenv(find_dotenv())

ignore_links = [
  "whatsapp",
  "javascript",
  "mailto",
]

replacements = {
  "‘":"",
  "’":"",
}
def getAllStopWords():
  stopwords = set()
  for language in justext.get_stoplists():
    stopwords.update(justext.get_stoplist(language))
  return stopwords

def extractlinks(link,content):
  link = urllib.parse.urlparse(link)
  links = []
  data = BeautifulSoup(content,"lxml")
  [links.append(x.get("href")) for x in data.find_all("a") if x.get("href")]
  links = [x for x in links if not x.startswith(tuple(ignore_links)) and not x.startswith("#") and not x == "/"]
  for i,x in enumerate(links):
    if x and not x.startswith("http"):
      links[i] = link._replace(path=re.sub(r"\.\.\/","",x),params="",query="",fragment="").geturl()
  links = list(set([x for x in links if x.startswith("http")]))
  return links

app = Flask(__name__)
app.secret_key = "thisissomethingsecret"
app.app_context().push()

@app.route('/', methods=['GET','POST'])
def homepage():
  if request.method == "POST":
    link = request.form.get("link",None)
    language = request.form.get("language",None)
    if not link:
      flash("Enter URL to Fetch.","danger")
    else:
      if not link.startswith(("http://","https://")):
        flash("Invalid URL.","danger")
      else:
        try:
          headers = {
              'User-Agent': 'Mozilla/5.0 (iPad; U; CPU OS 3_2_1 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Mobile/7B405'
          }
          response = requests.get(link,headers=headers,timeout=10)
          response.raise_for_status()
        except Exception as ex:
          flash("Server timed out.","danger")
        else:
          if not str(response.headers["Content-Type"]).startswith("text/html"):
            flash("Link is not valid HTML.","danger")
          else:
            if not language or language not in justext.get_stoplists():
              language = "All"
            if language in justext.get_stoplists() and language != "All":
              anyLangStopWords = justext.get_stoplist(language)
            else:
              anyLangStopWords = getAllStopWords()
            paragraphs = justext.justext(response.content,anyLangStopWords,99,100,0.1,0.32,0.2,200,True)
            paragraphs = [x.text for x in paragraphs if not x.is_boilerplate]
            links = extractlinks(link,response.content)
            if not paragraphs and not links:
              flash("No useful data found.","danger")
            else:
              if not paragraphs:
                flash("Found Links only.","warning")
                return render_template("homepage.html", link=link, links=links, language=language, languages=justext.get_stoplists())
              else:
                flash("Found Data and Links.","success")
                output = "\n".join(paragraphs).replace("\r\n","\n")
                for r in replacements:
                  output = output.replace(r,replacements[r])
              return render_template("homepage.html", link=link, links=links, outtext=output.split("\n"), language=language, languages=justext.get_stoplists())
      return render_template("homepage.html", link=link, language=language, languages=justext.get_stoplists())
  return render_template("homepage.html", languages=justext.get_stoplists())

@app.route('/about', methods=['GET','POST'])
def about():
  return render_template("about.html", languages=justext.get_stoplists())


if __name__ == "__main__":
    app.run(host="0.0.0.0",port="5002")