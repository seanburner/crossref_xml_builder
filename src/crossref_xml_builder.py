## ###################################################################################################################
##  Program :       Crossref_XML_Builder
##  Author  :
##  Install :   pip3 install requests  inspect platform argparse 
##  Example :
##              python3 crossref_xml.builder.py --csv_config=files/config.csv --display_config  --doi_batch_id=grant_0013
##              python3 crossref_xml.builder.py --csv_config=files/config.csv --display_config --xml_output_file=files/aicr_grants_20250623_Q=806.xml --doi_batch_id=aicr_grants_20250623

##  Notes   :
##              SciSpace XML builder    : https://scispace.com/for-publishers/crossref-deposit-xml/?ref=scispace.com
##              Crossref documentation  : https://www.crossref.org/documentation/schema-library/markup-guide-record-types/grants/
##                                          https://gitlab.com/crossref/schema/-/blob/master/best-practice-examples/grants-0.1.1.xml
##                                          https://gitlab.com/crossref/schema/-/blob/master/best-practice-examples/0.2.0_grant.xml
## ###################################################################################################################
import os
import re
import sys
import time
import pandas as pd
import numpy  as np 
import getpass
import inspect
import platform
import argparse
import functools
import requests 
import http.client
import urllib.request
from urllib.parse import urlparse

from datetime import datetime 

First_Indent = "\t * "

