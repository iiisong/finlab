'''
File to store preset values
'''

'''Loader Values'''
# list of tickers to load at launch (demo or other reasons)
    #  (ticker, year),  load all years if year is None
    #     ticker : str
    #         ticker symbol
    #     year : int, optional
    #         year covered (filed 1 year after), all year if optional
preload_list = [('META', None), 
           ('AAPL', 2017), 
           ('LUMN', 2022), 
           ('GWW', 2014)]


'''Parser Values'''

# str-to-str dictionary of with target, replacement as key-value pair respectively
ascii_replace_dict = {
    "&#160;": " ",
    "&#8217;": "'"
}

# dict mapping of item id to section label of 10-k form
id_to_section_label = {
    'i1': "Item 1.",
    'i1a': "Item 1A.",
    'i1b': "Item 1B.",
    'i3': "Item 2.",
    'i3': "Item 3.",
    'i4': "Item 4.",
    'i5': "Item 5.",
    'i6': "Item 6.",
    'i7': "Item 7.",
    'i7a': "Item 7A.",
    'i8': "Item 8.",
    'i9': "Item 9.",
    'i9': "Item 9A.",
    'i10': "Item 10.",
    'i11': "Item 11.",
    'i12': "Item 12.",
    'i13': "Item 13.",
    'i14': "Item 14.",
    'i15': "Item 15.",
}

# dict mapping of item id to section title of 10-k form
id_to_section_title = {
    'p1': "Part I",
    'i1': "Business",
    'i1a': "Risk Factors",
    'i1b': "Unresolved Staff Comments",
    'i2': "Properties",
    'i3': "Legal Proceedings",
    'i4': "Mine Safety Disclosures",
    'p2': "Part II",
    'i5': "Market for Registrant's Common Equity",# Related Stockholder Matters and Issuer Purchases of Equity Securities",
    'i6': "Selected Financial Data",
    'i7': "Management's Discussion and Analysis",# of Financial Condition and Results of Operations",
    'i7a': "Quantitative and Qualitative Disclosures About Market Risk",
    'i8': "Financial Statements and Supplementary Data",
    'i9': "Changes in and Disagreements with Accountants",# on Accounting and Financial Disclosure",
    'i9a': "Controls and Procedures",
    'i9b': "Other Information",
    'p3': "Part III",
    'i10': "Directors, Executive Officers and Corporate Governance",
    'i11': "Executive Compensation",
    'i12': "Security Ownership of Certain Beneficial Owners",# and Management and Related Stockholder Matters",
    'i13': "Certain Relationships and Related Transactions",#, and Director Independence",
    'i14': "Principal Accounting Fees and Services",
    'p4': "Part IV",
    'i15': "Exhibits, Financial Statement Schedules",
}

# dict mapping of item id to alternate titles or representations  of 10-k form
id_to_section_alts = {
    'i15': ["Exhibits and Financial Statement Schedules"],
}

# order of which sections appear in
id_order = ['p1', 'i1', 'i1a', 'i1b', 'i2', 'i3', 'i4', 'p2', 'i5', 'i6', 'i7', 'i7a', 'i8', 'i9', 'i9a', 'i9b', 'p3', 'i10', 'i11', 'i12', 'i13', 'i14', 'p4', 'i15']


''' Flask Presets '''

template = '''
<html>
    <head> 
        <title>SEC Insight</title> 
    </head>
    <body>
        <h1>Form-10K Insight Guru</h1>
        <p><em>Enter the company ticker and year to select the filing to process. </em></p>
        <form method="post" action=".">
            <label for="ticker">Ticker:</label>
            <input class="text" type="text" name="ticker" id="ticker" placeholder="ex. META">
            <label for="year">Year:</label>
            <input class="text" type="text" name="year"  id="year" placeholder="ex. 2023">
            <input type="submit" name="select_filing" value="Run">
        </form>
        {errors}
        <hr>
        <h2>{company} {year}</h2>
        <br> 
        <div><div>{insights}</div></div>
    </body>
</html>
<style>
    input.text{{width: 5em}}
</style>
'''