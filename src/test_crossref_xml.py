## ###################################################################################################################
##  Program :   Crossref_XML_Builder_Test
##  Author  :
##  Install :   pip3 install requests  inspect platform argparse 
##  Example :	Scaffolding for tests 
##  Notes   :
## ###################################################################################################################import pytest
from crossref_xml_builder import write_to_XML



# Test cases for write_to_XML function 
# CURRENTLY A WASTE SINCE THE FUNCTION RETURNS VOID 
def test_write_to_XML():
   assert write_to_XML(None ,  {}) == None

