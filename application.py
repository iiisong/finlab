from flask import Flask, request
import asyncio

from src.Form10KLoader import Form10KLoader
from src.Form10KText import Form10KText
from src.Form10KGuru import Form10KGuru

from src.presets import template

form = None
guru = None

# EB looks for an 'application' callable by default.
app = Flask(__name__)


# add a rule for the index page.
@app.route("/", methods=["GET", "POST"])
def main_page():
    errors = ""
    ticker = ""
    year = ""
    insights = ""
    
    if request.method == "POST":
        valid = True
        
        # validate company ticker
        if len(request.form['ticker'].strip()) <= 0:
            errors += "<p>Ticker cannot be empty.</p>\n"
            valid = False
        
        # validate year input
        try:
            # filed in following year
            year = int(request.form["year"])
        except:
            errors += "<p>{!r} is not a number.</p>\n".format(request.form["year"])
            valid = False
        
        # validate company input    
        try:
            ticker = request.form["ticker"].upper()
        except:
            valid = False
            
        if not valid:
            return template.format(company=ticker, year=year, errors=errors, insights=insights)
        
        else:
            form_path = loader.get_filepath(ticker, year)
            
            form = Form10KText(form_path)
            guru = Form10KGuru(form)
            
            insights_list = asyncio.run(guru.get_insights())
            
            insights = '</div><br><div>'.join(insights_list)
            
            return template.format(company=ticker, year=year, errors=errors, insights=insights)
            
    return template.format(company=ticker, year=year, errors=errors, insights=insights)


# # add a rule when the page is accessed with a name appended to the site
# # URL.
# application.add_url_rule('/<username>', 'hello', (lambda username:
#     header_text + home_link + footer_text))

# run the app.
if __name__ == "__main__":
    # set up Form10K loader
    loader = Form10KLoader()
    
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    app.debug = True
    app.run()