class XML_Builder :
    def __init__(self):
        """
            Initialize the base variables for the class         
        """
        self._Head_     = ""
        self._Body_     = ""
        
        self._XML_      = ""
        self._ROR_DF_   = None 


    def XML( self ) -> str :
        """
            Returns the XML after Buidling

            PARAMETERS :
            RETURNS    :
                        str  : formatted XML
        """

        return self._XML_



    
    def Build( self, configs : dict , csvFile : object , ror_df : object) -> None :
        """
            Build the XML from the configuration dictionary and the csv contents

            PARAMETER:
                        configs     :  configuration dictionary
                        csvFile     :  dataframe - input contents from csv file
                        ror_df      :  dataframe of ror entries for verification
            RETURNS  :
                        Nothing 
        """
        empty_resources =  0
        try:
            self._ROR_DF_ = ror_df
            empty_resources  = csvFile['url'].isna().sum()
            if empty_resources == csvFile.shape[0] :
                print("\t\t Resource column ( article landing page) is all empty, cannot proceed ")
                return

            
            if empty_resources > 0 :
                print("\t\t Resource column ( article landing page) is missing values, BE AWARE  ")
                
            self.BuildHead( configs )
            self.BuildBody( configs, csvFile )

            self._Body_ += "</doi_batch>"
            
            self._XML_ = self._Head_ + self._Body_
            
        except: 
            print("\t\t|EXCEPTION: XML_BUILDER::" + str(inspect.currentframe().f_code.co_name) + " - Ran into an exception:" )
            for entry in sys.exc_info():
                print("\t\t >>   " + str(entry) )

    
    def BuildHead ( self, configs : dict  ) -> None :
        """
            Build the <HEAD> </HEAD> portion of the XML

            PARAMETER :
                        configs :  configuration dictionary 
            RETURNS   :
                        Nothing 
        """
        contents = ""
        
        try:
            contents =  str('<?xml version="1.0" encoding="UTF-8"?> \n'+
                            '  <doi_batch xmlns="http://www.crossref.org/grant_id/0.2.0"\n' + 
                               '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n' +
                               '    xmlns:fr="http://www.crossref.org/fundref/submission/1.0"\n' + 
                               '    xsi:schemaLocation="http://www.crossref.org/grant_id/0.2.0 http://www.crossref.org/schemas/grant_id0.2.0.xsd \n' +
                               '    http://www.crossref.org/fundref/submission/1.0 http://www.crossref.org/schemas/fundref1.0.xsd" \n ' +
                               '    version="0.2.0"> \n')
            contents += ' <head> \n'
            contents += '\t<doi_batch_id>' + configs[ 'doi_batch_id' ] + '</doi_batch_id> \n'
            contents += '\t<timestamp>' + str(configs[ 'timestamp' ]).replace('.','')[:13] + '</timestamp>\n'
            contents += '\t<depositor>\n' 
            contents += '\t\t<depositor_name>Sean Burner</depositor_name>\n'
            contents += '\t\t<email_address>s.burner@aicr.org</email_address>\n'
            contents += '\t</depositor>\n'
            contents += f'\t<registrant>{configs[ "registrant" ]}</registrant>\n'
            contents += ' </head>\n'

            self._Head_ = contents
        except:
            print("\t\t|EXCEPTION: XML_BUILDER::" + str(inspect.currentframe().f_code.co_name) + " - Ran into an exception:" )
            for entry in sys.exc_info():
                print("\t\t >>   " + str(entry) )



    def Affiliation(   self, row, project_index : int , person_index : int , configs : dict , csvFile : object   ) -> str :
        """
            Build the <AFFILIATION> </AFFILIATION> portion of the XML where the bulk of the contents are 

            PARAMETER :
                        row           :  current row from csv data file
                        project_index :  indexx for which project is focus
                        person_index  :  indexx for which project is focus 
                        configs       :  configuration dictionary 
                        csvFile       :  dataframe - input contents from csv file
            RETURNS   :
                        string of formatted XML for AFFILIATIONS section
        """
        index               =  1
        ror                 = ""
        contents            = ""
        institution         = ""
        institution_cty     = ""
        
        try:      
            ror             = f'ror_{project_index:02}_{person_index:02}_{index:02}'
            institution     = f'institution_{project_index:02}_{person_index:02}_{index:02}'
            institution_cty = f'institution-country_{project_index:02}_{person_index:02}_{index:02}'

            while ( institution in csvFile.columns) and not(  pd.isnull( row[institution] ) ):
                contents   +=  f'\t\t<affiliation>\n'

                # NEED TO HAVE A SYSTEM TO CHECK THE NAME THAT MATCHESS ROR WHEN GIVEN OR ELSE IGNORE THE ROR ATTRIBUTE
                if ((ror  in csvFile.columns) and not(  pd.isnull(row[ror] ))   and
                        self._ROR_DF_ is not None  ):
                    institute_name = self._ROR_DF_[self._ROR_DF_["id"] == row[ror] ]['name'].values[0]
                    if institute_name != "" : 
                        contents +=  f'\t\t  <institution>{institute_name}</institution>\n'
                        contents += f'\t\t  <ROR>{row[ror]}</ROR>\n'
                    else:
                        contents   +=  f'\t\t  <institution>{row[institution]}</institution>\n'
                else:
                    if (institution_cty  in csvFile.columns)  and not( pd.isnull(  row[institution_cty] ) ):
                        contents   +=  f'\t\t  <institution country="{row[institution_cty]}">{row[institution]}</institution>\n'
                    else:
                        contents   +=  f'\t\t  <institution>{row[institution]}</institution>\n'
                
                contents   +=  f'\t\t</affiliation>\n'
                
                index += 1 
                ror             = f'ROR_{project_index:02}_{person_index:02}_{index:02}'
                institution     = f'institution_{project_index:02}_{person_index:02}_{index:02}'
                institution_cty = f'institution-country_{project_index:02}_{index:02}'
                
           

            return contents
        except:
            print("\t\t|EXCEPTION: XML_BUILDER::" + str(inspect.currentframe().f_code.co_name) + " - Ran into an exception:" )
            for entry in sys.exc_info():
                print("\t\t >>   " + str(entry) )



    def Investigators(   self, row, project_index : int , configs : dict , csvFile : object ) -> str :
        """
            Build the <INVESTIGATORS> </INVESTIGATORS> portion of the XML where the bulk of the contents are 

            PARAMETER :
                        row           :  current row from csv data file
                        project_index :  indexx for which project is focus 
                        configs       :  configuration dictionary 
                        csvFile       :  dataframe - input contents from csv file
            RETURNS   :
                        string of formatted XML for INVESTIGATORS section
        """
        index           =  1
        contents        = ""
        orchid          = ""
        givenName       = ""
        familyName      = ""
        alterName       = ""
        personRole      = "" 
        
        try:            
            contents        =  '\t<investigators>\n'
            orchid          = f'ORCID_{project_index:02}_{index:02}'
            givenName       = f'givenName_{project_index:02}_{index:02}'
            familyName      = f'familyName_{project_index:02}_{index:02}'
            alterName       = f'alternateName_{project_index:02}_{index:02}'
            personRole      = f'person_role_{project_index:02}_{index:02}'

            while ( givenName in csvFile.columns) or ( familyName in csvFile.columns) or ( alterName in csvFile.columns):
                if (personRole  in csvFile.columns)  and not( pd.isnull( row[personRole])  ):
                    contents   +=  f'\t  <person role="{configs[personRole]}">\n'
                else:
                    contents   +=  f'\t  <person role="investigator">\n'
                
                if (givenName  in csvFile.columns) and not(  pd.isnull(row[givenName] )):
                    contents += f'\t\t<givenName>{row[givenName]}</givenName>\n'
                if (familyName  in csvFile.columns) and not(  pd.isnull(row[familyName] ) ):
                    contents += f'\t\t<familyName>{row[familyName ]}</familyName>\n'
                if (alterName  in csvFile.columns)  and not(  pd.isnull( row[alterName] )  ):
                    contents += f'\t\t<alternateName>{row[alterName]}</alternateName>\n'
                    
                contents   += self.Affiliation(  row, project_index  , index,  configs , csvFile  )
                
                if (orchid in csvFile.columns)   and not( pd.isnull(row[orchid])  ):
                    contents += f'\t\t<ORCID>https://orcid.org/{row[orchid]}</ORCID>\n'
                contents   +=  f'\t  </person>\n'
                
                index += 1 
                orchid          = f'ORCID_{project_index:02}_{index:02}'          
                givenName       = f'givenName_{project_index:02}_{index:02}'
                familyName      = f'familyName_{project_index:02}_{index:02}'
                alterName       = f'alternateName_{project_index:02}_{index:02}'
                personRole      = f'person_role_{project_index:02}_{index:02}'
                
            contents        +=  '\t</investigators>\n'

            return contents
        except:
            print("\t\t|EXCEPTION: XML_BUILDER::" + str(inspect.currentframe().f_code.co_name) + " - Ran into an exception:" )
            for entry in sys.exc_info():
                print("\t\t >>   " + str(entry) )







    def Funding(   self, row, project_index : int , configs : dict , csvFile  ) -> str :
        """
            Build the <FUNDING> </FUNDING> portion of the XML where the bulk of the contents are 

            PARAMETER :
                        row           :  current row from csv data file
                        project_index :  indexx for which project is focus 
                        configs       :  configuration dictionary 
                        csvFile       :  dataframe - input contents from csv file
            RETURNS   :
                        string of formatted XML for FUNDING section
        """
        index           =  1
        contents        = ""
        fund_percent    = ""
        fund_name       = ""
        fund_id         = ""
        fund_scheme     = ""
        fund_type       = ""
        fund_amount     = ""
        fund_currency   = ""
        
        try:            
            
            fund_percent    = f'fund-percentage_{project_index:02}_{index:02}'
            fund_name       = f'funder-name_{project_index:02}_{index:02}'
            fund_id         = f'funder-id_{project_index:02}_{index:02}'
            fund_scheme     = f'fund-scheme_{project_index:02}_{index:02}'
            fund_type       = f'fund-type_{project_index:02}_{index:02}'
            fund_amount     = f'fund-amount_{project_index:02}_{index:02}'
            fund_currency   = f'fund-currency_{project_index:02}_{index:02}'

            while ( fund_amount in csvFile.columns) or ( fund_id  in csvFile.columns):
                contents   +=  f'\t<funding '
                if (fund_amount   in csvFile.columns)  and not( pd.isnull( row[fund_amount])  ):
                    contents   +=  f' amount="{row[fund_amount]}"'
                if (fund_currency   in csvFile.columns)  and not( pd.isnull( row[fund_currency])  ):
                    contents   +=  f' currency="{row[fund_currency]}"'
                if (fund_percent   in csvFile.columns)  and not( pd.isnull( row[fund_percent])  ):
                    contents   +=  f' funding-percentage="{row[fund_percent]}"'
                if (fund_type   in csvFile.columns)  and not( pd.isnull( row[fund_type])  ):
                    contents   +=  f' funding-type="{row[fund_type]}"'
                contents   +=  f' >\n'
                
                if (fund_name  in csvFile.columns) and not(  pd.isnull(row[fund_name] )):
                    contents += f'\t\t<funder-name>{row[fund_name]}</funder-name>\n'
                if (fund_id  in csvFile.columns) and not(  pd.isnull(row[fund_id] ) ):
                    contents += f'\t\t<funder-id>{row[fund_id ]}</funder-id>\n'
                if (fund_scheme  in csvFile.columns)  and not(  pd.isnull( row[fund_scheme] )  ):
                    contents += f'\t\t<funding-scheme>{row[fund_scheme]}</funding-scheme>\n'
                    
         
                contents   +=  f'\t</funding>\n'
                
                index += 1 
                fund_percent    = f'fund-percentage_{project_index:02}_{index:02}'
                fund_name       = f'funder-name_{project_index:02}_{index:02}'
                fund_id         = f'funder-id_{project_index:02}_{index:02}'
                fund_scheme     = f'fund-scheme_{project_index:02}_{index:02}'
                fund_type       = f'fund-type_{project_index:02}_{index:02}'
                fund_amount     = f'fund-amount_{project_index:02}_{index:02}'
                fund_currency   = f'fund-currency_{project_index:02}_{index:02}'
                
            

            return contents
        except:
            print("\t\t|EXCEPTION: XML_BUILDER::" + str(inspect.currentframe().f_code.co_name) + " - Ran into an exception:" )
            for entry in sys.exc_info():
                print("\t\t >>   " + str(entry) )


                
                
    def Project(   self, row, configs : dict , csvFile : object  ) -> str :
        """
            Build the <PPROJECT> </PROJECT> portion of the XML where the bulk of the contents are 

            PARAMETER :
                        row         :  current row from csv data file 
                        configs     :  configuration dictionary 
                        csvFile     :  dataframe - input contents from csv file
                        
            RETURNS   :
                        string of formatted XML for PROJECT section
        """
        index           = 1
        contents        = ""
        projToken       = ""
        descripToken    = ""
        award_end       = ""
        award_start     = ""
        award_amount    = ""
        award_currency  = ""
        
        try:
            contents        =  '     <project>\n'
            projToken       = f'project-title_{index:02}'
            descripToken    = f'description_{index:02}'
            award_end       = f'award-dates_end-date_{index:02}' 
            award_start     = f'award-dates_start-date_{index:02}' 
            award_amount    = f'award_amount_value_{index:02}'
            award_currency  = f'award_amount_currency_{index:02}' 
            
            while ( ( projToken in csvFile.columns) and not(  pd.isnull( row[projToken] ) ) ):
                contents += f'\t<project-title xml:lang="en">{row[projToken]}</project-title>\n'
                
                contents += self.Investigators( row, index  , configs , csvFile)

                ## INSTITUTION FOR THE PROJECT
                """
                institute   = f'institute_{index:02}'
                ror         = f'ror_{index:02}'
                if (  (institute in csvFile.columns and not(  pd.isnull( row[institute]) ) )  or
                      (ror in csvFile.columns and not(  pd.isnull( row[ror]) ) )     ):
                    contents += '\t<institution> \n'
                    if institute in csvFile.columns and not(  pd.isnull( row[institute]) ):
                        contents += f'\t\t<institution-name>{row[institute]}</institution-name> \n'
                    if ror in csvFile.columns and not(  pd.isnull( row[ror]) ):
                        contents += f'\t\t<institution-id>{row[ror]}</institution-id> \n'
                    contents += '\t</institution> \n'
                """
                if (descripToken  in csvFile.columns) and not(  pd.isnull( row[descripToken]) ):
                    contents += f'\t<description xml:lang="en">{row[descripToken]}</description>\n'
                    

                    
                if  (award_amount  in csvFile.columns) and not(  pd.isnull( row[award_amount]) )    :
                    contents += f'\t<award_amount '
                    if  (award_currency  in csvFile.columns) and not(  pd.isnull( row[award_currency])  ): 
                        contents += f'currency="{row[award_currency]}"' 
                    contents += f'>{row[award_amount]}</award_amount>\n'
                
                contents += self.Funding( row, index  , configs , csvFile  )
                
                if ( ( (award_start  in csvFile.columns) and not(  pd.isnull( row[award_start]) ) ) or 
                           ( (award_end  in csvFile.columns) and not(  pd.isnull( row[award_end]) ) )   ):
                    contents += f'\t<award-dates '
                    if ( (award_start  in csvFile.columns) and not(  pd.isnull( row[award_start]) ) ) :
                        contents += f' start-date="{row[award_start]}"  '
                    if ( (award_end  in csvFile.columns) and not(  pd.isnull( row[award_end]) ) )  :
                        contents += f' end-date="{row[award_end]}" '
                    contents += f' />\n'
                    
                index += 1      
                projToken       = f'project-title_{index:02}'
                descripToken    = f'description_{index:02}'
                award_end       = f'award-dates_end-date_{index:02}' 
                award_start     = f'award-dates_start-date_{index:02}' 
                award_amount    = f'award_amount_value_{index:02}'
                award_currency  = f'award_amount_currency_{index:02}'
            contents += '     </project>\n'
            
            return contents 
        except:
            print("\t\t|EXCEPTION: XML_BUILDER::" + str(inspect.currentframe().f_code.co_name) + " - Ran into an exception:" )
            for entry in sys.exc_info():
                print("\t\t >>   " + str(entry) )




    def DOI_data(   self, row, configs : dict , csvFile : object  ) -> str :
        """
            Build the <AFFILIATION> </AFFILIATION> portion of the XML where the bulk of the contents are 

            PARAMETER :
                        row           :  current row from csv data file
                        configs       :  configuration dictionary 
                        csvFile       :  dataframe - input contents from csv file
            RETURNS   :
                        string of formatted XML for DOI_DATA section
        """
        contents            = ""
        
        try:
            contents     =  '     <doi_data>\n'
            if ('url' in csvFile.columns) and not(  pd.isnull( row["url"] ) ) :
                contents     += f'       <doi>{row["doi"]}</doi>  \n'
            contents     += f'       <resource>{row["url"]}</resource> \n'
            contents     += f'    </doi_data>\n'

            return contents
        except:
            print("\t\t|EXCEPTION: XML_BUILDER::" + str(inspect.currentframe().f_code.co_name) + " - Ran into an exception:" )
            for entry in sys.exc_info():
                print("\t\t >>   " + str(entry) )



    def BuildBody ( self, configs : dict , csvFile : object ) -> None :
        """
            Build the <BODY> </BODY> portion of the XML where the bulk of the contents are 

            PARAMETER :
                        configs     :  configuration dictionary 
                        csvFile     :  dataframe - input contents from csv file
                        
            RETURNS   :
                        Nothing 
        """
        projIndex    = 1
        projToken    ="" 
        personIndex  = 0
        affilIndex   = 0
        contents     = ""
        
        try:
            contents =  ' <body>\n'
            #project title
            for index, row in csvFile.iterrows():
                contents += '   <grant>\n'
                contents += self.Project( row, configs , csvFile )
                
                # AWARD  INFO
                if ('award-number' in csvFile.columns) and not(  pd.isnull( row['award-number'] ) ) :
                    contents += f'     <award-number>{row["award-number"]}</award-number>\n'
                    if ('award-start-date' in csvFile.columns) and not(  pd.isnull( row['award-start-date'] ) ) :
                        contents += f'     <award-start-date>{row[award-start-date]}</award-start-date>\n'

                contents += self.DOI_data( row, configs , csvFile  )
 
                contents += '   </grant>\n\n'
                
            contents +=  ' </body>\n'
            self._Body_ = contents
        except:
            print("\t\t|EXCEPTION: XML_BUILDER::" + str(inspect.currentframe().f_code.co_name) + " - Ran into an exception:" )
            for entry in sys.exc_info():
                print("\t\t >>   " + str(entry) )







