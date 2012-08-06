'''
Created on 03.08.2012

@author: gschoenb
'''
from lxml import etree

class XmlReport(object):
    '''
    Creates an xml file with the test results of a device test.
    '''


    def __init__(self,testname):
        '''
        Constructor
        @param testname The name of the root tag, equals the name
        of the performance test. 
        '''
        
        ## The root tag of the xml file.
        self.__xml = etree.Element(testname)
        
    def getXml(self):
        return self.__xml
    
    def printXml(self):
        print(etree.tostring(self.__xml, xml_declaration=True))
    
    def xmlToFile(self,testname):
        self.__xml.write(testname + '.xml')