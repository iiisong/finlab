from sec_edgar_downloader import Downloader
import os
import re

from src.presets import preload_list

class Form10KLoader():
    '''
    Class used to load SEC Form 10-K. 
    
    Public Attributes:
        loaded          - lookup dict of loaded forms to years loaded ([-1] if every year)
    '''
    def __init__(self, filepath : str = "../data") -> None:
        '''
        Initializes and process Form 10-K documents.
        
        ### Arguments:
            filepath : str
                string representation of filepath
        '''
        # Initialize a downloader instance. Download filings to the current
        # working directory. Must declare company name and email address
        # to form a user-agent string that complies with the SEC Edgar's
        # programmatic downloading fair access policy.
        # User-Agent: <Company Name> <Email Address>
        self.filepath = filepath
        
        # instantiate Downloader object
        self._loader = Downloader("None", "isaacsong03@gmail.com", self.filepath)
        
        # dict of loaded ticker symbol to a set of years loaded, [-1] if all loaded
        #   non-loaded ticker symbol not in dict
        # self.loaded = {}
        self.loaded = {'META': {-1}, 
                       'AAPL': {2017, 2020}, 
                       'LUMN': {2022}, 
                       'GWW': {2014}}
        
        # preload list of forms
        self.load_list(preload_list)
        
    def load(self, ticker: str, year: int=None) -> None:
        '''
        Downloads the Form-10K file for specified company (and optionally limit to certain years).
        
        ### Arguments:
            ticker : str
                ticker symbol
            year : int, optional
                year covered (form filed following year), all year if optional
        '''
        # avoid re-downloading by checking if already downloaded
        if ticker in self.loaded and (-1 in self.loaded[ticker] or year in self.loaded[ticker]):
            return
        
        print(ticker, year)
        
        # add ticker to lookup dict if first occurance
        if ticker not in self.loaded:
            self.loaded[ticker] = set([])
            
        if year is None:
            # load all years
            self._loader.get("10-K", ticker, download_details=True)
            
            # set loaded set as all loaded
            self.loaded[ticker] = set([-1])
        else:
            # load specific year
            self._loader.get("10-K", ticker, after=f"{year}-01-01", before=f"{year + 1}-01-01", download_details=True)
            
            # add year to loaded set 
            self.loaded[ticker].add(year)
            
    def load_list(self, ticker_list: list[tuple[str, int]]) -> None:
        '''
        Downloads a series of Form-10K file for specified list of companies (and optionally limit to certain years).
        
        ### Arguments:
            ticker_tuple : str, int
                list of (ticker, year) to load. load all years if year is None
            
                    ticker : str
                        ticker symbol
                    year : int, optional
                        year covered (form filed following year), all year if optional
        '''
        for ticker, year in ticker_list:
            print(f"Loading {ticker} {year}")
            self.load(ticker, year)
            print(f"Loaded {ticker} {year}")
        
        print(f"All loaded")
            
    def is_loaded(self, ticker: str, year: int=None) -> bool:
        '''
        Check if the Form-10K file is already downloaded for specified company (and optionally limit to certain years).
        
        ### Arguments:
            ticker : str
                ticker symbol
            year : int, optional
                year covered (form filed following year), all year if optional
                
        ### Returns :
            loaded : bool
                boolean representing if specified file/files is already loaded
        '''
        loaded = False
        
        # check if all tickers loaded
        if year is None:
            loaded = ticker in self.loaded and -1 in self.loaded[ticker]
            
        # specific ticker loaded
        else:
            loaded =  ticker in self.loaded and (-1 in self.loaded[ticker] or year in self.loaded[ticker])
        
        return loaded
    
    
    def get_filepath(self, ticker: str, year: int=None) -> str:
        '''
        Return the relative filepath for the Form-10K file is already downloaded for specified company (and optionally limit to certain years).
        Loads ticker year if not loaded.
        
        ### Arguments:
            ticker : str
                ticker symbol
            year : int, optional
                year covered (form filed following year), all year if optional
                
        ### Returns :
             : str
                relative filepath to the filing, None if not found
        '''
        # check if already loaded
        if not self.is_loaded(ticker, year):
            # loads otherwise
            self.load(ticker, year + 1)
        
        # get last 2 digit of year, offset by 1 for filing year (1 year after covered)
        short_year = str(year + 1)[-2:] 
        
        # generate relative path to 10-K folder 
        rel_path = os.path.join(self.filepath, "sec-edgar-filings", ticker, "10-K")
        
        # list of all current paths
        dirs = os.listdir(rel_path)
        
        # select file
        for d in dirs:
            # match filename to year (xxxxxxxxxx-{00-99}-xxxxxx)
            file = re.match(rf'\d{{10}}-{short_year}-\d{{6}}', d)
            if file is not None:
                return os.path.join(rel_path, file[0], "primary-document.html")
        
        return None
        
        