def check_doi_links( doi_base : str , csvFile : object) -> None :
    """
        CHECKS TO SEE IF THE DOI LINKS /RESOURCE ARE ALREADY ACTIVE
        PARAMETERS :
                        doi_base    : base address to build doi links ( https:\\doi.org\\ )
                        csvFile     : dataframe of entries 
        RETURNS    :
                        nothing 
    """
    total    = 0
    doi_link = ""
    results  = { 'status' : { }, 'match' : {'True' : 0, 'False' : 0} }
    
    try:
        print("\n\n\t CONNECTION TIME               DOI                  STATUS  MATCHES            FINAL URL                 ")  
        for index, row in csvFile.iterrows():
            doi_link = doi_base + row["doi"]

            t_start = datetime.now() #time.time() 
            res     = requests.get(doi_link)
            t_end   = datetime.now() #time.time()
            total   += 1
            if res.status_code in results['status'] :
                results['status'][res.status_code] += 1
            else:
                results['status'][res.status_code] = 1
            results['match'][str(res.url==row['url'])] += 1
            print(f"\t {str(t_end-t_start):<13} | {doi_link:<33} | {res.status_code:<3} |  {res.url==row['url']}  | {res.url}  ")  
    except:
        print("\t\t|EXCEPTION: MAIN::" + str(inspect.currentframe().f_code.co_name) + " - Ran into an exception:" )
        for entry in sys.exc_info():
            print("\t\t >>   " + str(entry) )
    finally :        
        print("\n\t\t ========  Summary ========" )
        print(f"\t\t    TOTAL        : {total}" )
        print(f"\t\t    URL Matches  : True : {results['match']['True']}   False : {results['match']['False'] }" )
        print(f"\t\t\t ----- Links Statuses ------- " )
        for stat in results['status'].keys():
            print(f"\t\t\t   * {stat }  ->  {results['status'][stat]:03d} entries" )




