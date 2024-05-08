# Form 10K Guru

## Submission Information
Apologies for the late submission. Had 4 finals, move-out, and 24hr worth of flight travel within the past 12 days starting the day this assignment was released.

Originally planned to run on AWS Beanstalk but could not manage to configurate it in time. I am not a webdev so have little experience on that end.  There was continuous issues with deployment of the Flask app. To see it working, I made a [video](https://drive.google.com/file/d/1QyPPKGQIIrUCC4gCDNBddxX6NA67gvJK/view?usp=sharing).


## Technical Details

### Technical Summary
#### Techstack (All Python)
- sec_edgar_downloader
- BeautifulSoup
- Google Gemini 1.1.0 Pro API
- Flask (currently can run locally with Flask `python application.py`)
- ~~AWS Beanstalk (in progress, use local run above in meantime)~~ 
- (no frontend framework)

### Insights
- General Business Summary (Item 1)
    - Summarizes the overall business model and operation of the company. 
        - This is chosen as it is the simplest and most straightforward way to provide a short intro and base-line information about the company
- Financial Health (Item 8)
    - Assesses the overall financial state of the company
        - This and its subsections was chosen as it is the most cut-and-dry data and arguably the most valuable insight of a Form 10-K. This is as close to a medical report of a company as it reveals various aspects of its financial health and as it also includes recent history, it offers a good ay to analyze short term trends or instabilities.
    - Subsections of
        - Balance Sheet
        - Income Statement
        - Cash Flow
-
- Potential Future Insights
    - These are some developed or proposed insights to process int he future that was not implemented due to restrictions that comes along with free API's rate limits
        -  Risks (Item 1A)
            - Assesses the risks of the company
                - This is chosen as it is a valuable insight to detect if something is wrong. While the vast majority of the risks  are generally relatively boilerplate (in most times even all the risks mentioned), unusual risks are one of the earliest signs of red flags and can easily be the most important element of the whole form.
            - not used because exceeded rate limits
        - Managements Discussion and Analysis (Item 7)
        - Technnological industry sustainability (Item 1)

---

### Detailed Summary

#### Intro
The implementation is split into a pipeline of 4 different parts corresponding to the files `Form10KLoader.py`, `Form10KText.py`, `Form10KGuru.py`, and `application.py` which deals with the data loading, preprocessing, processing, and deployment respectively. It is split this way to have clean modular code with a clear direct pipeline from the loading to deployment. 

---
#### `Form10KLoader.py`
This class is responsible with the loading of the necessary Form 10-Ks that will be processed later. The library we are using is sec_edgar_downloader with its download_details flag to download human-readable, and mostly computer parsable, html webpage. By taking advantage of a cache system, it reduces the load time for repeated function calls. 

This class will only be used to handle the downloading and location of the data, the data (html string) is not directly sent from this class but instead being loaded directly from the file later.

This stage is relatively fully-fleshed and apart from better caching integration with the deployment, there are few potenital developments.

---

#### `Form10KText.py`
This class is responsbile with the pre-processing of the html and converts the html code into an indexed stripped-down text file that still maintains the main features of the original formatting. There are two main purposes of this class. 

The first goal of this stage would be to reduce the overall size of the data as it strips the extraneous html formatting which take up a substantial portion of the original html file. This reduction in size is necessary to cut down on the token-size for later when being sent to the LLM. With some html files going over a million tokens, this compresses the data while preserving the same level of information. 

The second goal of this stage would be to segment and index the massive document. Even after stripping away the html-formatting, the overall text file still exceeds the meager 60K-tokens per minute that Gemini allows. By locating the different "sections" of the text based on the legal requirements laid out by the SEC, we are able to break the document up into 16 sections. Through utilizing the table-of-contents and its anchors to split, we not only break the text down into smaller portions but also have the description of the content of each section. This allows us to easily know which section to load into the LLM whether preset or through RAG.

As this stage takes advantage of table-of-contents linking, it is by far the most fragile part of the project and prone to error. Additionally, it limits the code to only work on post-2010 files as the formatting is more inconsistent with links prior to this. This stage takes attempts different types of approaches to find the destination anchor of each section, starting with standard tag detection with BeautifulSoup to finally resorting to a small bit of regular expression. Large scale regular expression is not used for consistency considerations. LLM's are not used currently for speed considerations but can be used later. Future developments would be to improve consistency/range in recognizing destination anchors as well as potentially index non-anchored subsection valuable locations.

---

#### `Form10KGuru`
This class is responsible with the main processing of the text and generation fo the insight. Powered through *Google Gemini Pro*, this stage generates various valuable insights. As multiple insights requires multiple queries, each of which is very slow, we take advantage of asyncronous functions to have mutliple Gemini queries running in parallel. 

Each query takes advantage of some basic Retrieval Augmented Generation (RAG) and prompt engineering to provide the necessary textual information from the Form and to set up the response for easier parsing respectively. 

As this step requires the non-deterministic LLM's, this step is the main source of errors and inconsistencies. 
Such errors include:
-  Error 500: Internal System Failure. This is currently one of larger sources of inconsistencies. It is unsure where the error is located. Current speculation is that it is caused by exceeding the token per minute restriction from the server though it is a bit unclear as it sometimes errors more than 1 minute apart. Spacing requests 1.5-2 minutes apart seems to aleviate most of the issues.
- Parsing issues. Although some prompt engineering is done to encourage output string in a specific parseable manner, the nature of non-deterministic functions will still occasionally generate outputs that fail to confine to the specified format and break when attempted to parse

--- 

#### `application.py`
The last step of the pipeline is a simple bare-bones Flask webapp hosted on AWS Elastic Beanstalk without any frontend framework. Flask was chosen because of its easy integration with python which the rest of the code is written in. No front-end framework was used because of time-constraints and because of my relative experience working with backend-supported webapps. AWS Elastic Beanstalk was used because of its versatility and ease of deployment though that could be disputed. No buckets are used so any download request is downloaded on the server directly. This is another area of improvement.

This step is the main source of development currently as AWS has been breaking constantly and is still stuck in debugging.