import bs4 # for typing-use
from bs4 import BeautifulSoup
import re

from presets import ascii_replace_dict, id_to_section_label, id_to_section_title, id_to_section_alts

class Form10KText():
    '''
    Class used to extract text from SEC Form 10-K. 
    
    Public Attributes:
        filepath        - file path
        html            - html content
        text            - raw text content
        sections_ids    - list of section id's
        company         - company name
        year            - year covered (form filed following year)
        ein             - employer identification number (IRS)
        address         - address
        phone_number    - phone number
        form_results    - checkbox results of cover page (left-to-right, top-to-bottom)
        size            - length of text file in characters
    '''

    def __init__(self, filepath:str) -> None:
        '''
        Initializes and process Form 10-K documents.
        
        ### Arguments:
            filepath : str
                string representation of filepath
        '''
        # set filepath attribute
        self.filepath = filepath
        
        # set html attribute
        with open(filepath) as fp:
            self.html = fp.read()
            
        # clean-up html
        self.html = self.standardize_ascii(self.html, replace_dict=ascii_replace_dict)
        
        # soupify
        self._soup = BeautifulSoup(self.html, features='lxml')
        
        # extract section label to html location (index)
        self._html_indices = self.get_section_indices()
        
        # abuse python feature that has dict keys be mostly stable
        self.section_ids = ['intro', *id_to_section_label.keys(), 'end']
        
        # extract text and lookup table for section label id to index in text
        self.text, self._text_indices = self.extract_text()
        
        # set size attribute
        self.size = len(self.text)
        
        # extract general properties about filing
        try:
            self.company, self.year, self.ein, self.phone_number, self.address = self.extract_properties()
        except:
            print("extract properties failed")
            
        # extract form checkbox information (left-to-right, top-to-bottom)
        self.form_results = self.extract_checkboxes()
        
        
    @staticmethod
    def standardize_ascii(html: str, replace_dict: dict[str, str]=ascii_replace_dict) -> str:
        '''
        Standardizes file to clean special ascii characters like non-breaking space and special quote characters
        
        ### Arguments:
            html : str
                string representation of file
            replace_dict : dict[str, str], optional
                str-to-str dictionary of with target, replacement as key-value pair respectively
                default to pre-set dictionary set in parser.py
            
        ### Returns:
            standardized_text : str
                text after being replaced
        '''
        # create result file
        # partially redundant because python doesn't pass by reference
        standardized_text = html
        
        # iterate through replacement pairs
        for target, replacement in replace_dict.items():
            # replace each pair
            standardized_text = standardized_text.replace(target, replacement)
        
        return standardized_text


    def get_label_tag(self, label_id: str) -> bs4.element.Tag:
        '''
        Returns the html element of where label_id section starts.
        Section starts at the destination of where the label_id link from table of contents links to.
        
        ### Arguments:
            label_id : str
                string index of the section label id in document ['p1', 'i3', 'i5a', ...] 
            
        ### Returns:
            src_dest : bs4.element.Tag
                bs4.tag of which the label_id link in table of content is pointed to, None if not found
        '''
        # tag of table of content
        section_label = id_to_section_label[label_id].lower()
        toc_tag = self._soup.find_all(string=(lambda x: x 
                                              and (x.strip()[ : len(section_label)].lower() == section_label
                                                   or x.strip().lower() == section_label[:-1])))
        
        # check for long entry title
        if len(toc_tag) == 0: 
            long_title = id_to_section_title[label_id].lower()
            toc_tag = self._soup.find_all(string=(lambda x: x 
                                                  and (x.strip()[-len(long_title) : ].lower() == long_title 
                                                       or x.strip()[ : len(long_title)].lower() == long_title)))
                        
        # check for [Reserved] case
        if len(toc_tag) == 0: 
            reserved = f"{id_to_section_label[label_id]} [Reserved]".lower()
            toc_tag = self._soup.find_all(string=(lambda x: x and x.strip().lower() == reserved))
        
        # check for alternates
        if len(toc_tag) == 0:
            for alt in id_to_section_alts[label_id]:
                toc_tag = self._soup.find_all(string=(lambda x: x 
                                                    and (x.strip()[-len(alt) : ].lower() == alt.lower() 
                                                        or x.strip()[ : len(alt)].lower() == alt.lower())))
                
                if len(toc_tag) != 0:
                    break
                
        #debug
        if len(toc_tag) == 0:
            raise Exception(f'label_id {label_id}')
        
        # get anchor tag of tag
        anchor_tag = toc_tag[0]
        while not hasattr(anchor_tag, 'name') or anchor_tag.name not in ['a', 'tr']:
            anchor_tag = anchor_tag.parent
            
        # check for non-linked name case
        if anchor_tag.name == 'tr':
            anchor_tag = anchor_tag.find('a')
            if anchor_tag is None:
                return None
            
        # anchor id of the label (ex. sD0F7ECFEC8965FDE8B546D17642E8FED)
        anchor_id = anchor_tag['href'][1:]
        
        # destination anchor of label (where link points to in table of contents)
        src_dest = self._soup.find('a', attrs={'name': anchor_id})
        if src_dest == None:
            src_dest = self._soup.find(id=anchor_id)
        
        return src_dest


    def get_section_indices(self, label_list: list[str]=id_to_section_label.keys()) -> dict[str, int]:
        '''
        Creates and return lookup dict between label_id and integer index of location in the html string
        
        ### Arguments:
            label_list : list[str], optional
                list of label_id to generate index from, default to section labels of 10-K form
            
        ### Returns:
            id_to_index : dict[str, int]
                dict mapping string label_id to integer index of html
        '''
        # create id-to-tag lookup dict
        id_to_tag = {label: self.get_label_tag(label) for label in label_list}
        
        # create id-to-index lookup dict (-1 if not found)
        id_to_index = {id: self.html.find(str(tag)) if tag is not None else -1 for id, tag in id_to_tag.items()}
        
        return id_to_index
        
    def extract_subhtml(self, start_id: str=None, end_id: str=None, id_index: dict[str, int]=None) -> str:
        '''
        Extracts html between two tags
        Optional start and end tags cannot both be None
        
        ### Arguments:
            start_id : str, optional, default=None
                starting label_id for selection, inclusive, default to start if None
            end_id : str, optional, default=None
                ending label_id for selection non-inclusive, default to end if None
            id_index: dict[str, int], optional (default to self._html_indices)
                maps str label_id with int index in string
            
        ### Returns:
            sub_html : str
                substring of html representing the html between the two tags
                
        ### Exceptions:
            Exception
                start and end cannot both be None
        '''
        # assign default value
        if id_index is None:
            id_index = self._html_indices
        
        # trivial case
        if start_id is None and end_id is None:
            # raise Exception("start and end cannot both be None")
            return self.html
        
        # find index location of start of start tag
        start_index = id_index[start_id] if start_id is not None and start_id != 'intro' else 0
        
        # find index location of start of end tag
        end_index = id_index[end_id] if end_id is not None and end_id != 'end' else -1
        
        # get substring before start and end index
        sub_html = self.html[start_index : end_index]

        return sub_html

    @staticmethod
    def get_raw_text(html: str, soup: bs4.BeautifulSoup=None) -> str:
        '''
        Returns the raw text from html string
        
        ### Arguments:
            html : str
                html string
            soup : bs4.BeautifulSoup, optional (soupifies html otherwise)
                soup object of html string,
            
        ### Returns:
            text : str
                string of only the text in html
        '''
        formatted_text = ""
        
        if soup is None:
            soup = BeautifulSoup(html, 'html.parser')
        
        tag_stack = [soup]
        
        # manually iterates through the tags
        #       - stack-iterating .children instead of simple .descendents iteration because 
        #       of parents with hidden attributes. descendents would require tracking parent 
        #       and lineage which is much more complex than stack-iterating with children.
        while len(tag_stack) != 0:
            # pop first tag in stack
            tag = tag_stack.pop(0)
             
            # add text if string
            if type(tag) == bs4.element.NavigableString:
                formatted_text += tag
                continue
            
            # ignores all non-text childless bs4 html objects
            if not hasattr(tag, 'children'): continue
            
            # ignores all children of certain tags 
            if tag.name in ['title', 'ix:header']:
                continue
            
            # newline for new row
            if tag.name == 'tr':
                formatted_text += '\n'
            
            if tag.name == 'div':
                if tag.parent.name != 'td':
                    formatted_text += '\n'
                    
                else:
                    formatted_text += ' '
                    
            # puts child to front of tack
            tag_stack = [t for t in tag.children] + tag_stack
            
        return formatted_text.strip()
    
    def extract_text(self, id_index: dict[str, int]=None) -> tuple[str, dict[str, int]]:
        '''
        Extract text as well as location in text of sections
        
        ### Arguments:
            html : str
                html string
            label_id : str
                section label id
            id_index: dict[str, int], optional (default to self._html_indices)
                maps str label_id with int index in string
            
        ### Returns:
            result_text : str
                processed text of entire file
            text_indices : dict[str, int]
                dict of section labels id's to index in result_text
        '''
        # assign default value
        if id_index is None:
            id_index = self._html_indices
            
        # processed text of entire file
        result_text = ""
            
        # dict of section labels id's to index in result_text
        text_indices = {}
        
        # extract text from each section storing index location (barring end)
        for i in range(len(self.section_ids) - 1):
            id = self.section_ids[i]
            
            # skip if section not exist (-1)
            if id == -1:
                continue
            
            # set index location of each id
            text_indices[id] = len(result_text)
            
            # get next existing section
            next_i = -1
            for j in range(i + 1, len(self.section_ids) - 1):
                # dont need to check for all non-exist bc 'end' always at back
                if self._html_indices[self.section_ids[j]] != -1:
                    next_i = j
                    break
            
            # append section text to result_text
            result_text += self.get_raw_text(self.extract_subhtml(id, self.section_ids[next_i]))
            
        # set index location / length of end
        text_indices['end'] = len(result_text)
        
        return result_text, text_indices
    
    def get_section(self, label_id: str) -> str:
        '''
        Return section text of label_id from the text content.
        
        ### Arguments:
            label_id : str
                section label id
            
        ### Returns:
            text : str
                section text
        '''
        return self.text[self._text_indices[label_id] : 
                         self._text_indices[self.section_ids[self.section_ids.index(label_id) + 1]]]
    
    def extract_properties(self) -> tuple[str, int, str, str, str]:
        '''
        extracts filing properties
        
        ### Returns:
            company : str
                company ticker
            year : int
                year covered (form filed following year)
            ein : str
                employer identification number (IRS)
            address : str
                address
            phone_number : str
                phone number
        '''
        intro = self.get_section('intro')
        
        company = re.search(r'\n(.*)\n(?i)\(Exact name of Registrant as specified in its charter\)', intro)[1].strip()
        year = int(re.search(r'(?i)For the fiscal year ended \w+ \d+, (\d{4})', intro)[1].strip())
        ein = re.search(r'(?i)(\d{2}-\d{7})\n.+I.R.S. Employer', intro)[1].strip()
        phone_number = re.search(r'(?i)\n(.+)\n.+telephone number', intro)[1].strip()
        address = re.search(r'(?i)\n(.+)\n.+address', intro)[1].strip()
        
        return company, year, ein, phone_number, address
        
    def extract_checkboxes(self) -> list[bool]:
        '''
        extracts filing properties
        
        ### Returns:
            form_results : list[bool]
                checkbox results of cover page (left-to-right, top-to-bottom)
        '''
        intro = self.get_section('intro')
        boxes = [c for c in intro if c in ['☒', '☐']]
        return [b == '☒' for b in boxes]
    
    def print_info(self) -> None:
        '''Prints info about the form object'''
        # python prints are dumb
        print(f'''
Annual SEC Form-10K for {self.company} from {self.year} covering the overall financial performance over {self.year}. Form filed in {self.year + 1}.

Attributes:
    Company Name                                        {self.company}
    Year (filed in following year)                      {self.year}
    Employer Identification Number (IRS)                {self.ein}
    Address                                             {self.address}
    Phone Number                                        {self.phone_number}
    File Path                                           {self.filepath}
    Size (in characters)                                {self.size}
    ''')
        