def read_csv( fileName : str) -> object :
    """
        Read in the csv file 

        PARAMETER :
                    fileName  :  path and filename of csv file  
        RETURNS   :
                    df         : dataframe        
    """  
    df  = None 
    try:       
        if os.path.exists( fileName):
            try:
                df = pd.read_csv( fileName, encoding = "ISO-8859-1" )
            except :
                print('\t\t\t -> Problems reading into dataframe : ', fileName )
                for entry in sys.exc_info():
                    print("\t\t >>   " + str(entry) )
            return df 
        else:
            print("CSV File is not valid : " + fileName)
            return None          
    except:
        print("\t\t|EXCEPTION: MAIN::" + str(inspect.currentframe().f_code.co_name) + " - Ran into an exception:" )
        print("\t\t * Reading : " , fileName )
        for entry in sys.exc_info():
            print("\t\t >>   " + str(entry) )



def apply_csv_config ( configs : dict) -> dict:
    """
        IF THE USER PROVIDED A VALID CSV CONFIG FILE , APPLY THOSE SETTINGS AND THEN LATER APPLY OTHER COMMAND LINE ARGS

        PARAMETERS :
                        configs     : configuration dictionary 
        RETURNS    :
                        configuration dictionary 
    """
    config_file = None
    config_new  = { 'xml_output_file' :  str(datetime.now()).replace('-','').replace(' ','_').replace('.','').replace(':','') ,
                    'csv_input_file'  : "",
                    'article_type'    : '',
                    'doi_batch_id'    : '',
                    'timestamp'       :  str(datetime.now()).replace('-','').replace(' ','').replace(':','')[:13] ,  # prefer yyyymmddhhmmss or the unix epoch format ->  time.time()
                    'depositor_name'  : '',
                    'email_address'   : '',
                    'registrant'      : '',
                    'batch_log'       : '' ,
                    'csv_input_fields': False   ,
                    'ror_csv'         : '',
                    'check_links'     : False,
                    'doi_base'        : '',
                    'csv_config'      : '' ,
                    'display_config'  : False
                    } 
    try:
        if not os.path.exists(  configs['csv_config'] ) :
            print ("\t\t* Provided CSV config file was not present/readable")
            return configs

        config_file = read_csv( configs['csv_config'] )        
        for key in config_file.columns:            
            if key in config_new.keys():               
                config_new[ key] = config_file.iloc[0][key]

        # NOW APPLY WHAT WAS PARSED FROM THE COMMAND LINE         
        for key in configs.keys():
            if not ( configs[key] == '' or configs[key] == False ) :
                config_new[ key] = configs[key]
              
            
                
        return config_new
    except:
        print("\t\t|EXCEPTION: MAIN::" + str(inspect.currentframe().f_code.co_name) + " - Ran into an exception:" )        
        for entry in sys.exc_info():
            print("\t\t >>   " + str(entry) ) 

