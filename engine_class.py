from telethon import TelegramClient
from telethon.tl.types import InputMessagesFilterDocument
import asyncio
from datetime import datetime
from dateutil import tz
from os import mkdir

loop = asyncio.get_event_loop()

def convertUtcDatetimeToIstString(utcDatetime, tzInfo):
    utc = datetime.strptime(str(utcDatetime).split('+')[0], '%Y-%m-%d %H:%M:%S')
    fromutc = utc.replace(tzinfo=tzInfo)
    return str(fromutc.astimezone(tz.tzlocal())).split('+')[0]

def readBytes(B):
    B = float(B)
    KB = float(1024)
    MB = float(KB ** 2) # 1,048,576
    GB = float(KB ** 3) # 1,073,741,824
    TB = float(KB ** 4) # 1,099,511,627,776

    if B < KB:
        return '{0} {1}'.format(B,'Bytes' if 0 == B > 1 else 'Byte')
    elif KB <= B < MB:
        return '{0:.2f} KB'.format(B / KB)
    elif MB <= B < GB:
        return '{0:.2f} MB'.format(B / MB)
    elif GB <= B < TB:
        return '{0:.2f} GB'.format(B / GB)
    elif TB <= B:
        return '{0:.2f} TB'.format(B / TB)

def string_form(string, group=3, char=''):
    return char.join(string[i:i+group] for i in range(0, len(string), group))

class Telegram(TelegramClient):

    def __init__(self, phoneNumber, sessionCode, api_id, api_hash):
        asyncio.set_event_loop(loop)
        try:
            mkdir("sessions/" + sessionCode)
        except FileExistsError:
            pass
        self.phoneNumber = phoneNumber
        self.client = TelegramClient("sessions/" + sessionCode + "/" +  phoneNumber, api_id, api_hash, loop=loop)
        loop.run_until_complete(self.client.connect())

        
    def send_code(self):
        try:
            loop.run_until_complete(self.client.sign_in(self.phoneNumber))
            return "true"
        except Exception as e:
            return str(e)
    
    def validiate_code(self, code):
        try:
            loop.run_until_complete(self.client.sign_in(code=code))
            return "true"
        except Exception as e:
            return str(e)

    def log_out(self):
        loop.run_until_complete(self.client.log_out())
        return True

    async def __get_files(self):
        files = {}
        for message in await self.client.get_messages('me', filter=InputMessagesFilterDocument, limit=None):
            fileName = message.document.attributes[-1].file_name
            if len(fileName) > 22:
                mobileFileName = string_form(fileName, group=18, char="\n")
            else:
                mobileFileName = fileName
            files[str(message.id)] = [fileName,
                                    readBytes(message.media.document.size),
                                    convertUtcDatetimeToIstString(message.date, message.date.tzinfo),
                                    message.media.document.mime_type, mobileFileName, message]
        return files
    
    def get_saved_files(self):
        return loop.run_until_complete(self.__get_files())

    def is_user_connected(self):
        return loop.run_until_complete(self.client.is_user_authorized())

    def delete_file(self, id):
        try:
            loop.run_until_complete(self.client.delete_messages('me', id))
            return "true"
        except Exception as e:
            return str(e)

    def upload_file(self, file):
        return loop.run_until_complete(self.client.send_file("me", file, force_document=True))

    def downloadFile(self, filedata):
        return loop.run_until_complete(self.client.download_file(filedata))



