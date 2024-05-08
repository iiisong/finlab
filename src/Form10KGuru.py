import os
import asyncio
import google.generativeai as genai
import time

from Form10KText import Form10KText

class Form10KGuru():
    '''
    Generates of insights of text
    
    Public Attributes:
        form          - Form10KText object of form
        company         - company name
        year            - year covered (form filed following year)
    '''
    def __init__(self, form: Form10KText):
        '''
        Initializes and generates insights fromForm 10-K documents.
        
        ### Arguments:
            filepath : str
                string representation of filepath
        '''
        self.form = form
        self.company, self.year = form.company, form.year
        self.max_retries = 5
        self.delay = 60
        
        # configure and setup model
        genai.configure(api_key=os.environ["GEMINI_KEY"])
        self._model = genai.GenerativeModel('gemini-pro')
        
    
    async def get_insights(self) -> list[str]:
        '''
        Asyncronously returns list of insights.
        
        ### Returns:
            summaries : list[str[]
                generated summary
        '''
        return await asyncio.gather(self.generate_business_summary(), # business summary
                                    self.generate_financial_assessment(), # financial summary
                                    # self.generate_risk_assessment(), # risks
                                    )
        return result
        
    async def generate_business_summary(self, text: str=None)->str:
        '''
        Asyncronously generates a summary of general business operations of company.
        
        ### Returns:
            summary : str
                generated summary
        '''
        
        text = self.form.get_section('i1') if text is None else text
        prompt = f'''
        Item 1 of its Form 10-K: {text}
        
        Summarize briefly the general summary of its business model in raw text'''
        
        response = await self._model.generate_content_async(prompt)
        
        
        return f'''
            <h3>Business Summary</h3>
            <p>{response.text}</p>
        '''
    
    async def generate_financial_assessment(self, text: str=None)->str:
        '''
        Asyncronously assess the health of the finance reports of the company.
        
        ### Returns:
            summary : str
                generated html summary
        '''
        text = self.form.get_section('i8') if text is None else text
        prompt = f'''
        Item 8 of its Form 10-K: {text}
        
        Assess the financial health of the company specifically its balance sheet, income statement, and cash flow statement with explanation. 
        Return in a list output like "{{overall finance score}};;{{balance sheet score}};;{{reason}};;{{income statement score}};;{{reason}};;{{cash flow score}};;{{reason}}" with each element separated by double semicolons where 
        scores are in integers between 1 and 5, where 1 is the most unhealthy and 5 is the healthiest, and reasons are in normal text. 
        I am aware that you are not a financial expert but still want your opinion.
        '''
        response = await self._model.generate_content_async(prompt)
        print(response)
        
        # parse response
        ofs, bss, bss_r, ics, ics_r, cfs, cfs_r = response.text.split(';;')
        ofs, bss, ics, cfs = int(float(ofs)), int(float(bss)), int(float(ics)), int(float(cfs))
        self.finance_score = ofs
        
        return f'''
            <h3>Financial Score {'★' * ofs}{'☆' * (5 - ofs)}</h3>
            <div>
                <h4>Balance Sheet Score {'★' * bss}{'☆' * (5 - bss)}</h3>
                <p>{bss_r}</p>
            </div>
            <div>
                <h4>Income Statement Score {'★' * ics}{'☆' * (5 - ics)}</h3>
                <p>{ics_r}</p>
            </div>
            <div>
                <h4>Cash Flow Score {'★' * cfs}{'☆' * (5 - cfs)}</h3>
                <p>{cfs_r}</p>
            </div>
        '''
        
    async def generate_risk_assessment(self, text: str=None)->str:
        '''
        Asyncronously assess the health of the risks of the company.
        
        ### Returns:
            summary : str
                generated html summary
        '''
        text = self.form.get_section('i1a') if text is None else text
        prompt = f'''
        Item 1A of its Form 10-K: {text}
        
        Assess the risks of the company with special attention to more unusual risks considering the boilerplate nature of many Item 1A's. 
        Return in a Python list output like "{{overall risk score}};;{{reason}}" where 
        scores are in integers between 1 and 5, where 1 is the most unhealthy and 5 is the healthiest, and reasons are in normal text. 
        I am aware that you are not a financial expert but still want your opinion.
        '''

        response = await self._model.generate_content_async(prompt)
        print(response)
        
        # parse response
        ors, ors_r = response.text.split(';;')
        ors = int(float(ors))
        self.risk_score = ors
        
        return f'''
            <h3>Risk Score {'★' * ors}{'☆' * (5 - ors)}</h3>
            <p>{ors_r}</p>
        '''
    
    # UNUSED
    async def generate_market_temperature(self, text: str=None)->str:
        '''
        Asyncronously assess the tone of DMA
        
        ### Params:
            text : str
                text input to model
        
        ### Returns:
            summary : str
                generated summary
        '''
        
        text = self.form.get_section('i7') if text is None else text
        prompt = f'''
        Item 7 of Form 10-K: {text}
        
        Briefly assess the tone and optimism of management. 
        Return in a Python list output like "{{overall risk score}};;{{reason}}" where 
        scores are in integers between 1 and 5, where 1 is the most pessimistic and 5 is the optimistic, and reasons are in in normal text. 
        I am aware that you are not a financial expert but still want your opinion.
        '''

        response = await self._model.generate_content_async(prompt)
        return response.text
    
    # UNUSED
    async def generate_future_proof(self, text: str=None)->str:
        '''
        Asyncronously Estimate how future-proof current business model is to current AI developemnts.
        
        ### Params:
            text : str
                text input to model
        
        ### Returns:
            summary : str
                generated summary
        '''
        
        text = self.form.get_section('i1')
        prompt = f"How sustainable is the business model technical-wise in face of the current AI boom and score it out of 10 with 0 being not sustainable at all. Here is the Business Summary of their Form 10-K: {text}"

        response = await self._model.generate_content_async(prompt)
        return response.text