def update_args_field ( argValue , defaultValue  ) -> {} :
    """
        Updates the fields from the argument list. This way  preserves any default values
        
        PARAMETERS :
                    argValue      :  current field in the argparse
                    defaultValue  :  default value to assign if argValue is empty
        RETURNS    :
            the updated version of the configuration dictionary 
        
    """    
    if argValue or (not isinstance(argValue, bool) and argValue is not None and len( argValue) > 1):
        return argValue
    else:
        return defaultValue


def display_config(  configs : dict) -> None :
    """
        DISPLAY THE CONFIGURATION TO BE USED IN THE APPLICATION

        PARAMETERS:
                        configs    ; configuration dictionary 
        RETURNS   :
                        nothing 
    """

    try:
        print(f"{First_Indent}Application Configuration ")
        for key in configs.keys() :
            print(f'\t\t  {key:<20} | {configs[key]} ')
    except:
        print("\t\t|EXCEPTION: MAIN::" + str(inspect.currentframe().f_code.co_name) + " - Ran into an exception:" )
        for entry in sys.exc_info():
            print("\t\t >>   " + str(entry) )

            
def display_csv_input_fields() -> None :
    """
        Print the fields for the input csv file depending on the type of upload
        
        PARAMETERS:
        RETURNS   :
    """
    line         = "" 
    grant_fields = {
        'project-title_xx'              :{ 'type':'text',       'value' :"" ,                                           'note' : '_xx  represents a counter for multiple projects'},
        'description_xx'                :{ 'type':'text',       'value' :"" ,                                           'note' :'description of the project, _xx  represents a counter for multiple projects'},
        'award_amount_currency_xx'      :{ 'type':'enumerated', 'value' :"USD" ,                                        'note' :"Currency of grant,  _xx  represents a counter for multiple projects"},
        'award_amount_value_xx'         :{ 'type':'float',      'value' :"" ,                                           'note' :"Dollar amount given to the grant without ',' or '$',  _xx  represents multiple projects "},
        'funding-type_xx_aa'            :{ 'type':'enumerated', 'value' :"contract / grant" ,                           'note' :'Type of funding to be used '},
        'funding-amount_xx_aa'          :{ 'type':'enumerated', 'value' :"USD / EUR" ,                                  'note' :'Currency of funding, _aa  represents a counter for multiple funding sources per project'},
        'funding-currency_xx_aa'        :{ 'type':'float',      'value' :"" ,                                           'note' :'dollar value without commas, _aa  represents a counter for multiple funding sources per project'},
        'funding-percentage_xx_aa'      :{ 'type':'integer',    'value' :"" ,                                           'note' :'percentage grant was funded, _aa  represents a counter for multiple funding sources per project'},
        'funding-name_xx_aa'            :{ 'type':'text',       'value' :"" ,                                           'note' :'name of organization or individual that funded grant, _aa  represents a counter for multiple funding sources'},
        'funding-id_xx_aa'              :{ 'type':'hyperlink', 'value' :"" ,                                            'note' :'doi id link,  _aa  represents a counter for multiple funding sources'},
        'funding-scheme_xx_aa'          :{ 'type':'text',       'value' :"grant" ,                                      'note' :'Type of funding applied,  _xx  represents a counter for multiple projects'},
        'award-dates_start-date_xx'     :{ 'type':'yyyy-mm-dd', 'value' :"" ,                                           'note' :'Award Start Date, _xx  represents a counter for multiple projects '},
        'award-dates_end-date_xx'       :{ 'type':'yyyy-mm-dd', 'value' :"" ,                                           'note' :'Award End Date , _xx  represents a counter for multiple projects'},
        
        'person_role_xx_yy'             :{ 'type':'enumerated', 'value' :"lead_investigator / co-lead_investigator" ,   'note' :'_yy  represents a counter for multiple people'},
        'givenName_xx_yy'               :{ 'type':'text',       'value' :"" ,                                           'note' :'_yy  represents a counter for multiple people'},
        'alternateName_xx_yy'           :{ 'type':'text',       'value' :"" ,                                           'note' :'_yy  represents a counter for multiple people'},
        'familyName_xx_yy'              :{ 'type':'text',       'value' :"" ,                                           'note' :'_yy  represents a counter for multiple people'},
        'institution_xx_yy_zz'          :{ 'type':'text',       'value' :"" ,                                           'note' :'_zz  represents a counter for multiple institutions'},
        'institution-country_xx_yy_zz'  :{ 'type':'text',       'value' :"" ,                                           'note' :'Country where institution resides, _zz  represents a counter for multiple institutions'},
        'ROR_xx_yy_zz'                  :{ 'type':'text',       'value' :"" ,                                           'note' :'_zz  represents a counter for multiple institutions'},
        'ORCHiD_xx_yy'                  :{ 'type':'hypertext',  'value' :"" ,                                           'note' :'_yy  represents a counter for multiple people'},

        'institution_xx'                :{ 'type':'text',       'value' :"" ,                                           'note' :'Institution associated with Grant, _xx  represents a counter for multiple projects '},
        'award-number'                  :{ 'type':'integer',    'value' :"" ,                                           'note' :'ID number associated with this Grant'},
        'award-start-date'              :{ 'type':'yyyy-mm-dd', 'value' :"" ,                                           'note' :'Award Payment Start Date '}, 
        
        'doi'                           :{ 'type':'text',       'value' :"" ,                                           'note' :'DOI ID '},        
        'resource'                      :{ 'type':'hyperlink',  'value' :"" ,                                           'note' :'Landing page for article or research paper '}
       }

    
    try:
        print( f'\n Fields required in the CSV input file : ' )

        print( f"\n\t==============================   GRANT  =====================================================")
        print( f"\tFIELD NAME                         TYPE                     DEFAULT                  NOTES")
        for key, value  in grant_fields.items() :
            line = "\t{:<30}{:>5}".format(  key ," ")
            for key2, value2 in value.items() :
                line +=  "{:<20}{:>5}".format( value2, "" )
            print( line) 
            
    except:
        print("\t\t|EXCEPTION: MAIN::" + str(inspect.currentframe().f_code.co_name) + " - Ran into an exception:" )
        for entry in sys.exc_info():
            print("\t\t >>   " + str(entry) )


            
