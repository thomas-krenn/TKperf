'''
Created on Sep 26, 2014

@author: gschoenb
'''

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class Mail(object):
    '''
    Sending emails via local smtp.
    '''


    def __init__(self, subj, sender, rcpt):
        '''
        Constructor
        '''
        self.__msg = MIMEMultipart()
        self.__msg['Subject'] = subj
        self.__msg['From'] = sender
        self.__msgmsg['To'] = rcpt

    def addMsg(self, msg):
        msgText = MIMEText(msg, 'plain')
        self.__msg.attach(msgText)

    def addAttachment(self,att):
        msg.attach(MIMEText(file(att).read())