'''
Created on Sep 26, 2014

@author: gschoenb
'''

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from os import path

class Mail(object):
    '''
    Sending emails via local smtp.
    '''

    def __init__(self, subj, sender, rcpt):
        '''
        Constructor
        '''
        self.__sender = sender
        self.__rcpt = rcpt
        self.__msg = MIMEMultipart()
        self.__msg['Subject'] = subj
        self.__msg['From'] = sender
        self.__msg['To'] = rcpt
        self.__smtp = smtplib.SMTP('mail.thomas-krenn.com')

    def addMsg(self, msg):
        msgText = MIMEText(msg, 'plain')
        self.__msg.attach(msgText)

    def addPDFAttachment(self,filename):
        fp=open(filename,'rb')
        att = MIMEApplication(fp.read(),_subtype="pdf")
        fp.close()
        name = path.basename(path.normpath(filename))
        att.add_header('Content-Disposition','attachment',filename=name)
        self.__msg.attach(att)

    def send(self):
        self.__smtp.sendmail(self.__sender, self.__rcpt, self.__msg.as_string())
        self.__smtp.quit()