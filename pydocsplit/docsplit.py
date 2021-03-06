#!/usr/bin/env python

#Python implementation of the DocumentCloud's Docsplit utility
#http://github.com/anderser/pydocsplit
#
import os
import subprocess
import tempfile
from imageextract import ImageExtractor

#DOCSPLIT settings - change this to your docsplit location
DOCSPLIT_JAVA_ROOT = '/Users/anders/.gem/ruby/1.8/gems/docsplit-0.1.0'

#Not necessary to change these
DOCSPLIT_CLASSPATH = os.path.join (DOCSPLIT_JAVA_ROOT,
                                    "build") + os.pathsep + os.path.join(DOCSPLIT_JAVA_ROOT, "vendor", "'*'")

DOCSPLIT_LOGGING = "-Djava.util.logging.config.file=%s/vendor/logging.properties" % DOCSPLIT_JAVA_ROOT

DOCSPLIT_HEADLESS = "-Djava.awt.headless=true"


class ExtractionError(Exception):
    def __init__(self, cmd, msg):
        self.cmd = cmd
        self.msg = msg

class Docsplit:
    
    def __init__(self):
        pass
    
    def extract_pages(self, pdf, **kwargs):
        """
        Extracts each page of a pdf file and saves as separate pdf files
        
        Usage:
        >>>d = Docsplit()
        >>>d.extract_pages('/path/to/my/document.doc', output='/path/to/outputdir/', pages='1-2')
        """
        pdf = self.ensure_pdf(pdf)
        return self.run("org.documentcloud.ExtractPages", pdf, **kwargs)
    
    def extract_text(self, pdf, **kwargs):
        """
        Extracts text from a PDF
        The text is saved as a text file with same base name as your document in the 
        output dir specified. 
        
        Using the returntext=True returns the text extracted in addition
        to saving the text file. At the moment the returntext only works if all pages are 
        extracted i.e. there is no pages argument.
        
        Usage:
        >>>d = Docsplit()
        >>>d.extract_text('/path/to/my/pdffile.pdf', output='/path/to/outputdir/')
        >>>d.extract_text('/path/to/my/pdffile.pdf', output='/path/to/outputdir/', returntext=True)
        """
        
        returntext = False        
        if 'returntext' in kwargs:
            if kwargs['returntext'] == True:
                returntext = True
            kwargs.pop('returntext')
        
        basename, ext = os.path.splitext(os.path.basename(pdf))
        pdf = self.ensure_pdf(pdf)
        response = self.run("org.documentcloud.ExtractText", pdf, **kwargs)
        
        if returntext == True and response is not None and 'pages' not in kwargs:
            txtfile = open("%s.txt" % os.path.join(kwargs['output'], basename), 'r')
            response = txtfile.read()
            txtfile.close()
            
        return response
        
    def extract_pdf(self, doc, **kwargs):
        """
        Extracts pdf file from a document (i.e. .doc, .pdf, .rtf, .xls) using OpenOffice
        
        Usage:
        >>>d = Docsplit()
        >>>d.extract_pdf('/path/to/my/document.doc', output='/path/to/outputdir/')
        """
        
        filename, ext = os.path.splitext(os.path.basename(doc))
        
        return self.run("-jar %s/vendor/jodconverter/jodconverter-cli-2.2.2.jar %s %s/%s.pdf" 
                        %  (DOCSPLIT_JAVA_ROOT, doc, kwargs['output'], filename), '') 
    
    def extract_images(self, pdf, **kwargs):
        """
        Extracts each page of a pdf file and saves as images of given size and format
        
        Parameters:
        sizes: list of sizes i.e. ['500x', '250x']
        formats: list of formats i.e. ['jpg', 'png']
        pages (optional): list of pages either as list [1,2,5,6] or as a string in this format ['1-10']
        
        Usage:
        >>>d = Docsplit()
        >>>d.extract_images('/path/to/my/pdffile.pdf', output='/path/to/outputdir/', sizes=['500x', '250x'], formats=['png', 'jpg'], pages=[1,2,5,7])
        """
        pdf = self.ensure_pdf(pdf)
        i = ImageExtractor()
        return i.extract(pdf, **kwargs)
    
    def extract_meta(self, pdf, meta, **kwargs):
        """
        Extracts meta data from pdf file. Returns value of meta field as string
        Valid meta data fields:
        author, date, creator, keywords, producer, subject, title, length
        
        Usage:
        >>>d = Docsplit()
        >>>d.extract_meta('/path/to/my/pdffile.pdf', 'title')
        """
        pdf = self.ensure_pdf(pdf)
        return self.run("org.documentcloud.ExtractInfo %s" % meta, pdf, **kwargs)
    
    def kwargs_parse(self, kwargs):
        
        return ' '.join(["--%s %s" % (key, kwargs[key]) for key in kwargs])
    
    def ensure_pdf(self, doc):
        
        basename, ext = os.path.splitext(os.path.basename(doc))
        
        if ext.lower() == '.pdf':
            return doc
        else:
            tempdir = os.path.join(tempfile.gettempdir(), 'docsplit')
            self.extract_pdf(doc, output=tempdir)
            return "%s.pdf" % os.path.join(tempdir, basename)
        
    
    def run(self, command, pdf, **kwargs):
        
        args = self.kwargs_parse(kwargs)

        cmd = "java %s %s -cp %s %s %s %s 2>&1" % (DOCSPLIT_HEADLESS, DOCSPLIT_LOGGING, DOCSPLIT_CLASSPATH, 
                                                   command, args, pdf)

        try: 
            proc = subprocess.Popen('%s' % cmd, shell=True, stdout=subprocess.PIPE)
            
        except OsError, e:
            print e
        
        else: 
            if proc.wait() != 0:
                try:
                    raise ExtractionError(cmd, proc.communicate()[0])
                except ExtractionError, err:
                    print err.cmd, err.msg
                    return False
            else:
                return proc.communicate()[0]