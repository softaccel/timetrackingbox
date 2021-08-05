import serial
import struct


class RDM6300(object):
    """
    A class that implements tag reading for the RDM6300 module

    ...
    Attributes
    ----------
    START_CODE : hex byte
        The code each tag starts with
    
    END_CODE : hex byte
        The code each tag ends with

    __rfid_reader : serial object
        An object that deals with communication between Orange Pi and the RDM6300 module
        using the serial protocol
    
    __raw_tag_data : string
        A string containing the raw data on the read tag
    
    """

    START_CODE = 0x02
    END_CODE = 0x03
    
    __rfid_reader = None
    __raw_tag_data = None


    def __init__(self, serial_port = '/dev/ttyS0', baudRate = 9600):
        """
        Parameters
        ----------

        serial_port : string
            Serial port to read from
        
        baudRate : 9600
            Baudrate of the serial communication
        
        """

        self.__rfid_reader = serial.Serial(port = serial_port, baudrate = baudRate, bytesize = serial.EIGHTBITS, timeout = 1)


    def __del__(self):
        """
        Closes serial communication before the object is deleted

        """

        if (self.__rfid_reader != None) and (self.__rfid_reader.isOpen() == True):
            self.__rfid_reader.close()


    def __clear(self):
        while self.__rfid_reader.in_waiting:
            self.__rfid_reader.read()


    def __read(self):
        """
        Reads data from the serial port and tries to decode a tag

        Returns :
            True if the opperation was successful or false otherwise

        Raises :
            Exception if any error occurs
        
        """

        self.__raw_data = None
        
        tag = ''
        calculated_checksum = 0
        receivedData = []
        data_fragment = []
        index = 0
	
        while True:
            if self.__rfid_reader.in_waiting:
                data_fragment = self.__rfid_reader.read()

                if len(data_fragment) != 0:
                    if index == 0 or index == 13:
                        data_fragment = struct.unpack('@B', data_fragment)[0]
                    else:
                        tag += str(struct.unpack('@B', data_fragment)[0])

                        data_fragment = int(data_fragment, 16)

                    receivedData.append(data_fragment)
                    index += 1
                
                if index == 14:
                    if (receivedData[0] != self.START_CODE) or (receivedData[13] != self.END_CODE):
                        raise Exception('Invalid start/stop bytes!')

                    for i in range(1, 11, 2):
                        byte = (receivedData[i] << 4) | (receivedData[i + 1])

                        calculated_checksum ^= byte
                    
                    received_checksum = (receivedData[11] << 4) | receivedData[12]

                    if calculated_checksum != received_checksum:
                        raise Exception('Invalid checksum!')

                    self.__raw_tag_data = tag
                    self.__tag = receivedData
		    
                    return True
            else:
                yield False
        
        return False
    

    def readTag(self):
        """
        Keeps reading data until a valid tag is received

        Returns :
            True when the data has been successfully read or False if a KeyboardInterrupt canceled the operation
        
        """

        self.__read_gen = self.__read()
        self.reset()

    
    def done(self):
        if self.__raw_tag_data != None:
            return True

        try:
            if next(self.__read_gen) != True:
                return False
        
        except StopIteration as e:
            if e.value == True:
                return True
            
            self.readTag()
        
        return False
    

    def reset(self):
        self.__clear()
        self.__raw_tag_data = None
        self.__raw_data = None


    @property
    def rawTag(self):
        """
        Gets the raw tag in uppercase hex format without checksum.

        Returns:
            The raw tag (10 bytes)
        
        """
        
        return self.__raw_tag_data[0:10]
    

    @property
    def tagType(self):
        """
        Gets the type of read tag in hex format (first 4 bytes).
        
        Returns:
            The tag type
        
        """

        if self.__raw_tag_data != None:
            return hex(int(self.__raw_tag_data[0:4], 16))
        
        return None
    

    @property
    def tagID(self):
        """
        Gets the tag ID in decimal format, e.g. "0001234567".
        
        Returns:
            The tag ID
        
        """

        if self.__tag != None:
            return "000" + str(int(''.join([hex(l)[2:] for l in self.__tag[5: 11]]), 16))

        return None