def parse_arguments() -> {} :
    """
        Parse the command line arguements  for configuration info , if not use the defaults
        
        PARAMETERS:
        RETURNS   :
    """
    args        = None 
    temp        = None    
    parser      = argparse.ArgumentParser(description='Import data from Data Application tool')
    confFields  = { 'xml_output_file' : "",
                    'csv_input_file'  : "",
                    'article_type'    : '',
                    'doi_batch_id'    : '',
                    'timestamp'       : "",
                    'depositor_name'  : '',
                    'email_address'   : '',
                    'registrant'      : '',
                    'batch_log'       : '' ,
                    'csv_input_fields': False   ,
                    'ror_csv'         : '',
                    'check_links'     : False,
                    'doi_base'        : '',
                    'csv_config'      : '' ,
                    'display_config'  : False
                    }
    matrix  = {	        'xml_output_file' : { 'help': 'The xml file version of the data for upload', 	'action' : None } ,
        		'csv_input_file'  : { 'help':	'csv file with fields' , 			'action' : None}, 
        		'article_type' 	  : { 'help': 'type of article to upload : grant', 		'action' : None },
			'doi_batch_id'    : { 'help': 'Batch name , should be unique' , 		'action' : None}, 
			'depositor_name'  : { 'help':	'Individual responsible for uploading xml', 	'action' : None}, 
			'email_address'	  : { 'help': 'Email of depositor' ,  			        'action' : None}, 
			'batch_log'       : { 'help': 'log of batch files created by this app', 	'action' : None }, 
			'registrant'	  : { 'help': 'Name of organization curating doi entries' , 	'action' : None},
			'csv_input_fields': { 'help': 'Display the fields for the csv file' , 	        'action' : 'store_true'},
			'ror_csv'	  : { 'help': 'csv file of ROR entries ( id, name ...) ' , 	'action' : None },
			'check_links'     : { 'help': 'check the doi links' , 			        'action' :'store_true' },
			'doi_base'	  : { 'help': 'https doi base to use when building links ', 	'action' : None },      
			'csv_config'	  : { 'help': 'CSV formatted configurtion file', 		'action' : None }, 
			'display_config'  : { 'help': 'Display the configuration', 			'action' : 'store_true'}
		}
    try:
        # SET DEFAULTS        
        for key in matrix.keys() :            
            parser.add_argument('--'+key     , help = matrix[key]['help'], action= matrix[key]['action'], dest=key )
        
        args = parser.parse_args()

        for key in matrix.keys() :
            confFields[key]   = update_args_field (  getattr(args, key) , confFields[key]) 


        return confFields

    except:
        print("\t\t|EXCEPTION: MAIN::" + str(inspect.currentframe().f_code.co_name) + " - Ran into an exception:" )
        for entry in sys.exc_info():
            print("\t\t >>   " + str(entry) )

