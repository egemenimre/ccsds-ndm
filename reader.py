"""

"""
import re
class Tag:
    """
    This class is used for any XML tag. It takes two parameter: tag and line.
    User can reach
        the content (str) , 
        the attributes (dict) and 
        the attr (list) which is a list containing attribute names and attribute values of the tag.

    Attributes
    ----------
    tag: str
        correct form of the tag
    line: str
        a string that contains the tag and inner tags/content
    """


    def __init__(self,tag:str,line:str):
        self.line = line
        self.tag = tag

        # to get content, take the line from first occurunce of '>' to </tag>
        self.content = self.line[self.line.find('>')+1:re.search(f"</{tag}>".format(tag=self.tag),self.line).start()]
        
        self.attributes = {}

        # the list of the attributes
        # to get the attributes, replace content, <, >, <>, </> and spaces with empty string, then split the string by space 
        self.attr = self.line.replace(self.content,"").replace(self.tag,"").replace("<>","").replace("</>","").replace(">","").replace("<","").strip().split()

        # if there is one or more attribute
        if len(self.attr) >0:
            # for every string in self.attr
            for a in range(len(self.attr)):

                # split by "=" sign
                self.sp = self.attr[a].split("=")

                # then assign a new variable with the name of the attribute that has a value of attribute's value 
                self.attributes[self.sp[0]] = self.sp[1]
class Xml:
    """
    This class is used for a XML file. It takes one parameter: file_directory.
    
    User can reach
        by using openfile method,
            the file_content (str): purified form from spaces and the NewLine characters
        by using find_ method
            the all_tags (list): list of Tag class members
            the ltag_ind (list): list of tag's indexes of the form <tag> 
            the rtag_ind (list): list of tag's indexes of the form </tag> 
    Attributes
    ----------
    file_directory: str
        file directory of the XML file
    """
    def __init__(self,file_directory):
        self.file_directory = file_directory
    def openfile(self):
        """
        openfile method opens the file and purified the file content from spaces and NewLine characters.
        It does not take any parameter.
        """
        # open the file
        self.file = open(self.file_directory,"r+",encoding="utf8")
        # replace all spaces and \n's with empty string
        self.file_content = self.file.read().replace("    ","").replace("\n","")
    def closefile(self):
        """
        closefile method closes the file.
        It does not take any parameter.
        """
        self.file.close()
    def show(self):
        """
        show method prints the purified form of file content.
        It does not take ant parameter.
        """
        self.openfile()
        print(self.file_content)
        self.closefile()

    def find_(self,tag:str)->list:
        """
        find_ method finds all members of the given tag in file_content, then returns a list that contains Tags.
        
        Parameters
        ----------
        tag: str
            the correct form of the tag's name

        Raises
        ------
        Exception
            If not closed tag is found: Some of the tags may not be closed!
        Exception
            If the tag cannot be found: There is no {tag} tag.
        """
        # make sure self.tag is a string
        self.tag = str(tag)
        self.openfile()
        self.all_tags = []

        line_ = self.file_content
        
        # make a list of indexes of the opening tag
        # the tag name may be found in another tag's name. 
        # To prevent that, use regex and make sure after the tag's name, there will be no another letter or number but there will be a space/spaces
        self.ltag_ind = [m.start() for m in re.finditer('<'+self.tag+'([^a-zA-Z0-9].*?)>',line_)]

        # make a list of indexes of closing tag
        # to get the tag from the begining to the end, add 3 and length of the tag name 
        # (3 for / , > and index)
        self.rtag_ind = [m.start()+len(self.tag)+3 for m in re.finditer('</'+self.tag+'>', line_)]

        # check if tag exist and if the number of opening and closing tags are equal  
        if len(self.ltag_ind)>0 and len(self.rtag_ind)>0 and len(self.ltag_ind) == len(self.rtag_ind):
            for i in range(len(self.ltag_ind)):

                # for each found tag, make a Tag member and append to self.all_tags
                # to get each tag and it's content for each found tag, take self.file_content from opening tag index to closing tag index: line_[self.ltag_ind[i]:self.rtag_ind[i]]
                self.all_tags.append(Tag(self.tag, line_[self.ltag_ind[i]:self.rtag_ind[i]]))

        # if the number of opening and closing tags are not equal, raise an Exception
        elif len(self.ltag_ind) != len(self.rtag_ind):
            raise Exception("Some of the tags may not be closed!")

        # if there is no found tag, raise an Exception
        elif len(self.ltag_ind) <= 0 or len(self.rtag_ind)<=0:
            raise Exception(f"There is no {tag} tag".format(tag=self.tag))

        self.closefile()
        return self.all_tags