def write_to_XML( xmlBuilder : object , configs : dict  ) -> None :
    """
        Write contents of the XML builder into file provided in configs

        PARAMETERS :
                    xmlBuilder  :  custom object to build xml contents
                    configs     :  dictionary of configuration info
                    
        RETURNS    :
                    Nothing 
    """

    try:
        with open( configs['xml_output_file']  ,"w") as xmlFile :
            xmlFile.write( xmlBuilder.XML().replace('&', '&amp;') )
        print( f"{First_Indent}Created XML : {configs['xml_output_file']}" )  
        
    except:
        print("\t\t|EXCEPTION: MAIN::" + str(inspect.currentframe().f_code.co_name) + " - Ran into an exception:" )
        for entry in sys.exc_info():
            print("\t\t >>   " + str(entry) )


            
def main() -> None :
    """
        main logic of application 
    """
    ror_df          = None    
    configs         = None
    config1         = None 
    batchLog        = None
    csvFile         = None
    xmlBuilder      = XML_Builder()
    required_fields = ['url','doi','project-title_01','award-number']
    
    try:
        # GET THE CONFIGURATION - EITHER DEFAULTS OR COMMAND LINE GIVEN        
        config1 = parse_arguments()       

        #IF CSV_CONFIG  USE THIS FIRST, THEN COMMAND LINE ARGS
        print( 'Checking csv_config ' )
        if config1['csv_config'] != ''  :
            configs = apply_csv_config ( config1)
        else :
            configs = config1 
            
        # IF THE USER NEEDS TO KNOW WHICH FIELDS TO INCLUDE
        print( 'Checking  csv input fields ' )
        if configs['csv_input_fields'] :
            display_csv_input_fields()
            
        # LOAD  THE BATCH LOG FILE
        # 2025-06-23  doesnt look like Crossref cares about re-using the batch id/name , so this is vestigial 
        #if configs['batch_log'] :
        #    batchLog = read_csv( fileName = configs['batch_log']  )
        #    print( 'batch log : ' + str(  batchLog )  )
        #else:
        #    print(' No Batch log ')

        # DISPLAY THE CONFIG IF SELECTED
        print( 'Checking display config ' )
        if configs['display_config'] :
            display_config(  configs)        

        # LOAD THE INPUT FILE
        print( 'Checking csv input file ' )
        if configs['csv_input_file'] != "" :
            csvFile = read_csv(fileName = configs['csv_input_file'])

            # CHECK IF THE DOI LINKS/RESOURCE ARE ALREADY ACTIVE  FOR DOI_DATA SECTION 
            if configs['check_links'] :
                check_doi_links( configs['doi_base'], csvFile)
            else:
                if configs['ror_csv'] != "" :
                    ror_df = read_csv( '../../CrossRef/15132361/v1.63-2025-04-03-ror-data/v1.63-2025-04-03-ror-data.csv')
                else:
                    print( '\t\t+ Proceeding without ROR verification')

                # CHECK TO MAKE SURE ATLEAST  REQUIRED FIELDS ARE IN THE CSVFILE 
                if not( set(required_fields).issubset( set (csvFile.columns ) )):
                    print (f"{First_Indent}Missing required fields in the CSV file , cannot proceed :  {required_fields}" )
                    return
                
                xmlBuilder.Build( configs, csvFile, ror_df )
                if  (configs['xml_output_file'] is None ) or len(configs['xml_output_file']) == 0  :
                    print( f"{First_Indent}No XML file provided for output, sending to screen : " )
                    print( xmlBuilder.XML() ) 
                else:
                    write_to_XML( xmlBuilder, configs )   
        else:
            print ( f"{First_Indent}No Input given, so no output can be provided")
        
    except:
        print("\t\t|EXCEPTION: MAIN::" + str(inspect.currentframe().f_code.co_name) + " - Ran into an exception:" )
        for entry in sys.exc_info():
            print("\t\t >>   " + str(entry) )


main()    
